"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { observeLazyElement } from "@/lib/ui/lazy";

export function useInfiniteScroll<T>(
  loadPage: (page: number) => Promise<T[]>,
  options?: {
    pageSize?: number;
    initialPage?: number;
  }
) {
  const pageSize = options?.pageSize ?? 20;
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(options?.initialPage ?? 1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const nextItems = await loadPage(page);

      setItems((current) => [...current, ...nextItems]);
      setHasMore(nextItems.length >= pageSize);
      setPage((current) => current + 1);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError
          : new Error(String(loadError))
      );
    } finally {
      setLoading(false);
    }
  }, [hasMore, loadPage, loading, page, pageSize]);

  useEffect(() => {
    void loadMore().catch(() => undefined);
  }, []);

  useEffect(() => {
    const element = sentinelRef.current;

    if (!element || !hasMore) {
      return;
    }

    return observeLazyElement(element, () => {
      void loadMore();
    });
  }, [hasMore, loadMore]);

  const reset = useCallback(() => {
    setItems([]);
    setPage(options?.initialPage ?? 1);
    setHasMore(true);
    setError(null);
  }, [options?.initialPage]);

  return {
    items,
    loading,
    hasMore,
    error,
    sentinelRef,
    loadMore,
    reset,
  };
}
