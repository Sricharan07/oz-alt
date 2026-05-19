import { KeyRound, LogIn, Menu, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useConsoleAccount } from "../../hooks/useConsoleAccount.js";

export function Topbar({ collapsed, mobileOpen, onToggleMobile }) {
  const account = useConsoleAccount();
  const emailName = account.user?.email ? account.user.email.split("@")[0] : "Account";

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
          {account.authenticated ? (
            <>
              <Link className="top-button" to="/settings" aria-label="Open account">
                <LogIn size={15} aria-hidden="true" />
                <span>{emailName}</span>
              </Link>
              <button className="top-button" type="button" onClick={() => void account.logout()}>
                <span>Logout</span>
              </button>
            </>
          ) : (
            <Link className="top-button" to="/sign-in" aria-label="Sign in">
              <LogIn size={15} aria-hidden="true" />
              <span>Sign in</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
