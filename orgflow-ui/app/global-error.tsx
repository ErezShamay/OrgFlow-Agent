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
    <main className="of-loading-screen of-container py-20 text-center">
      <h1 className="of-page-title text-2xl">Something went wrong</h1>
      <p className="of-page-desc mx-auto max-w-lg text-sm">
        {error.message}
      </p>
      <div className="mt-6">
        <Button variant="accent" onClick={reset}>
          Try again
        </Button>
      </div>
    </main>
  );
}
