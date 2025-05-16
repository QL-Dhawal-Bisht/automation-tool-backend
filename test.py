from supabase import create_client
SUPABASE_URL = "https://mggvulbvgteamxghjoce.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1nZ3Z1bGJ2Z3RlYW14Z2hqb2NlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2OTkxMjcsImV4cCI6MjA2MDI3NTEyN30.0mByptXZXPckzwAlEfnIFKAK219lUQ2OZLQwZH9hE4Y"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
try:
    # Test reading test_cases
    response = supabase.table("test_cases").select("id, response").eq("id", 24).execute()
    print("Test cases:", response.data)
    # Test updating response field
    supabase.table("test_cases").update({
        "response": '{"test": "sample"}'
    }).eq("id", 24).execute()
    print("Update successful")
except Exception as e:
    print(f"Error: {str(e)}")