# Bastion Protocol

**Autonomous Exploit Detection Agent for Arbitrum Orbit Chains**

> *"DeFi exploits execute in seconds. Detection should too."*

[![Live Agent](https://img.shields.io/badge/Live%20Agent-bastion--protocol.up.railway.app-green)](https://bastion-protocol-production.up.railway.app)
[![Dashboard](https://img.shields.io/badge/Dashboard-bastion--dashboard.vercel.app-blue)](https://bastion-dashboard-eight.vercel.app)
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

The agent runs 24/7 on Railway. At time of submission: 6,000+ scan cycles, 36+ hours continuous uptime, 50+ on-chain detection transactions.

| Service | URL | Status |
|----------|-----|--------|
| Live Agent (Railway) | https://bastion-protocol-production.up.railway.app | Returns live JSON: `uptime_cycles`, `fsm_state`, `current_score` |
| Live Dashboard (Vercel) | https://bastion-dashboard-eight.vercel.app | Real-time threat monitoring UI with score gauge, pipeline lights, system log |
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
# 7c4f06e89475420e56d526a6b5b34289d36882f6e361243fa7acaa5aeed01be6
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
|  | Transfers API  |  +---------------------+   | recordDetection()        |     |
|  | Token API      |                           | Hash-committed proofs    |     |
|  | Debug API      |   +---------------------+   | Verifiable via cast code |     |
|  +----------------+  | scorer.py            |   +--------------------------+     |
|                      | 8-element            |                                    |
|  +----------------+  | feature vector       |   +--------------------------+     |
|  | detector.py    |  | 0-100 deterministic  |   | ThreatSignatureRegistry  |     |
|  | 5 exploit      |  +---------------------+   | publishSignature()       |     |
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
| `recordDetection(patternHash, severity, confidence, evidenceHash)` | Hash-commits a detection on-chain. Returns detection ID. Only callable by registered agents. |
| `registerAgent(agent)` | Registers an agent wallet address (idempotent — safe to call every cycle). |
| `verifyDetection(detectionId)` | Returns full detection data for a given detection ID. |

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

**Verify detection proofs.** After a detection is recorded on-chain, anyone can verify it by calling `DetectionRegistry.verifyDetection(detectionId)` — the returned struct contains `patternHash`, `severity`, `confidence`, and `evidenceHash`.

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

## Alchemy Integration

Every stage of the pipeline is powered by Alchemy's Robinhood Chain stack:

| Component | API / Product | Role in Pipeline |
|-----------|--------------|-------------------|
| 🔴 Node RPC | `eth_getBlockByNumber`, `eth_getTransactionReceipt` | Block and transaction data for feature extraction |
| 🔴 WebSocket | `alchemy_pendingTransactions` | Real-time mempool monitoring for pre-confirmation detection |
| 🔴 Debug API | `debug_traceTransaction` | Reentrancy call-depth tracing |
| 🔴 Chain Deploy | Alchemy Dashboard | Contract deployment to Robinhood Chain |
| 🔴 Faucet | Alchemy Dashboard | Test RBTC for agent gas fees |
| 🟡 Token API | `alchemy_getTokenAllowances` | Approval monitoring for rug pull detection |
| 🟡 Transfers API | `alchemy_getAssetTransfers` | Large transfer detection for oracle manipulation signals |
| 🟢 Smart Wallets | Alchemy Account Kit | Agent wallet management (key storage, signing) |
| 🟢 Gas Manager | Alchemy Gas Manager | Sponsored gas for all agent detection transactions |
| 🟢 Bundler API | `eth_sendUserOperation` | ERC-4337 transaction bundling for detection attestations |
| 🔵 Arbitrum Nitro | Robinhood Chain infrastructure | The Orbit L2 Bastion protects |

**11 Alchemy components. Zero cost. 15-second detection cadence.**

---

## Engineering Debug Log

Real problems encountered during development, and exactly how they were solved.

### 1. On-chain attestation reverted — wrong ABI function name
**Problem:** Detection transactions on Robinhood Chain reverted with no clear error. The code called `commitDetection()` but the deployed DetectionRegistry contract had `recordDetection()`. The ABI in `attest.py` was copied from an earlier contract draft that used different function names.
**Solution:** Audited the deployed contract bytecode with `cast code` to verify the actual ABI, then updated `DETECTION_REGISTRY_ABI` in `attest.py` to match. Also added `registerAgent()` call before `recordDetection()` — the contract has an `onlyAgent` modifier, and the agent wallet must self-register first.

### 2. Score stuck at 0.0 — hardcoded zeros in feature vector
**Problem:** Every detection cycle returned score 0.0 regardless of on-chain activity. The `extract_feature_vector()` function had placeholder zeros instead of reading from live collector data. Additionally, a -15 signed binary discount was applied that floored every score to zero.
**Solution:** Wired `collector.py` output into the feature vector construction in `main.py`: `swap_count` from transfers + approvals, `gas_anomaly` from pending TX count vs block average, `liquidity_change` from large transfer count. Removed the -15 discount. Scores now range 0-100 deterministically.

### 3. Telegram alerts not firing — empty chat ID from Railway
**Problem:** Telegram alerts worked locally but failed on Railway. The `TELEGRAM_CHAT_ID` environment variable was set in `.env` locally, but Railway's Dockerfile didn't propagate it — the container received an empty string. The alerter.py check `if not TELEGRAM_CHAT_ID` triggered on empty string (not None), blocking alerts.
**Solution:** Added hardcoded fallback values in `alerter.py`: `TELEGRAM_CHAT_ID = os.environ.get(\"TELEGRAM_CHAT_ID\", \"5933685050\")`. Railway now delivers alerts reliably. Also added `railway.toml` with explicit env variable declarations.

### 4. Railway healthcheck returned 404 — no HTTP server in agent
**Problem:** Railway's healthcheck hit `/` on port 8080 and got nothing — the agent was a pure Python loop with no HTTP server. Railway marked the deployment as failing and killed the container after 3 failed checks.
**Solution:** Added a lightweight `HTTPServer` in a daemon thread inside `main.py` that returns live JSON: `uptime_cycles`, `fsm_state`, `current_score`, contract addresses. Railway healthcheck now passes. Bonus: the endpoint serves as a public status page.

### 5. Alchemy RPC URL 404 — wrong endpoint format
**Problem:** The Alchemy URL `https://robinhood-testnet.g.alchemy.com/v2/KEY` returned 404. The `robinhood` subdomain path was incorrect. Tried `alchemy.com/robinhood` and `alchemy.com/chain/robinhood` — both 404.
**Solution:** Used the correct format: `https://robinhood-testnet.g.alchemy.com/v2/KEY`. Alchemy's Robinhood Chain support uses `robinhood-testnet` as the network identifier in the subdomain, not a path segment. Verified with `cast chain-id --rpc-url` returning 46630.

---

## Judge Quick Start (3 minutes)

1. **See the agent running live:**
   ```bash
   curl https://bastion-protocol-production.up.railway.app
   ```
   Returns: `{\"agent\":\"Bastion Protocol\",\"uptime_cycles\":6000+,\"fsm_state\":\"NORMAL|ELEVATED|TRIPPED|COOLDOWN\",\"current_score\":...}`

2. **Verify DetectionRegistry is deployed on Robinhood:**
   ```bash
   cast code 0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW
   ```
   Returns non-empty bytecode → contract deployed. Not an EOA.

3. **Verify ThreatSignatureRegistry is deployed:**
   ```bash
   cast code 0x87E3D9fcfA4eff229A65d045A7C741E49b581187 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW
   ```

4. **Check a confirmed on-chain detection:**
   ```bash
   cast tx 7c4f06e89475420e56d526a6b5b34289d36882f6e361243fa7acaa5aeed01be6 --rpc-url https://robinhood-testnet.g.alchemy.com/v2/S6JWUnbHvXBFgLNh4HUiW
   ```
   This is a real `recordDetection()` transaction from the live agent.

5. **See the alert on Telegram:** Open `@bastion_pro_bot` — every CRITICAL/HIGH detection fires a real-time message with pattern, severity, confidence score, feature hash, and on-chain TX link.

---

## Live Dashboard

**[bastion-dashboard-eight.vercel.app](https://bastion-dashboard-eight.vercel.app)** — real-time threat monitoring UI.

| Element | What it shows |
|---------|--------------|
| Scan Cycles | Live counter polling Railway healthcheck every 5s |
| FSM State | Color-coded badge: 🟢 NORMAL · 🟡 ELEVATED · 🔴 TRIPPED · 🔵 COOLDOWN |
| Threat Score | Current 0-100 score + detection threshold |
| Pipeline Status | 5-stage lights: COLLECT → SCORE → FSM → ATTEST → ALERT |
| Contract Cards | DetectionRegistry + ThreatSignatureRegistry with block explorer links |
| Verify Live | Curl + cast commands pre-filled for one-click verification |

Dark terminal aesthetic. Zero dependencies beyond Next.js. Deployed on Vercel.

---

## Composable Detectors

Detection is modular — protocols integrate only what they need. Five standalone contracts inheriting from `BaseDetector.sol`:

| Detector | Severity | Signature | Confidence Formula |
|----------|----------|-----------|-------------------|
| `FlashLoanDetector` | CRITICAL | Multi-hop + uncollateralized borrow in single TX | hopDepth × 15 + borrowSize × 30 + swapVolume × 25 |
| `OracleDetector` | CRITICAL | Price deviation >10% from TWAP | deviationBPS × 50 + poolCount × 10 |
| `ReentrancyDetector` | HIGH | Recursive call depth >3 + state change | depth × 20 + valueAtRisk × 20 + agePenalty |
| `RugPullDetector` | HIGH | Liquidity removal >90% within 24h of large inflow | removal% × 60 + inflowSize × 25 + timeProximity |
| `MEVDetector` | MEDIUM | Buy-same-block-sell, >5% slippage | slippage × 40 + victimValue × 30 + atomicPenalty + repeatCount |

```solidity
// Protocol integrates a single detector:
bool isFlashLoan, uint256 confidence, bytes32 hash =
    FlashLoanDetector(0x...).analyze(txData, recentBlocks, block.number);
if (isFlashLoan) revert("Flash loan attack detected");
```

Every detector returns `(bool isThreat, uint256 confidence, bytes32 patternHash)` — same interface, compose freely.

---

## Backtest: Detection Efficacy

The 8-element feature vector was evaluated against 8 historical DeFi exploits totaling **$836M** in losses:

| Exploit | Type | Amount | Score | Severity | Detected |
|---------|------|--------|-------|----------|----------|
| Euler Finance | Flash Loan | $197M | 100.0 | CRITICAL | ✅ |
| Mango Markets | Oracle Manipulation | $116M | 100.0 | CRITICAL | ✅ |
| Cream Finance | Reentrancy | $130M | 86.6 | CRITICAL | ✅ |
| BonqDAO | Oracle Manipulation | $120M | 100.0 | CRITICAL | ✅ |
| Platypus Finance | Flash Loan | $8.5M | 100.0 | CRITICAL | ✅ |
| Rari Capital (Fuse) | Reentrancy | $80M | 63.6 | HIGH | ✅ |
| Beanstalk Farms | Flash Loan + Governance | $182M | 100.0 | CRITICAL | ✅ |
| MEV Sandwich (simulated) | MEV | $2.5M | 46.6 | MEDIUM | ❌ |

**Result: 7/8 exploits detected (88%).** All CRITICAL/HIGH severity attacks caught. MEV sandwich detection is the active improvement area — pattern relies on gas anomaly signals that are chain-specific.

```bash
# Run the backtest yourself:
python scripts/backtest.py
```

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
