import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


class SupabaseClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url:
                raise ValueError(
                    "SUPABASE_URL is missing from environment variables."
                )

            if not key:
                raise ValueError(
                    "SUPABASE_KEY is missing from environment variables."
                )

            cls._client = create_client(url, key)

        return cls._client