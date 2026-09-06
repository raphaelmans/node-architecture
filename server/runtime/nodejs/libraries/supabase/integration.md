# Supabase Integration

> Vendor-specific integration patterns for Supabase, including authentication, storage, and database access within the layered architecture.

Read [the data-access convention](./data-access.md) for current architecture ownership. The concrete auth and database examples here demonstrate a combined Supabase + Drizzle stack, not a mandatory ORM layer. Provider commands and APIs must be checked against matching official documentation before use.

> **For complete authentication implementation**, see [auth.md](./auth.md) which covers tRPC integration, user roles, Next.js Proxy, and the full registration flow.

## Overview

Supabase provides three main services used in this architecture:

| Service      | Purpose                                    | Layer                          | Documentation |
| ------------ | ------------------------------------------ | ------------------------------ | ------------- |
| **Auth**     | User authentication, sessions, magic links | Controller → Service/Use Case → Repository | [auth.md](./auth.md) |
| **Storage**  | Object/file storage with signed URLs       | Controller → Use Case → Provider adapter | Below |
| **Database** | Direct data API/functions or selected Drizzle adapter | Repository | [Data access](./data-access.md) |

```text
framework adapter
  -> AuthController
       -> AuthService -> IAuthRepository -> Supabase Auth adapter
  -> UpdateProfileImageController
       -> UpdateProfileImageUseCase
            +-> ProfileService -> IProfileRepository -> Drizzle/PostgreSQL
            +-> ObjectStorage -> Supabase Storage adapter
```

---

## Authentication

> **Complete documentation**: See [auth.md](./auth.md) for the full authentication implementation including:
> - **PKCE flow** for magic links and email verification
> - tRPC context and session extraction
> - User roles table with Drizzle
> - Registration use case with multi-service orchestration
> - Next.js Proxy for route protection
> - Request-scoped factory patterns
> - Supabase Dashboard configuration (Site URL, email templates)

### Quick Summary

This implementation uses **PKCE flow** (not implicit flow) for magic links:

| Flow | Route | Method |
|------|-------|--------|
| Magic Link | `/auth/confirm?token_hash=xxx&type=magiclink` | `verifyOtp()` |
| Signup | `/auth/confirm?token_hash=xxx&type=signup` | `verifyOtp()` |
| Recovery | `/auth/confirm?token_hash=xxx&type=recovery` | `verifyOtp()` |
| OAuth | `/auth/callback?code=xxx` | `exchangeCodeForSession()` |

```typescript
// Inner request-scoped service factory (needs cookies)
function makeAuthService(cookies: CookieMethodsServer) {
  const client = createClient(env.SUPABASE_URL, env.SUPABASE_PUBLISHABLE_KEY, cookies);
  return new AuthService(
    new AuthRepository(client),
    getContainer().appLogger,
  );
}

// Public framework adapters resolve this outer factory.
export function makeLoginWithMagicLinkController(cookies: CookieMethodsServer) {
  return new LoginWithMagicLinkController(makeAuthService(cookies));
}

// In tRPC router
loginWithMagicLink: publicProcedure
  .input(MagicLinkInputSchema)
  .mutation(async ({ input, ctx }) => {
    const result = await makeLoginWithMagicLinkController(ctx.cookies)
      .execute(input, { origin: ctx.origin });
    const response = MagicLinkResponseSchema.parse(result);
    return wrapResponse(response);
  }),
```

**Important Supabase Dashboard Settings:**
- **Site URL** must be set to your production domain (used in `{{ .SiteURL }}` email template variable)
- **Email templates** should use: `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=magiclink`

---

## FormData + Upload Boundary (Next.js)

Supabase storage integrations commonly receive files from FormData flows (for example avatar/logo/proof uploads).

For transport-layer conventions (`FormData` routing, batching split, `zod-form-data` parsing), use:

- [Next.js FormData Transport](../../metaframeworks/nextjs/formdata-transport.md)

This Supabase document remains focused on storage adapter and bucket/policy integration concerns.

---

## Object Storage

### Storage Interface (Port)

Define a vendor-agnostic interface in the kernel or shared layer:

```typescript
// shared/kernel/storage.ts

export interface ObjectStorage {
  uploadFile(file: Blob, path: string): Promise<void>;
  getSignedUrl(path: string): Promise<string>;
  getPublicUrl(path: string): string;
  downloadBlob(path: string): Promise<Blob>;
  deleteFile(path: string): Promise<void>;
}
```

### Supabase Storage Adapter

```typescript
// shared/infra/supabase/object-storage.ts

import { createClient } from "./create-client";
import type { ObjectStorage } from "@/shared/kernel/storage";
import { BadGatewayError } from "@/shared/kernel/errors";

class ObjectStorageProviderError extends BadGatewayError {
  readonly code = "OBJECT_STORAGE_PROVIDER_FAILED";

  constructor(operation: string, details?: Record<string, unknown>) {
    super("Object storage provider request failed", { operation, ...details });
  }
}

function storageFailure(
  operation: string,
  error?: { message?: string },
): ObjectStorageProviderError {
  return new ObjectStorageProviderError(operation, {
    providerMessage: error?.message,
  });
}

export class SupabaseObjectStorage implements ObjectStorage {
  constructor(
    private client: ReturnType<typeof createClient>,
    private bucket: string,
    private signedURLExpSeconds: number = 24 * 60 * 60,
  ) {}

  async uploadFile(file: Blob, path: string): Promise<void> {
    const { error } = await this.client.storage
      .from(this.bucket)
      .upload(path, file, { upsert: true });

    if (error) throw storageFailure("upload", error);
  }

  async getSignedUrl(path: string): Promise<string> {
    const { data, error } = await this.client.storage
      .from(this.bucket)
      .createSignedUrl(path, this.signedURLExpSeconds);

    if (error) throw storageFailure("create_signed_url", error);
    if (!data?.signedUrl) throw storageFailure("create_signed_url");

    return data.signedUrl;
  }

  getPublicUrl(path: string): string {
    const { data } = this.client.storage.from(this.bucket).getPublicUrl(path);
    return data.publicUrl;
  }

  async downloadBlob(path: string): Promise<Blob> {
    const { data, error } = await this.client.storage
      .from(this.bucket)
      .download(path);

    if (error) throw storageFailure("download", error);
    if (!data) throw storageFailure("download");

    return data;
  }

  async deleteFile(path: string): Promise<void> {
    const { error } = await this.client.storage
      .from(this.bucket)
      .remove([path]);

    if (error) throw storageFailure("delete", error);
  }
}
```

### Storage Client (Path-Scoped Operations)

```typescript
// shared/infra/services/storage-client.ts

import type { ObjectStorage } from "@/shared/kernel/storage";

const PATHS = {
  IMAGES: "images/",
  PROFILE_IMAGES: "profile-images/",
  COMPANY_LOGOS: "company-logos/",
  DOCUMENTS: "documents/",
} as const;

type StoragePath = (typeof PATHS)[keyof typeof PATHS];

class PathScopedOperations {
  constructor(
    private storage: ObjectStorage,
    private basePath: StoragePath,
  ) {}

  async uploadFile(file: Blob, filename: string): Promise<void> {
    return this.storage.uploadFile(file, this.basePath + filename);
  }

  getPublicUrl(filename: string): string {
    return this.storage.getPublicUrl(this.basePath + filename);
  }

  async getSignedUrl(filename: string): Promise<string> {
    return this.storage.getSignedUrl(this.basePath + filename);
  }

  async downloadBlob(filename: string): Promise<Blob> {
    return this.storage.downloadBlob(this.basePath + filename);
  }

  async deleteFile(filename: string): Promise<void> {
    return this.storage.deleteFile(this.basePath + filename);
  }
}

export class StorageClient {
  constructor(private storage: ObjectStorage) {}

  images() {
    return new PathScopedOperations(this.storage, PATHS.IMAGES);
  }

  profileImages() {
    return new PathScopedOperations(this.storage, PATHS.PROFILE_IMAGES);
  }

  companyLogos() {
    return new PathScopedOperations(this.storage, PATHS.COMPANY_LOGOS);
  }

  documents() {
    return new PathScopedOperations(this.storage, PATHS.DOCUMENTS);
  }
}
```

### Usage Pattern

```typescript
// In a use case (external storage is a side effect)
const storage = makeStorageClient();

// Upload profile image
await storage.profileImages().uploadFile(imageBlob, `${userId}.jpg`);

// Get public URL
const url = storage.profileImages().getPublicUrl(`${userId}.jpg`);

// Get signed URL (for private buckets)
const signedUrl = await storage.profileImages().getSignedUrl(`${userId}.jpg`);
```

---

## Database (Drizzle + Supabase)

### Connection Setup

```typescript
// shared/infra/db/drizzle.ts

import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const connectionString = process.env.DATABASE_URL!;

const client = postgres(connectionString);
export const db = drizzle(client, { schema });

export type AppDatabase = typeof db;
```

### Repository Pattern

This example selects Drizzle for database operations. A Supabase-only repository instead calls the SDK/data API behind the same application-owned contract; atomic multi-write methods use a database function. Map provider rows to application records in either implementation.

```typescript
// modules/profile/repositories/profile.repository.ts

import { eq } from "drizzle-orm";
import { profiles } from "@/shared/infra/db/schema";
import type { AppDatabase } from "@/shared/infra/db/drizzle";
import type { TransactionOptions } from "@/shared/kernel/transaction";
import type { DrizzleTransaction } from "@/shared/infra/db/types";

export class ProfileRepo {
  constructor(private db: AppDatabase) {}

  private getClient(options?: TransactionOptions): AppDatabase | DrizzleTransaction {
    return (options?.tx as unknown as DrizzleTransaction) ?? this.db;
  }

  async getById(id: string, options?: TransactionOptions) {
    const result = await this.getClient(options).query.profiles.findFirst({
      where: eq(profiles.id, id),
    });
    return result ?? null;
  }

  async getByUserId(userId: string, options?: TransactionOptions) {
    const result = await this.getClient(options)
      .select()
      .from(profiles)
      .where(eq(profiles.userId, userId))
      .limit(1);

    return result[0] ?? null;
  }

  async create(data: InsertProfile, options?: TransactionOptions) {
    const [result] = await this.getClient(options)
      .insert(profiles)
      .values(data)
      .returning();

    return result;
  }

  async update(id: string, data: Partial<UpdateProfile>, options?: TransactionOptions) {
    const [result] = await this.getClient(options)
      .update(profiles)
      .set(data)
      .where(eq(profiles.id, id))
      .returning();

    return result;
  }
}
```

---

## Request-Scoped Composition

Keep global infrastructure in the shared container, but create cookie-bound Supabase clients through module factories for each request. Do not pass a `ServiceProvider`/service locator into application code.

```typescript
// modules/auth/factories/auth.factory.ts

function makeAuthService(cookies: CookieMethodsServer): IAuthService {
  const client = createRequestSupabaseClient(cookies);
  const repository: IAuthRepository = new AuthRepository(client);
  return new AuthService(repository, getContainer().appLogger);
}

// modules/profile/factories/profile-image.factory.ts

export function makeUpdateProfileImageUseCase(
  cookies: CookieMethodsServer,
): UpdateProfileImageUseCase {
  const storage: ObjectStorage = new SupabaseObjectStorage(
    createRequestSupabaseClient(cookies),
    "default-bucket",
  );

  return new UpdateProfileImageUseCase(
    makeProfileService(),
    storage,
    getContainer().appLogger,
  );
}

export function makeUpdateProfileImageController(
  cookies: CookieMethodsServer,
): IUpdateProfileImageController {
  return new UpdateProfileImageController(
    makeUpdateProfileImageUseCase(cookies),
  );
}
```

Privileged service-role clients use a separate server-only factory and are injected only into narrowly scoped admin/worker adapters. Never expose them through a generic locator.

---

## Auth-Storage Relationship

Storage plus database mutation is multi-system orchestration, so a use case owns it. The profile service remains unaware of Supabase and storage SDKs.

```typescript
// modules/profile/use-cases/update-profile-image.use-case.ts

export class UpdateProfileImageUseCase {
  constructor(
    private readonly profileService: IProfileService,
    private readonly storage: ObjectStorage,
    private readonly logger: AppLogger,
  ) {}

  async execute(
    userId: string,
    imageFile: Blob,
  ): Promise<string> {
    const profile = await this.profileService.findByUserId(userId);
    if (!profile) {
      throw new ProfileNotFoundError(userId);
    }

    const path = `profile-images/${profile.id}.jpg`;
    await this.storage.uploadFile(imageFile, path);

    const imageUrl = this.storage.getPublicUrl(path);
    try {
      await this.profileService.setProfileImage(profile.id, imageUrl);
    } catch (error) {
      try {
        await this.storage.deleteFile(path);
      } catch (compensationError) {
        this.logger.error(
          {
            err: compensationError,
            "otel.event.name": "profile.image.compensation_failed",
            [APP_ATTRIBUTES.targetUserId]: userId,
          },
          "Profile image compensation failed",
        );
      }
      throw error;
    }

    return imageUrl;
  }
}
```

This is a compensating workflow, not a database transaction spanning Supabase Storage and PostgreSQL. Add an orphan-object reconciliation job if failed deletion cannot be ignored.

---

## Bucket Configuration

### Supabase Dashboard Setup

1. **Create bucket** in Supabase Dashboard → Storage
2. **Configure policies** for RLS:

```sql
-- Allow authenticated users to upload to their own folder
CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'default-bucket' AND
  (storage.foldername(name))[1] = 'profile-images' AND
  (storage.foldername(name))[2] = auth.uid()::text
);

-- Allow public read access to profile images
CREATE POLICY "Public profile images"
ON storage.objects FOR SELECT
TO public
USING (
  bucket_id = 'default-bucket' AND
  (storage.foldername(name))[1] = 'profile-images'
);
```

### Privileged Secret-Key Client

When using `SUPABASE_SECRET_KEY`, RLS is bypassed. Keep this client in a
separate, narrowly named server-only factory. It is useful for:

- Background jobs
- Admin operations
- Server-side uploads

---

## Environment Variables

```bash
# .env.local

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...

# Database (can be Supabase connection string)
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

Legacy `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY` values may still
exist in older projects, but new documentation and factories use the
publishable/secret key names consistently.

---

## Checklist

### Authentication Setup Checks

- [ ] Create Supabase client with cookie handling
- [ ] Implement AuthRepo with auth methods
- [ ] Implement AuthService
- [ ] Wire request-scoped auth dependencies in module factories

### Storage

- [ ] Define `ObjectStorage` interface (vendor-agnostic)
- [ ] Implement `SupabaseObjectStorage` adapter
- [ ] Optionally add a path-scoped storage adapter when repeated prefixes justify it
- [ ] Configure bucket and RLS policies
- [ ] Wire storage adapters into use cases through module factories

### Database

- [ ] Select direct Supabase access or Drizzle for each repository; no ORM is required for direct access
- [ ] Keep provider-generated row types inside adapters and return application records
- [ ] Use one database function for an atomic data-API operation; test preconditions, rollback, and replay

### Integration

- [ ] Request-scoped factories accept `CookieMethodsServer`
- [ ] Auth and Storage use Supabase client
- [ ] Database uses the explicitly selected adapter; mixed HTTP and SQL calls do not share a transaction
- [ ] User-scoped clients are the ordinary path; privileged keys appear only in narrowly authorized server-only factories

---

## Architecture Alignment

| Core Principle            | Supabase Implementation                       |
| ------------------------- | --------------------------------------------- |
| **Explicit DI**           | Module factories create request-scoped instances |
| **Interface abstraction** | `ObjectStorage` interface hides Supabase      |
| **Repository pattern**    | AuthRepo, ProfileRepo encapsulate data access |
| **Application/domain**    | Use cases orchestrate providers; services own one domain |
| **Atomicity**             | Real shared transaction for Drizzle or a purpose-specific Supabase database function |
