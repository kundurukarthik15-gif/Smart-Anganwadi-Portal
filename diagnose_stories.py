import os
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    print("Connected to Supabase client successfully.")
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    exit(1)

# Test story record
test_story = {
    "title": "Diagnostic Test Story",
    "language": "English",
    "category": "Moral Stories",
    "emoji": "📖",
    "preview": "This is a temporary test story to check database permissions and constraints.",
    "has_audio": False,
    "pdf_url": "https://example.com/test.pdf",
    "audio_url": None,
    "video_url": None,
    "youtube_url": None,
    "center_id": "11111111-1111-1111-1111-111111111111",  # Test center ID
    "uploaded_by": None,
    "content_type": "pdf",
    "is_global": True,
    "url_link": None
}

print("\n--- Testing Insertion into 'stories' table ---")
try:
    res = supabase.table("stories").insert(test_story).execute()
    print("✅ Success! Test story inserted successfully.")
    print(f"Inserted record ID: {res.data[0]['id']}")
    
    # Clean up test record
    print("Cleaning up test record...")
    supabase.table("stories").delete().eq("id", res.data[0]['id']).execute()
    print("Cleanup successful.")
    
except Exception as e:
    print("❌ ERROR OCCURRED:")
    print(str(e))
    
    # Provide helpful pointers based on error content
    err_msg = str(e).lower()
    if "foreign key" in err_msg or "fkey" in err_msg:
        print("\n💡 Tip: This is a FOREIGN KEY error. The center_id '11111111-1111-1111-1111-111111111111' does not exist in your 'centers' table.")
        print("To fix this, check your 'centers' table in the Supabase Dashboard, copy a valid UUID from the 'id' column, and update the CSV with it.")
    elif "row-level security" in err_msg or "rls" in err_msg or "security policy" in err_msg:
        print("\n💡 Tip: This is a ROW LEVEL SECURITY (RLS) error.")
        print("To fix this, run this SQL in your Supabase SQL Editor:")
        print("    ALTER TABLE public.stories DISABLE ROW LEVEL SECURITY;")
    elif "check constraint" in err_msg:
        print("\n💡 Tip: This is a CHECK CONSTRAINT error. One of the columns (like language or content_type) has an invalid value.")
    elif "column" in err_msg and "does not exist" in err_msg:
        print("\n💡 Tip: One of the columns in the CSV does not exist in your database table schema.")
        print("Double-check if you applied the SQL upgrades in 'sql/migration_stories_global.sql' to add the 'content_type', 'is_global', and 'url_link' columns.")
