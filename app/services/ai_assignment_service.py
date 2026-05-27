from app.db.supabase_client import (
    supabase
)


class AIAssignmentService:

    def __init__(self):

        self.client = (
            supabase
        )

    # ==========================================
    # GET BEST ASSIGNEE
    # ==========================================

    def get_best_assignee(
        self,
        project_id: str,
    ):

        profiles = (
            self.get_available_profiles()
        )

        if not profiles:
            return None

        ranked_profiles = []

        for profile in profiles:

            workload = (
                self.get_profile_workload(
                    profile["id"]
                )
            )

            score = (
                self.calculate_assignment_score(
                    profile,
                    workload,
                )
            )

            ranked_profiles.append({

                "profile":
                    profile,

                "score":
                    score,

                "workload":
                    workload,
            })

        ranked_profiles.sort(

            key=lambda item:
                item["score"],

            reverse=True,
        )

        return ranked_profiles[0][
            "profile"
        ]

    # ==========================================
    # GET AVAILABLE PROFILES
    # ==========================================

    def get_available_profiles(
        self,
    ):

        response = (
            self.client
            .table("profiles")
            .select("*")
            .in_(
                "role",
                [
                    "ADMIN",
                    "MANAGER",
                ]
            )
            .execute()
        )

        return response.data

    # ==========================================
    # GET WORKLOAD
    # ==========================================

    def get_profile_workload(
        self,
        profile_id: str,
    ):

        response = (
            self.client
            .table(
                "operational_actions"
            )
            .select("id")

            .eq(
                "assigned_to",
                profile_id
            )

            .in_(
                "status",
                [
                    "OPEN",
                    "IN_PROGRESS",
                    "BLOCKED",
                ]
            )

            .execute()
        )

        return len(
            response.data
        )

    # ==========================================
    # CALCULATE SCORE
    # ==========================================

    def calculate_assignment_score(
        self,
        profile: dict,
        workload: int,
    ):

        role = (
            profile.get(
                "role"
            )
        )

        base_score = 100

        if role == "ADMIN":

            base_score += 20

        if role == "MANAGER":

            base_score += 10

        workload_penalty = (
            workload * 5
        )

        final_score = (
            base_score
            - workload_penalty
        )

        return final_score