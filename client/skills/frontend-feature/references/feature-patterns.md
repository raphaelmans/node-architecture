# Feature Patterns Reference

## List View Pattern

```typescript
// src/features/<feature>/components/<feature>-list.tsx
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { trpc } from '@/lib/trpc/client';
import appRoutes from '@/common/app-routes';
import { useQuery<Feature>Pagination } from '../hooks';
import { <Feature>Card } from './<feature>-card';

export function <Feature>List() {
  const router = useRouter();
  const { page, setPage } = useQuery<Feature>Pagination();

  const listQuery = trpc.<module>.list.useQuery({
    page,
    limit: 20,
  });

  if (listQuery.isLoading) {
    return <ListSkeleton />;
  }

  if (listQuery.isError) {
    return <ErrorDisplay error={listQuery.error} retry={listQuery.refetch} />;
  }

  const { data, meta } = listQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">
          {meta.total} <Feature>s
        </h2>
        <Button onClick={() => router.push(appRoutes.<feature>.new)}>
          Create New
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data.map((item) => (
          <<Feature>Card key={item.id} item={item} />
        ))}
      </div>

      {meta.nextCursor && (
        <Button
          variant="outline"
          onClick={() => setPage(page + 1)}
        >
          Load More
        </Button>
      )}
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-32" />
      ))}
    </div>
  );
}
```

## Card Pattern

```typescript
// src/features/<feature>/components/<feature>-card.tsx
'use client';

import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import appRoutes from '@/common/app-routes';
import type { <Entity> } from '@/lib/modules/<module>/dtos';

interface <Feature>CardProps {
  item: <Entity>;
}

export function <Feature>Card({ item }: <Feature>CardProps) {
  const router = useRouter();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{item.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{item.description}</p>
      </CardContent>
      <CardFooter className="gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push(appRoutes.<feature>.view(item.id))}
        >
          View
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push(appRoutes.<feature>.edit(item.id))}
        >
          Edit
        </Button>
      </CardFooter>
    </Card>
  );
}
```

## Detail View Pattern

```typescript
// src/features/<feature>/components/<feature>-view.tsx
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { trpc } from '@/lib/trpc/client';
import appRoutes from '@/common/app-routes';
import { useCatchErrorToast } from '@/common/hooks';
import { <Feature>ViewSkeleton } from './<feature>-skeleton';

interface <Feature>ViewProps {
  <entity>Id: string;
}

export function <Feature>View({ <entity>Id }: <Feature>ViewProps) {
  const router = useRouter();
  const trpcUtils = trpc.useUtils();
  const catchErrorToast = useCatchErrorToast();

  const <entity>Query = trpc.<module>.getById.useQuery({ id: <entity>Id });
  const deleteMut = trpc.<module>.delete.useMutation();

  const handleDelete = async () => {
    if (!confirm('Are you sure?')) return;
    
    return catchErrorToast(
      async () => {
        await deleteMut.mutateAsync({ id: <entity>Id });
        await trpcUtils.<module>.list.invalidate();
        router.push(appRoutes.<feature>.list);
      },
      { description: 'Deleted successfully!' },
    );
  };

  if (<entity>Query.isLoading) {
    return <<Feature>ViewSkeleton />;
  }

  if (<entity>Query.isError) {
    return <ErrorDisplay error={<entity>Query.error} />;
  }

  const <entity> = <entity>Query.data;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{<entity>.name}</CardTitle>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(appRoutes.<feature>.edit(<entity>Id))}
          >
            Edit
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMut.isPending}
          >
            Delete
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <dl className="space-y-4">
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Description</dt>
            <dd>{<entity>.description || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Created</dt>
            <dd>{new Date(<entity>.createdAt).toLocaleDateString()}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
```

## Tab Navigation Pattern

```typescript
// src/features/<feature>/components/<feature>-tabs.tsx
'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useQuery<Feature>Tab } from '../hooks';
import { <Feature>Details } from './<feature>-details';
import { <Feature>Settings } from './<feature>-settings';
import { <Feature>History } from './<feature>-history';

interface <Feature>TabsProps {
  <entity>Id: string;
}

export function <Feature>Tabs({ <entity>Id }: <Feature>TabsProps) {
  const [tab, setTab] = useQuery<Feature>Tab();

  return (
    <Tabs value={tab ?? 'details'} onValueChange={setTab}>
      <TabsList>
        <TabsTrigger value="details">Details</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
        <TabsTrigger value="history">History</TabsTrigger>
      </TabsList>
      <TabsContent value="details">
        <<Feature>Details <entity>Id={<entity>Id} />
      </TabsContent>
      <TabsContent value="settings">
        <<Feature>Settings <entity>Id={<entity>Id} />
      </TabsContent>
      <TabsContent value="history">
        <<Feature>History <entity>Id={<entity>Id} />
      </TabsContent>
    </Tabs>
  );
}
```

## Dialog/Modal Pattern

```typescript
// src/features/<feature>/components/<feature>-dialog.tsx
'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { <Feature>Form } from './<feature>-form';

interface <Feature>DialogProps {
  trigger?: React.ReactNode;
  <entity>Id?: string;
  onSuccess?: () => void;
}

export function <Feature>Dialog({
  trigger,
  <entity>Id,
  onSuccess,
}: <Feature>DialogProps) {
  const [open, setOpen] = useState(false);

  const handleSuccess = () => {
    setOpen(false);
    onSuccess?.();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? <Button>{<entity>Id ? 'Edit' : 'Create'}</Button>}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {<entity>Id ? 'Edit <Feature>' : 'New <Feature>'}
          </DialogTitle>
          <DialogDescription>
            {<entity>Id
              ? 'Update the details below.'
              : 'Fill in the details to create a new <feature>.'}
          </DialogDescription>
        </DialogHeader>
        <<Feature>Form
          <entity>Id={<entity>Id}
          onSuccess={handleSuccess}
          isDialog
        />
      </DialogContent>
    </Dialog>
  );
}
```

## Infinite Scroll Pattern

```typescript
// src/features/<feature>/components/<feature>-infinite-list.tsx
'use client';

import { useEffect } from 'react';
import { useInView } from 'react-intersection-observer';
import { trpc } from '@/lib/trpc/client';
import { <Feature>Card } from './<feature>-card';
import { Skeleton } from '@/components/ui/skeleton';

export function <Feature>InfiniteList() {
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = trpc.<module>.list.useInfiniteQuery(
    { limit: 20 },
    {
      getNextPageParam: (lastPage) => lastPage.meta.nextCursor,
    },
  );

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (isLoading) {
    return <ListSkeleton />;
  }

  const items = data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <<Feature>Card key={item.id} item={item} />
        ))}
      </div>

      {/* Infinite scroll trigger */}
      <div ref={ref} className="h-10">
        {isFetchingNextPage && (
          <div className="flex justify-center">
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        )}
      </div>
    </div>
  );
}
```

## Search with Filters Pattern

```typescript
// src/features/<feature>/components/<feature>-filters.tsx
'use client';

import { StandardSearch } from '@/components/common/StandardSearch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useQuery<Feature>Search, useQuery<Feature>Status } from '../hooks';

export function <Feature>Filters() {
  const [search, setSearch] = useQuery<Feature>Search();
  const [status, setStatus] = useQuery<Feature>Status();

  return (
    <div className="flex gap-4">
      <StandardSearch
        onSearch={setSearch}
        placeholder="Search..."
        containerClassName="flex-1"
      />
      <Select value={status ?? ''} onValueChange={setStatus}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">All</SelectItem>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="inactive">Inactive</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

// In hooks.ts
export const useQuery<Feature>Search = () => {
  return useQueryState(
    appQueryParams.search,
    parseAsString.withOptions({ history: 'replace' }),
  );
};

export const useQuery<Feature>Status = () => {
  return useQueryState(
    'status',
    parseAsStringLiteral(['active', 'inactive']).withOptions({ history: 'replace' }),
  );
};
```

## File Tree Structure

```
src/features/<feature>/
├── components/
│   ├── <feature>-form.tsx           # Create/Edit form
│   ├── <feature>-form-fields.tsx    # Form field components
│   ├── <feature>-list.tsx           # List view
│   ├── <feature>-card.tsx           # Card component
│   ├── <feature>-view.tsx           # Detail view
│   ├── <feature>-tabs.tsx           # Tabbed interface
│   ├── <feature>-dialog.tsx         # Modal form
│   ├── <feature>-filters.tsx        # Search/filter bar
│   └── <feature>-skeleton.tsx       # Loading skeletons
├── stores/                          # Zustand stores (if needed)
│   └── <name>-store.ts
├── hooks.ts                         # URL state hooks
└── schemas.ts                       # Zod schemas
```
