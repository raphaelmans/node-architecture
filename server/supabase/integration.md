# Supabase Integration

> Vendor-specific integration patterns for Supabase, including authentication, storage, and database access within the layered architecture.

> **For complete authentication implementation**, see [auth.md](./auth.md) which covers tRPC integration, user roles, Next.js middleware, and the full registration flow.

## Overview

Supabase provides three main services used in this architecture:

| Service      | Purpose                                    | Layer                          | Documentation |
| ------------ | ------------------------------------------ | ------------------------------ | ------------- |
| **Auth**     | User authentication, sessions, magic links | Repository → Service → Use Case | [auth.md](./auth.md) |
| **Storage**  | Object/file storage with signed URLs       | Repository (adapter) → Service | Below |
| **Database** | PostgreSQL via Drizzle ORM                 | Repository                     | Below |

```
┌─────────────────────────────────────────────────────────────────┐
│                         Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ AuthService  │  │ ProfileSvc   │  │ ObjectStorageClient  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
┌─────────┼─────────────────┼─────────────────────┼───────────────┐
│         │           Repository Layer            │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌─────────▼────────────┐   │
│  │   AuthRepo   │  │  ProfileRepo │  │ SupabaseObjectStorage│   │
│  │ (Supabase)   │  │  (Drizzle)   │  │      (Adapter)       │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐
   │  Supabase   │   │  PostgreSQL │   │   Supabase Storage  │
   │    Auth     │   │  (Drizzle)  │   │       Bucket        │
   └─────────────┘   └─────────────┘   └─────────────────────┘
```

---

## Authentication

> **Complete documentation**: See [auth.md](./auth.md) for the full authentication implementation including:
> - tRPC context and session extraction
> - User roles table with Drizzle
> - Registration use case with multi-service orchestration
> - Next.js middleware for route protection
> - Request-scoped factory patterns

### Quick Summary

```typescript
// Request-scoped factories (need cookies)
export function makeAuthService(cookies: CookieMethodsServer) {
  const client = createClient(env.SUPABASE_URL, env.SUPABASE_SECRET_KEY, cookies);
  return new AuthService(new AuthRepository(client));
}

// In tRPC router
login: publicProcedure
  .input(LoginSchema)
  .mutation(async ({ input, ctx }) => {
    const authService = makeAuthService(ctx.cookies);
    return authService.signIn(input.email, input.password);
  }),
```

---

## Object Storage

### Storage Interface (Port)

Define a vendor-agnostic interface in the kernel or shared layer:

```typescript
// shared/kernel/storage.ts

export interface ObjectStorage {
  uploadFile(file: Blob, path: string): Promise<void>;
  getSignedURL(path: string): Promise<string>;
  getPublicURL(path: string): string;
  downloadBlob(path: string): Promise<Blob>;
  deleteFile(path: string): Promise<void>;
}
```

### Supabase Storage Adapter

```typescript
// shared/infra/supabase/object-storage.ts

import { createClient } from "./create-client";
import type { ObjectStorage } from "@/shared/kernel/storage";

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

    if (error) throw error;
  }

  async getSignedURL(path: string): Promise<string> {
    const { data, error } = await this.client.storage
      .from(this.bucket)
      .createSignedUrl(path, this.signedURLExpSeconds);

    if (error) throw error;
    if (!data?.signedUrl) throw new Error("Failed to get signed URL");

    return data.signedUrl;
  }

  getPublicURL(path: string): string {
    const { data } = this.client.storage.from(this.bucket).getPublicUrl(path);
    return data.publicUrl;
  }

  async downloadBlob(path: string): Promise<Blob> {
    const { data, error } = await this.client.storage
      .from(this.bucket)
      .download(path);

    if (error) throw error;
    if (!data) throw new Error("Failed to download file");

    return data;
  }

  async deleteFile(path: string): Promise<void> {
    const { error } = await this.client.storage
      .from(this.bucket)
      .remove([path]);

    if (error) throw error;
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

  getPublicURL(filename: string): string {
    return this.storage.getPublicURL(this.basePath + filename);
  }

  async getSignedURL(filename: string): Promise<string> {
    return this.storage.getSignedURL(this.basePath + filename);
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

  Images() {
    return new PathScopedOperations(this.storage, PATHS.IMAGES);
  }

  ProfileImages() {
    return new PathScopedOperations(this.storage, PATHS.PROFILE_IMAGES);
  }

  CompanyLogos() {
    return new PathScopedOperations(this.storage, PATHS.COMPANY_LOGOS);
  }

  Documents() {
    return new PathScopedOperations(this.storage, PATHS.DOCUMENTS);
  }
}
```

### Usage Pattern

```typescript
// In service or use case
const storage = makeStorageClient();

// Upload profile image
await storage.ProfileImages().uploadFile(imageBlob, `${userId}.jpg`);

// Get public URL
const url = storage.ProfileImages().getPublicURL(`${userId}.jpg`);

// Get signed URL (for private buckets)
const signedUrl = await storage.ProfileImages().getSignedURL(`${userId}.jpg`);
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

Repositories use Drizzle, not the Supabase client, for database operations:

```typescript
// modules/profile/repositories/profile.repository.ts

import { eq } from "drizzle-orm";
import { profiles } from "@/shared/infra/db/schema";
import type { AppDatabase } from "@/shared/infra/db/drizzle";
import type { Tx } from "@/shared/kernel/transaction";

export class ProfileRepo {
  constructor(private db: AppDatabase) {}

  async getById(id: string, tx?: Tx) {
    const result = await (tx ?? this.db).query.profiles.findFirst({
      where: eq(profiles.id, id),
    });
    return result ?? null;
  }

  async getByUserId(userId: string, tx?: Tx) {
    const result = await (tx ?? this.db)
      .select()
      .from(profiles)
      .where(eq(profiles.userId, userId))
      .limit(1);

    return result[0] ?? null;
  }

  async create(data: InsertProfile, tx?: Tx) {
    const [result] = await (tx ?? this.db)
      .insert(profiles)
      .values(data)
      .returning();

    return result;
  }

  async update(id: string, data: Partial<UpdateProfile>, tx?: Tx) {
    const [result] = await (tx ?? this.db)
      .update(profiles)
      .set(data)
      .where(eq(profiles.id, id))
      .returning();

    return result;
  }
}
```

---

## Service Provider (Factory)

The service provider wires up all Supabase-dependent services:

```typescript
// shared/infra/container.ts

import { CookieMethodsServer } from "@supabase/ssr";
import { createClient } from "./supabase/create-client";
import { SupabaseObjectStorage } from "./supabase/object-storage";
import { StorageClient } from "./services/storage-client";
import { AuthRepo } from "@/modules/auth/repositories/auth.repository";
import { AuthService } from "@/modules/auth/services/auth.service";
import { ProfileRepo } from "@/modules/profile/repositories/profile.repository";
import { ProfileService } from "@/modules/profile/services/profile.service";
import db from "./db/drizzle";
import { env } from "@/shared/env";

const SIGNED_URL_EXPIRY = 24 * 60 * 60; // 24 hours

export class ServiceProvider {
  private sbClient?: ReturnType<typeof createClient>;
  private dbInstance = db;

  // Cached instances
  private authRepo?: AuthRepo;
  private authService?: AuthService;
  private profileRepo?: ProfileRepo;
  private profileService?: ProfileService;
  private objectStorage?: StorageClient;

  constructor(private cookies: CookieMethodsServer) {}

  // Supabase client (for auth + storage)
  private sb() {
    if (!this.sbClient) {
      this.sbClient = createClient(
        env.SUPABASE_URL,
        env.SUPABASE_SERVICE_ROLE_KEY,
        this.cookies,
      );
    }
    return this.sbClient;
  }

  // Auth
  AuthRepo() {
    if (!this.authRepo) {
      this.authRepo = new AuthRepo(this.sb());
    }
    return this.authRepo;
  }

  AuthService() {
    if (!this.authService) {
      this.authService = new AuthService(this.AuthRepo());
    }
    return this.authService;
  }

  // Profile (uses Drizzle, not Supabase client)
  ProfileRepo() {
    if (!this.profileRepo) {
      this.profileRepo = new ProfileRepo(this.dbInstance);
    }
    return this.profileRepo;
  }

  ProfileService() {
    if (!this.profileService) {
      this.profileService = new ProfileService(this.ProfileRepo());
    }
    return this.profileService;
  }

  // Object Storage
  ObjectStorage() {
    if (!this.objectStorage) {
      this.objectStorage = new StorageClient(
        new SupabaseObjectStorage(
          this.sb(),
          "default-bucket",
          SIGNED_URL_EXPIRY,
        ),
      );
    }
    return this.objectStorage;
  }
}
```

---

## Auth-Storage Relationship

Storage operations often require authentication context:

```typescript
// Example: Upload profile image (requires authenticated user)

export class ProfileService {
  constructor(
    private profileRepo: ProfileRepo,
    private storage: StorageClient,
    private transactionManager: TransactionManager,
  ) {}

  async uploadProfileImage(
    userId: string,
    imageFile: Blob,
    ctx?: RequestContext,
  ): Promise<string> {
    // 1. Verify user exists
    const profile = await this.profileRepo.getByUserId(userId, ctx?.tx);
    if (!profile) {
      throw new ProfileNotFoundError(userId);
    }

    // 2. Upload to storage
    const filename = `${profile.id}.jpg`;
    await this.storage.ProfileImages().uploadFile(imageFile, filename);

    // 3. Update profile with image URL
    const imageUrl = this.storage.ProfileImages().getPublicURL(filename);
    await this.profileRepo.update(
      profile.id,
      { profileImageUrl: imageUrl },
      ctx?.tx,
    );

    return imageUrl;
  }
}
```

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

### Service Role Bypass

When using `SUPABASE_SERVICE_ROLE_KEY`, RLS is bypassed. This is useful for:

- Background jobs
- Admin operations
- Server-side uploads

---

## Environment Variables

```bash
# .env.local

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Database (can be Supabase connection string)
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

---

## Checklist

### Authentication

- [ ] Create Supabase client with cookie handling
- [ ] Implement AuthRepo with auth methods
- [ ] Implement AuthService
- [ ] Wire in ServiceProvider

### Storage

- [ ] Define `ObjectStorage` interface (vendor-agnostic)
- [ ] Implement `SupabaseObjectStorage` adapter
- [ ] Create `StorageClient` with path-scoped operations
- [ ] Configure bucket and RLS policies
- [ ] Wire in ServiceProvider

### Database

- [ ] Set up Drizzle with Supabase connection string
- [ ] Generate types from Supabase schema
- [ ] Repositories use Drizzle (not Supabase client)

### Integration

- [ ] ServiceProvider accepts `CookieMethodsServer`
- [ ] Auth and Storage use Supabase client
- [ ] Database uses Drizzle client
- [ ] Service role key for server-side operations

---

## Architecture Alignment

| Core Principle            | Supabase Implementation                       |
| ------------------------- | --------------------------------------------- |
| **Explicit DI**           | ServiceProvider creates all instances         |
| **Interface abstraction** | `ObjectStorage` interface hides Supabase      |
| **Repository pattern**    | AuthRepo, ProfileRepo encapsulate data access |
| **Service layer**         | Business logic in services, not repos         |
| **Transaction context**   | Drizzle repos accept `tx` parameter           |
