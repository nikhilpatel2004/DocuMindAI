import { NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo";
import { getUser, logout } from "../api";

const linkClass = ({ isActive }) => "app-nav-link" + (isActive ? " active" : "");

export default function AppNav() {
  const user = getUser();
  const displayName = user?.username || user?.email;

  return (
    <header className="app-nav">
      <div className="app-nav-inner">
        <div className="app-nav-brand">
          <BrandLogo size={30} />
          <span className="app-nav-name">DocuMind AI</span>
        </div>

        <nav className="app-nav-links">
          <NavLink to="/" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/upload" className={linkClass}>
            Upload
          </NavLink>
          <NavLink to="/chat" className={linkClass}>
            Chat
          </NavLink>
        </nav>

        <div className="user-nav-section">
          {displayName && (
            <span className="user-email-chip" title={user?.email || displayName}>
              {displayName}
            </span>
          )}
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={logout}
            title="Log out of your account"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
