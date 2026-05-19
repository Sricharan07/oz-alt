import { PanelLeftClose, PanelLeftOpen, Settings, Shield } from "lucide-react";
import { NavLink } from "react-router-dom";
import { runtimeConfig } from "../../config.js";
import { navItems } from "./navigation.js";

export function Sidebar({ collapsed, onToggleCollapse }) {
  const config = runtimeConfig();

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <nav className="nav-links" aria-label="Primary navigation">
        <div className="nav-group">
          <div className="sub-links">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sub-link-content ${isActive ? "active" : ""}`}
              >
                <span className="sidebar-icon">
                  <item.icon size={18} aria-hidden="true" />
                </span>
                {!collapsed ? <p>{item.label}</p> : null}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      <div className="sidebar-footer">
        <a className="sub-link-content sidebar-pro-link" href={config.adminUrl}>
          <span className="sidebar-icon">
            <Settings size={18} aria-hidden="true" />
          </span>
          {!collapsed ? (
            <span className="sidebar-pro-copy">
              <span className="sidebar-pro-title">Admin</span>
              <span className="sidebar-pro-subtitle">Catalog control</span>
            </span>
          ) : null}
        </a>
        <a className="sub-link-content" href="/privacy">
          <span className="sidebar-icon">
            <Shield size={18} aria-hidden="true" />
          </span>
          {!collapsed ? <p>Privacy</p> : null}
        </a>
        <button
          type="button"
          className="sidebar-collapse-btn"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
        </button>
      </div>
    </aside>
  );
}
