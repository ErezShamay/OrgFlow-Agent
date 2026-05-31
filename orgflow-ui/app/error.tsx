"use client";

import Button from "@/components/ui/Button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="of-dashboard-page of-container flex min-h-[50vh] flex-col items-center justify-center text-center">
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
