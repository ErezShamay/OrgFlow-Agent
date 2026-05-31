type SkeletonProps = {
  className?: string;
  lines?: number;
};

export function Skeleton({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      aria-hidden="true"
      className={`
        animate-pulse
        rounded-2xl
        bg-zinc-200
        dark:bg-zinc-800
        ${className}
      `}
    />
  );
}

export function SkeletonText({
  lines = 3,
  className = "",
}: SkeletonProps) {
  return (
    <div
      className={`space-y-3 ${className}`}
      aria-busy="true"
      aria-label="Loading content"
    >
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={`h-4 ${index === lines - 1 ? "w-2/3" : "w-full"}`}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div
      className="of-card of-card-p8"
      aria-busy="true"
      aria-label="Loading card"
    >
      <Skeleton className="mb-4 h-8 w-1/2" />
      <SkeletonText lines={4} />
    </div>
  );
}

export function SkeletonList({
  count = 3,
}: {
  count?: number;
}) {
  return (
    <div className="grid gap-6">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  );
}
