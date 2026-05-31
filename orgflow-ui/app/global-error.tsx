"use client";

import Button from "@/components/ui/Button";

export default function RootGlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-zinc-100 p-10 text-zinc-900">
        <main className="mx-auto max-w-lg text-center">
          <h1 className="text-2xl font-bold">
            Application error
          </h1>
          <p className="mt-3 text-sm text-zinc-600">
            {error.message}
          </p>
          <div className="mt-6">
            <Button onClick={reset}>Reload</Button>
          </div>
        </main>
      </body>
    </html>
  );
}
