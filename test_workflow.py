import time

import requests

BASE = "http://127.0.0.1:8000"

print("1. upload reference photo...")
with open("test_reference.jpg", "rb") as f:
    response = requests.post(
        f"{BASE}/api/upload", files={"file": ("test_reference.jpg", f, "image/jpeg")}
    )
print("   status:", response.status_code)
data = response.json()
session_id = data["session_id"]
print("   session:", session_id, "| preview len:", len(data["preview"]))

print("2. upload rejects bad type...")
response = requests.post(
    f"{BASE}/api/upload", files={"file": ("notes.txt", b"hello", "text/plain")}
)
print("   status:", response.status_code, response.json())

print("3. status before consent...")
response = requests.get(f"{BASE}/api/sessions/{session_id}/status")
print("   ", response.json()["consent_confirmed"], response.json()["scenes"]["luxury_cinematic"])

print("4. generate without consent...")
response = requests.post(
    f"{BASE}/api/sessions/{session_id}/generate",
    json={"scenes": ["luxury_cinematic", "beach_destination", "traditional_indian"]},
)
print("   status:", response.status_code, response.json())

print("5. confirm consent...")
response = requests.post(f"{BASE}/api/sessions/{session_id}/consent")
print("   status:", response.status_code, response.json())

print("6. start generation...")
start = time.time()
response = requests.post(
    f"{BASE}/api/sessions/{session_id}/generate",
    json={"scenes": ["luxury_cinematic", "beach_destination", "traditional_indian"]},
)
print("   status:", response.status_code, response.json())

print("7. poll status...")
while time.time() - start < 240:
    response = requests.get(f"{BASE}/api/sessions/{session_id}/status")
    payload = response.json()
    statuses = {k: v["status"] for k, v in payload["scenes"].items()}
    print("   ", round(time.time() - start, 1), "s", statuses, "settled:", payload["all_settled"])
    if payload["all_settled"]:
        for key, scene in payload["scenes"].items():
            if scene["error"]:
                print(f"   {key} error: {scene['error']}")
        break
    time.sleep(5)

print("8. portrait endpoint when not completed...")
response = requests.get(f"{BASE}/api/sessions/{session_id}/portrait/luxury_cinematic")
print("   status:", response.status_code, response.json() if response.status_code != 200 else "image!")

print("9. zip download when nothing completed...")
response = requests.get(f"{BASE}/api/sessions/{session_id}/download")
print("   status:", response.status_code)

print("10. reset session...")
response = requests.post(f"{BASE}/api/sessions/{session_id}/reset")
print("   status:", response.status_code, response.json())

print("11. status after reset...")
response = requests.get(f"{BASE}/api/sessions/{session_id}/status")
print("   status:", response.status_code, response.json())

print("12. frontend served at / ...")
response = requests.get(f"{BASE}/")
print("   status:", response.status_code, "| has root div:", '<div id="root">' in response.text)
