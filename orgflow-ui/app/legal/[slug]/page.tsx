import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Download, FileText } from "lucide-react";

import BrandLogo from "@/components/ui/BrandLogo";
import {
  getLegalDocument,
  listLegalDocuments,
} from "@/lib/legal/documents";

type LegalPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return listLegalDocuments().map((document) => ({
    slug: document.slug,
  }));
}

export async function generateMetadata({
  params,
}: LegalPageProps): Promise<Metadata> {
  const { slug } = await params;
  const document = getLegalDocument(slug);

  if (!document) {
    return {
      title: "מסמך משפטי",
    };
  }

  return {
    title: `${document.title} | ElayoAI`,
    description: document.description,
  };
}

export default async function LegalDocumentPage({
  params,
}: LegalPageProps) {
  const { slug } = await params;
  const document = getLegalDocument(slug);

  if (!document) {
    notFound();
  }

  return (
    <main className="of-auth-page">
      <div
        className="
          pointer-events-none
          absolute
          inset-0
          overflow-hidden
        "
        aria-hidden
      >
        <div className="of-landing-orb of-landing-orb-1 absolute" />
        <div className="of-landing-orb of-landing-orb-2 absolute" />
      </div>

      <div className="of-auth-card of-animate-fade-up mx-auto w-full max-w-lg">
        <div className="mb-8 flex justify-center">
          <BrandLogo size="lg" href="/" />
        </div>

        <div className="mb-8 text-center">
          <div
            className="
              mx-auto
              mb-4
              flex
              h-14
              w-14
              items-center
              justify-center
              rounded-2xl
              bg-brand/10
              text-brand
              dark:bg-brand/20
              dark:text-brand-light
            "
          >
            <FileText className="h-7 w-7" aria-hidden />
          </div>

          <h1 className="text-3xl font-black tracking-tight">
            {document.title}
          </h1>
          <p className="mt-2 text-sm text-zinc-500">
            {document.description}
          </p>
        </div>

        <div className="space-y-4">
          <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
            המסמך זמין להורדה בפורמט Word. ניתן לפתוח אותו במחשב או במכשיר
            נייד לקריאה מלאה.
          </p>

          <a
            href={document.downloadHref}
            download={document.fileName}
            className="
              of-focus-ring
              inline-flex
              w-full
              items-center
              justify-center
              gap-2
              rounded-2xl
              bg-gradient-to-l
              from-brand
              to-brand-gold
              px-6
              py-3
              text-base
              font-semibold
              text-white
              shadow-lg
              shadow-brand/20
              transition-all
              hover:brightness-110
            "
          >
            <Download className="h-5 w-5" aria-hidden />
            הורדת המסמך
          </a>
        </div>

        <p className="mt-8 text-center text-sm text-zinc-500">
          <Link
            href="/auth/login"
            className="font-medium text-brand hover:underline dark:text-brand-light"
          >
            חזרה להתחברות
          </Link>
        </p>
      </div>
    </main>
  );
}
