def test_w7_catalog_and_task_api(client) -> None:
    summary = client.get("/api/arena/w7/catalog")
    tasks = client.get("/api/arena/w7/tasks")
    detail = client.get("/api/arena/w7/tasks/w7-jml-joiner-001-v1")
    assert summary.status_code == 200
    assert summary.json()["template_count"] == 30
    assert summary.json()["instance_count"] == 90
    assert tasks.status_code == 200
    assert len(tasks.json()) == 90
    assert detail.status_code == 200
    assert detail.json()["fixture_version"] == "w7-jml-fixture/1.0"


def test_w7_reset_grade_and_reporting_boundary(client) -> None:
    task_id = "w7-jml-joiner-001-v1"
    first = client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    second = client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    grade = client.post(f"/api/arena/w7/tasks/{task_id}/grade")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert grade.status_code == 200
    assert grade.json()["passed"] is False

    reporting_id = "w7-jml-joiner-011-v1"
    assert client.post(f"/api/arena/w7/tasks/{reporting_id}/reset-seed", json={}).status_code == 403
    assert client.post(f"/api/arena/w7/tasks/{reporting_id}/grade").status_code == 403
    assert client.get("/api/arena/w7/tasks/w7-jml-unknown-001-v1").status_code == 404
