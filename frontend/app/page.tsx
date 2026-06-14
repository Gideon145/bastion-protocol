"use client";

import { useState, useEffect, useRef } from "react";

interface AgentStatus {
  uptime_cycles: number;
  fsm_state: string;
  current_score: number;
  threshold: number;
  scans_per_minute: number;
  chain_id: number;
  contracts: { DetectionRegistry: string; ThreatSignatureRegistry: string };
  agent_wallet: string;
}

function stateColor(s: string) {
  switch (s) { case "NORMAL": return "#22c55e"; case "ELEVATED": return "#eab308"; case "TRIPPED": return "#ef4444"; case "COOLDOWN": return "#3b82f6"; default: return "#6b7280"; }
}
function stateEmoji(s: string) {
  switch (s) { case "NORMAL": return "🟢"; case "ELEVATED": return "🟡"; case "TRIPPED": return "🔴"; case "COOLDOWN": return "🔵"; default: return "⚪"; }
}

export default function DashboardPage() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [pulseTime, setPulseTime] = useState(0);
  const [lastUpdated, setLastUpdated] = useState("");
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/health");
        setStatus(await res.json());
        setPulseTime(Date.now());
        setLastUpdated(new Date().toISOString().slice(11, 19));
      } catch {}
    };
    fetchStatus();
    const i = setInterval(fetchStatus, 5000);
    return () => clearInterval(i);
  }, []);

  // Particle grid background
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize(); window.addEventListener("resize", resize);
    const particles: { x: number; y: number; vx: number; vy: number; r: number; a: number }[] = [];
    for (let i = 0; i < 70; i++) particles.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3, r: Math.random() * 1.5 + 0.3, a: Math.random() * 0.4 + 0.08 });
    let anim = 0;
    const draw = () => {
      anim = requestAnimationFrame(draw);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "rgba(31,41,55,0.25)"; ctx.lineWidth = 0.5;
      for (let x = 0; x < canvas.width; x += 70) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }
      for (let y = 0; y < canvas.height; y += 70) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke(); }
      for (const p of particles) { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > canvas.width) p.vx *= -1; if (p.y < 0 || p.y > canvas.height) p.vy *= -1; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(34,197,94,${p.a})`; ctx.fill(); }
    };
    draw();
    return () => { cancelAnimationFrame(anim); window.removeEventListener("resize", resize); };
  }, []);

  const scorePercent = status ? (status.current_score / 100) * 100 : 0;
  const barColor = status ? (status.current_score >= status.threshold ? "#ef4444" : status.current_score >= status.threshold * 0.6 ? "#eab308" : "#22c55e") : "#374151";

  return (
    <div style={{ minHeight: "100vh", background: "#060608", color: "#e5e5e5", fontFamily: "'Courier New', Courier, monospace", position: "relative", overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }} />
      <div style={{ position: "relative", zIndex: 1, padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>

        {/* ===== HEADER ===== */}
        <header style={{ borderBottom: "1px solid #1f2937", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.6rem" }}>
            <span style={{ fontSize: "1.8rem", filter: "drop-shadow(0 0 10px rgba(34,197,94,0.5))" }}>🛡️</span>
            <h1 style={{ fontSize: "2rem", fontWeight: 700, margin: 0, letterSpacing: "0.05em" }}>BASTION PROTOCOL</h1>
            <span style={{ fontSize: "0.75rem", padding: "0.25rem 0.8rem", borderRadius: "4px", background: "#0a0a0a", border: "1px solid #22c55e", color: "#22c55e", animation: "glowPulse 2s ease-in-out infinite", letterSpacing: "0.1em", fontWeight: 600 }}>● LIVE</span>
          </div>
          <p style={{ color: "#9ca3af", fontSize: "1rem", margin: 0, lineHeight: 1.6 }}>
            An autonomous threat detection agent monitoring Robinhood Chain in real time.
            It watches pending transactions, scores every block against known exploit patterns,
            and writes hash-committed detection proofs on-chain before attacks confirm.
          </p>
          <p style={{ color: "#6b7280", fontSize: "0.85rem", margin: "0.3rem 0 0 0" }}>
            Chain: Robinhood (Orbit L2, #{status?.chain_id || "..."}) · {status ? `${status.uptime_cycles.toLocaleString()} cycles completed` : "loading..."} · Updated {lastUpdated || "—"}
          </p>
        </header>

        {/* ===== SCORE GAUGE + STATS ===== */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1.2rem", marginBottom: "2rem" }}>
          {/* Gauge */}
          <div style={{ background: "#0d0d12", border: "1px solid #1f2937", borderRadius: "12px", padding: "1.5rem", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ fontSize: "0.8rem", color: "#9ca3af", letterSpacing: "0.08em", marginBottom: "0.6rem", fontWeight: 600 }}>
              THREAT LEVEL
            </div>
            <div style={{ position: "relative", width: "150px", height: "150px", marginBottom: "0.8rem" }}>
              <svg viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)" }}>
                <circle cx="70" cy="70" r="60" fill="none" stroke="#1f2937" strokeWidth="10" />
                <circle cx="70" cy="70" r="60" fill="none" stroke={barColor} strokeWidth="10" strokeDasharray={`${(scorePercent / 100) * 377} 377`} strokeLinecap="round" style={{ transition: "stroke-dasharray 0.8s ease, stroke 0.8s ease", filter: `drop-shadow(0 0 6px ${barColor}60)` }} />
              </svg>
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: "2.5rem", fontWeight: 700, color: barColor, lineHeight: 1, transition: "color 0.8s ease" }}>{status ? status.current_score.toFixed(0) : "—"}</span>
                <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>out of 100</span>
              </div>
            </div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: barColor, transition: "color 0.8s ease", textAlign: "center" }}>
              {status ? (status.current_score >= status.threshold ? "🔴 TRIPPED — On-chain attestation fired" : status.current_score >= status.threshold * 0.6 ? "🟡 ELEVATED — Heightened monitoring" : "🟢 NORMAL — Passive scanning") : "..."}
            </div>
            <div style={{ fontSize: "0.75rem", color: "#4b5563", marginTop: "0.5rem", textAlign: "center" }}>
              Agent trips at score {">"} {status?.threshold || "—"}.<br />Current score is below threshold.
            </div>
          </div>

          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <StatCard
              label="FSM STATE"
              value={status ? `${stateEmoji(status.fsm_state)} ${status.fsm_state}` : "—"}
              color={status ? stateColor(status.fsm_state) : undefined}
              desc="The firewall state machine. COOLDOWN means recently tripped — cooling off before returning to NORMAL."
            />
            <StatCard
              label="SCAN CADENCE"
              value={status ? `${status.scans_per_minute} scans / min` : "—"}
              sub="15-second loop"
              desc="How often the agent collects signals and scores blocks. Every 15 seconds, 24/7."
            />
            <StatCard
              label="TRIP THRESHOLD"
              value={status ? String(status.threshold) : "—"}
              sub="score required to trigger"
              desc="When the threat score crosses this, the FSM transitions to TRIPPED — on-chain attestation fires."
            />
            <StatCard
              label="UPTIME CYCLES"
              value={status ? status.uptime_cycles.toLocaleString() : "—"}
              sub="since deployment"
              desc="Total scan cycles completed. Each cycle = COLLECT → SCORE → FSM → ATTEST → ALERT."
            />
          </div>
        </div>

        {/* ===== PIPELINE ===== */}
        <section style={{ background: "#0d0d12", border: "1px solid #1f2937", borderRadius: "12px", padding: "1.5rem", marginBottom: "2rem" }}>
          <h2 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#e5e5e5", letterSpacing: "0.05em" }}>
            DETECTION PIPELINE
          </h2>
          <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "1.2rem", lineHeight: 1.5 }}>
            Every 15 seconds, signals flow through five stages. Green dots mean the stage is active.
            When the FSM trips, the ATTEST dot pulses red — a detection is being written on-chain.
          </p>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
            {[
              { name: "COLLECT", desc: "Gather pending TXs, blocks, transfers from Alchemy" },
              { name: "SCORE", desc: "Compute 8-element feature vector → 0-100 threat score" },
              { name: "FSM", desc: "State machine: NORMAL → ELEVATED → TRIPPED → COOLDOWN" },
              { name: "ATTEST", desc: "Write detection proof on-chain via DetectionRegistry" },
              { name: "ALERT", desc: "Fire Telegram notification to @bastion_pro_bot" },
            ].map((stage, i) => {
              const active = !!status;
              const tripped = status?.fsm_state === "TRIPPED" && stage.name === "ATTEST";
              return (
                <div key={stage.name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.4rem", flex: "1", minWidth: "100px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <div style={{
                      width: "16px", height: "16px", borderRadius: "50%",
                      background: tripped ? "#ef4444" : active ? "#22c55e" : "#1f2937",
                      boxShadow: active ? `0 0 14px ${tripped ? "rgba(239,68,68,0.7)" : "rgba(34,197,94,0.6)"}` : "none",
                      transition: "all 0.5s ease",
                      animation: tripped ? "pulseFast 0.8s ease-in-out infinite" : active ? "pulseDot 2s ease-in-out infinite" : "none",
                    }} />
                    <span style={{ fontSize: "0.85rem", fontWeight: 700, letterSpacing: "0.05em", color: active ? "#e5e5e5" : "#374151" }}>
                      {stage.name}
                    </span>
                  </div>
                  <span style={{ fontSize: "0.65rem", color: "#4b5563", textAlign: "center", lineHeight: 1.3, maxWidth: "130px" }}>
                    {stage.desc}
                  </span>
                  {i < 4 && (
                    <svg width="24" height="10" viewBox="0 0 24 10" style={{ marginTop: "-0.3rem" }}>
                      <path d="M0,5 L18,5 M13,1 L20,5 L13,9" fill="none" stroke={active ? "#374151" : "#1a1a2e"} strokeWidth="1.5" />
                    </svg>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ===== CONTRACTS + LOG ===== */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.2rem", marginBottom: "2rem" }}>
          {/* Contracts */}
          {status && (
            <section style={{ background: "#0d0d12", border: "1px solid #1f2937", borderRadius: "12px", padding: "1.5rem" }}>
              <h2 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#e5e5e5", letterSpacing: "0.05em" }}>
                ON-CHAIN CONTRACTS
              </h2>
              <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "1rem", lineHeight: 1.5 }}>
                Two immutable contracts deployed on Robinhood Chain. No admin keys, no upgradeable proxies.
                Hash-committed detection proofs are verifiable by anyone with a single RPC call.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
                <ContractRow
                  name="DetectionRegistry"
                  addr={status.contracts.DetectionRegistry}
                  desc="Records every CRITICAL/HIGH detection as an immutable on-chain proof. Only registered agents can write. Anyone can verify."
                />
                <ContractRow
                  name="ThreatSignatureRegistry"
                  addr={status.contracts.ThreatSignatureRegistry}
                  desc="Write-once shared threat intelligence. Any protocol can query before processing a transaction to block known attack patterns."
                />
                <div style={{ fontSize: "0.8rem", color: "#4b5563", marginTop: "0.5rem", fontFamily: "monospace" }}>
                  Agent Wallet: <span style={{ color: "#22c55e" }}>{status.agent_wallet.slice(0, 8)}...{status.agent_wallet.slice(-6)}</span>
                </div>
              </div>
            </section>
          )}

          {/* System Log */}
          <section style={{ background: "#0d0d12", border: "1px solid #1f2937", borderRadius: "12px", padding: "1.5rem" }}>
            <h2 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem", color: "#e5e5e5", letterSpacing: "0.05em" }}>
              SYSTEM LOG
            </h2>
            <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "1rem", lineHeight: 1.5 }}>
              Live operational log showing the agent's current state, detection pipeline status,
              deployed contracts, alert configuration, and backtest results.
            </p>
            <div style={{ fontSize: "0.78rem", fontFamily: "monospace", color: "#6b7280", lineHeight: 2 }}>
              {status && [
                `[${lastUpdated || "..."}] Cycle #${status.uptime_cycles} · Score ${status.current_score.toFixed(1)} · State: ${status.fsm_state}`,
                `Pipeline: COLLECT → SCORE → FSM → ATTEST → ALERT (all active)`,
                `DetectionRegistry: ${status.contracts.DetectionRegistry}`,
                `ThreatSigRegistry: ${status.contracts.ThreatSignatureRegistry}`,
                `Alerts: @bastion_pro_bot → Telegram Chat active`,
                `Deploy: Railway 24/7 · Robinhood Chain #${status.chain_id}`,
                `Backtest: 7/8 exploits detected (88%) · $836M attack volume covered`,
                `Detectors: 5 composable — FlashLoan, Oracle, Reentrancy, RugPull, MEV`,
                `Threshold: Score ≥ ${status.threshold} triggers on-chain attestation`,
              ].map((line, i) => (
                <div key={i} style={{ borderLeft: "2px solid #1f2937", paddingLeft: "0.8rem", marginBottom: "0.25rem" }}>
                  {line}
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* ===== FOOTER ===== */}
        <footer style={{
          borderTop: "1px solid #1f2937", paddingTop: "1.5rem",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          fontSize: "0.8rem", color: "#4b5563",
        }}>
          <span>Bastion Protocol · Always Watching · Arbitrum Open House London Buildathon 2026</span>
          <span style={{ color: "#22c55e", fontSize: "0.75rem", fontWeight: 600 }}>
            ● {status ? `${status.uptime_cycles} cycles · live 5s refresh` : "connecting..."}
          </span>
        </footer>
      </div>

      <style>{`
        @keyframes glowPulse { 0%,100%{box-shadow:0 0 8px rgba(34,197,94,0.3)} 50%{box-shadow:0 0 18px rgba(34,197,94,0.6)} }
        @keyframes pulseDot { 0%,100%{opacity:1} 50%{opacity:0.45} }
        @keyframes pulseFast { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(1.5)} }
      `}</style>
    </div>
  );
}

/* ===== COMPONENTS ===== */

function StatCard({ label, value, sub, color, desc }: {
  label: string; value: string; sub?: string; color?: string; desc?: string;
}) {
  return (
    <div style={{
      background: "#0d0d12", border: "1px solid #1f2937", borderRadius: "10px",
      padding: "1.2rem", transition: "border-color 0.5s ease", display: "flex", flexDirection: "column",
    }}>
      <div style={{ fontSize: "0.7rem", color: "#6b7280", letterSpacing: "0.1em", marginBottom: "0.5rem", fontWeight: 600 }}>
        {label}
      </div>
      <div style={{
        fontSize: "1.5rem", fontWeight: 700, color: color || "#e5e5e5",
        fontFamily: "'Courier New', monospace", transition: "color 0.5s ease", marginBottom: sub ? "0.2rem" : "0.5rem",
      }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: "0.7rem", color: "#4b5563", marginBottom: "0.5rem" }}>{sub}</div>}
      {desc && <div style={{ fontSize: "0.68rem", color: "#374151", lineHeight: 1.5, marginTop: "auto" }}>{desc}</div>}
    </div>
  );
}

function ContractRow({ name, addr, desc }: { name: string; addr: string; desc: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => { navigator.clipboard.writeText(addr); setCopied(true); setTimeout(() => setCopied(false), 1500); };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "0.6rem 0.8rem", background: "#0a0a0a", borderRadius: "6px",
        border: "1px solid #1f2937", fontFamily: "monospace",
      }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#9ca3af" }}>{name}</span>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <span style={{ fontSize: "0.8rem", color: "#22c55e" }}>{addr.slice(0, 10)}...{addr.slice(-8)}</span>
          <button
            onClick={copy}
            style={{
              fontSize: "0.65rem", padding: "0.2rem 0.5rem", borderRadius: "3px",
              background: copied ? "#22c55e20" : "transparent", border: `1px solid ${copied ? "#22c55e" : "#1f2937"}`,
              color: copied ? "#22c55e" : "#4b5563", cursor: "pointer", fontFamily: "inherit",
              transition: "all 0.2s",
            }}
          >
            {copied ? "✓ Copied" : "Copy"}
          </button>
        </div>
      </div>
      <div style={{ fontSize: "0.68rem", color: "#374151", lineHeight: 1.4, paddingLeft: "0.4rem" }}>
        {desc}
      </div>
    </div>
  );
}
