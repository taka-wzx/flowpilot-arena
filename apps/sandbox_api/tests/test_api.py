from fastapi.testclient import TestClient

EMPLOYEE = {
    "first_name": "Avery",
    "last_name": "Example",
    "work_email": "avery.example@flowpilot.invalid",
    "department": "Platform Engineering",
    "job_title": "Sandbox Engineer",
    "location": "Shanghai Lab",
    "start_date": "2026-08-03",
    "status": "confirmed",
}


def test_health_is_static(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sandbox-api", "version": "0.1.0"}


def test_complete_synthetic_onboarding_closure(client: TestClient) -> None:
    employee_response = client.post("/api/hris/employees", json=EMPLOYEE)
    assert employee_response.status_code == 201
    employee_id = employee_response.json()["id"]

    creations = [
        (
            "/api/itsm/tickets",
            {"employee_id": employee_id, "title": "Synthetic onboarding for Avery Example"},
        ),
        (
            "/api/iam/accounts",
            {"employee_id": employee_id, "username": "avery.example"},
        ),
        (
            "/api/assets/devices",
            {
                "employee_id": employee_id,
                "asset_tag": "SYN-LAPTOP-0001",
                "model": "ExampleBook 14",
            },
        ),
        (
            "/api/mail/mailboxes",
            {
                "employee_id": employee_id,
                "address": "avery.example@flowpilot.invalid",
            },
        ),
    ]

    for path, payload in creations:
        response = client.post(path, json=payload)
        assert response.status_code == 201
        assert response.json()["employee_id"] == employee_id

    list_paths = [
        "/api/hris/employees",
        "/api/itsm/tickets",
        "/api/iam/accounts",
        "/api/assets/devices",
        "/api/mail/mailboxes",
    ]
    for path in list_paths:
        response = client.get(path)
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_rejects_non_synthetic_email_and_unknown_employee(client: TestClient) -> None:
    real_domain_payload = {**EMPLOYEE, "work_email": "avery@example.com"}
    assert client.post("/api/hris/employees", json=real_domain_payload).status_code == 422

    response = client.post(
        "/api/itsm/tickets",
        json={"employee_id": 999, "title": "Synthetic missing employee"},
    )
    assert response.status_code == 404


def test_rejects_duplicate_business_keys(client: TestClient) -> None:
    assert client.post("/api/hris/employees", json=EMPLOYEE).status_code == 201
    duplicate = client.post("/api/hris/employees", json=EMPLOYEE)
    assert duplicate.status_code == 409
