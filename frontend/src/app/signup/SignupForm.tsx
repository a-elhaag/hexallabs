"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "~/lib/supabase/client";

export function SignupForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }
    setDone(true);
    setLoading(false);
  }

  const fieldStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #a89080",
    background: "#fff",
    color: "#2c2c2c",
    fontSize: 14,
    marginBottom: 16,
    boxSizing: "border-box",
    outline: "none",
    transition: "border-color 300ms cubic-bezier(0.16, 1, 0.3, 1)",
  };

  if (done) {
    return (
      <div
        style={{
          background: "#f5f1ed",
          borderRadius: 16,
          padding: 40,
          width: 360,
          textAlign: "center",
        }}
      >
        <h1
          style={{
            color: "#2c2c2c",
            fontFamily: "var(--font-quicksand), sans-serif",
            fontSize: 24,
            fontWeight: 700,
            marginBottom: 16,
          }}
        >
          Check your email
        </h1>
        <p style={{ color: "#a89080", fontSize: 14 }}>
          Confirmation link sent to <strong>{email}</strong>.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ background: "#f5f1ed", borderRadius: 16, padding: 40, width: 360 }}
    >
      <h1
        style={{
          color: "#2c2c2c",
          fontFamily: "var(--font-quicksand), sans-serif",
          fontSize: 24,
          fontWeight: 700,
          marginBottom: 24,
        }}
      >
        Create account
      </h1>
      {error && (
        <p style={{ color: "#e55", fontSize: 14, marginBottom: 16 }}>{error}</p>
      )}
      <label style={{ display: "block", color: "#2c2c2c", fontSize: 13, marginBottom: 4 }}>
        Email
      </label>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        style={fieldStyle}
      />
      <label style={{ display: "block", color: "#2c2c2c", fontSize: 13, marginBottom: 4 }}>
        Password
      </label>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={6}
        style={{ ...fieldStyle, marginBottom: 24 }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          width: "100%",
          padding: "12px 0",
          borderRadius: 8,
          border: "none",
          background: "#6290c3",
          color: "#fff",
          fontSize: 15,
          fontWeight: 600,
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.7 : 1,
          transition: "transform 300ms cubic-bezier(0.16, 1, 0.3, 1), opacity 300ms",
        }}
      >
        {loading ? "Creating…" : "Create account"}
      </button>
      <p style={{ marginTop: 20, textAlign: "center", fontSize: 13, color: "#a89080" }}>
        Have an account?{" "}
        <Link href="/login" style={{ color: "#6290c3" }}>
          Sign in
        </Link>
      </p>
    </form>
  );
}
