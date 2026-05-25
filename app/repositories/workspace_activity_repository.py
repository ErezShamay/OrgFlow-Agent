from app.db.supabase_client import supabase


class WorkspaceActivityRepository:

    @staticmethod
    def create_activity(
        project_id: str,
        activity_type: str,
        title: str,
        description: str = None,
        metadata: dict = None,
    ):

        response = (
            supabase.table("workspace_activity")
            .insert({
                "project_id": project_id,
                "activity_type": activity_type,
                "title": title,
                "description": description,
                "metadata": metadata,
            })
            .execute()
        )

        return response.data

    @staticmethod
    def get_project_activity(
        project_id: str
    ):

        response = (
            supabase.table("workspace_activity")
            .select("*")
            .eq("project_id", project_id)
            .order(
                "created_at",
                desc=True
            )
            .limit(50)
            .execute()
        )

        return response.data