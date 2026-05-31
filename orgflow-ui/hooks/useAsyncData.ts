"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { showToast } from "@/lib/ui/toast";

export type AsyncDataState<T> = {
  data: T | null;
  loading: boolean;
  error: Error | null;
  retryCount: number;
};

export function useAsyncData<T>(
  loader: () => Promise<T>,
  options?: {
    enabled?: boolean;
    showErrorToast?: boolean;
    errorMessage?: string;
  }
) {
  const enabled = options?.enabled ?? true;
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const [state, setState] = useState<AsyncDataState<T>>({
    data: null,
    loading: enabled,
    error: null,
    retryCount: 0,
  });

  const execute = useCallback(async () => {
    setState((current) => ({
      ...current,
      loading: true,
      error: null,
    }));

    try {
      const data = await loaderRef.current();

      setState((current) => ({
        ...current,
        data,
        loading: false,
        error: null,
      }));

      return data;
    } catch (error) {
      const normalized =
        error instanceof Error
          ? error
          : new Error(String(error));

      setState((current) => ({
        ...current,
        loading: false,
        error: normalized,
      }));

      if (options?.showErrorToast) {
        showToast(
          options.errorMessage ?? normalized.message,
          "error"
        );
      }

      throw normalized;
    }
  }, [options?.errorMessage, options?.showErrorToast]);

  const retry = useCallback(async () => {
    setState((current) => ({
      ...current,
      retryCount: current.retryCount + 1,
    }));

    return execute();
  }, [execute]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    void execute().catch(() => undefined);
  }, [enabled, execute, state.retryCount]);

  return {
    ...state,
    reload: execute,
    retry,
  };
}
