# shadcn/ui + Tailwind Architecture

This guide covers the UI component architecture using shadcn/ui with Tailwind CSS.

---

## Dependencies

```json
{
  "tailwindcss": "^3.4.17",
  "tailwind-merge": "^2.6.0",
  "tailwindcss-animate": "^1.0.7",
  "class-variance-authority": "^0.7.1",
  "clsx": "^2.1.1",
  "@radix-ui/react-*": "various"
}
```

---

## Component Hierarchy

```
src/components/
├── ui/                    # Layer 1: Primitive components (shadcn)
│   ├── button.tsx
│   ├── input.tsx
│   ├── form.tsx
│   ├── dialog.tsx
│   └── ...
└── custom-ui/             # Layer 2: Composite business components
    └── ...
```

### Layer 1: UI Primitives

- Direct shadcn/ui components
- Built on Radix UI primitives
- Unstyled/minimally styled
- Generic, reusable across projects

### Layer 2: Custom UI

- Composed from primitives
- Application-specific styling
- Business logic awareness
- Domain-specific patterns

---

## Utility Functions

### cn() - Class Name Merger

```typescript
// src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Usage:**

```typescript
<div className={cn(
  'base-styles',
  isActive && 'active-styles',
  className  // Allow override from props
)} />
```

---

## shadcn/ui Form Components

### Form Component Structure

```typescript
// src/components/ui/form.tsx
import { FormProvider, Controller, useFormContext } from 'react-hook-form'

// Form = FormProvider wrapper
const Form = FormProvider

// FormField = Controller with context
const FormField = ({ ...props }: ControllerProps) => (
  <FormFieldContext.Provider value={{ name: props.name }}>
    <Controller {...props} />
  </FormFieldContext.Provider>
)

// FormItem = Field wrapper with ID context
const FormItem = forwardRef(({ className, ...props }, ref) => {
  const id = useId()
  return (
    <FormItemContext.Provider value={{ id }}>
      <div ref={ref} className={cn('space-y-2', className)} {...props} />
    </FormItemContext.Provider>
  )
})

// FormLabel = Label with error styling
const FormLabel = forwardRef(({ className, ...props }, ref) => {
  const { error, formItemId } = useFormField()
  return (
    <Label
      ref={ref}
      className={cn(error && 'text-destructive', className)}
      htmlFor={formItemId}
      {...props}
    />
  )
})

// FormControl = Slot with ARIA attributes
const FormControl = forwardRef(({ ...props }, ref) => {
  const { error, formItemId, formDescriptionId, formMessageId } = useFormField()
  return (
    <Slot
      ref={ref}
      id={formItemId}
      aria-describedby={!error ? formDescriptionId : `${formDescriptionId} ${formMessageId}`}
      aria-invalid={!!error}
      {...props}
    />
  )
})

// FormMessage = Error message display
const FormMessage = forwardRef(({ className, children, ...props }, ref) => {
  const { error, formMessageId } = useFormField()
  const body = error ? String(error?.message) : children
  if (!body) return null
  return (
    <p
      ref={ref}
      id={formMessageId}
      className={cn('text-[0.8rem] font-medium text-destructive', className)}
      {...props}
    >
      {body}
    </p>
  )
})
```

### useFormField Hook

```typescript
const useFormField = () => {
  const fieldContext = useContext(FormFieldContext)
  const itemContext = useContext(FormItemContext)
  const { getFieldState, formState } = useFormContext()
  const fieldState = getFieldState(fieldContext.name, formState)

  return {
    id: itemContext.id,
    name: fieldContext.name,
    formItemId: `${itemContext.id}-form-item`,
    formDescriptionId: `${itemContext.id}-form-item-description`,
    formMessageId: `${itemContext.id}-form-item-message`,
    ...fieldState, // error, isDirty, isTouched, etc.
  }
}
```

---

## Button Component with CVA

```typescript
// src/components/ui/button.tsx
import { cva, type VariantProps } from 'class-variance-authority'

const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90',
        outline: 'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading, children, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading ? <Spinner className='mr-2' /> : null}
        {children}
      </Comp>
    )
  }
)
```

---

## Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
```

---

## CSS Variables (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode values */
  }
}
```

---

## Component Usage Patterns

### Form Field Pattern

```typescript
<FormField
  control={control}
  name='fieldName'
  render={({ field }) => (
    <FormItem>
      <FormLabel>Label</FormLabel>
      <FormControl>
        <Input {...field} />
      </FormControl>
      <FormDescription>Helper text</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Dialog Pattern

```typescript
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
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

---

## Best Practices

1. **Use `cn()` for conditional classes**

```typescript
className={cn('base', condition && 'conditional', className)}
```

2. **Prefer gap over margin for spacing**

```typescript
<div className='flex gap-4'>  {/* Good */}
<div className='flex'><div className='mr-4'>  {/* Avoid */}
```

3. **Use CSS variables for theming**

```typescript
className = 'bg-background text-foreground' // Uses CSS vars
```

4. **Leverage CVA for variant components**

```typescript
const variants = cva('base', { variants: { ... } })
```

5. **Keep primitives generic, customize in features**

```typescript
// ui/button.tsx - generic
// features/auth/components/auth-button.tsx - specific styling
```
