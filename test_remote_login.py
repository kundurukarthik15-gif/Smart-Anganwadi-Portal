import urllib.request
import urllib.error
import json
import ssl

print("=== Smart Anganwadi Portal — Remote Render API Tester ===")

render_url = input("Please enter your Render deployment URL (e.g., https://smart-anganwadi-portal.onrender.com): ").strip()
if not render_url:
    print("❌ Render URL cannot be empty.")
    exit(1)

# Standardize URL
if render_url.endswith("/"):
    render_url = render_url[:-1]
if not render_url.startswith("http"):
    render_url = "https://" + render_url

login_api_url = f"{render_url}/api/auth/login"
print(f"\nSending login request to: {login_api_url}")

credentials = {
    "email": "teacher@anganwadi.gov.in",
    "password": "teach@123"
}

req = urllib.request.Request(
    login_api_url,
    data=json.dumps(credentials).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=context, timeout=15) as response:
        status = response.status
        body = response.read().decode("utf-8")
        print(f"\n✅ SUCCESS! Server responded with status: {status}")
        try:
            print("Response JSON:")
            print(json.dumps(json.loads(body), indent=3))
        except Exception:
            print(f"Response Body (Raw): {body}")
            
except urllib.error.HTTPError as e:
    status = e.code
    body = e.read().decode("utf-8")
    print(f"\n❌ SERVER RETURNED ERROR (Status {status}):")
    try:
        print(json.dumps(json.loads(body), indent=3))
    except Exception:
        print(f"Response Body (Raw): {body}")
        
except Exception as e:
    print(f"\n❌ CONNECTION ERROR: Could not connect to Render server.")
    print(str(e))
