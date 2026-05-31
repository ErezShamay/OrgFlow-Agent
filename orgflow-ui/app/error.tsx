"use client";

import { useEffect } from "react";

import Button from "@/components/ui/Button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="of-container flex min-h-screen flex-col items-center justify-center py-20 text-center">
      <h1 className="text-2xl font-bold">Something went wrong</h1>
      <p className="mt-3 max-w-lg text-sm text-zinc-500">
        {error.message}
      </p>
      <div className="mt-6">
        <Button onClick={reset}>Try again</Button>
      </div>
    </main>
  );
}
