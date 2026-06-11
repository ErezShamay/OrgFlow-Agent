import { redirect } from "next/navigation";

export default function UploadLegacyRedirectPage() {
  redirect("/field-reports/upload");
}
