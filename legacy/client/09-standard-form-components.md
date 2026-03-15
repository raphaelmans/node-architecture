# Standard Form Components

This guide outlines the conventions for creating abstracted, standardized form components that reduce boilerplate and enforce consistency.

> **Status:** Convention finalized. This is the standard pattern for all new forms.

---

## Conventions Summary

| Convention     | Standard                                                  |
| -------------- | --------------------------------------------------------- |
| Type Safety    | Generic components with explicit `<TFieldValues>`         |
| Field Variants | Support `size` and `variant` props                        |
| Complex Fields | Use composition via `StandardFormField`                   |
| Error Handling | Use `StandardFormError` component, place anywhere         |
| Layout         | Set default on `StandardFormProvider`, override per-field |
| Search         | Use `StandardSearch` (standalone, not form-tied)          |
| Debounce       | Always configurable via `debounceMs` prop                 |

---

## Problem Statement

Current form implementation requires repetitive boilerplate:

```typescript
// Current: Verbose, repetitive pattern
<FormField
  control={control}
  name='firstName'
  render={({ field }) => (
    <FormItem>
      <FormLabel>First Name</FormLabel>
      <FormControl>
        <Input placeholder='John' {...field} />
      </FormControl>
      <FormDescription>Your first name</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

**Issues:**

- Repeated structure for every field
- Easy to forget `FormMessage` or `FormControl`
- Inconsistent prop patterns across forms
- Verbose render props

---

## Design Decisions

| Decision       | Choice                                          | Rationale                           |
| -------------- | ----------------------------------------------- | ----------------------------------- |
| Type Safety    | Option A: Generic Components                    | Explicit generics, full type safety |
| Field Variants | Yes                                             | Support `size`, `variant` props     |
| Async Options  | Deferred                                        | Handle later                        |
| Complex Fields | Composition                                     | Children-based for flexibility      |
| Error Handling | Option B: `StandardFormError` component         | Composable, placeable anywhere      |
| Layout Control | Option B: Provider default + per-field override | Flexible with sensible defaults     |

---

## Component Architecture

```
src/components/form/
├── StandardFormProvider.tsx      # Form context + provider wrapper
├── StandardFormError.tsx         # Global/root error display
├── fields/
│   ├── StandardFormInput.tsx     # Text input field
│   ├── StandardFormSelect.tsx    # Select dropdown field
│   ├── StandardFormTextarea.tsx  # Textarea field
│   ├── StandardFormCheckbox.tsx  # Checkbox field
│   ├── StandardFormSwitch.tsx    # Switch/toggle field
│   ├── StandardFormDatePicker.tsx# Date picker field
│   └── StandardFormField.tsx     # Composition wrapper for custom fields
├── types.ts                      # Shared types
├── context.tsx                   # Form context for layout defaults
└── index.ts                      # Barrel export

src/components/common/
└── StandardSearch.tsx            # Standalone search (not form-tied)
```

---

## Core Types

```typescript
// src/components/form/types.ts
import { FieldPath, FieldValues } from 'react-hook-form'

// Layout options
export type FormLayout = 'vertical' | 'horizontal' | 'inline'

// Base props shared by all form fields
export interface StandardFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  name: TName
  label?: string
  description?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  className?: string
  layout?: FormLayout // Override provider default
}

// Size and variant options
export type FieldSize = 'sm' | 'default' | 'lg'
export type FieldVariant = 'default' | 'ghost' | 'outlined'

// Extended props for input fields
export interface StandardInputProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> extends StandardFieldProps<TFieldValues, TName> {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  autoComplete?: string
  size?: FieldSize
  variant?: FieldVariant
}

// Extended props for select fields
export interface StandardSelectProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> extends StandardFieldProps<TFieldValues, TName> {
  options: Array<{ label: string; value: string }>
  emptyOptionLabel?: string
  size?: FieldSize
}

// Props for composition wrapper
export interface StandardFormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> extends Omit<StandardFieldProps<TFieldValues, TName>, 'placeholder'> {
  children: React.ReactNode
}
```

---

## StandardFormProvider

```typescript
// src/components/form/context.tsx
import { createContext, useContext } from 'react'
import { FormLayout } from './types'

interface StandardFormContextValue {
  layout: FormLayout
}

const StandardFormContext = createContext<StandardFormContextValue>({
  layout: 'vertical',
})

export const useStandardFormContext = () => useContext(StandardFormContext)

export { StandardFormContext }
```

```typescript
// src/components/form/StandardFormProvider.tsx
'use client'

import { FieldValues, UseFormReturn, FormProvider } from 'react-hook-form'
import { StandardFormContext } from './context'
import { FormLayout } from './types'
import { cn } from '@/lib/utils'

interface StandardFormProviderProps<TFieldValues extends FieldValues> {
  form: UseFormReturn<TFieldValues>
  onSubmit: (data: TFieldValues) => void | Promise<void>
  onError?: (errors: any) => void
  children: React.ReactNode
  className?: string
  layout?: FormLayout  // Default layout for all fields
}

export function StandardFormProvider<TFieldValues extends FieldValues>({
  form,
  onSubmit,
  onError,
  children,
  className,
  layout = 'vertical',
}: StandardFormProviderProps<TFieldValues>) {
  return (
    <StandardFormContext.Provider value={{ layout }}>
      <FormProvider {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit, onError)}
          className={cn('space-y-4', className)}
        >
          {children}
        </form>
      </FormProvider>
    </StandardFormContext.Provider>
  )
}
```

---

## StandardFormError

```typescript
// src/components/form/StandardFormError.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StandardFormErrorProps {
  className?: string
}

export function StandardFormError({ className }: StandardFormErrorProps) {
  const { formState: { errors } } = useFormContext()

  // Access root-level errors (set via form.setError('root', { message: '...' }))
  const rootError = errors.root?.message as string | undefined

  if (!rootError) return null

  return (
    <Alert variant='destructive' className={cn(className)}>
      <AlertCircle className='h-4 w-4' />
      <AlertDescription>{rootError}</AlertDescription>
    </Alert>
  )
}
```

**Usage:**

```typescript
// In mutation error handler
const onSubmit = async (data: FormData) => {
  try {
    await mutation.mutateAsync(data)
  } catch (error) {
    form.setError('root', { message: 'Failed to save. Please try again.' })
  }
}

// In form
<StandardFormProvider form={form} onSubmit={onSubmit}>
  <StandardFormError />  {/* Placed at top */}
  <StandardFormInput name='email' label='Email' />
  <StandardFormError />  {/* Or at bottom, or both */}
</StandardFormProvider>
```

---

## StandardFormInput

```typescript
// src/components/form/fields/StandardFormInput.tsx
'use client'

import { FieldPath, FieldValues, useFormContext } from 'react-hook-form'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useStandardFormContext } from '../context'
import { StandardInputProps, FormLayout } from '../types'
import { cn } from '@/lib/utils'

const layoutStyles: Record<FormLayout, string> = {
  vertical: 'flex flex-col space-y-2',
  horizontal: 'flex flex-row items-center gap-4 [&>label]:w-[200px] [&>label]:text-right',
  inline: '',
}

const sizeStyles = {
  sm: 'h-8 text-sm',
  default: 'h-9',
  lg: 'h-11 text-lg',
}

export function StandardFormInput<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  name,
  label,
  description,
  placeholder,
  disabled,
  required,
  type = 'text',
  autoComplete,
  className,
  layout: layoutOverride,
  size = 'default',
}: StandardInputProps<TFieldValues, TName>) {
  const { control } = useFormContext<TFieldValues>()
  const { layout: providerLayout } = useStandardFormContext()
  const layout = layoutOverride ?? providerLayout

  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className={cn(layoutStyles[layout], className)}>
          {label && layout !== 'inline' && (
            <FormLabel>
              {label}
              {required && <span className='ml-1 text-destructive'>*</span>}
            </FormLabel>
          )}
          <div className='flex-1'>
            <FormControl>
              <Input
                type={type}
                placeholder={layout === 'inline' ? label : placeholder}
                autoComplete={autoComplete}
                disabled={disabled}
                className={cn(sizeStyles[size])}
                {...field}
              />
            </FormControl>
            {description && <FormDescription>{description}</FormDescription>}
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  )
}
```

---

## StandardFormSelect

```typescript
// src/components/form/fields/StandardFormSelect.tsx
'use client'

import { FieldPath, FieldValues, useFormContext } from 'react-hook-form'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useStandardFormContext } from '../context'
import { StandardSelectProps, FormLayout } from '../types'
import { cn } from '@/lib/utils'

const layoutStyles: Record<FormLayout, string> = {
  vertical: 'flex flex-col space-y-2',
  horizontal: 'flex flex-row items-center gap-4 [&>label]:w-[200px] [&>label]:text-right',
  inline: '',
}

export function StandardFormSelect<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  name,
  label,
  description,
  placeholder,
  disabled,
  required,
  options,
  emptyOptionLabel,
  className,
  layout: layoutOverride,
}: StandardSelectProps<TFieldValues, TName>) {
  const { control } = useFormContext<TFieldValues>()
  const { layout: providerLayout } = useStandardFormContext()
  const layout = layoutOverride ?? providerLayout

  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className={cn(layoutStyles[layout], className)}>
          {label && layout !== 'inline' && (
            <FormLabel>
              {label}
              {required && <span className='ml-1 text-destructive'>*</span>}
            </FormLabel>
          )}
          <div className='flex-1'>
            <Select
              onValueChange={field.onChange}
              defaultValue={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder={placeholder} />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {emptyOptionLabel && (
                  <SelectItem value=''>{emptyOptionLabel}</SelectItem>
                )}
                {options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {description && <FormDescription>{description}</FormDescription>}
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  )
}
```

---

## StandardFormField (Composition Wrapper)

For complex/custom fields using composition pattern:

```typescript
// src/components/form/fields/StandardFormField.tsx
'use client'

import { FieldPath, FieldValues, useFormContext } from 'react-hook-form'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import { useStandardFormContext } from '../context'
import { StandardFormFieldProps, FormLayout } from '../types'
import { cn } from '@/lib/utils'

const layoutStyles: Record<FormLayout, string> = {
  vertical: 'flex flex-col space-y-2',
  horizontal: 'flex flex-row items-center gap-4 [&>label]:w-[200px] [&>label]:text-right',
  inline: '',
}

export function StandardFormField<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  name,
  label,
  description,
  disabled,
  required,
  className,
  layout: layoutOverride,
  children,
}: StandardFormFieldProps<TFieldValues, TName>) {
  const { control } = useFormContext<TFieldValues>()
  const { layout: providerLayout } = useStandardFormContext()
  const layout = layoutOverride ?? providerLayout

  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className={cn(layoutStyles[layout], className)}>
          {label && layout !== 'inline' && (
            <FormLabel>
              {label}
              {required && <span className='ml-1 text-destructive'>*</span>}
            </FormLabel>
          )}
          <div className='flex-1'>
            <FormControl>
              {/* Clone children with field props */}
              {typeof children === 'function'
                ? children({ field, disabled })
                : children
              }
            </FormControl>
            {description && <FormDescription>{description}</FormDescription>}
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  )
}
```

**Usage (Composition):**

```typescript
<StandardFormField<ProfileFormHandler>
  name='avatar'
  label='Profile Picture'
  description='Max 5MB, JPG or PNG'
>
  {({ field }) => (
    <FileUploader
      value={field.value}
      onChange={field.onChange}
      accept='image/*'
      maxSize={5 * 1024 * 1024}
    />
  )}
</StandardFormField>
```

---

## StandardSearch (Standalone)

Not tied to react-hook-form. For table filters, search bars, etc.

```typescript
// src/components/common/StandardSearch.tsx
'use client'

import { forwardRef, InputHTMLAttributes, useId, useState, useCallback } from 'react'
import debounce from 'debounce'
import { SearchIcon, X, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type SearchSize = 'sm' | 'default' | 'lg'

interface StandardSearchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'size'> {
  /** Callback fired with debounced search value */
  onSearch: (query: string) => void
  /** Debounce delay in milliseconds (default: 300) */
  debounceMs?: number
  /** Show loading spinner */
  isLoading?: boolean
  /** Show clear button when value exists */
  showClear?: boolean
  /** Size variant */
  size?: SearchSize
  /** Container class name */
  containerClassName?: string
}

const sizeStyles: Record<SearchSize, { input: string; icon: string; button: string }> = {
  sm: {
    input: 'h-8 pl-8 pr-8 text-sm',
    icon: 'h-4 w-4 left-2',
    button: 'h-6 w-6 right-1',
  },
  default: {
    input: 'h-9 pl-9 pr-9',
    icon: 'h-4 w-4 left-2.5',
    button: 'h-7 w-7 right-1',
  },
  lg: {
    input: 'h-11 pl-10 pr-10 text-lg',
    icon: 'h-5 w-5 left-3',
    button: 'h-8 w-8 right-1.5',
  },
}

const StandardSearch = forwardRef<HTMLInputElement, StandardSearchProps>(
  (
    {
      onSearch,
      debounceMs = 300,
      isLoading = false,
      showClear = true,
      size = 'default',
      containerClassName,
      className,
      placeholder = 'Search...',
      ...props
    },
    ref,
  ) => {
    const id = useId()
    const [internalValue, setInternalValue] = useState('')
    const styles = sizeStyles[size]

    // Debounced search callback
    // eslint-disable-next-line react-hooks/exhaustive-deps
    const debouncedSearch = useCallback(
      debounce((value: string) => {
        onSearch(value)
      }, debounceMs),
      [onSearch, debounceMs],
    )

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setInternalValue(value)
      debouncedSearch(value)
    }

    const handleClear = () => {
      setInternalValue('')
      onSearch('')
      debouncedSearch.clear()
    }

    const showClearButton = showClear && internalValue && !isLoading

    return (
      <div className={cn('relative', containerClassName)}>
        <SearchIcon
          className={cn(
            'absolute top-1/2 -translate-y-1/2 text-muted-foreground',
            styles.icon,
          )}
        />
        <Input
          id={id}
          ref={ref}
          type='search'
          value={internalValue}
          onChange={handleChange}
          placeholder={placeholder}
          className={cn(styles.input, className)}
          {...props}
        />
        {isLoading && (
          <Loader2
            className={cn(
              'absolute top-1/2 -translate-y-1/2 animate-spin text-muted-foreground',
              styles.button,
            )}
          />
        )}
        {showClearButton && (
          <Button
            type='button'
            variant='ghost'
            size='icon'
            onClick={handleClear}
            className={cn(
              'absolute top-1/2 -translate-y-1/2 rounded-full',
              styles.button,
            )}
          >
            <X className='h-3 w-3' />
            <span className='sr-only'>Clear search</span>
          </Button>
        )}
      </div>
    )
  },
)

StandardSearch.displayName = 'StandardSearch'

export { StandardSearch }
export type { StandardSearchProps }
```

**Usage:**

```typescript
// Basic usage
<StandardSearch
  onSearch={(query) => console.log(query)}
  placeholder='Search users...'
/>

// With loading state and custom debounce
<StandardSearch
  onSearch={handleSearch}
  debounceMs={500}
  isLoading={isSearching}
  size='lg'
/>

// Controlled with URL state (nuqs)
const [search, setSearch] = useQueryState('q')

<StandardSearch
  onSearch={setSearch}
  debounceMs={300}
/>
```

---

## Complete Usage Example

### Before (Current Pattern)

```typescript
export default function ProfileForm() {
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        {mutation.error && (
          <Alert variant='destructive'>{mutation.error.message}</Alert>
        )}
        <FormField
          control={form.control}
          name='firstName'
          render={({ field }) => (
            <FormItem>
              <FormLabel>First Name</FormLabel>
              <FormControl>
                <Input placeholder='John' {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='status'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Status</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder='Select status' />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value='active'>Active</SelectItem>
                  <SelectItem value='inactive'>Inactive</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type='submit'>Submit</Button>
      </form>
    </Form>
  )
}
```

### After (Standardized Pattern)

```typescript
export default function ProfileForm() {
  const form = useForm<ProfileFormHandler>({
    resolver: zodResolver(profileFormSchema),
  })

  const onSubmit = async (data: ProfileFormHandler) => {
    try {
      await mutation.mutateAsync(data)
    } catch (error) {
      form.setError('root', { message: 'Failed to save profile' })
    }
  }

  return (
    <StandardFormProvider form={form} onSubmit={onSubmit}>
      <StandardFormError />

      <StandardFormInput<ProfileFormHandler>
        name='firstName'
        label='First Name'
        placeholder='John'
        required
      />

      <StandardFormSelect<ProfileFormHandler>
        name='status'
        label='Status'
        placeholder='Select status'
        options={[
          { label: 'Active', value: 'active' },
          { label: 'Inactive', value: 'inactive' },
        ]}
      />

      <Button type='submit'>Submit</Button>
    </StandardFormProvider>
  )
}
```

### Horizontal Layout (Settings Page)

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout='horizontal'>
  <StandardFormError />

  <StandardFormInput<SettingsFormHandler>
    name='displayName'
    label='Display Name'
  />

  <StandardFormSelect<SettingsFormHandler>
    name='timezone'
    label='Timezone'
    options={timezoneOptions}
  />

  {/* Override to vertical for this field */}
  <StandardFormField<SettingsFormHandler>
    name='bio'
    label='Bio'
    layout='vertical'
  >
    {({ field }) => (
      <RichTextEditor value={field.value} onChange={field.onChange} />
    )}
  </StandardFormField>
</StandardFormProvider>
```

---

## Barrel Export

```typescript
// src/components/form/index.ts
export { StandardFormProvider } from './StandardFormProvider'
export { StandardFormError } from './StandardFormError'
export { StandardFormInput } from './fields/StandardFormInput'
export { StandardFormSelect } from './fields/StandardFormSelect'
export { StandardFormField } from './fields/StandardFormField'
export { useStandardFormContext } from './context'
export type * from './types'

// src/components/common/index.ts
export { StandardSearch } from './StandardSearch'
export type { StandardSearchProps } from './StandardSearch'
```

---

## Implementation Checklist

- [ ] Create `src/components/form/types.ts`
- [ ] Create `src/components/form/context.tsx`
- [ ] Create `src/components/form/StandardFormProvider.tsx`
- [ ] Create `src/components/form/StandardFormError.tsx`
- [ ] Create `src/components/form/fields/StandardFormInput.tsx`
- [ ] Create `src/components/form/fields/StandardFormSelect.tsx`
- [ ] Create `src/components/form/fields/StandardFormField.tsx`
- [ ] Create `src/components/form/index.ts`
- [ ] Create `src/components/common/StandardSearch.tsx`
- [ ] Add remaining field types (Textarea, Checkbox, Switch, DatePicker)
- [ ] Migrate existing forms incrementally
- [ ] Deprecate old `SearchInput` component

---

## Quick Reference

### Form Setup

```typescript
<StandardFormProvider form={form} onSubmit={onSubmit} layout='vertical'>
  <StandardFormError />
  <StandardFormInput<T> name='field' label='Label' />
  <Button type='submit'>Submit</Button>
</StandardFormProvider>
```

### Field Types

```typescript
// Text input
<StandardFormInput<T> name='email' label='Email' type='email' required />

// Select
<StandardFormSelect<T> name='role' label='Role' options={options} />

// Custom (composition)
<StandardFormField<T> name='avatar' label='Avatar'>
  {({ field }) => <CustomComponent {...field} />}
</StandardFormField>
```

### Standalone Search

```typescript
<StandardSearch onSearch={handleSearch} debounceMs={300} isLoading={isPending} />
```

### Layout Override

```typescript
// Provider default
<StandardFormProvider layout='horizontal'>
  <StandardFormInput name='a' />          {/* horizontal */}
  <StandardFormInput name='b' layout='vertical' />  {/* override */}
</StandardFormProvider>
```

### Error Handling

```typescript
// Set root error
form.setError('root', { message: 'API error' })

// Display anywhere
<StandardFormError />
```
