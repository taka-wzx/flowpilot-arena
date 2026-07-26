import { useEffect, useState, type MouseEvent } from "react";

import "./App.css";
import { AssetPage } from "./pages/AssetPage";
import { HrisPage } from "./pages/HrisPage";
import { IamPage } from "./pages/IamPage";
import { ItsmPage } from "./pages/ItsmPage";
import { MailPage } from "./pages/MailPage";

const modules = [
  ["/hris", "HRIS"],
  ["/itsm", "ITSM"],
  ["/iam", "IAM"],
  ["/assets", "Asset"],
  ["/mail", "Mail"],
] as const;

const pages = {
  "/hris": HrisPage,
  "/itsm": ItsmPage,
  "/iam": IamPage,
  "/assets": AssetPage,
  "/mail": MailPage,
} as const;

export function App() {
  const [currentPath, setCurrentPath] = useState<keyof typeof pages>(() => normalizedPath());
  const CurrentPage = pages[currentPath];

  useEffect(() => {
    const handlePopState = () => setCurrentPath(normalizedPath());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (event: MouseEvent<HTMLAnchorElement>, path: keyof typeof pages) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    event.preventDefault();
    window.history.pushState({}, "", path);
    setCurrentPath(path);
  };

  return (
    <>
      <header className="app-header">
        <div>
          <p className="eyebrow">FlowPilot Arena · W2</p>
          <h1>Synthetic Enterprise Sandbox</h1>
          <p>Manual onboarding only. No agent, grader, reset, or real enterprise data.</p>
        </div>
        <span className="environment-badge">SYNTHETIC DATA</span>
      </header>
      <nav aria-label="Sandbox modules">
        {modules.map(([path, label]) => (
          <a
            key={path}
            href={path}
            className={path === currentPath ? "active" : undefined}
            onClick={(event) => navigate(event, path)}
          >
            {label}
          </a>
        ))}
      </nav>
      <main>
        <CurrentPage />
      </main>
    </>
  );
}

function normalizedPath(): keyof typeof pages {
  const requestedPath = window.location.pathname;
  if (requestedPath in pages) {
    return requestedPath as keyof typeof pages;
  }
  window.history.replaceState({}, "", "/hris");
  return "/hris";
}
