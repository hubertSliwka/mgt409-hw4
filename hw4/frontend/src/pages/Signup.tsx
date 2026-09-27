import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { usePageContext } from "../state/PageContext";

export function Signup() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const { setContext } = usePageContext();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setContext({ page: "signup", product_id: null });
  }, [setContext]);

  const update = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("The two passwords do not match.");
      return;
    }
    if (form.password.length < 8) {
      setError("Use at least 8 characters for the password.");
      return;
    }
    setBusy(true);
    try {
      const { confirm: _confirm, ...payload } = form;
      await register(payload);
      navigate("/products");
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "Could not create the account.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page auth">
      <form className="card" onSubmit={submit}>
        <p className="eyebrow">Two minutes, tops</p>
        <h1>Create account</h1>

        <div className="card__row">
          <label>
            First name
            <input value={form.first_name} onChange={update("first_name")} autoComplete="given-name" required />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update("last_name")} autoComplete="family-name" required />
          </label>
        </div>

        <label>
          Email
          <input type="email" value={form.email} onChange={update("email")} autoComplete="email" required />
        </label>

        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={update("password")}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        <label>
          Confirm password
          <input
            type="password"
            value={form.confirm}
            onChange={update("confirm")}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="button button--solid button--lg" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>

        <p className="card__foot">
          Already have one? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
