import os
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    print("✅ Connected to Supabase client successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Supabase client: {e}")
    exit(1)

print("\n=== Smart Anganwadi Portal — Google Auth Mismatch Diagnoser ===")

email = input("Please enter your Google account email address: ").strip().lower()
if not email:
    print("❌ Email cannot be empty.")
    exit(1)

print(f"\n1. Checking public.users table for email '{email}'...")
try:
    res_public = supabase.table("users").select("id, full_name, center_id").eq("email", email).execute()
    public_user = res_public.data[0] if res_public.data else None
    
    if public_user:
        print(f"   Found in public.users:")
        print(f"   - Name: {public_user['full_name']}")
        print(f"   - Profile ID (UUID): {public_user['id']}")
        print(f"   - Center ID: {public_user['center_id']}")
    else:
        print(f"   ℹ️ No profile found for '{email}' in public.users table.")
except Exception as e:
    print(f"   ❌ Error querying public.users: {e}")
    public_user = None

print(f"\n2. Checking Supabase Auth (auth.users) for email '{email}'...")
auth_user = None
try:
    # Use Supabase admin auth API to list/get user
    # Note: supabase-py admin auth client is accessed via auth.admin
    res_auth = supabase.auth.admin.list_users()
    for u in res_auth:
        if u.email.lower() == email:
            auth_user = u
            break
            
    if auth_user:
        print(f"   Found in auth.users:")
        print(f"   - Auth ID (UUID): {auth_user.id}")
        print(f"   - Provider: {auth_user.app_metadata.get('provider')}")
        print(f"   - Created At: {auth_user.created_at}")
    else:
        print(f"   ℹ️ No auth record found for '{email}' in Supabase Auth.")
except Exception as e:
    print(f"   ❌ Error querying auth.users: {e}")

# 3. Analyze results
print("\n=== Analysis ===")
if public_user and auth_user:
    if public_user['id'] != auth_user.id:
        print("⚠️ MISMATCH DETECTED!")
        print(f"   Your Google Auth ID is '{auth_user.id}', but your profile ID in public.users is '{public_user['id']}'.")
        print("   This causes Google Login to crash because the database sees the email as already taken under a different ID.")
        
        fix = input("\nWould you like to fix this mismatch automatically now? (y/n): ").strip().lower()
        if fix == 'y' or fix == 'yes':
            try:
                # Update the ID in public.users
                print("Updating profile ID in public.users...")
                
                # To prevent foreign key constraints from blocking us, we can update it
                # We will update the user ID in the users table.
                # Since id is the primary key, we will delete the old record and insert with new ID, 
                # or update it if ON UPDATE CASCADE is supported.
                # Let's do a safe transfer:
                old_id = public_user['id']
                new_id = auth_user.id
                
                # Update using Supabase RPC or direct SQL if possible, or manual update
                # Let's perform an update of the ID
                supabase.table("users").update({"id": new_id}).eq("id", old_id).execute()
                print("   ✅ Profile ID successfully updated to match your Google Auth ID!")
                print("   Please try logging in with Google now!")
            except Exception as ex:
                print(f"   ❌ Failed to update ID: {ex}")
                print("   Try running this SQL in your Supabase SQL Editor:")
                print(f"   UPDATE public.users SET id = '{new_id}' WHERE id = '{old_id}';")
    else:
        print("✅ No mismatch. The public profile ID matches the auth ID perfectly.")
        print("   Google login should be working. Let's make sure your browser has cleared its old cookies.")
elif not public_user and auth_user:
    print("ℹ️ Auth record exists, but no public profile exists yet.")
    print("   Google login should automatically provision your profile when you sign in.")
elif public_user and not auth_user:
    print("ℹ️ Public profile exists, but no Auth record exists yet.")
    print("   This is typical for pre-seeded demo accounts. Sign in with the password 'admin@123' first.")
else:
    print("ℹ️ No records found in either table. You are a completely new user.")
    print("   Google Login will create both your auth record and your profile record automatically.")
