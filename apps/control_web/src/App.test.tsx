import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import App from "./App";
import { clearInMemoryAuth } from "./auth";

describe("App", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    window.sessionStorage.clear();
    clearInMemoryAuth();
  });

  it("shows only the minimal W10 signed-out identity experience", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FlowPilot Arena" })).toBeInTheDocument();
    expect(screen.getByText("W10 / Identity boundary")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Sign in with local OIDC" }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/approval/iu)).not.toBeInTheDocument();
  });
});
