import urllib.request
import urllib.error
import json
import ssl

print("=== Smart Anganwadi Portal — Remote Profile Verifier ===")

render_url = "https://smart-anganwadi-portal.onrender.com"
token = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImVjYjNjYjIxLWQwMzEtNGJmZS1hZDcwLTliMzhkODEzZWNkMCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2Zyd3RtcWt3bXRub2licm55dHJ0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiYmJiYmJiYi1iYmJiLWJiYmItYmJiYi1iYmJiYmJiYmJiYmIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzgxNTQ1NjUzLCJpYXQiOjE3ODE1NDIwNTMsImVtYWlsIjoidGVhY2hlckBhbmdhbndhZGkuZ292LmluIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiU2F2aXRyaSBCYWkifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc4MTU0MjA1M31dLCJzZXNzaW9uX2lkIjoiNjg5ZTJkYjYtODAxZC00YjE3LWE3YTgtNzQ0ODgzZTVjYjg1IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.CNH0kkcSyTUqBDk8vfxkDYU9o3Q64FfKHGsuvttoOLhVuHcKF9C0kwRUkLfA94ic9qyrqra8SZDRJHznVg8cUA"

profile_api_url = f"{render_url}/api/auth/profile"
print(f"Sending request to: {profile_api_url}")

req = urllib.request.Request(
    profile_api_url,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    },
    method="GET"
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
