import pytest

from app.db import supabase_client
from app.db.supabase_client import SupabaseClient


def test_supabase_client_when_configured():
    if supabase_client.supabase is None:
        pytest.skip("Supabase is not configured")

    client = SupabaseClient.get_client()
    assert client is not None
