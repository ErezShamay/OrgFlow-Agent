import Spinner from "@/components/ui/Spinner";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function LoadingState({
  message,
  variant = "skeleton",
  skeletonCount = 3,
}: {
  message?: string;
  variant?: "spinner" | "skeleton";
  skeletonCount?: number;
}) {
  if (variant === "spinner") {
    return (
      <div
        className="
          flex
          min-h-48
          flex-col
          items-center
          justify-center
          gap-4
        "
        role="status"
        aria-live="polite"
      >
        <Spinner label={message ?? "Loading"} />
        {message ? (
          <p className="text-sm text-zinc-500">{message}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div role="status" aria-live="polite">
      {message ? (
        <p className="mb-6 text-sm text-zinc-500">{message}</p>
      ) : null}
      <SkeletonList count={skeletonCount} />
    </div>
  );
}
