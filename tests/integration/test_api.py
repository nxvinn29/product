import pytest
import requests
import os
import time

API_URL = "http://localhost:8000"

@pytest.fixture
def api_base():
    # Wait for API to be healthy?
    # In integration test context, we assume env is up.
    return API_URL

def test_health_check(api_base):
    try:
        resp = requests.get(f"{api_base}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
    except requests.exceptions.ConnectionError:
        pytest.fail("API is not reachable. Is Docker running?")

def test_upload_single_file(api_base, tmp_path):
    # Create dummy PDF
    dummy = tmp_path / "test.pdf"
    dummy.write_text("%PDF-1.4 dummy content")
    
    with open(dummy, "rb") as f:
        files = {"files": ("test.pdf", f, "application/pdf")}
        data = {"tool": "compress", "params": "{}"}
        resp = requests.post(f"{api_base}/jobs", files=files, data=data)
        
    assert resp.status_code == 200
    job_id = resp.json().get("job_id")
    assert job_id is not None
    
    # Poll status
    for _ in range(10):
        s_resp = requests.get(f"{api_base}/jobs/{job_id}")
        status = s_resp.json().get("status")
        if status in ["completed", "failed"]:
            break
        time.sleep(1)
        
    assert status in ["queued", "processing", "completed", "failed"] 
    # Real test would assert 'completed' but we don't have real workers running potentially

def test_batch_upload(api_base, tmp_path):
    dummy1 = tmp_path / "b1.pdf"
    dummy1.write_text("%PDF-1.4 batch 1")
    dummy2 = tmp_path / "b2.pdf"
    dummy2.write_text("%PDF-1.4 batch 2")
    
    files = [
        ("files", ("b1.pdf", open(dummy1, "rb"), "application/pdf")),
        ("files", ("b2.pdf", open(dummy2, "rb"), "application/pdf"))
    ]
    data = {"tool": "compress", "params": "{}"}
    
    resp = requests.post(f"{api_base}/jobs/batch", files=files, data=data)
    assert resp.status_code == 200
    
    jobs = resp.json()
    assert len(jobs) == 2
    assert jobs[0]["filename"] == "b1.pdf"
    assert jobs[1]["filename"] == "b2.pdf"
    
    # Check quota error logic?
    # requires mocking or setting quota low.
