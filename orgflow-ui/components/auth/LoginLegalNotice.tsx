import Link from "next/link";

import {
  LEGAL_DOCUMENTS,
} from "@/lib/legal/documents";

export default function LoginLegalNotice() {
  return (
    <footer
      className="
        relative
        z-10
        w-full
        max-w-md
        px-2
        pt-6
        text-center
        text-xs
        leading-relaxed
        text-zinc-500
        dark:text-zinc-400
      "
    >
      <p>
        בכניסה למערכת אתם מאשרים את{" "}
        <Link
          href={LEGAL_DOCUMENTS.terms.href}
          className="font-medium text-brand hover:underline dark:text-brand-light"
        >
          תנאי השימוש
        </Link>
        , את{" "}
        <Link
          href={LEGAL_DOCUMENTS.privacy.href}
          className="font-medium text-brand hover:underline dark:text-brand-light"
        >
          מדיניות הפרטיות
        </Link>{" "}
        ואת{" "}
        <Link
          href={LEGAL_DOCUMENTS["ai-transparency"].href}
          className="font-medium text-brand hover:underline dark:text-brand-light"
        >
          מדיניות שקיפות ה-AI
        </Link>
        .
      </p>
    </footer>
  );
}
