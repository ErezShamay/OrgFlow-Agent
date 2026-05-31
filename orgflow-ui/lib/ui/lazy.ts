export function createLazyLoader<T>(
  loader: () => Promise<T>
): () => Promise<T> {
  let cached: T | null = null;
  let pending: Promise<T> | null = null;

  return async () => {
    if (cached !== null) {
      return cached;
    }

    if (!pending) {
      pending = loader().then((value) => {
        cached = value;
        return value;
      });
    }

    return pending;
  };
}

export function shouldLazyLoad(
  element: Element | null,
  rootMargin = "200px"
): boolean {
  if (!element || typeof IntersectionObserver === "undefined") {
    return true;
  }

  return false;
}

export type LazyLoadOptions = {
  rootMargin?: string;
  threshold?: number;
};

export function observeLazyElement(
  element: Element,
  onVisible: () => void,
  options: LazyLoadOptions = {}
): () => void {
  if (typeof IntersectionObserver === "undefined") {
    onVisible();
    return () => undefined;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];

      if (entry?.isIntersecting) {
        onVisible();
        observer.disconnect();
      }
    },
    {
      rootMargin: options.rootMargin ?? "200px",
      threshold: options.threshold ?? 0.1,
    }
  );

  observer.observe(element);

  return () => observer.disconnect();
}
