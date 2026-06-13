# Bastion Protocol — Autonomous Exploit Detection for Arbitrum

A 24/7 autonomous agent that monitors blockchain mempools in real time, scores every transaction against known exploit patterns, and writes immutable detection proofs on-chain before attacks confirm.

Built for Arbitrum Open House London Buildathon, June 2026.

---

## Problem

DeFi protocols lost $1.8B to exploits in 2025. Flash loans, oracle manipulation, reentrancy, and MEV attacks execute in seconds. Existing monitoring tools notify teams after the fact — when funds are already gone. There is no real-time, on-chain threat detection system native to Arbitrum Orbit chains.

---

## What Bastion Does

Bastion is an autonomous agent that runs a 15-second detection loop against the Robinhood Chain (Arbitrum Orbit L2, Chain ID 46630). Each cycle:

1. Collects pending transactions, debug traces, large transfers, and token approvals from Alchemy APIs
2. Scores every block using an 8-element canonical feature vector producing a deterministic 0-100 threat score
3. Feeds the score through a 4-state FSM with hysteresis to prevent false positives
4. When the FSM trips, writes a hash-committed detection proof on-chain and sends a Telegram alert

The on-chain detection proof is verifiable by any protocol or user via `keccak256(pattern, severity, blockNumber, timestamp)`.

---

## Architecture

```
BASTION PROTOCOL AGENT — 15s loop, deployed 24/7 on Railway

  Alchemy APIs ──▶ 1. COLLECT ──▶ 2. SCORE ──▶ 3. FSM ──▶ 4. ATTEST + ALERT
  (WS, RPC,       (mempool,      (8-element   (NORMAL →    (on-chain proof,
   Transfers,      debug trace,   feature      ELEVATED →   Telegram alert)
   Tokens)         large swaps,   vector →     TRIPPED →
                   approvals)     0-100)       COOLDOWN)
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

### FSM States

| State | Condition | Behavior |
|-------|-----------|----------|
| NORMAL | Score < 40 | Passive monitoring |
| ELEVATED | Score 40-60 sustained | Heightened scrutiny, increased sampling |
| TRIPPED | Score ≥ 61 | On-chain attestation, Telegram alert, Threat Registry update |
| COOLDOWN | After TRIPPED, 5 minute decay | Prevents alert fatigue, hysteresis return to NORMAL |

---

## Detection Coverage

| Pattern | Severity | Threshold |
|---------|----------|-----------|
| Flash Loan Attack | CRITICAL | 80% |
| Oracle Manipulation | CRITICAL | 85% |
| Reentrancy | HIGH | 75% |
| Rug Pull / Exit Scam | HIGH | 80% |
| MEV Sandwich | MEDIUM | 70% |

Verification uses 2-of-3 consensus: Rule Engine (deterministic pattern matching), Gemini 2.5 Flash (AI semantic analysis of tx traces), and Oracle Feed (cross-reference with on-chain price data).

---

## On-Chain Contracts

Deployed on Robinhood Chain (Chain ID 46630).

| Contract | Address | Purpose |
|----------|---------|---------|
| DetectionRegistry | `0x57C7f2F3051928E2cc7C871Bac590bF1d4BF4c8e` | Hash-commits every detection proof; verifiable by anyone |
| ThreatSignatureRegistry | `0x87E3D9fcfA4eff229A65d045A7C741E49b581187` | Write-once shared threat intel; protocols query to check known threats |

Agent wallet: `0x94A4365E6B7E79791258A3Fa071824BC2b75a394` (0.01 ETH, gas-sponsored via Alchemy Gas Manager)

---

## Deployment

The agent runs 24/7 on Railway (free tier). Build uses the project Dockerfile with Python 3.12-slim.

```bash
git clone https://github.com/Gideon145/bastion-protocol.git
cd bastion-protocol
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
python agent/main.py
```

Current status (as of June 13, 2026): 1,656+ scan cycles, 7+ hours continuous uptime, FSM state: NORMAL.

---

## Sponsor Technology

11 Alchemy components across Robinhood/Arbitrum:

| Alchemy Product | Usage |
|-----------------|-------|
| Chain Deploy | Contract deployment to Robinhood 46630 |
| Node RPC | Block and transaction queries |
| WebSocket | Real-time pending transaction feed |
| Debug API | Transaction tracing for reentrancy detection |
| Token API | Approval monitoring and token metadata |
| Transfers API | Large transfer detection and liquidity tracking |
| Smart Wallets | ERC-4337 account abstraction for agent wallet |
| Gas Manager | Sponsored gas for zero-cost on-chain attestations |
| Bundler API | Batch threat signature submissions |
| Arbitrum Nitro | Fast block times for low-latency detection |
| Robinhood Faucet | Testnet ETH for agent operations |

---

## Project Structure

```
bastion-protocol/
├── agent/
│   ├── main.py              # 15s detection loop + FSM pipeline
│   ├── collector.py         # Alchemy API signal collectors
│   ├── detector.py          # 5 exploit pattern detectors
│   ├── scorer.py            # 8-element feature vector scoring
│   ├── fsm.py               # FirewallFSM state machine
│   ├── verifier.py          # 2/3 consensus (Rule + AI + Oracle)
│   ├── alerter.py           # Telegram alert integration
│   ├── attest.py            # On-chain attestation via DetectionRegistry
│   └── alchemy_kit.py       # Smart Wallet, Gas Manager, Bundler wrappers
├── contracts/
│   ├── DetectionRegistry.sol       # Hash-committed detection proofs
│   └── ThreatSignatureRegistry.sol # Write-once shared threat intel
├── scripts/
│   └── deploy.py            # Contract deployment
├── Dockerfile               # Railway deployment (in .gitignore)
├── Dockerfile.example       # Reference Dockerfile without secrets
├── railway.toml             # Railway deployment config
├── .env.example             # Environment variable template
└── requirements.txt         # Python dependencies
```

---

## Security Model

- Write-once Threat Registry: signatures cannot be modified or deleted after publication
- Hash-committed Detections: `keccak256(pattern, severity, blockNumber, timestamp)` stored on-chain
- Gas-sponsored Attestations: Alchemy Gas Manager covers all agent transaction costs
- No privileged roles: no `onlyOwner`, no upgradeable proxies, no backdoors
- Hysteresis-based FSM: prevents false positive alert fatigue via state transitions requiring sustained scores

---

## License

MIT — Built for Arbitrum Open House London Buildathon, June 2026
