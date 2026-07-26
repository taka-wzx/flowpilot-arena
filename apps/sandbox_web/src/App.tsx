import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";

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

export function App() {
  return (
    <BrowserRouter>
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
          <NavLink key={path} to={path}>
            {label}
          </NavLink>
        ))}
      </nav>
      <main>
        <Routes>
          <Route path="/hris" element={<HrisPage />} />
          <Route path="/itsm" element={<ItsmPage />} />
          <Route path="/iam" element={<IamPage />} />
          <Route path="/assets" element={<AssetPage />} />
          <Route path="/mail" element={<MailPage />} />
          <Route path="*" element={<Navigate to="/hris" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
