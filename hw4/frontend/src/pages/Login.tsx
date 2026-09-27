import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { usePageContext } from "../state/PageContext";

export function Login() {
  const { signIn, user } = useAuth();
  const navigate = useNavigate();
  const { setContext } = usePageContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setContext({ page: "login", product_id: null });
  }, [setContext]);

  useEffect(() => {
    if (user) navigate("/products");
  }, [user, navigate]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(email, password);
      navigate("/products");
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page auth">
      <form className="card" onSubmit={submit}>
        <p className="eyebrow">Welcome back</p>
        <h1>Log in</h1>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="button button--solid button--lg" disabled={busy}>
          {busy ? "Signing in…" : "Log in"}
        </button>

        <p className="card__foot">
          New here? <Link to="/signup">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
