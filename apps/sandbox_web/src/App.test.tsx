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

  it("replaces an unknown route with the HRIS default", async () => {
    window.history.pushState({}, "", "/unknown");
    render(<App />);
    expect(window.location.pathname).toBe("/hris");
    expect(screen.getByRole("heading", { name: "Employee profiles" })).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  });

  it("navigates between modules without a document reload", async () => {
    window.history.pushState({}, "", "/hris");
    render(<App />);
    await userEvent.click(screen.getByRole("link", { name: "ITSM" }));
    expect(window.location.pathname).toBe("/itsm");
    expect(screen.getByRole("heading", { name: "Onboarding tickets" })).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
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

it("submits the bounded HRIS transfer transition", async () => {
  const transferred = {
    id: 41001,
    first_name: "SyntheticTarget",
    last_name: "Mover001V1",
    work_email: "w7-mover-001-v1-target@flowpilot.invalid",
    department: "Synthetic Transfer Department",
    job_title: "Synthetic Transfer Lead",
    location: "Synthetic Transfer Location",
    start_date: "2027-01-10",
    status: "transferred",
    created_at: "2027-01-01T00:00:00Z",
  };
  const fetchMock = vi.mocked(fetch);
  fetchMock
    .mockResolvedValueOnce({ ok: true, json: async () => [] } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => transferred } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => [transferred] } as Response);

  window.history.pushState({}, "", "/hris");
  render(<App />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Show transitions" }));
  await user.type(screen.getByLabelText("Transfer employee ID"), "41001");
  await user.type(screen.getByLabelText("New department"), "Synthetic Transfer Department");
  await user.type(screen.getByLabelText("New job title"), "Synthetic Transfer Lead");
  await user.type(screen.getByLabelText("New location"), "Synthetic Transfer Location");
  await user.click(screen.getByRole("button", { name: "Transfer employee" }));

  expect(await screen.findByText("transferred")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    "/api/hris/employees/41001/transfer",
    expect.objectContaining({ method: "PATCH" }),
  );
});
