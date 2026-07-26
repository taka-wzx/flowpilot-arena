import { useCallback, useEffect, useState, type FormEvent } from "react";

import { createRecord, listRecords } from "../api";
import type { Account } from "../types";

const path = "/api/iam/accounts";

export function IamPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    try {
      setAccounts(await listRecords<Account>(path));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load accounts");
    }
  }, []);
  useEffect(() => {
    void listRecords<Account>(path)
      .then(setAccounts)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createRecord<Account>(path, {
        employee_id: Number(data.get("employee_id")),
        username: data.get("username"),
      });
      form.reset();
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create account");
    }
  }

  return (
    <section>
      <div className="section-heading"><div><p className="module-code">03 / IAM</p><h2>Ordinary accounts</h2></div><p>W2 permits only the basic employee role; no administrator privileges.</p></div>
      <form onSubmit={submit}>
        <label>Employee ID<input name="employee_id" type="number" min="1" required /></label>
        <label>Username<input name="username" pattern="[a-z][a-z0-9.]{2,79}" required /></label>
        <button type="submit">Create account</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="records">{accounts.length === 0 ? <p>No IAM accounts yet.</p> : accounts.map((account) => (
        <article key={account.id}><strong>#{account.id} · {account.username}</strong><span>Employee #{account.employee_id} · role {account.role}</span><em>{account.status}</em></article>
      ))}</div>
    </section>
  );
}
