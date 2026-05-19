import { KeyRound, LogIn, Menu, Search } from "lucide-react";
import { Link } from "react-router-dom";

export function Topbar({ collapsed, mobileOpen, onToggleMobile }) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="mobile-nav-toggle"
        onClick={onToggleMobile}
        aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={mobileOpen}
      >
        <Menu size={15} aria-hidden="true" />
        {mobileOpen ? "Close" : "Menu"}
      </button>

      <Link className={`topbar-brand ${collapsed ? "collapsed" : ""}`} to="/dashboard" aria-label="Oz dashboard">
        <span className="brand-mark">oz</span>
        {!collapsed ? <span className="topbar-brand-text">Console</span> : null}
      </Link>

      <div className="right-container">
        <div className="top-buttons">
          <Link className="top-button search-bar" to="/libraries">
            <Search size={15} aria-hidden="true" />
            <span>Search catalog</span>
          </Link>
          <a className="top-button" href="/device" aria-label="Approve CLI device">
            <KeyRound size={15} aria-hidden="true" />
            <span>Device</span>
          </a>
          <Link className="top-button" to="/sign-in" aria-label="Sign in">
            <LogIn size={15} aria-hidden="true" />
            <span>Sign in</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
