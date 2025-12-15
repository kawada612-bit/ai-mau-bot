
import requests
import sys

def test():
    try:
        print("Testing Health Endpoint...")
        r = requests.get("http://localhost:8080/health")
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print("❌ Health check failed")
            sys.exit(1)

        print("\nTesting Chat Endpoint (Valid)...")
        r = requests.post("http://localhost:8080/api/chat", json={"text": "ライブいつ？", "user_name": "Tester"})
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
             print("❌ Valid chat request failed")
             sys.exit(1)

        print("\nTesting Chat Endpoint (Invalid - Empty Text)...")
        r = requests.post("http://localhost:8080/api/chat", json={"text": "", "user_name": "BadUser"})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        if r.status_code != 422:
             print("❌ Validation check failed (expected 422)")
             sys.exit(1)
        
        print("\n✅ All tests passed!")


    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test()
