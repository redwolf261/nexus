"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      // OAuth2 password flow uses form data
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${API_BASE}/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Login failed" }));
        throw new Error(body.detail || "Invalid credentials");
      }

      const data = await res.json();
      localStorage.setItem("nexus_token", data.access_token);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      {/* Background grid */}
      <div className="fixed inset-0 opacity-[0.03] bg-[radial-gradient(#00ff88_1px,transparent_1px)] [background-size:32px_32px]" />

      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono text-[10px] text-emerald-500 tracking-[0.3em] uppercase">Secure Terminal</span>
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <h1 className="text-4xl font-bold text-white font-mono tracking-widest">NEXUS</h1>
          <p className="text-slate-400 mt-2 text-sm tracking-wider font-mono">
            Karnataka State Police Intelligence Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
          <div className="mb-6 flex items-center gap-2">
            <div className="h-px flex-1 bg-slate-700" />
            <span className="text-slate-500 text-xs font-mono tracking-widest uppercase">Authentication Required</span>
            <div className="h-px flex-1 bg-slate-700" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-widest">
                Officer ID / Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 font-mono text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all placeholder-slate-600"
                placeholder="Enter officer ID..."
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-widest">
                Access Code
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 font-mono text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all placeholder-slate-600"
                placeholder="••••••••••••"
              />
            </div>

            {error && (
              <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg px-4 py-3 text-rose-300 text-xs font-mono">
                ⚠ {error}
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 px-6 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-mono font-bold tracking-widest uppercase rounded-lg transition-all shadow-lg shadow-emerald-900/30 text-sm"
            >
              {loading ? "AUTHENTICATING..." : "ESTABLISH SECURE LINK"}
            </button>
          </form>

          {/* Demo credentials box */}
          <div className="mt-6 p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
            <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">Demo Credentials</p>
            <div className="grid grid-cols-2 gap-x-4 text-xs font-mono">
              <div>
                <span className="text-slate-500">Admin:</span>{" "}
                <button
                  type="button"
                  className="text-emerald-400 hover:text-emerald-300"
                  onClick={() => { setUsername("admin"); setPassword("nexus_admin_2024"); }}
                >
                  admin / nexus_admin_2024
                </button>
              </div>
              <div>
                <span className="text-slate-500">Analyst:</span>{" "}
                <button
                  type="button"
                  className="text-cyan-400 hover:text-cyan-300"
                  onClick={() => { setUsername("analyst1"); setPassword("analyst_pass_2024"); }}
                >
                  analyst1 / analyst_pass_2024
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-slate-600 text-xs font-mono mt-6 tracking-wider">
          NEXUS v1.0.0-rc1 · Karnataka State Police · Classified System
        </p>
      </div>
    </div>
  );
}
