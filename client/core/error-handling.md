# Error Handling

> Conventions for handling errors: toasts, form errors, and error boundaries.

## Error Types

| Error Type        | Source              | Handling                 |
| ----------------- | ------------------- | ------------------------ |
| Validation errors | Zod/react-hook-form | Field-level messages     |
| API errors        | tRPC mutations      | Toast or form root error |
| Query errors      | tRPC queries        | Error UI or retry        |
| Unexpected errors | Runtime exceptions  | Error boundary           |

## Error Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Error Occurs                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   Form Validation       │     │      API/Runtime Error      │
│   (Zod + RHF)           │     │                             │
└───────────┬─────────────┘     └──────────────┬──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│  FormMessage per field  │     │  Is it recoverable?         │
│  StandardFormError      │     └──────────────┬──────────────┘
└─────────────────────────┘                    │
                                   ┌───────────┴───────────┐
                                   ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Yes: Toast     │     │  No: Error      │
                        │  or form.setError│     │  Boundary       │
                        └─────────────────┘     └─────────────────┘
```

## Form Validation Errors

### Field-Level Errors

Handled automatically by `StandardForm` components:

```typescript
<StandardFormInput<FormType>
  name='email'
  label='Email'
/>
// FormMessage displays validation error automatically
```

### Root-Level Errors

For API or business logic errors:

```typescript
// Display
<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />  {/* Renders errors.root.message */}
  {/* fields */}
</StandardFormProvider>

// Set error
form.setError('root', { message: 'Email already exists' })
```

### Validation Error Handler

```typescript
const onError = (errors: FieldErrors<FormType>) => {
  // Optional: Show toast with all errors
  const messages = Object.values(errors)
    .map(e => e?.message)
    .filter(Boolean)
    .join(', ')

  toast({
    description: messages,
    variant: 'destructive',
  })
}

<StandardFormProvider form={form} onSubmit={onSubmit} onError={onError}>
```

## API Errors (Toast Pattern)

### useCatchErrorToast Hook

```typescript
// src/common/hooks.ts

export function useCatchErrorToast() {
  const { toast } = useToast();

  return async <T>(
    fn: () => Promise<T>,
    options?: { description?: string },
  ): Promise<T | undefined> => {
    try {
      const result = await fn();
      if (options?.description) {
        toast({ description: options.description });
      }
      return result;
    } catch (error) {
      toast({
        description:
          error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
      return undefined;
    }
  };
}
```

### Usage in Forms

```typescript
const catchErrorToast = useCatchErrorToast();

const onSubmit = async (data: FormType) => {
  return catchErrorToast(
    async () => {
      await mutation.mutateAsync(data);
      await trpcUtils.entity.invalidate();
      router.push(appRoutes.success);
    },
    { description: "Saved successfully!" },
  );
};
```

### Usage with Form Root Error

For errors that should display in the form (not just toast):

```typescript
const onSubmit = async (data: FormType) => {
  try {
    await mutation.mutateAsync(data);
    toast({ description: "Saved successfully!" });
    router.push(appRoutes.success);
  } catch (error) {
    if (error instanceof TRPCClientError) {
      // Show in form
      form.setError("root", { message: error.message });
    } else {
      // Fallback to toast
      toast({
        description: "An unexpected error occurred",
        variant: "destructive",
      });
    }
  }
};
```

## Query Errors

### Basic Error Handling

```typescript
const profileQuery = trpc.profile.get.useQuery()

if (profileQuery.isError) {
  return <ErrorDisplay error={profileQuery.error} />
}
```

### Custom Retry Logic

```typescript
const profileQuery = trpc.profile.get.useQuery(undefined, {
  retry: (attempt, error) => {
    // Don't retry on 404
    if (isTRPCNotFoundError(error)) return false;
    // Retry up to 3 times for other errors
    return attempt <= 3;
  },
});
```

### Error Helper

```typescript
// src/common/utils.ts

import { TRPCClientError } from "@trpc/client";

export function isTRPCNotFoundError(error: unknown): boolean {
  return error instanceof TRPCClientError && error.data?.code === "NOT_FOUND";
}

export function isTRPCUnauthorizedError(error: unknown): boolean {
  return (
    error instanceof TRPCClientError && error.data?.code === "UNAUTHORIZED"
  );
}
```

## Error Boundaries

### Basic Error Boundary

```typescript
// src/components/error-boundary.tsx
'use client'

import { Component, ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Report to error tracking service (Sentry, etc.)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className='flex flex-col items-center justify-center p-8'>
          <h2 className='text-lg font-semibold'>Something went wrong</h2>
          <p className='text-muted-foreground mb-4'>
            {this.state.error?.message}
          </p>
          <Button onClick={() => this.setState({ hasError: false })}>
            Try again
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}
```

### Next.js Error Boundary (App Router)

```typescript
// src/app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className='flex flex-col items-center justify-center min-h-screen'>
      <h2 className='text-2xl font-bold mb-4'>Something went wrong</h2>
      <p className='text-muted-foreground mb-4'>{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

### Route-Level Error Boundary

```typescript
// src/app/(authenticated)/dashboard/error.tsx
'use client'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  return (
    <div className='p-8'>
      <h2>Failed to load dashboard</h2>
      <Button onClick={reset}>Retry</Button>
    </div>
  )
}
```

## Toast Component

### Setup

```typescript
// src/components/ui/toaster.tsx
import { useToast } from '@/hooks/use-toast'
import { Toast, ToastProvider, ToastViewport } from '@/components/ui/toast'

export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider>
      {toasts.map(({ id, title, description, action, ...props }) => (
        <Toast key={id} {...props}>
          {title && <ToastTitle>{title}</ToastTitle>}
          {description && <ToastDescription>{description}</ToastDescription>}
          {action}
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  )
}
```

### Usage

```typescript
const { toast } = useToast();

// Success
toast({ description: "Profile saved successfully!" });

// Error
toast({
  description: "Failed to save profile",
  variant: "destructive",
});

// With title
toast({
  title: "Error",
  description: "Something went wrong",
  variant: "destructive",
});
```

## Error Display Component

```typescript
// src/components/error-display.tsx

interface ErrorDisplayProps {
  error: Error | null
  title?: string
  retry?: () => void
}

export function ErrorDisplay({ error, title, retry }: ErrorDisplayProps) {
  if (!error) return null

  return (
    <div className='rounded-lg border border-destructive/50 bg-destructive/10 p-4'>
      <h3 className='font-semibold text-destructive'>
        {title ?? 'Error'}
      </h3>
      <p className='text-sm text-destructive/80 mt-1'>
        {error.message}
      </p>
      {retry && (
        <Button
          variant='outline'
          size='sm'
          onClick={retry}
          className='mt-3'
        >
          Try again
        </Button>
      )}
    </div>
  )
}
```

## Conventions Summary

| Error Type         | Handling Method                                    |
| ------------------ | -------------------------------------------------- |
| Field validation   | `FormMessage` (automatic)                          |
| API error (form)   | `form.setError('root', ...)` + `StandardFormError` |
| API error (action) | `useCatchErrorToast`                               |
| Query error        | `isError` check + `ErrorDisplay`                   |
| Unexpected error   | Error boundary                                     |

## Checklist

- [ ] Form fields display validation errors via `FormMessage`
- [ ] `StandardFormError` placed in forms for root errors
- [ ] API errors use `useCatchErrorToast` or `form.setError`
- [ ] Query errors handled with `isError` check
- [ ] Route-level `error.tsx` files for unexpected errors
- [ ] Toast provider in root layout
- [ ] Error tracking integration (Sentry, etc.)
