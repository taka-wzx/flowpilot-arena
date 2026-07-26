import { useCallback, useEffect, useState, type FormEvent } from "react";

import { createRecord, listRecords } from "../api";
import type { Employee } from "../types";

const path = "/api/hris/employees";

export function HrisPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setEmployees(await listRecords<Employee>(path));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load employees");
    }
  }, []);

  useEffect(() => {
    void listRecords<Employee>(path)
      .then(setEmployees)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createRecord<Employee>(path, {
        first_name: data.get("first_name"),
        last_name: data.get("last_name"),
        work_email: data.get("work_email"),
        department: data.get("department"),
        job_title: data.get("job_title"),
        location: data.get("location"),
        start_date: data.get("start_date"),
      });
      form.reset();
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create employee");
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div><p className="module-code">01 / HRIS</p><h2>Employee profiles</h2></div>
        <p>Create the synthetic employee first and reuse the returned ID in every module.</p>
      </div>
      <form onSubmit={submit}>
        <label>First name<input name="first_name" required /></label>
        <label>Last name<input name="last_name" required /></label>
        <label>Work email<input name="work_email" type="email" placeholder="name@flowpilot.invalid" required /></label>
        <label>Department<input name="department" required /></label>
        <label>Job title<input name="job_title" required /></label>
        <label>Location<input name="location" required /></label>
        <label>Start date<input name="start_date" type="date" required /></label>
        <button type="submit">Confirm employee</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="records" aria-live="polite">
        {employees.length === 0 ? <p>No synthetic employees yet.</p> : employees.map((employee) => (
          <article key={employee.id}>
            <strong>#{employee.id} · {employee.first_name} {employee.last_name}</strong>
            <span>{employee.job_title} · {employee.department}</span>
            <span>{employee.work_email} · {employee.location} · {employee.start_date}</span>
            <em>{employee.status}</em>
          </article>
        ))}
      </div>
    </section>
  );
}
