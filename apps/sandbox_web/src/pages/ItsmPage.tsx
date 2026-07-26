import { useCallback, useEffect, useState, type FormEvent } from "react";

import { createRecord, listRecords } from "../api";
import type { Ticket } from "../types";

const path = "/api/itsm/tickets";

export function ItsmPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    try {
      setTickets(await listRecords<Ticket>(path));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load tickets");
    }
  }, []);
  useEffect(() => {
    void listRecords<Ticket>(path)
      .then(setTickets)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createRecord<Ticket>(path, {
        employee_id: Number(data.get("employee_id")),
        title: data.get("title"),
      });
      form.reset();
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create ticket");
    }
  }

  return (
    <section>
      <div className="section-heading"><div><p className="module-code">02 / ITSM</p><h2>Onboarding tickets</h2></div><p>Open one ticket for the HRIS employee ID.</p></div>
      <form onSubmit={submit}>
        <label>Employee ID<input name="employee_id" type="number" min="1" required /></label>
        <label className="wide">Ticket title<input name="title" required /></label>
        <button type="submit">Create ticket</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="records">{tickets.length === 0 ? <p>No onboarding tickets yet.</p> : tickets.map((ticket) => (
        <article key={ticket.id}><strong>#{ticket.id} · {ticket.title}</strong><span>Employee #{ticket.employee_id}</span><em>{ticket.status}</em></article>
      ))}</div>
    </section>
  );
}
