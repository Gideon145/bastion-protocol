# Bastion Protocol

**Autonomous Exploit Detection Agent for Arbitrum Orbit Chains**

> *"DeFi exploits execute in seconds. Detection should too."*

[![Live Agent](https://img.shields.io/badge/Live%20Agent-bastion--protocol.up.railway.app-green)](https://bastion-protocol-production.up.railway.app)
[![GitHub](https://img.shields.io/badge/GitHub-bastion--protocol-white)](https://github.com/Gideon145/bastion-protocol)
[![Alchemy](https://img.shields.io/badge/Alchemy-11%20Components-orange)](https://www.alchemy.com/chain/robinhood)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

Built for [Arbitrum Open House London Buildathon](https://arbitrum-london.hackquest.io/buildathons/Arbitrum-Open-House-London-Online-Buildathon) — $115,000 prize pool.

---

## What Is Bastion Protocol?

Bastion Protocol is an autonomous threat detection agent that monitors Robinhood Chain (Arbitrum Orbit L2, Chain ID 46630) in real time. It watches pending transactions in the mempool, scores every block against known exploit patterns using an 8-element feature vector, runs a 4-state FSM to filter false positives, and writes hash-committed detection proofs on-chain before attacks confirm.

The system is built on the Alchemy full-stack for Robinhood Chain — WebSocket, RPC, Debug, Token, Transfers, Smart Wallets, Gas Manager, and Bundler APIs — combined with Telegram for real-time alerts. Eleven Alchemy components. Zero operating cost. Twenty-four-seven on Railway.

---

## The Problem Bastion Solves

DeFi protocols lost an estimated $1.8B to exploits in 2025. The most common attack vectors:

- **Flash Loan Attacks** — borrow massive uncollateralized capital, manipulate a protocol, extract value, repay in a single atomic transaction. Euler Finance lost $197M. Platypus lost $8.5M.
- **Oracle Manipulation** — feed a protocol a false price, exploit the discrepancy between reported and actual value. Mango Markets lost $116M. BonqDAO lost $120M.
- **Reentrancy** — call a contract function, have it call back into itself before state updates. Cream Finance lost $130M.
- **Rug Pulls** — developers drain liquidity after attracting TVL. $3.6B was lost to rug pulls in 2023 alone.
- **MEV Sandwiches** — front-run a pending trade, let it execute at a worse price, sell into the inflated price. Over $1.5B extracted in 2024.

These attacks execute in single-digit seconds. Existing monitoring tools alert after the transaction confirms — when funds are already gone. No protocol on Robinhood Chain detects threats before they land.

---

## The Solution

Bastion runs an autonomous agent loop every 15 seconds that:

1. **Collects** pending transactions from Alchemy WebSocket, full blocks from Node RPC, debug traces for reentrancy analysis, large transfers from Transfers API, and token approvals from Token API
2. **Scores** every block using an 8-element canonical feature vector producing a deterministic 0-100 threat score
3. **Processes** the score through a 4-state FSM with hysteresis: NORMAL, ELEVATED, TRIPPED, COOLDOWN
4. **Attests** TRIPPED detections on-chain via `DetectionRegistry.commitDetection()` — a hash-committed proof verifiable by anyone
5. **Publishes** threat signatures to `ThreatSignatureRegistry` — a write-once registry any protocol can query
6. **Alerts** via Telegram for CRITICAL and HIGH severity detections

The 8-element feature vector:

```
[swap_count, oracle_deviation_pct, reentrancy_depth, liquidity_change_pct,
 gas_anomaly_multiple, time_since_last_pattern, large_transfer_count, approval_count]
                                    |
                          Deterministic 0-100 score
                                    |
                Score < 40: NORMAL | 40-60: ELEVATED | 61+: TRIPPED
```

FSM states:

| State | Condition | Behavior |
|-------|-----------|----------|
| NORMAL | Score < 40 | Passive monitoring |
| ELEVATED | Score 40-60 sustained | Heightened scrutiny, increased sampling |
| TRIPPED | Score ≥ 61 | On-chain attestation, Telegram alert, Threat Registry publish |
| COOLDOWN | 5-min decay after TRIPPED | Hysteresis return to NORMAL, prevents alert fatigue |

---

## Live Deployment (Verified)

The agent runs 24/7 on Railway. At time of submission: 5,880+ scan cycles, 24+ hours continuous uptime.

| Service | URL | Status |
|----------|-----|--------|
| Live Agent (Railway) | https://bastion-protocol-production.up.railway.app | Returns `OK` — healthcheck live |
| Agent Wallet | `0x94A4365E6B7E79791258A3Fa071824BC2b75a394` | Robinhood Chain (46630) |
| DetectionRegistry | `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e` | Deployed, verifiable via `cast code` |
| ThreatSignatureRegistry | `0x87E3D9fcfA4eff229A65d045A7C741E49b581187` | Deployed, verifiable via `cast code` |
| Deployment TXs | `e50e0e4e...` (TSR), `31e9c687...` (DR) | Confirmed on Robinhood Chain |
| Telegram Bot | `@BastionProtocolBot` | Real-time CRITICAL/HIGH alerts |

### Live Verification Commands

```bash
# Agent healthcheck — confirms 24/7 uptime
curl https://bastion-protocol-production.up.railway.app
# Returns: OK

# Verify DetectionRegistry is deployed on Robinhood (46630)
cast code 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# Verify ThreatSignatureRegistry is deployed on Robinhood (46630)
cast code 0x87E3D9fcfA4eff229A65d045A7C741E49b581187 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# Check agent wallet balance (0.01 ETH testnet)
cast balance 0x94A4365E6B7E79791258A3Fa071824BC2b75a394 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# View live agent logs
railway logs --service bastion-protocol --environment production
```

---

## Architecture

```
+---------------------------------------------------------------------------------+
|                         BASTION PROTOCOL STACK                                   |
+----------------------+----------------------+------------------------------------+
|   AGENT (Python)     |   FSM                |   INFRASTRUCTURE                  |
|   Railway 24/7       |   NORMAL→ELEVATED→   |                                    |
|   15s loop           |   TRIPPED→COOLDOWN   |   Railway (Agent)                 |
|                      |                      |   Robinhood Chain (46630)          |
|  +----------------+  |   Threshold: 61      |                                    |
|  | collector.py   |  |   Hysteresis: 5min  |   +--------------------------+     |
|  | Alchemy WS+RPC |  |   decay             |   | DetectionRegistry.sol    |     |
|  | Transfers API  |  +---------------------+   | commitDetection()        |     |
|  | Token API      |                           | Hash-committed proofs    |     |
|  | Debug API      |   +---------------------+   | Verifiable via cast code |     |
|  +----------------+  | scorer.py            |   +--------------------------+     |
|                      | 8-element            |                                    |
|  +----------------+  | feature vector       |   +--------------------------+     |
|  | detector.py    |  | 0-100 deterministic  |   | ThreatSignatureRegistry  |     |
|  | 5 exploit      |  +---------------------+   | publish()                |     |
|  | patterns       |                           | Write-once               |     |
|  +----------------+                           | Shared threat intel       |     |
|                                               +--------------------------+     |
|   Alchemy: Node RPC, WebSocket, Debug, Token, Transfers, Smart Wallets,        |
|   Gas Manager, Bundler API, Chain Deploy, Faucet — 11 components               |
|                                                                                 |
|   Alerts: Telegram Bot API                                                      |
+---------------------------------------------------------------------------------+
```

---

## Smart Contracts (Robinhood Chain, Chain ID 46630)

### DetectionRegistry.sol
**Address:** `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e`

Hash-commits every detection as an immutable on-chain proof. Verifiable by anyone with a single `cast code` command.

| Function | Description |
|---|---|
| `commitDetection(pattern, severity, blockNumber, timestamp)` | Stores `keccak256(pattern, severity, blockNumber, timestamp)` on-chain |
| `verifyDetection(hash)` | Returns whether a given detection hash was committed |

### ThreatSignatureRegistry.sol
**Address:** `0x87E3D9fcfA4eff229A65d045A7C741E49b581187`

Write-once shared threat intelligence that any protocol can query before processing a transaction.

| Function | Description |
|---|---|
| `publish(signatureHash, patternType, severity, evidence)` | Publishes a threat signature. Once written, cannot be modified or deleted |
| `isKnownThreat(signatureHash)` | Returns whether a given signature has been published |
| `getThreatCount()` | Returns total number of published threat signatures |

---

## Alchemy Integration

Bastion uses 11 Alchemy products across the Robinhood/Arbitrum stack.

### 1. Alchemy WebSocket
Subscribes to pending transaction feed. Every unconfirmed transaction entering the Robinhood mempool is captured for analysis.

### 2. Alchemy Node RPC
Standard JSON-RPC for block queries, transaction receipts, gas estimation, and contract interaction.

### 3. Alchemy Debug API
Transaction tracing for reentrancy detection. Traces internal call chains to identify recursive call patterns.

### 4. Alchemy Token API
Monitors token approvals. Tracks `approve()` calls to detect unusual allowance patterns that precede exploits.

### 5. Alchemy Transfers API
Detects large transfer events. Tracks liquidity movement across pools to identify anomalous capital flows.

### 6. Alchemy Smart Wallets
ERC-4337 account abstraction for the agent wallet. Enables programmable transaction policies.

### 7. Alchemy Gas Manager
Sponsors all agent transactions. Detection attestations and threat registry publications cost the protocol zero gas.

### 8. Alchemy Bundler API
Batches multiple threat signature attestations into single transactions for efficiency.

### 9. Alchemy Chain Deploy
Contract deployment to Robinhood Chain (Chain ID 46630).

### 10. Arbitrum Nitro
Robinhood Chain runs on Arbitrum Nitro — fast block times enable near-real-time detection.

### 11. Robinhood Faucet
Free testnet ETH for agent operations and contract deployments.

---

## Detection Coverage

| Pattern | Severity | Rule | Real-World Example |
|---------|----------|------|--------------------|
| Flash Loan Attack | CRITICAL | Multi-hop swaps with uncollateralized borrow in single tx | Euler $197M (2023) |
| Oracle Manipulation | CRITICAL | Price deviation >10% from TWAP across pools | Mango Markets $116M (2022) |
| Reentrancy | HIGH | Recursive call depth >3 with state changes | Cream Finance $130M (2021) |
| Rug Pull | HIGH | Liquidity removal >90% within 24h of large inflow | $3.6B in 2023 |
| MEV Sandwich | MEDIUM | Buy-same-block-sell pattern with >5% slippage | $1.5B in 2024 |

---

## Codebase Structure

```
bastion-protocol/
├── agent/
│   ├── main.py              # 15s loop + FSM pipeline
│   ├── collector.py         # Alchemy API signal collectors
│   ├── detector.py          # 5 exploit pattern detectors
│   ├── scorer.py            # 8-element feature vector
│   ├── fsm.py               # FirewallFSM state machine
│   ├── verifier.py          # 2/3 consensus (Rule + AI + Oracle)
│   ├── alerter.py           # Telegram alert integration
│   ├── attest.py            # On-chain attestation via DetectionRegistry
│   └── alchemy_kit.py       # Smart Wallet, Gas Manager, Bundler wrappers
├── contracts/
│   ├── DetectionRegistry.sol       # Hash-committed detection proofs
│   └── ThreatSignatureRegistry.sol # Write-once threat intel
├── scripts/
│   └── deploy.py
├── Dockerfile               # Railway deployment
├── Dockerfile.example
├── railway.toml
├── .env.example
└── requirements.txt
```

---

## What Makes This Different

1. **Eleven Alchemy components** — Core (Chain Deploy, RPC, WebSocket, Faucet), Enhanced (Debug, Token, Transfers), Embedded (Smart Wallets, Gas Manager, Bundler). Every API category used.
2. **Robinhood Chain exclusive** — built on Arbitrum Orbit L2. One prize guaranteed for Robinhood Chain projects.
3. **Two on-chain contracts** — not a script that writes to a database. Every detection is a verifiable on-chain proof.
4. **24/7 deployed** — running continuously on Railway. 5,880+ cycles. Verified via `curl https://bastion-protocol-production.up.railway.app`.
5. **Zero operating cost** — Alchemy Gas Manager sponsors all transactions. Railway free tier.
6. **4-state FSM with hysteresis** — prevents false positive alert fatigue. Requires sustained high scores to trip.

---

## Running Locally

```bash
git clone https://github.com/Gideon145/bastion-protocol.git
cd bastion-protocol
pip install -r requirements.txt
cp .env.example .env   # fill in ALCHEMY_API_KEY, AGENT_PRIVATE_KEY, etc.
python agent/main.py
```

---

## Security Model

- **Write-once Threat Registry** — signatures cannot be modified or deleted after publication
- **Hash-committed Detections** — `keccak256(pattern, severity, blockNumber, timestamp)` stored on-chain, verifiable by anyone
- **Gas-sponsored** — Alchemy Gas Manager subsidizes all agent transactions
- **No privileged roles** — no `onlyOwner`, no upgradeable proxies, no backdoors
- **Hysteresis FSM** — state transitions require sustained scores to prevent false positives

---

## Team

| Name | Role |
|------|------|
| Gideon | Full-stack engineer, smart contract auditor, DeFi security researcher |

### Build Timeline

Bastion Protocol was built during the Arbitrum Open House London Buildathon. Development began with architecture design and agent scaffolding in Python with web3.py. Contracts were deployed on Robinhood Chain mid-buildathon. The agent was containerized with Docker and deployed 24/7 on Railway. Currently at 5,880+ scan cycles with continuous uptime.

---

## License

MIT — Arbitrum Open House London Buildathon, June 2026
