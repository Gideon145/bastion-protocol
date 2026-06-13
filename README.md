# Bastion Protocol

**Autonomous Exploit Detection Agent for Arbitrum Orbit Chains**

> *"DeFi exploits execute in seconds. Detection should too."*

[![Live Agent](https://img.shields.io/badge/Live%20Agent-railway.app%2Fbastion-green)](https://railway.com/project/0668e86d-51d8-4084-b101-fc4ff1ff4fb6)
[![Chain](https://img.shields.io/badge/Chain-Robinhood%20(46630)-brightgreen)](https://robinhood-testnet.g.alchemy.com)
[![Alchemy](https://img.shields.io/badge/Alchemy-11%20Components-blue)](https://www.alchemy.com/robinhood)

---

## What Is Bastion Protocol?

Bastion Protocol is an autonomous threat detection agent that monitors Robinhood Chain (Arbitrum Orbit L2, Chain ID 46630) in real time. It watches pending transactions in the mempool, scores every block against known exploit patterns using an 8-element feature vector, runs a 4-state FSM to filter false positives, and writes hash-committed detection proofs on-chain before attacks confirm.

The system is built on the Alchemy full-stack for Robinhood Chain: WebSocket, RPC, Debug, Token, Transfers, Smart Wallets, Gas Manager, and Bundler APIs — combined with Google Gemini 2.5 Flash for AI-assisted verification and Telegram for real-time alerts.

---

## The Problem Bastion Solves

DeFi protocols lost an estimated **$1.8B to exploits in 2025**. Here is how the most common attacks work:

- **Flash Loan Attacks** — borrow massive uncollateralized capital, manipulate a protocol, extract value, repay in a single atomic transaction. Euler Finance lost $197M. Platypus lost $8.5M.
- **Oracle Manipulation** — feed a protocol a false price, exploit the discrepancy between reported and actual value. Mango Markets lost $116M. BonqDAO lost $120M.
- **Reentrancy** — call a contract function, have it call back into itself before state updates. Cream Finance lost $130M. Hundred Finance lost $7M.
- **Rug Pulls & Exit Scams** — developers drain liquidity after attracting TVL. $3.6B was lost to rug pulls in 2023 alone.
- **MEV Sandwiches** — front-run a pending trade, let it execute at worse price, sell into the inflated price. Over $1.5B extracted in 2024.

The common thread: these attacks execute in single-digit seconds. Existing monitoring tools alert *after* the transaction confirms — when funds are already gone. **No protocol on Robinhood Chain detects threats before they land.**

---

## The Solution

Bastion runs an autonomous agent loop every **15 seconds** that:

1. **Collects** pending transactions from Alchemy WebSocket, full blocks from RPC, debug traces for reentrancy analysis, large transfers from the Transfers API, and token approvals from the Token API
2. **Scores** every block using an 8-element canonical feature vector producing a deterministic 0-100 threat score
3. **Processes** the score through a 4-state FSM with hysteresis: NORMAL, ELEVATED, TRIPPED, COOLDOWN
4. **Verifies** TRIPPED detections through 2-of-3 consensus: Rule Engine (deterministic pattern matching), Gemini 2.5 Flash (AI semantic analysis), Oracle Feed (cross-reference on-chain data)
5. **Attests** detections on-chain via `DetectionRegistry.commitDetection()` — a hash-committed proof verifiable by anyone
6. **Publishes** threat signatures to `ThreatSignatureRegistry` — a write-once registry any protocol can query to check known threats
7. **Alerts** via Telegram for CRITICAL and HIGH severity detections
8. **Runs** gas-sponsored — all agent transactions are subsidized by Alchemy Gas Manager, zero cost to the protocol

The 8-element feature vector:

```
[swap_count, oracle_deviation_pct, reentrancy_depth, liquidity_change_pct,
 gas_anomaly_multiple, time_since_last_pattern, large_transfer_count, approval_count]
                                    |
                          Deterministic 0-100 score
                                    |
                Score < 40: NORMAL | 40-60: ELEVATED | 61+: TRIPPED
```

FSM states and behavior:

| State | Condition | Behavior |
|-------|-----------|----------|
| NORMAL | Score < 40 | Passive monitoring |
| ELEVATED | Score 40-60 sustained | Heightened scrutiny, increased sampling rate |
| TRIPPED | Score ≥ 61 | On-chain attestation, Telegram alert, Threat Registry publish |
| COOLDOWN | 5-min decay after TRIPPED | Hysteresis return to NORMAL, prevents alert fatigue |

---

## Live Deployment (Verified)

| Service | URL | Status |
|---|---|---|
| Live Agent (Railway) | https://railway.com/project/0668e86d-51d8-4084-b101-fc4ff1ff4fb6 | 24/7, 1,656+ cycles |
| Agent Wallet | https://robinhood-testnet.g.alchemy.com | `0x94A4365E6B7E79791258A3Fa071824BC2b75a394` |
| DetectionRegistry | Robinhood Chain (46630) | `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e` |
| ThreatSignatureRegistry | Robinhood Chain (46630) | `0x87E3D9fcfA4eff229A65d045A7C741E49b581187` |

### Live Verification Commands

```bash
# Agent logs — running 24/7, 15s cadence
railway logs --service bastion-protocol --environment production

# Contract deployment verified on-chain
# DetectionRegistry: 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e
# ThreatSignatureRegistry: 0x87E3D9fcfA4eff229A65d045A7C741E49b581187
# Chain: Robinhood (46630), deployer: 0x94A4365E6B7E79791258A3Fa071824BC2b75a394

# Verify DetectionRegistry deployment
cast code 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# Verify ThreatSignatureRegistry deployment
cast code 0x87E3D9fcfA4eff229A65d045A7C741E49b581187 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW
```

---

## Architecture

```
+---------------------------------------------------------------------------------+
|                         BASTION PROTOCOL STACK                                  |
+----------------------+----------------------+------------------------------------+
|   AGENT (Python)     |   VERIFICATION       |   INFRASTRUCTURE                  |
|   Railway 24/7       |                      |                                    |
|   15s loop           |   2/3 Consensus      |   Railway (Agent)                 |
|                      |   Rule + AI + Oracle |   Robinhood Chain (46630)          |
|  +----------------+  |                      |                                    |
|  | collector.py   |  |  Rule: deterministic |   +--------------------------+     |
|  | Alchemy WS+RPC |  |  pattern matching   |   | DetectionRegistry.sol    |     |
|  | Transfers API  |  |                      |   | commitDetection()        |     |
|  | Token API      |  |  AI: Gemini 2.5      |   | Hash-committed proofs    |     |
|  | Debug API      |  |  Flash semantic      |   | Verifiable by anyone     |     |
|  +----------------+  |  tx trace analysis   |   +--------------------------+     |
|                      |                      |                                    |
|  +----------------+  |  Oracle: on-chain    |   +--------------------------+     |
|  | scorer.py      |  |  price/liquidity    |   | ThreatSignatureRegistry  |     |
|  | 8-element      |  |  cross-reference    |   | publish()                |     |
|  | feature vector |  +---------------------+   | Write-once               |     |
|  | 0-100 score    |                           | Shared threat intel       |     |
|  +----------------+                           +--------------------------+     |
|                      |                                                         |
|  +----------------+  |  Alchemy Components:                                     |
|  | fsm.py         |  |  Node RPC, WebSocket, Debug API, Token API,             |
|  | FirewallFSM    |  |  Transfers API, Smart Wallets, Gas Manager,             |
|  | NORMAL →       |  |  Bundler API, Chain Deploy, Faucet                       |
|  | ELEVATED →     |  |                                                         |
|  | TRIPPED →      |  |  AI: Google Gemini 2.5 Flash                            |
|  | COOLDOWN       |  |  Alerts: Telegram Bot API                                |
|  +----------------+  |                                                         |
+----------------------+---------------------------------------------------------+
```

---

## Smart Contracts (Robinhood Chain, Chain ID 46630)

### DetectionRegistry.sol
**Address:** `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e`

Hash-commits every detection as an immutable on-chain proof.

| Function | Description |
|---|---|
| `commitDetection(pattern, severity, blockNumber, timestamp)` | Stores `keccak256(pattern, severity, blockNumber, timestamp)` on-chain. Verifiable by anyone. |
| `verifyDetection(hash)` | Returns whether a given detection hash was committed. |

### ThreatSignatureRegistry.sol
**Address:** `0x87E3D9fcfA4eff229A65d045A7C741E49b581187`

Write-once shared threat intelligence that any protocol can query.

| Function | Description |
|---|---|
| `publish(signatureHash, patternType, severity, evidence)` | Publishes a threat signature. Once written, cannot be modified or deleted. |
| `isKnownThreat(signatureHash)` | Returns whether a given signature has been published. Protocols query this before processing transactions. |
| `getThreatCount()` | Returns total number of published threat signatures. |

---

## Alchemy Integration

Bastion uses **11 Alchemy products** across the Robinhood/Arbitrum stack:

### 1. Alchemy WebSocket (`wss://robinhood-testnet.g.alchemy.com/v2/...`)
Subscribes to pending transaction feed. Every unconfirmed transaction entering the Robinhood mempool is captured for analysis.

### 2. Alchemy Node RPC (`https://robinhood-testnet.g.alchemy.com/v2/...`)
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

All Alchemy API calls are logged with timestamps in the agent output, providing verifiable proof of sponsor technology usage.

---

## Detection Coverage

| Pattern | Severity | Confidence Threshold | Real-World Example |
|---------|----------|---------------------|--------------------|
| Flash Loan Attack | CRITICAL | 80% | Euler $197M (2023) |
| Oracle Manipulation | CRITICAL | 85% | Mango Markets $116M (2022) |
| Reentrancy | HIGH | 75% | Cream Finance $130M (2021) |
| Rug Pull / Exit Scam | HIGH | 80% | $3.6B total in 2023 |
| MEV Sandwich | MEDIUM | 70% | $1.5B extracted in 2024 |

---

## Quick Start

```bash
git clone https://github.com/Gideon145/bastion-protocol.git
cd bastion-protocol
pip install -r requirements.txt
cp .env.example .env   # fill in ALCHEMY_API_KEY, AGENT_PRIVATE_KEY, etc.
python agent/main.py
```

---

## Project Structure

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
│   ├── attest.py            # On-chain attestation
│   └── alchemy_kit.py       # Smart Wallet, Gas Manager, Bundler wrappers
├── contracts/
│   ├── DetectionRegistry.sol       # Hash-committed detection proofs
│   └── ThreatSignatureRegistry.sol # Write-once threat intel
├── scripts/
│   └── deploy.py
├── Dockerfile.example
├── railway.toml
├── .env.example
└── requirements.txt
```

---

## Security Model

- **Write-once Threat Registry**: signatures cannot be modified or deleted after publication — no censorship possible
- **Hash-committed Detections**: `keccak256(pattern, severity, blockNumber, timestamp)` stored on-chain — verifiable by any third party
- **Gas-sponsored**: Alchemy Gas Manager subsidizes all agent transactions — the protocol absorbs cost
- **No privileged roles**: no `onlyOwner`, no upgradeable proxies, no backdoors — contracts are immutable after deployment
- **Hysteresis FSM**: state transitions require sustained scores — prevents false positive alert fatigue

---

## License

MIT — Built for Arbitrum Open House London Buildathon, June 2026
