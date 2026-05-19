import { useCallback, useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar.jsx";
import { Topbar } from "./Topbar.jsx";

export function AppShell() {
  const location = useLocation();
  const contentRef = useRef(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const scrollToTop = useCallback(() => {
    contentRef.current?.scrollTo?.({ top: 0, left: 0, behavior: "auto" });
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    scrollToTop();
  }, [location.pathname, location.search, scrollToTop]);

  useEffect(() => {
    if (typeof document === "undefined") {
      return undefined;
    }
    if (!mobileOpen) {
      return undefined;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileOpen]);

  return (
    <div className={`dashboard-layout ${mobileOpen ? "sidebar-open" : ""} ${collapsed ? "sidebar-collapsed" : ""}`}>
      <Topbar collapsed={collapsed} mobileOpen={mobileOpen} onToggleMobile={() => setMobileOpen((open) => !open)} />
      <div className="main-container">
        <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed((value) => !value)} />
        <button type="button" className="sidebar-backdrop" onClick={() => setMobileOpen(false)} aria-label="Close navigation menu" />
        <main className="page-content" ref={contentRef}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
