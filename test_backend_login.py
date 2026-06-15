import os
import json
from app import app

print("=== Flask Backend Authentication Test ===")

# Create Flask test client
client = app.test_client()

# Credentials to test
credentials = {
    "email": "teacher@anganwadi.gov.in",
    "password": "teach@123"
}

print(f"\n1. Sending POST request to /api/auth/login with email '{credentials['email']}'...")
try:
    login_response = client.post(
        "/api/auth/login",
        data=json.dumps(credentials),
        content_type="application/json"
    )
    
    print(f"   Status Code: {login_response.status_code}")
    login_data = json.loads(login_response.data.decode())
    print(f"   Response JSON:\n   {json.dumps(login_data, indent=3)}")
    
    if login_response.status_code == 200 and login_data.get("success"):
        token = login_data["data"]["token"]
        print(f"\n✅ Login succeeded! Token generated (length {len(token)}).")
        
        # 2. Test profile fetch
        print(f"\n2. Sending GET request to /api/auth/profile using the generated token...")
        profile_response = client.get(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"   Status Code: {profile_response.status_code}")
        profile_data = json.loads(profile_response.data.decode())
        print(f"   Response JSON:\n   {json.dumps(profile_data, indent=3)}")
        
        if profile_response.status_code == 200:
            print("\n✅ Success! Token is valid and profile was retrieved successfully.")
        else:
            print("\n❌ Failure! The token was generated successfully, but the backend rejected it when verifying.")
    else:
        print("\n❌ Failure! The login request failed.")
        
except Exception as e:
    print(f"\n❌ Error occurred during execution: {e}")
    import traceback
    traceback.print_exc()
