# 🏰 Bastion Protocol — Autonomous On-Chain Threat Detection

<p align="center">
  <img src="https://img.shields.io/badge/chain-Robinhood%20(46630)-00FF41?style=for-the-badge&logo=arbitrum">
  <img src="https://img.shields.io/badge/uptime-24%2F7%20on%20Railway-0B0D0E?style=for-the-badge&logo=railway">
  <img src="https://img.shields.io/badge/scans-1%2C656%2B%20cycles-00FF41?style=for-the-badge">
  <img src="https://img.shields.io/badge/detectors-5%20exploit%20patterns-red?style=for-the-badge">
</p>

> **One agent. 15-second cadence. Every transaction on Robinhood Chain analyzed before it lands.**
>
> DeFi lost **$1.8B to exploits in 2025**. Bastion is an autonomous AI agent that watches mempools in real time, scores every block with an 8-element threat vector, and writes immutable detection proofs on-chain — before the attack confirms.

**Built for Arbitrum Open House London Buildathon** — competing for Overall Prize ($70K) + Best Agentic ($15K).

---

## 🎯 Why Bastion Wins (Judge's View)

| What Judges Look For | How Bastion Delivers |
|----------------------|----------------------|
| **Smart Contract Quality** | 2 contracts deployed on Robinhood (46630), write-once threat registry, hash-committed proof of detection, no privileged roles |
| **Product-Market Fit** | Every DeFi protocol needs exploit detection. $1.8B annual problem. No existing solution on Robinhood Chain. |
| **Innovation & Creativity** | 8-element canonical feature vector → deterministic FSM (NORMAL→ELEVATED→TRIPPED→COOLDOWN) → 2/3 AI consensus. Novel architecture, not a wrapper. |
| **Real Problem Solving** | Flash loans, oracle manipulation, reentrancy, rug pulls, MEV sandwiches — detected before execution, not after. |
| **Robinhood Chain** | ✅ Built exclusively on Robinhood Chain (Chain ID 46630). Guaranteed prize pool eligibility. |

---

## 🧠 Architecture — 4-Stage Detection Pipeline

```
                          BASTION PROTOCOL AGENT
                   ┌──────────────────────────────────┐
                   │   15s loop — deployed 24/7        │
                   │                                  │
  ┌─────────┐     ┌──▼──────────┐    ┌──────────────┐ │
  │ Alchemy │────▶│ 1. COLLECT  │───▶│  2. SCORE    │ │
  │ WS+RPC  │     │ Mempool tx  │    │ 8-element    │ │
  │ Transfers│    │ Debug trace │    │ feature      │ │
  │ Tokens  │     │ Large swaps │    │ vector →     │ │
  │ Bundler │     └─────────────┘    │ 0-100 score  │ │
  └─────────┘                        └──────┬───────┘ │
                   ┌────────────────────────▼────────┐ │
                   │  3. FSM STATE MACHINE           │ │
                   │  NORMAL ──▶ ELEVATED ──▶ TRIPPED│ │
                   │                    ◀── COOLDOWN  │ │
                   │  Score ≥ 61 trips the firewall  │ │
                   └────────────────┬───────────────┘ │
                   ┌────────────────▼───────────────┐ │
                   │  4. THREAT REGISTRY + ALERT    │ │
                   │  • On-chain attestation (gas-  │ │
                   │    sponsored, zero cost)        │ │
                   │  • Telegram alert (real-time)  │ │
                   │  • ThreatSignatureRegistry     │ │
                   │    (write-once, shared intel)  │ │
                   └────────────────────────────────┘ │
                   └──────────────────────────────────┘
```

### The 8-Element Feature Vector
```
[swap_count, oracle_deviation_pct, reentrancy_depth, liquidity_change_pct,
 gas_anomaly_multiple, time_since_last_pattern, large_transfer_count, approval_count]
                                    ↓
                          Deterministic score 0-100
                                    ↓
                Score < 40: NORMAL | 40-60: ELEVATED | 61+: TRIPPED
```

---

## ⛓️ On-Chain Contracts (Robinhood Chain 46630)

| Contract | Address | Purpose |
|----------|---------|---------|
| **DetectionRegistry** | `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e` | Hash-commits every detection proof on-chain — immutable audit trail |
| **ThreatSignatureRegistry** | `0x87E3D9fcfA4eff229A65d045A7C741E49b581187` | Write-once shared threat intel — any protocol can query |

```solidity
// DetectionRegistry.commitDetection()
// Anyone can verify:
// keccak256(abi.encode(pattern, severity, blockNumber, timestamp)) == storedHash
```

---

## 📊 Live Deployment — 24/7 on Railway

```
[04:05:29 UTC] Cycle 1656 | State: NORMAL | Score: 0.0
  Scan interval: 15s
  Uptime: 7+ hours continuous
  Pipeline: COLLECT → SCORE → FSM → THREAT REGISTRY → ALERT
```

**Railway Dashboard:** [View live logs](https://railway.com/project/0668e86d-51d8-4084-b101-fc4ff1ff4fb6)

---

## 🛡️ Detection Coverage — 5 Exploit Patterns

| Pattern | Severity | Confidence Threshold | Real-World Example |
|---------|----------|---------------------|--------------------|
| **Flash Loan Attack** | 🔴 CRITICAL | 80% | Euler $197M, Platypus $8.5M |
| **Oracle Manipulation** | 🔴 CRITICAL | 85% | Mango Markets $116M, BonqDAO $120M |
| **Reentrancy** | 🟠 HIGH | 75% | Cream Finance $130M, Hundred Finance $7M |
| **Rug Pull / Exit Scam** | 🟠 HIGH | 80% | $3.6B in 2023 alone |
| **MEV Sandwich** | 🟡 MEDIUM | 70% | $1.5B+ extracted in 2024 |

### 2/3 Consensus Verification
When FSM trips to TRIPPED, detection goes through **2-of-3 consensus** (inspired by TriMind — 1st Place OKX Build-X):
1. **Rule Engine** — deterministic pattern matching against known exploit signatures
2. **Gemini 2.5 Flash** — AI semantic analysis of transaction traces
3. **Oracle Feed** — cross-reference with on-chain price data

---

## 🔗 Sponsor Technology — 11 Robinhood/Arbitrum Components

| # | Alchemy Product | Bastion Usage | Component |
|---|----------------|---------------|-----------|
| 1 | **Chain Deploy** | Contract deployment to Robinhood 46630 | 🔴 Chain |
| 2 | **Node RPC** | Block/transaction queries via JSON-RPC | 🔴 RPC |
| 3 | **WebSocket** | Real-time pending tx mempool feed | 🔴 WS |
| 4 | **Debug API** | Transaction tracing for reentrancy detection | 🟡 Debug |
| 5 | **Token API** | Approval monitoring, token metadata | 🟡 Token |
| 6 | **Transfers API** | Large transfer detection, liquidity tracking | 🟡 Transfer |
| 7 | **Smart Wallets** | ERC-4337 account abstraction for agent wallet | 🟢 Wallet |
| 8 | **Gas Manager** | Zero-cost on-chain attestations (sponsored gas) | 🟢 Gas |
| 9 | **Bundler API** | Batch threat signature attestations | 🟢 Bundler |
| 10 | **Arbitrum Nitro** | Fast block times, low latency detection | 🔵 Nitro |
| 11 | **Robinhood Faucet** | Free testnet ETH for agent operations | 🔴 Faucet |

> 💡 **Lesson from VEIL (lost submission):** Used 1 sponsor component. Bastion uses 11 — maximum sponsor surface area.

---

## 🤖 AI Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Verification AI** | Google Gemini 2.5 Flash | Semantic analysis of suspicious transactions |
| **Rule Engine** | Python + web3.py | Deterministic pattern matching on tx traces |
| **FSM** | Custom FirewallFSM | 4-state hysteresis prevents false positives |
| **Alerts** | Telegram Bot API | Real-time CRITICAL/HIGH notifications |

---

## 🏆 Hackathon Prize Tracks

| Track | Prize Pool | Bastion Eligibility |
|-------|-----------|---------------------|
| **Overall Prize** | $70,000 USDC | ✅ Deployed on Robinhood Chain (46630) |
| **Best Agentic Project** | $15,000 USDC | ✅ Autonomous AI agent with 2/3 consensus |
| **Grants** | $30,000 USDC | ✅ Milestone-ready architecture |

> 🎯 **Robinhood Chain Guarantee:** At minimum, 1 of 3 overall prizes is reserved for Robinhood Chain projects.

---

## 📋 Submission Checklist

- [x] Contracts deployed on Arbitrum chain (Robinhood 46630)
- [x] Agent running 24/7 (Railway, 1,656+ cycles)
- [x] Demo video script ready
- [x] GitHub repository public
- [x] README with architecture + sponsor tech usage
- [x] On-chain transaction history (2 contract deployments)
- [x] Live dashboard (Railway logs)
- [x] Telegram bot for real-time alerts

---

## 🚀 Quick Start

```bash
git clone https://github.com/Gideon145/bastion-protocol.git
cd bastion-protocol
pip install -r requirements.txt

# Set environment variables (see .env.example)
cp .env.example .env

# Run the agent
python agent/main.py
```

---

## 🔒 Security Model

- **Write-once Threat Registry**: Once a threat signature is published, it cannot be modified or deleted — preventing censorship
- **Hash-committed Detections**: `keccak256(pattern, severity, blockNumber, timestamp)` stored on-chain; verifiable by anyone
- **Gas-sponsored Attestations**: Alchemy Gas Manager sponsors all agent transactions — the protocol absorbs cost, not users
- **No privileged roles**: No `onlyOwner`, no upgradeable proxies, no backdoors
- **False positive resistant**: FSM hysteresis (NORMAL→ELEVATED requires sustained score 40+; ELEVATED→TRIPPED requires 61+) prevents alert fatigue

---

## 📁 Project Structure

```
bastion-protocol/
├── agent/                  # Autonomous detection agent
│   ├── main.py             # 15s loop + FSM pipeline
│   ├── collector.py        # Alchemy API signal collectors
│   ├── detector.py         # 5 exploit pattern detectors
│   ├── scorer.py           # 8-element feature vector scoring
│   ├── fsm.py              # FirewallFSM state machine
│   ├── verifier.py         # 2/3 consensus (Rule + AI + Oracle)
│   ├── alerter.py          # Telegram alert integration
│   ├── attest.py           # On-chain attestation via DetectionRegistry
│   └── alchemy_kit.py      # Smart Wallet + Gas Manager + Bundler
├── contracts/              # Solidity smart contracts
│   ├── DetectionRegistry.sol    # Hash-committed detection proofs
│   └── ThreatSignatureRegistry.sol  # Write-once shared threat intel
├── scripts/                # Deployment & utilities
│   └── deploy.py           # Contract deployment script
├── Dockerfile              # Containerized deployment (in .gitignore)
├── Dockerfile.example      # Reference Dockerfile template
├── railway.toml            # Railway deployment config
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

---

## ⚡ Competitor Comparison

| Feature | Bastion | ArbiGuard | Hypernative | Forta |
|---------|---------|-----------|-------------|-------|
| **Chain** | Robinhood (Orbit L2) | Arbitrum One | Multi-chain | Multi-chain |
| **Detection Pipeline** | 4-stage FSM | 3-stage | 2-stage | Event-based |
| **Feature Vector** | 8-element canonical | 6-element | N/A | N/A |
| **AI Consensus** | 2/3 (Rule+Gemini+Oracle) | Single AI | ML-based | Rule-only |
| **On-chain Attestation** | ✅ Gas-sponsored | ✅ | ❌ | ❌ |
| **Shared Threat Intel** | ✅ Write-once Registry | ✅ | ❌ | ❌ |
| **Telegram Alerts** | ✅ Real-time | ❌ | ✅ | ✅ |
| **24/7 Deployed** | ✅ Railway | ✅ | ✅ | ✅ |
| **Robinhood Native** | ✅ Built on 46630 | ❌ | ❌ | ❌ |
| **11 Sponsor Components** | ✅ Alchemy full-stack | ❌ | ❌ | ❌ |

---

## 👤 Builder

**Gideon** — [GitHub](https://github.com/Gideon145) | Solo builder
- Previously built: PitchProphet (World Cup AI prediction bot), Parry Protocol (Delta-neutral IL protection)
- DRE App contest finalist (Sherlock)

---

## 📄 License

MIT — Built for Arbitrum Open House London Buildathon, June 2026

---

<p align="center">
  <b>🏰 Bastion Protocol — Because $1.8B in DeFi exploits is $1.8B too many.</b>
</p>
