import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("identifies the W1 foundation boundary", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FlowPilot Arena" })).toBeInTheDocument();
    expect(screen.getByText("W1 / Foundation")).toBeInTheDocument();
    expect(screen.getByText(/No Sandbox or enterprise application pages/)).toBeInTheDocument();
  });
});
