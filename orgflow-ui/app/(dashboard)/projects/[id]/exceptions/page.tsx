import { redirect } from "next/navigation";

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ProjectExceptionsPage({
  params,
}: Props) {
  const { id } = await params;
  redirect(`/projects/${id}/escalations`);
}
