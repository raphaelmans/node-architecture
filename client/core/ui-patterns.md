# UI Patterns

> Conventions for UI components using shadcn/ui, Tailwind CSS, and component separation.

## Component Hierarchy

```
src/components/
├── ui/                    # Layer 1: Primitives (shadcn/ui)
│   ├── button.tsx
│   ├── input.tsx
│   ├── form.tsx
│   └── ...
├── form/                  # Layer 2: StandardForm components
│   ├── StandardFormProvider.tsx
│   ├── StandardFormInput.tsx
│   └── ...
└── custom-ui/             # Layer 3: Composed business components
    ├── data-table.tsx
    └── ...

src/features/<feature>/components/
├── <feature>-form.tsx         # Business component
└── <feature>-form-fields.tsx  # Presentation components
```

## Layer Definitions

### UI Primitives (shadcn/ui)

**Location:** `src/components/ui/`

- Direct shadcn/ui components
- Built on Radix UI
- Generic, reusable across any project
- No business logic

### StandardForm Components

**Location:** `src/components/form/`

- Form-specific abstractions
- Built on react-hook-form + shadcn/ui
- Reduce form boilerplate
- See [Forms](./forms.md) for details

### Custom UI Components

**Location:** `src/components/custom-ui/`

- Composed from primitives
- Application-specific styling
- Reusable patterns (data tables, cards, etc.)
- Still no feature-specific business logic

### Feature Components

**Location:** `src/features/<feature>/components/`

- Feature-specific UI
- May contain business logic (business components)
- Or pure presentation (form fields, cards)

## shadcn/ui Conventions

### Installation

```bash
npx shadcn@latest add button input form
```

### cn() Utility

```typescript
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Usage:**

```typescript
<div className={cn(
  'base-class',
  isActive && 'active-class',
  className,  // Allow override via props
)} />
```

### Component Variants (CVA)

```typescript
import { cva, type VariantProps } from 'class-variance-authority'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground',
        outline: 'border border-input bg-background',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 px-3 text-xs',
        lg: 'h-10 px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading && <Spinner className='mr-2' />}
      {children}
    </button>
  ),
)
```

## Tailwind Conventions

### Spacing

Prefer `gap` over margins:

```typescript
// Good
<div className='flex gap-4'>

// Avoid
<div className='flex'>
  <div className='mr-4'>
```

### Responsive Design

Mobile-first approach:

```typescript
<div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
```

### Color Usage

Use semantic colors from CSS variables:

```typescript
// Good - semantic
className = "bg-background text-foreground";
className = "bg-primary text-primary-foreground";
className = "text-muted-foreground";

// Avoid - hardcoded
className = "bg-white text-black";
className = "bg-blue-500";
```

### CSS Variables

```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    /* ... */
  }
}
```

## Component Separation

### Business vs Presentation

| Aspect        | Business Component   | Presentation Component      |
| ------------- | -------------------- | --------------------------- |
| Data fetching | Yes                  | No                          |
| Mutations     | Yes                  | No                          |
| Form state    | Owns (`useForm`)     | Consumes (`useFormContext`) |
| Navigation    | Yes                  | No                          |
| Location      | `<feature>-form.tsx` | `<feature>-form-fields.tsx` |

### Business Component Example

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

export default function ProfileForm() {
  // Data fetching
  const profileQuery = trpc.profile.get.useQuery()

  // Form state ownership
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  // Mutations
  const updateMut = trpc.profile.update.useMutation()

  // Business logic
  const onSubmit = async (data: ProfileFormHandler) => {
    await updateMut.mutateAsync(data)
    await trpcUtils.profile.invalidate()
    router.push(appRoutes.dashboard)
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <ProfileFirstNameField />  {/* Presentation */}
      <ProfileLastNameField />   {/* Presentation */}
      <Button type='submit'>Save</Button>
    </StandardFormProvider>
  )
}
```

### Presentation Component Example

```typescript
// src/features/profile/components/profile-form-fields.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import type { ProfileFormHandler } from '../schemas'

export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormHandler>()

  // Pure rendering - no business logic
  return (
    <StandardFormInput<ProfileFormHandler>
      name='firstName'
      label='First Name'
      placeholder='John'
      required
    />
  )
}
```

## Common Patterns

### Card Pattern

```typescript
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### Dialog Pattern

```typescript
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button onClick={() => setOpen(false)}>Close</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Select Pattern

```typescript
<Select value={value} onValueChange={onChange}>
  <SelectTrigger>
    <SelectValue placeholder='Select...' />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value='option1'>Option 1</SelectItem>
    <SelectItem value='option2'>Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Skeleton Pattern

```typescript
export function ProfileFormSkeleton() {
  return (
    <div className='space-y-4'>
      {Array.from({ length: 5 }).map((_, i) => (
        <div className='space-y-2' key={i}>
          <Skeleton className='h-4 w-20' />
          <Skeleton className='h-10 w-full' />
        </div>
      ))}
      <Skeleton className='h-10 w-32' />
    </div>
  )
}
```

## Best Practices

### Do

- Use `cn()` for conditional classes
- Use semantic color variables
- Use `gap` for spacing
- Keep primitives generic
- Separate business from presentation

### Don't

- Don't hardcode colors
- Don't use margins when gap works
- Don't put business logic in primitives
- Don't fetch data in presentation components

## Checklist

- [ ] UI primitives in `components/ui/`
- [ ] Custom components in `components/custom-ui/`
- [ ] Feature components in `features/<feature>/components/`
- [ ] Business components handle data, presentation components render
- [ ] Using `cn()` for class composition
- [ ] Using semantic colors from CSS variables
- [ ] Mobile-first responsive design
- [ ] Skeletons for loading states
