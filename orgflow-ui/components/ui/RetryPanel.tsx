"use client";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { useI18n } from "@/providers/I18nProvider";

export default function RetryPanel({
  title,
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry: () => void;
}) {
  const { t } = useI18n();

  return (
    <Card className="text-center">
      <h2 className="text-lg font-semibold">
        {title ?? t("common.error")}
      </h2>

      {message ? (
        <p className="mt-2 text-sm text-zinc-500">{message}</p>
      ) : null}

      <div className="mt-6 flex justify-center">
        <Button onClick={onRetry}>{t("common.retry")}</Button>
      </div>
    </Card>
  );
}
