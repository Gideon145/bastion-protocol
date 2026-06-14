# Bastion Protocol

**Autonomous Exploit Detection Agent for Arbitrum Orbit Chains**

> *"DeFi exploits execute in seconds. Detection should too."*

[![Live Agent](https://img.shields.io/badge/Live%20Agent-bastion--protocol.up.railway.app-green)](https://bastion-protocol-production.up.railway.app)
[![GitHub](https://img.shields.io/badge/GitHub-bastion--protocol-white)](https://github.com/Gideon145/bastion-protocol)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)



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
| Live Agent (Railway) | https://bastion-protocol-production.up.railway.app | Returns live JSON: `uptime_cycles`, `fsm_state`, `current_score` |
| Agent Wallet | `0x94A4365E6B7E79791258A3Fa071824BC2b75a394` | Robinhood Chain (46630) |
| DetectionRegistry | `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e` | Deployed, verifiable via `cast code` |
| ThreatSignatureRegistry | `0x87E3D9fcfA4eff229A65d045A7C741E49b581187` | Deployed, verifiable via `cast code` |
| Deployment TXs | `e50e0e4e...` (TSR), `31e9c687...` (DR) | Confirmed on Robinhood Chain |
| Telegram Bot | `@BastionProtocolBot` | Real-time CRITICAL/HIGH alerts |

### Live Verification Commands

```bash
# Agent healthcheck — live JSON with uptime, FSM state, current score
curl https://bastion-protocol-production.up.railway.app

# Verify DetectionRegistry is deployed on Robinhood (46630)
cast code 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# Verify ThreatSignatureRegistry is deployed on Robinhood (46630)
cast code 0x87E3D9fcfA4eff229A65d045A7C741E49b581187 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW

# View live agent logs including on-chain detection transactions
railway logs --service bastion-protocol --environment production

# Confirmed detection transactions on Robinhood Chain:
# 3c74a4363e07421063750d50db16ce112a617c24bbd3903f81fc3b879188f8ce
# 933e24d47b631d199cc2ca900b0eba87e16c283cb3e158415c69a4a5c551a1b6
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

## Protocol Integration

Any DeFi protocol on Robinhood Chain can integrate with Bastion in two ways:

**Query the Threat Registry before processing transactions.** Before executing a user transaction, call `ThreatSignatureRegistry.isKnownThreat(signatureHash)`. If the signature matches a known attack pattern, reject the transaction.

```solidity
// In your protocol's swap/lend/borrow function:
if (ThreatSignatureRegistry(0x87E3...).isKnownThreat(signatureHash)) {
    revert("Transaction matches known exploit pattern");
}
```

**Verify detection proofs.** After a detection is published, anyone can verify it by calling `DetectionRegistry.verifyDetection(hash)` and comparing against the stored `keccak256(pattern, severity, blockNumber, timestamp)`.

```solidity
// Verify a detection was actually committed on-chain:
bool wasDetected = DetectionRegistry(0x57C7...).verifyDetection(detectionHash);
```

Both contracts are immutable — no `onlyOwner`, no upgradeable proxies, no backdoors. Once deployed, they cannot be modified.

---

## Detection Pipeline

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
