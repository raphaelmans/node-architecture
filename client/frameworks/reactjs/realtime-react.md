# Realtime Subscriptions (React)

> React lifecycle adapter for the provider-neutral realtime contracts in `client/core/realtime.md`.

## Hook Ownership

Expose one `useMod<Feature>RealtimeSync` hook when a mounted React subtree owns a subscription. The hook resolves a composition-root-owned feature realtime API, manages subscription teardown, and coordinates cache reconciliation.

```typescript
export function useModReservationRealtimeSync(reservationId: string) {
  const realtimeApi = getReservationRealtimeApi();
  const queryClient = useQueryClient();
  const hasConnected = useRef(false);
  const hasGap = useRef(false);

  useEffect(() => {
    const subscription = realtimeApi.subscribe({
      reservationId,
      onEvent(event) {
        queryClient.setQueryData(
          reservationKeys.detail(reservationId),
          (current) => applyReservationEvent(current, event),
        );
        void queryClient.invalidateQueries({
          queryKey: reservationKeys.detail(reservationId),
        });
      },
      onStateChange(state) {
        if (state === "connected") {
          if (hasConnected.current && hasGap.current) {
            hasGap.current = false;
            void queryClient.invalidateQueries({
              queryKey: reservationKeys.detail(reservationId),
            });
          }
          hasConnected.current = true;
          return;
        }

        if (hasConnected.current && (state === "disconnected" || state === "error")) {
          hasGap.current = true;
        }
      },
    });

    return () => {
      void subscription.unsubscribe();
    };
  }, [queryClient, realtimeApi, reservationId]);
}
```

## Rules

- Keep provider SDK types and channel construction out of React hooks.
- Subscribe in an effect and always return teardown.
- Resolve a stable API instance; do not construct it during render.
- Keep event reducers pure and test them separately.
- Coalesce invalidation for bursty streams even when every event is patched locally.
- Avoid React state for connection bookkeeping that does not affect rendering; refs prevent lifecycle bookkeeping from causing rerenders.
- If connection state is user-visible, expose a small derived UI state rather than the provider status enum.
- Test the hook with a fake `I<Feature>RealtimeApi` and a fresh QueryClient.
