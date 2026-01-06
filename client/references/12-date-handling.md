# Date Handling

This guide covers date manipulation and formatting using `date-fns`.

---

## Dependencies

```json
{
  "date-fns": "^4.1.0",
  "date-fns-tz": "^3.2.0"
}
```

---

## Convention

> **Always use `date-fns`** for date manipulation. Do not use native `Date` methods for formatting or complex calculations.

---

## Common Operations

### Formatting

```typescript
import { format, formatDistanceToNow, formatRelative } from 'date-fns'

// Basic formatting
format(new Date(), 'yyyy-MM-dd') // "2024-01-15"
format(new Date(), 'MMM d, yyyy') // "Jan 15, 2024"
format(new Date(), 'EEEE, MMMM do') // "Monday, January 15th"
format(new Date(), 'h:mm a') // "3:30 PM"
format(new Date(), 'yyyy-MM-dd HH:mm:ss') // "2024-01-15 15:30:00"

// Relative time
formatDistanceToNow(new Date('2024-01-10')) // "5 days ago"
formatDistanceToNow(date, { addSuffix: true }) // "in 5 days" or "5 days ago"

// Relative with context
formatRelative(new Date('2024-01-10'), new Date()) // "last Wednesday"
```

### Format Tokens

| Token  | Example | Description         |
| ------ | ------- | ------------------- |
| `yyyy` | 2024    | Full year           |
| `yy`   | 24      | 2-digit year        |
| `MMMM` | January | Full month          |
| `MMM`  | Jan     | Abbreviated month   |
| `MM`   | 01      | 2-digit month       |
| `dd`   | 15      | 2-digit day         |
| `d`    | 5       | Day of month        |
| `EEEE` | Monday  | Full weekday        |
| `EEE`  | Mon     | Abbreviated weekday |
| `HH`   | 15      | 24-hour hour        |
| `hh`   | 03      | 12-hour hour        |
| `mm`   | 30      | Minutes             |
| `ss`   | 45      | Seconds             |
| `a`    | PM      | AM/PM               |

---

### Parsing

```typescript
import { parse, parseISO } from 'date-fns'

// Parse ISO string (most common)
const date = parseISO('2024-01-15T10:30:00Z')

// Parse custom format
const date2 = parse('01/15/2024', 'MM/dd/yyyy', new Date())
const date3 = parse('Jan 15, 2024', 'MMM d, yyyy', new Date())
```

---

### Manipulation

```typescript
import {
  addDays,
  addWeeks,
  addMonths,
  addYears,
  subDays,
  startOfDay,
  endOfDay,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
} from 'date-fns'

const now = new Date()

// Add/subtract
addDays(now, 5) // 5 days from now
subDays(now, 5) // 5 days ago
addWeeks(now, 2) // 2 weeks from now
addMonths(now, 1) // 1 month from now

// Boundaries
startOfDay(now) // Today at 00:00:00
endOfDay(now) // Today at 23:59:59
startOfWeek(now) // Start of current week
startOfMonth(now) // First day of month
```

---

### Comparison

```typescript
import {
  isBefore,
  isAfter,
  isSameDay,
  isWithinInterval,
  differenceInDays,
  differenceInHours,
  isPast,
  isFuture,
} from 'date-fns'

const date1 = new Date('2024-01-15')
const date2 = new Date('2024-01-20')

// Comparisons
isBefore(date1, date2) // true
isAfter(date1, date2) // false
isSameDay(date1, date2) // false
isPast(date1) // depends on current date
isFuture(date1) // depends on current date

// Intervals
isWithinInterval(new Date(), { start: date1, end: date2 }) // boolean

// Differences
differenceInDays(date2, date1) // 5
differenceInHours(date2, date1) // 120
```

---

## Timezone Handling

```typescript
import { formatInTimeZone, toZonedTime, fromZonedTime } from 'date-fns-tz'

const utcDate = new Date('2024-01-15T10:00:00Z')
const timeZone = 'America/New_York'

// Format in specific timezone
formatInTimeZone(utcDate, timeZone, 'yyyy-MM-dd HH:mm:ss zzz')
// "2024-01-15 05:00:00 EST"

// Convert UTC to zoned time (for display)
const nyTime = toZonedTime(utcDate, timeZone)

// Convert zoned time to UTC (for storage)
const utc = fromZonedTime(nyTime, timeZone)
```

---

## Common Patterns

### Display Helpers

```typescript
// src/lib/utils/date.ts
import { format, formatDistanceToNow, isToday, isYesterday } from 'date-fns'

export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, yyyy h:mm a')
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, yyyy')
}

export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'h:mm a')
}

export function formatRelativeDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date

  if (isToday(d)) return `Today at ${format(d, 'h:mm a')}`
  if (isYesterday(d)) return `Yesterday at ${format(d, 'h:mm a')}`

  return format(d, 'MMM d, yyyy')
}

export function formatTimeAgo(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return formatDistanceToNow(d, { addSuffix: true })
}
```

### Usage in Components

```typescript
import { formatDate, formatTimeAgo } from '@/lib/utils/date'

function PostCard({ post }: { post: Post }) {
  return (
    <div>
      <h2>{post.title}</h2>
      <time dateTime={post.createdAt.toISOString()}>
        {formatTimeAgo(post.createdAt)}
      </time>
    </div>
  )
}
```

---

## Best Practices

1. **Store dates in UTC** - Always store ISO strings or UTC timestamps

   ```typescript
   // Database: 2024-01-15T10:00:00.000Z
   ```

2. **Parse on boundaries** - Parse strings to Date at API boundaries

   ```typescript
   const date = parseISO(apiResponse.createdAt)
   ```

3. **Format for display only** - Format at render time

   ```typescript
   <time>{format(date, 'MMM d, yyyy')}</time>
   ```

4. **Use ISO for APIs** - Send ISO strings to/from APIs

   ```typescript
   const payload = { createdAt: date.toISOString() }
   ```

5. **Handle timezones explicitly** - Use `date-fns-tz` when timezone matters
   ```typescript
   formatInTimeZone(date, userTimezone, 'yyyy-MM-dd HH:mm')
   ```

---

## Avoid

```typescript
// Bad: Native Date formatting
date.toLocaleDateString() // Inconsistent across browsers

// Bad: String manipulation
date.toString().split(' ')[0]

// Bad: Manual calculations
new Date(date.getTime() + 24 * 60 * 60 * 1000) // Use addDays()

// Good: date-fns
import { format, addDays } from 'date-fns'
format(date, 'yyyy-MM-dd')
addDays(date, 1)
```
