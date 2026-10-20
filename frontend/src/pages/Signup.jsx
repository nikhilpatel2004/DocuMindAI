import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";
import { apiFetch, setToken, setUser, isAuthenticated } from "../api";

export default function Signup() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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

    const cleanEmail = email.trim();
    const cleanUsername = username.trim();
    if (!cleanUsername || !cleanEmail || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }

    if (cleanUsername.length < 2 || cleanUsername.length > 40) {
      setError("Username must be 2-40 characters long.");
      return;
    }

    if (!/^[A-Za-z0-9][A-Za-z0-9 ._-]*$/.test(cleanUsername)) {
      setError(
        "Username can use letters, numbers, spaces, dots, underscores, or hyphens."
      );
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
      setError("Password must contain at least one letter and one number.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          password,
          username: cleanUsername,
        }),
      });

      if (data.access_token) {
        setToken(data.access_token);
        setUser(data.user);
        navigate("/", { replace: true });
      } else {
        setError("Account created, but no token was returned. Please log in.");
      }
    } catch (err) {
      setError(err.message || "Failed to register. Please check your details and try again.");
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
          <h1 className="auth-title">Create your account</h1>
          <p className="auth-subtitle">Get started with your private, isolated document workspace</p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: 18 }}>
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="signup-username">
              Username
            </label>
            <input
              id="signup-username"
              type="text"
              className="form-input"
              placeholder="How should we greet you?"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="nickname"
              maxLength={40}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-email">
              Email address
            </label>
            <input
              id="signup-email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-password">
              Password
            </label>
            <input
              id="signup-password"
              type="password"
              className="form-input"
              placeholder="At least 8 characters (letters + numbers)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
            <span className="form-hint">Must be 8+ characters with at least one letter and one number.</span>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-confirm-password">
              Confirm Password
            </label>
            <input
              id="signup-confirm-password"
              type="password"
              className="form-input"
              placeholder="Repeat your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
