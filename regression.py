import urllib.request
import urllib.parse
import json
import time
import os
import random

BASE_URL = "http://127.0.0.1:9876/api"

def api_request(method, path, data=None):
    url = BASE_URL + path
    headers = {}
    if data is not None:
        data = json.dumps(data).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except:
            return e.code, body
    except Exception as e:
        return 0, str(e)

def test_api():
    print("--- Starting Regression Tests ---")
    ts = int(time.time())
    proj_name = f"Auto Project {ts}"
    cat_name = f"Auto Category {ts}"

    # 1. Projects
    print(f"Testing Projects ({proj_name})...")
    status, res = api_request("POST", "/projects", {"name": proj_name, "description": "test"})
    assert status == 201, f"Expected 201, got {status}: {res}"
    proj_id = res["id"]

    status, res = api_request("PUT", f"/projects/{proj_id}", {"name": f"{proj_name} Renamed"})
    assert status == 200, f"Expected 200, got {status}: {res}"

    # 2. Categories
    print(f"Testing Categories ({cat_name})...")
    status, res = api_request("POST", "/categories", {"name": cat_name})
    assert status == 201, f"Expected 201, got {status}: {res}"
    cat_id = res["id"]

    status, res = api_request("PUT", f"/categories/{cat_id}", {"name": f"{cat_name} Renamed"})
    assert status == 200, f"Expected 200, got {status}: {res}"

    status, res = api_request("POST", f"/categories/{cat_id}/subcategories", {"name": "Auto Sub"})
    assert status == 201, f"Expected 201, got {status}: {res}"
    sub_id = res["id"]

    status, res = api_request("PUT", f"/categories/{cat_id}/subcategories/{sub_id}", {"name": "Auto Sub Renamed"})
    assert status == 200, f"Expected 200, got {status}: {res}"

    # 3. Sessions (Manual Entry - Duration mode)
    print("Testing Manual Sessions (Duration)...")
    status, res = api_request("POST", "/sessions", {
        "date": "2026-03-01",
        "duration": "1.5h",
        "project_id": proj_id,
        "notes": "Automated regression session"
    })
    assert status == 201, f"Expected 201, got {status}: {res}"
    session_id = res["session_id"]

    # 4. Session Update (Metadata + Duration)
    print("Testing Session Update...")
    status, res = api_request("PUT", f"/sessions/{session_id}", {
        "date": "2026-03-01",
        "duration": "2.5h",
        "project_id": proj_id,
        "category_id": cat_id,
        "notes": "Automated regression session updated"
    })
    assert status == 200, f"Expected 200, got {status}: {res}"

    # 5. Totals Dashboard
    print("Testing Totals...")
    status, res = api_request("GET", "/stats/totals?period=year")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["total_sessions"] > 0, f"Expected sessions, got {res}"

    # 6. Timer Start/Stop with optional category
    print("Testing Timer...")
    status, res = api_request("POST", "/timer/start", {"project_id": proj_id})
    assert status == 200, f"Expected 200, got {status}: {res}"
    time.sleep(1)
    status, res = api_request("POST", "/timer/stop")
    assert status == 200, f"Expected 200, got {status}: {res}"
    timer_session_id = res["summary"]["session_id"]

    # 7. Export Generation
    print("Testing Exports...")
    for fmt in ["excel", "pdf", "word"]:
        print(f"  Generating {fmt}...")
        status, res = api_request("POST", "/export", {
            "format": fmt,
            "start_date": "2026-03-01",
            "end_date": "2026-03-31"
        })
        assert status == 200, f"Expected 200, got {status}: {res}"
        assert "file" in res, f"Expected file in response, got {res}"

    # 8. Cleanup
    print("Cleaning up...")
    api_request("DELETE", f"/sessions/{session_id}")
    api_request("DELETE", f"/sessions/{timer_session_id}")
    api_request("DELETE", f"/subcategories/{sub_id}")
    api_request("DELETE", f"/categories/{cat_id}")
    api_request("DELETE", f"/projects/{proj_id}")

    print("--- All API tests passed! ---")


if __name__ == "__main__":
    test_api()
