import { Link, useSearchParams } from "react-router-dom";

export function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const [params] = useSearchParams();
  const next = safeNext(params.get("next") || "");

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="brand compact" to="/dashboard">
          <span className="brand-mark">oz</span>
          <span className="brand-text">Console</span>
        </Link>
        <h1>{isSignup ? "Create account" : "Sign in"}</h1>
        <form method="post" action={isSignup ? "/signup" : "/login"} className="auth-form">
          {next ? <input type="hidden" name="next" value={next} /> : null}
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete={isSignup ? "new-password" : "current-password"} minLength={12} required />
          </label>
          {isSignup ? (
            <label>
              Confirm password
              <input name="confirm_password" type="password" autoComplete="new-password" minLength={12} required />
            </label>
          ) : null}
          <button className="button primary wide" type="submit">
            {isSignup ? "Create account" : "Sign in"}
          </button>
        </form>
        <p className="auth-switch">
          {isSignup ? "Already have an account?" : "Need an account?"}{" "}
          <Link to={`${isSignup ? "/sign-in" : "/sign-up"}${next ? `?next=${encodeURIComponent(next)}` : ""}`}>
            {isSignup ? "Sign in" : "Create one"}
          </Link>
        </p>
      </section>
    </main>
  );
}

function safeNext(value) {
  return value.startsWith("/") && !value.startsWith("//") ? value : "";
}
