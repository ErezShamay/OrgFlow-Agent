import LoadingState from "@/components/ui/LoadingState";

export default function FieldReportsLoading() {
  return (
    <div className="of-container mx-auto max-w-3xl p-8">
      <LoadingState message="טוען הפקת דוחות..." variant="spinner" />
    </div>
  );
}
