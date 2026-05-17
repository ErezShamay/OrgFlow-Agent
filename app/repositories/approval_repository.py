from app.db.supabase_client import SupabaseClient


class ApprovalRepository:
    def __init__(self):
        self.client = SupabaseClient.get_client()

    def create_approval_request(
        self,
        workflow_type: str,
        payload: dict
    ):
        response = (
            self.client
            .table("approval_requests")
            .insert({
                "workflow_type": workflow_type,
                "payload": payload,
                "status": "PENDING"
            })
            .execute()
        )

        return response.data[0]

    def get_approval_request(
        self,
        approval_id: int
    ):
        response = (
            self.client
            .table("approval_requests")
            .select("*")
            .eq("id", approval_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def approve_request(
        self,
        approval_id: int
    ):
        response = (
            self.client
            .table("approval_requests")
            .update({
                "status": "APPROVED"
            })
            .eq("id", approval_id)
            .execute()
        )

        return response.data[0]