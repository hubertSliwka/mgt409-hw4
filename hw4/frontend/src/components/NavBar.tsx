import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products", end: false },
  { to: "/about", label: "About Us", end: false },
];

export function NavBar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="nav">
      <NavLink to="/" className="nav__brand">
        <span className="nav__mark">CC</span>
        <span>
          <strong>Campus Customs</strong>
          <em>New Haven, CT</em>
        </span>
      </NavLink>

      <nav className="nav__links" aria-label="Main">
        {LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="nav__account">
        {user ? (
          <>
            <span className="nav__hello">Hi, {user.first_name}</span>
            <button
              type="button"
              className="button button--ghost"
              onClick={() => {
                signOut();
                navigate("/");
              }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="button button--ghost">
              Log in
            </NavLink>
            <NavLink to="/signup" className="button button--solid">
              Create account
            </NavLink>
          </>
        )}
      </div>
    </header>
  );
}
