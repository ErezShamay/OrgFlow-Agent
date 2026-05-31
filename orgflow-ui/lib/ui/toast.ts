import { toast as sonnerToast } from "sonner";

export type ToastKind =
  | "success"
  | "error"
  | "info"
  | "warning"
  | "loading";

export function showToast(
  message: string,
  kind: ToastKind = "info",
  description?: string
) {
  const options = description ? { description } : undefined;

  switch (kind) {
    case "success":
      return sonnerToast.success(message, options);
    case "error":
      return sonnerToast.error(message, options);
    case "warning":
      return sonnerToast.warning(message, options);
    case "loading":
      return sonnerToast.loading(message, options);
    default:
      return sonnerToast.info(message, options);
  }
}

export function showPromiseToast<T>(
  promise: Promise<T>,
  messages: {
    loading: string;
    success: string;
    error: string;
  }
) {
  return sonnerToast.promise(promise, messages);
}

export function dismissToast(id?: string | number) {
  sonnerToast.dismiss(id);
}
