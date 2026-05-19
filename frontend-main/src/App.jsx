import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/shell/AppShell.jsx";
import {
  AccountPage,
  AuthPage,
  LibrariesPage,
  LibraryDetailPage,
  NotFoundPage,
  OverviewPage,
  SetupPage,
  StatusPage
} from "./pages/index.js";

export default function App() {
  return (
    <Routes>
      <Route path="/sign-in" element={<AuthPage mode="login" />} />
      <Route path="/sign-up" element={<AuthPage mode="signup" />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<OverviewPage />} />
        <Route path="/console" element={<Navigate to="/dashboard" replace />} />
        <Route path="/libraries" element={<LibrariesPage />} />
        <Route path="/libraries/:vendor/*" element={<LibraryDetailPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/settings" element={<AccountPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
