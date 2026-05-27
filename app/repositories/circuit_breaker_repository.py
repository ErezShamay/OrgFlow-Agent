from app.db.supabase_client import (
    supabase
)

from app.schemas.circuit_breaker import (
    CircuitBreaker
)


class CircuitBreakerRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "circuit_breakers"
        )

    # ==========================================
    # GET BREAKER
    # ==========================================

    def get_breaker(
        self,
        breaker_key: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "breaker_key",
                breaker_key
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ==========================================
    # CREATE BREAKER
    # ==========================================

    def create_breaker(
        self,
        breaker: CircuitBreaker,
    ):

        response = (
            self.client
            .table(self.table_name)
            .insert(
                breaker.model_dump()
            )
            .execute()
        )

        return response.data[0]

    # ==========================================
    # UPDATE BREAKER
    # ==========================================

    def update_breaker(
        self,
        breaker_key: str,
        data: dict,
    ):

        self.client \
            .table(self.table_name) \
            .update(data) \
            .eq(
                "breaker_key",
                breaker_key
            ) \
            .execute()