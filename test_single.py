import time

import requests

BASE = "http://127.0.0.1:8000"

with open("test_reference.jpg", "rb") as f:
    response = requests.post(
        f"{BASE}/api/upload", files={"file": ("test_reference.jpg", f, "image/jpeg")}
    )
session_id = response.json()["session_id"]
requests.post(f"{BASE}/api/sessions/{session_id}/consent")
print("session:", session_id)

start = time.time()
response = requests.post(
    f"{BASE}/api/sessions/{session_id}/generate", json={"scenes": ["luxury_cinematic"]}
)
print("start:", response.json())

final = None
while time.time() - start < 240:
    payload = requests.get(f"{BASE}/api/sessions/{session_id}/status").json()
    scene = payload["scenes"]["luxury_cinematic"]
    print(f"  {round(time.time() - start, 1)}s {scene['status']}")
    if scene["status"] in ("completed", "failed"):
        final = scene
        break
    time.sleep(4)

if final and final["status"] == "completed":
    print("SUCCESS in", round(time.time() - start, 1), "s")
    img = requests.get(f"{BASE}/api/sessions/{session_id}/portrait/luxury_cinematic")
    print("portrait:", img.status_code, img.headers.get("content-type"), len(img.content), "bytes")
    with open("test_result.jpg", "wb") as f:
        f.write(img.content)
else:
    print("RESULT:", final["status"] if final else "timeout")
    print("error:", final["error"] if final else "no settle within 240s")
