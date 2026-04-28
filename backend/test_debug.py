from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()

with TestClient(app) as client:
    # Test GET first
    r = client.get("/api/documents")
    print("GET Status:", r.status_code)
    print("GET Count:", len(r.json()))

    # Test DELETE
    r = client.delete("/api/documents")
    print("DELETE Status:", r.status_code)
    print("DELETE Body:", r.text)

    # Test GET after
    r = client.get("/api/documents")
    print("GET After Status:", r.status_code)
    print("GET After Count:", len(r.json()))

