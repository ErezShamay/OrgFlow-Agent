export default function AppLoadingScreen({
  message = "טוען...",
}: {
  message?: string;
}) {
  return (
    <main className="of-loading-screen">
      <div className="of-spinner" role="status" aria-label={message} />
      <p className="text-lg font-semibold text-zinc-600 dark:text-zinc-400">
        {message}
      </p>
    </main>
  );
}
