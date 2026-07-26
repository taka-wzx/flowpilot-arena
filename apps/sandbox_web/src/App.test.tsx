import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const routes = [
  ["/hris", "Employee profiles"],
  ["/itsm", "Onboarding tickets"],
  ["/iam", "Ordinary accounts"],
  ["/assets", "Device assignments"],
  ["/mail", "Mailboxes"],
] as const;

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Sandbox module routes", () => {
  it.each(routes)("renders %s", async (route, heading) => {
    window.history.pushState({}, "", route);
    render(<App />);
    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  });
});

it("submits the synthetic HRIS employee and refreshes the list", async () => {
  const employee = {
    id: 1,
    first_name: "Avery",
    last_name: "Example",
    work_email: "avery.example@flowpilot.invalid",
    department: "Platform Engineering",
    job_title: "Sandbox Engineer",
    location: "Shanghai Lab",
    start_date: "2026-08-03",
    status: "confirmed",
    created_at: "2026-07-26T00:00:00Z",
  };
  const fetchMock = vi.mocked(fetch);
  fetchMock
    .mockResolvedValueOnce({ ok: true, json: async () => [] } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => employee } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => [employee] } as Response);

  window.history.pushState({}, "", "/hris");
  render(<App />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("First name"), "Avery");
  await user.type(screen.getByLabelText("Last name"), "Example");
  await user.type(screen.getByLabelText("Work email"), "avery.example@flowpilot.invalid");
  await user.type(screen.getByLabelText("Department"), "Platform Engineering");
  await user.type(screen.getByLabelText("Job title"), "Sandbox Engineer");
  await user.type(screen.getByLabelText("Location"), "Shanghai Lab");
  await user.type(screen.getByLabelText("Start date"), "2026-08-03");
  await user.click(screen.getByRole("button", { name: "Confirm employee" }));

  expect(await screen.findByText("#1 · Avery Example")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    "/api/hris/employees",
    expect.objectContaining({ method: "POST" }),
  );
});
