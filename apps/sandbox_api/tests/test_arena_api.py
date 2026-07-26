from fastapi.testclient import TestClient


def test_arena_api_reset_manual_completion_grade_and_baseline(client: TestClient) -> None:
    tasks_response = client.get("/api/arena/tasks")
    assert tasks_response.status_code == 200
    assert len(tasks_response.json()) == 10
    task = tasks_response.json()[0]
    task_id = task["task_id"]
    detail = client.get(f"/api/arena/tasks/{task_id}")
    assert detail.status_code == 200
    assert detail.json()["canonical_checksum"] == task["canonical_checksum"]

    first_reset = client.post(f"/api/arena/tasks/{task_id}/reset-seed")
    second_reset = client.post(f"/api/arena/tasks/{task_id}/reset-seed")
    assert first_reset.status_code == second_reset.status_code == 200
    assert first_reset.json() == second_reset.json()
    assert first_reset.json()["seed_summary"]["counts"]["employees"] == 2

    employee_id = first_reset.json()["seed_summary"]["employee_ids"][0]
    creations = [
        (
            "/api/itsm/tickets",
            {"employee_id": employee_id, "title": "Synthetic onboarding: Nova Quill [W3-001]"},
        ),
        ("/api/iam/accounts", {"employee_id": employee_id, "username": "nova.quill.w3001"}),
        (
            "/api/assets/devices",
            {
                "employee_id": employee_id,
                "asset_tag": "SYN-W3-001-LAPTOP",
                "model": "ExampleBook Air 13",
            },
        ),
        (
            "/api/mail/mailboxes",
            {"employee_id": employee_id, "address": "nova.quill.w3001@flowpilot.invalid"},
        ),
    ]
    for path, payload in creations:
        response = client.post(path, json=payload)
        assert response.status_code == 201
        assert response.json()["arena_task_id"] == task_id

    first_grade = client.post(f"/api/arena/tasks/{task_id}/grade")
    second_grade = client.post(f"/api/arena/tasks/{task_id}/grade")
    assert first_grade.status_code == second_grade.status_code == 200
    assert first_grade.json() == second_grade.json()
    assert first_grade.json()["total_score"] == 100
    assert first_grade.json()["passed"] is True

    baseline = client.post(
        "/api/arena/baselines",
        json={
            "record_id": "baseline-w3-api-sample-001",
            "task_id": task_id,
            "operator_alias": "anon-api-operator",
            "started_at": "2026-07-26T05:00:00Z",
            "ended_at": "2026-07-26T05:09:30Z",
            "action_count": 16,
            "notes": "Synthetic API acceptance record",
        },
    )
    assert baseline.status_code == 201
    assert baseline.json()["duration_seconds"] == 570
    assert client.get("/api/arena/baselines").json()[0]["record_id"] == "baseline-w3-api-sample-001"


def test_arena_api_rejects_unknown_task_and_arbitrary_payload(client: TestClient) -> None:
    assert client.post("/api/arena/tasks/w3-joiner-999/reset-seed").status_code == 404
    response = client.post(
        "/api/arena/tasks/w3-joiner-001/reset-seed",
        json={"sql": "DROP TABLE employees"},
    )
    assert response.status_code == 422

    invalid_baseline = client.post(
        "/api/arena/baselines",
        json={
            "record_id": "baseline-w3-invalid-001",
            "task_id": "w3-joiner-001",
            "operator_alias": "anon-test",
            "started_at": "2026-07-26T05:00:00Z",
            "ended_at": "2026-07-26T05:01:00Z",
            "action_count": 1,
            "final_score": 0,
            "browser_telemetry": "forbidden",
        },
    )
    assert invalid_baseline.status_code == 422
