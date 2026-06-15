import urllib.request
import json
import ssl

print("=== Smart Anganwadi Portal — Remote Diagnose Tester ===")

render_url = "https://smart-anganwadi-portal.onrender.com"
diagnose_url = f"{render_url}/api/diagnose"
print(f"Calling: {diagnose_url}")

try:
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(diagnose_url, context=context, timeout=15) as response:
        status = response.status
        body = response.read().decode("utf-8")
        print(f"\n✅ SUCCESS! Server responded with status: {status}")
        try:
            print("Response JSON:")
            print(json.dumps(json.loads(body), indent=3))
        except Exception:
            print(f"Response Body (Raw): {body}")
            
except Exception as e:
    print(f"\n❌ ERROR Calling Diagnose Route: {e}")
    if hasattr(e, 'read'):
        try:
            print(e.read().decode("utf-8"))
        except Exception:
            pass
