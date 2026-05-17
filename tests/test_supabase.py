from app.db.supabase_client import SupabaseClient

client = SupabaseClient.get_client()

print(client)