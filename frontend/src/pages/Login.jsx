import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";
import { apiFetch, setToken, setUser, isAuthenticated } from "../api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated()) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (data.access_token) {
        setToken(data.access_token);
        setUser(data.user);
        navigate("/", { replace: true });
      } else {
        setError("Login succeeded but no token was returned.");
      }
    } catch (err) {
      setError(err.message || "Failed to log in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper app-shell">
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="app-nav-brand" style={{ textDecoration: "none" }}>
            <BrandLogo size={34} />
            <span className="app-nav-name" style={{ fontSize: 18 }}>DocuMind AI</span>
          </Link>
          <h1 className="auth-title">Welcome back</h1>
          <p className="auth-subtitle">Log in to your private document workspace</p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: 18 }}>
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-email">
              Email address
            </label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", padding: "11px 16px", marginTop: 4 }}
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div className="auth-footer">
          Don't have an account? <Link to="/signup">Create an account</Link>
        </div>
      </div>
    </div>
  );
}
