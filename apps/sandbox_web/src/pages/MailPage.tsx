import { useCallback, useEffect, useState, type FormEvent } from "react";

import { createRecord, listRecords } from "../api";
import type { Mailbox } from "../types";

const path = "/api/mail/mailboxes";

export function MailPage() {
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    try {
      setMailboxes(await listRecords<Mailbox>(path));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load mailboxes");
    }
  }, []);
  useEffect(() => {
    void listRecords<Mailbox>(path)
      .then(setMailboxes)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createRecord<Mailbox>(path, {
        employee_id: Number(data.get("employee_id")),
        address: data.get("address"),
      });
      form.reset();
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create mailbox");
    }
  }

  return (
    <section>
      <div className="section-heading"><div><p className="module-code">05 / MAIL</p><h2>Mailboxes</h2></div><p>Create only a non-deliverable .invalid mailbox.</p></div>
      <form onSubmit={submit}>
        <label>Employee ID<input name="employee_id" type="number" min="1" required /></label>
        <label className="wide">Mailbox address<input name="address" type="email" placeholder="name@flowpilot.invalid" required /></label>
        <button type="submit">Create mailbox</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="records">{mailboxes.length === 0 ? <p>No mailboxes yet.</p> : mailboxes.map((mailbox) => (
        <article key={mailbox.id}><strong>#{mailbox.id} · {mailbox.address}</strong><span>Employee #{mailbox.employee_id}</span><em>{mailbox.status}</em></article>
      ))}</div>
    </section>
  );
}
