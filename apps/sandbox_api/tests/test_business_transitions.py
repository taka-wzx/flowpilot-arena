def test_mover_transfer_and_close_are_strict_typed_transitions(client) -> None:
    task_id = "w7-jml-mover-001-v1"
    detail = client.get(f"/api/arena/w7/tasks/{task_id}").json()
    employee_id = detail["supplied_values"]["employee_id"]
    client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})

    transfer = client.patch(
        f"/api/hris/employees/{employee_id}/transfer",
        json={
            "department": detail["supplied_values"]["new_department"],
            "job_title": detail["supplied_values"]["new_job_title"],
            "location": detail["supplied_values"]["new_location"],
        },
    )
    close = client.patch(f"/api/itsm/employees/{employee_id}/close", json={})
    assert transfer.status_code == 200
    assert transfer.json()["status"] == "transferred"
    assert close.status_code == 200
    assert close.json()["status"] == "closed"
    assert client.patch(f"/api/itsm/employees/{employee_id}/close", json={}).status_code == 409
    assert (
        client.patch(
            f"/api/hris/employees/{employee_id}/disable",
            json={"selector": "#unsafe"},
        ).status_code
        == 422
    )


def test_leaver_transitions_are_non_deleting_and_fail_closed(client) -> None:
    task_id = "w7-jml-leaver-001-v1"
    detail = client.get(f"/api/arena/w7/tasks/{task_id}").json()
    employee_id = detail["supplied_values"]["employee_id"]
    client.post(f"/api/arena/w7/tasks/{task_id}/reset-seed", json={})
    transitions = (
        (f"/api/hris/employees/{employee_id}/disable", "disabled"),
        (f"/api/itsm/employees/{employee_id}/close", "closed"),
        (f"/api/iam/employees/{employee_id}/revoke", "revoked"),
        (f"/api/assets/employees/{employee_id}/release", "released"),
        (f"/api/mail/employees/{employee_id}/disable", "disabled"),
    )
    for path, expected_status in transitions:
        response = client.patch(path, json={})
        assert response.status_code == 200
        assert response.json()["status"] == expected_status
        assert client.patch(path, json={}).status_code == 409

    assert client.delete(f"/api/hris/employees/{employee_id}").status_code == 404
    grade = client.post(f"/api/arena/w7/tasks/{task_id}/grade")
    assert grade.status_code == 200
    assert grade.json()["total_score"] == 100
    assert grade.json()["passed"] is True
