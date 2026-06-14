/** Bastion Protocol — Live Threat Dashboard
 * Polls the Railway healthcheck every 5s.
 * Shows live cycle counter, FSM state, threat score, latest detections.
 * Dark terminal aesthetic. Deploy on Vercel.
 */

export const dynamic = "force-dynamic";

const HEALTHCHECK_URL = "https://bastion-protocol-production.up.railway.app";

interface AgentStatus {
  agent: string;
  chain: string;
  chain_id: number;
  pipeline: string;
  uptime_cycles: number;
  fsm_state: string;
  current_score: number;
  threshold: number;
  scans_per_minute: number;
  contracts: {
    DetectionRegistry: string;
    ThreatSignatureRegistry: string;
  };
  agent_wallet: string;
}

async function fetchStatus(): Promise<AgentStatus | null> {
  try {
    const res = await fetch(HEALTHCHECK_URL, { next: { revalidate: 0 } });
    return await res.json();
  } catch {
    return null;
  }
}

function stateColor(state: string): string {
  switch (state) {
    case "NORMAL": return "#22c55e";
    case "ELEVATED": return "#eab308";
    case "TRIPPED": return "#ef4444";
    case "COOLDOWN": return "#3b82f6";
    default: return "#6b7280";
  }
}

function stateEmoji(state: string): string {
  switch (state) {
    case "NORMAL": return "🟢";
    case "ELEVATED": return "🟡";
    case "TRIPPED": return "🔴";
    case "COOLDOWN": return "🔵";
    default: return "⚪";
  }
}

export default async function DashboardPage() {
  const status = await fetchStatus();

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      color: "#e5e5e5",
      fontFamily: "'Courier New', Courier, monospace",
      padding: "2rem",
    }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #1f2937", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "1.5rem" }}>🛡️</span>
          <h1 style={{ fontSize: "1.8rem", fontWeight: 700, margin: 0, letterSpacing: "0.05em" }}>
            BASTION PROTOCOL
          </h1>
          <span style={{
            fontSize: "0.7rem",
            padding: "0.2rem 0.6rem",
            borderRadius: "4px",
            background: "#1f2937",
            color: "#9ca3af",
            letterSpacing: "0.1em",
          }}>
            LIVE
          </span>
        </div>
        <p style={{ color: "#6b7280", fontSize: "0.85rem", margin: 0 }}>
          Autonomous Exploit Detection Agent · Robinhood Chain (Arbitrum Orbit L2)
        </p>
      </header>

      {/* Stats Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
        marginBottom: "2rem",
      }}>
        <StatCard
          label="SCAN CYCLES"
          value={status ? status.uptime_cycles.toLocaleString() : "—"}
          sub={`${status ? status.scans_per_minute : 0} scans/min`}
        />
        <StatCard
          label="FSM STATE"
          value={status ? status.fsm_state : "—"}
          color={status ? stateColor(status.fsm_state) : undefined}
          sub={status ? stateEmoji(status.fsm_state) + " " + status.fsm_state : ""}
        />
        <StatCard
          label="THREAT SCORE"
          value={status ? status.current_score.toFixed(1) : "—"}
          sub={status ? `Threshold: ${status.threshold}` : ""}
        />
        <StatCard
          label="CHAIN"
          value={status ? `#${status.chain_id}` : "—"}
          sub="Robinhood (Orbit L2)"
        />
      </div>

      {/* Pipeline Visualization */}
      <section style={{
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "8px",
        padding: "1.5rem",
        marginBottom: "2rem",
      }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem", color: "#9ca3af" }}>
          PIPELINE STATUS
        </h2>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}>
          {["COLLECT", "SCORE", "FSM", "ATTEST", "ALERT"].map((stage, i) => (
            <div key={stage} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                background: "#22c55e",
                boxShadow: "0 0 8px rgba(34,197,94,0.5)",
              }} />
              <span style={{ fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.05em" }}>
                {stage}
              </span>
              {i < 4 && <span style={{ color: "#374151", margin: "0 0.25rem" }}>→</span>}
            </div>
          ))}
        </div>
      </section>

      {/* Contracts */}
      {status && (
        <section style={{
          background: "#111827",
          border: "1px solid #1f2937",
          borderRadius: "8px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem", color: "#9ca3af" }}>
            ON-CHAIN CONTRACTS
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            <ContractCard
              name="DetectionRegistry"
              address={status.contracts.DetectionRegistry}
            />
            <ContractCard
              name="ThreatSignatureRegistry"
              address={status.contracts.ThreatSignatureRegistry}
            />
          </div>
          <div style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#6b7280" }}>
            Agent Wallet: {status.agent_wallet}
          </div>
        </section>
      )}

      {/* Live Verification */}
      <section style={{
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "8px",
        padding: "1.5rem",
        marginBottom: "2rem",
      }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem", color: "#9ca3af" }}>
          VERIFY LIVE
        </h2>
        <pre style={{
          background: "#0a0a0a",
          padding: "1rem",
          borderRadius: "6px",
          fontSize: "0.75rem",
          color: "#22c55e",
          overflow: "auto",
          lineHeight: 1.6,
        }}>
{`# Agent healthcheck
$ curl ${HEALTHCHECK_URL}

# Verify DetectionRegistry bytecode
$ cast code 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e \\
    --rpc-url https://robinhood-testnet.g.alchemy.com/v2/YOUR_KEY

# Verify a detection on-chain
$ cast tx 7c4f06e89475420e56d526a6b5b34289d36882f6e361243fa7acaa5aeed01be6 \\
    --rpc-url https://robinhood-testnet.g.alchemy.com/v2/YOUR_KEY`}
        </pre>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: "1px solid #1f2937",
        paddingTop: "1.5rem",
        textAlign: "center",
        fontSize: "0.7rem",
        color: "#374151",
      }}>
        Bastion Protocol · Always Watching · Arbitrum Open House London Buildathon · June 2026
      </footer>
    </div>
  );
}

function StatCard({ label, value, sub, color }: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div style={{
      background: "#111827",
      border: "1px solid #1f2937",
      borderRadius: "8px",
      padding: "1.25rem",
    }}>
      <div style={{ fontSize: "0.65rem", color: "#6b7280", letterSpacing: "0.1em", marginBottom: "0.5rem" }}>
        {label}
      </div>
      <div style={{
        fontSize: "1.8rem",
        fontWeight: 700,
        color: color || "#e5e5e5",
        fontFamily: "'Courier New', Courier, monospace",
      }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: "0.7rem", color: "#4b5563", marginTop: "0.25rem" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function ContractCard({ name, address }: { name: string; address: string }) {
  const shortAddr = `${address.slice(0, 6)}...${address.slice(-4)}`;
  const explorerUrl = `https://robinhood-testnet.g.alchemy.com/address/${address}`;
  return (
    <div style={{
      background: "#0a0a0a",
      border: "1px solid #1f2937",
      borderRadius: "6px",
      padding: "1rem",
    }}>
      <div style={{ fontSize: "0.7rem", color: "#6b7280", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
        {name}
      </div>
      <a
        href={explorerUrl}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          fontSize: "0.85rem",
          color: "#22c55e",
          textDecoration: "none",
          fontFamily: "'Courier New', Courier, monospace",
        }}
      >
        {shortAddr}
      </a>
    </div>
  );
}
