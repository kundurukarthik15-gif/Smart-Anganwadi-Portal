import os
import urllib.request
import urllib.error
import json
import ssl
from dotenv import load_dotenv

load_dotenv()

print("=== Smart Anganwadi Portal — Local Supabase Auth direct test ===")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key Length: {len(supabase_key or '')}")

token = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImVjYjNjYjIxLWQwMzEtNGJmZS1hZDcwLTliMzhkODEzZWNkMCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2Zyd3RtcWt3bXRub2licm55dHJ0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiYmJiYmJiYi1iYmJiLWJiYmItYmJiYi1iYmJiYmJiYmJiYmIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzgxNTQ1NjUzLCJpYXQiOjE3ODE1NDIwNTMsImVtYWlsIjoidGVhY2hlckBhbmdhbndhZGkuZ292LmluIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiU2F2aXRyaSBCYWkifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc4MTU0MjA1M31dLCJzZXNzaW9uX2lkIjoiNjg5ZTJkYjYtODAxZC00YjE3LWE3YTgtNzQ0ODgzZTVjYjg1IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.CNH0kkcSyTUqBDk8vfxkDYU9o3Q64FfKHGsuvttoOLhVuHcKF9C0kwRUkLfA94ic9qyrqra8SZDRJHznVg8cUA"

url = f"{supabase_url}/auth/v1/user"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("apikey", supabase_key)

try:
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=context, timeout=10) as response:
        if response.status == 200:
            print("\n✅ SUCCESS! Local credentials successfully verified the token.")
            print("Response:")
            print(json.dumps(json.loads(response.read().decode()), indent=3))
            print("\n👉 Conclusion: Your local credentials are 100% correct.")
            print("This means the credentials entered in your Render Environment Variables are incorrect (e.g. have copy-paste quotes or spaces).")
            
except urllib.error.HTTPError as e:
    print(f"\n❌ Error verification failed (Status {e.code}):")
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
