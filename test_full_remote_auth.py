import urllib.request
import urllib.error
import json
import ssl

print("=== Smart Anganwadi Portal — Full Remote Auth Tester ===")

render_url = input("Please enter your Render deployment URL (e.g., https://smart-anganwadi-portal.onrender.com): ").strip()
if not render_url:
    print("❌ Render URL cannot be empty.")
    exit(1)

# Standardize URL
if render_url.endswith("/"):
    render_url = render_url[:-1]
if not render_url.startswith("http"):
    render_url = "https://" + render_url

# 1. Login Request
login_api_url = f"{render_url}/api/auth/login"
print(f"\n1. Sending POST request to: {login_api_url}...")

credentials = {
    "email": "teacher@anganwadi.gov.in",
    "password": "teach@123"
}

req_login = urllib.request.Request(
    login_api_url,
    data=json.dumps(credentials).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

token = None
try:
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req_login, context=context, timeout=15) as response:
        body = response.read().decode("utf-8")
        login_data = json.loads(body)
        print(f"   ✅ Login Succeeded (Status {response.status})")
        token = login_data["data"]["token"]
        print(f"   Generated Token (length {len(token)})")
        
except urllib.error.HTTPError as e:
    print(f"   ❌ Login Failed (Status {e.code})")
    print(e.read().decode("utf-8"))
    exit(1)
except Exception as e:
    print(f"   ❌ Connection Error: {e}")
    exit(1)

# 2. Profile Request with Fresh Token
if token:
    profile_api_url = f"{render_url}/api/auth/profile"
    print(f"\n2. Sending GET request to: {profile_api_url} using fresh token...")
    
    req_profile = urllib.request.Request(
        profile_api_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req_profile, context=context, timeout=15) as response:
            body = response.read().decode("utf-8")
            print(f"   ✅ Profile Fetched Successfully (Status {response.status})")
            print("Response JSON:")
            print(json.dumps(json.loads(body), indent=3))
            print("\n🎉 Auth is fully working on your Render server!")
            
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"   ❌ Profile Fetch Rejected (Status {e.code})")
        try:
            print(json.dumps(json.loads(body), indent=3))
        except Exception:
            print(f"Response: {body}")
            
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
