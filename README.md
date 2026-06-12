# Bastion Protocol — Autonomous Exploit Detection for Arbitrum

An autonomous AI agent that monitors Arbitrum in real time, detects DeFi exploit patterns before they execute, and triggers on-chain firewalls via the Threat Signature Registry.

> Built for Arbitrum Open House London Buildathon — $115K prize pool

## Architecture — FSM + Threat Registry (stolen from ArbiGuard)

```
┌─────────────────────────────────────────────────────────┐
│              BASTION PROTOCOL AGENT (15s loop)           │
│                                                         │
│  COLLECT → SCORE → FSM STATE MACHINE → THREAT REGISTRY  │
│                                                         │
│  • Mempool scanner (Robinhood Chain via Alchemy)        │
│  • 8-element feature vector → deterministic score 0-100 │
│  • FSM: NORMAL → ELEVATED → TRIPPED → COOLDOWN          │
│  • ThreatSignatureRegistry: write-once, protects all     │
│  • Telegram alerts for CRITICAL/HIGH                     │
│  • On-chain attestation (Gas-sponsored, zero cost)      │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack — 11 Robinhood/Arbitrum Components

| Layer | Technology | Robinhood Component |
|-------|-----------|---------------------|
| Chain | Solidity on Robinhood Testnet (Chain ID 46630) | 🔴 Chain Deployment |
| RPC | Alchemy Node API | 🔴 JSON-RPC |
| Mempool | Alchemy WebSocket | 🔴 Real-time tx feed |
| Debug | Alchemy Debug API | 🟡 Tx tracing |
| Tokens | Alchemy Token API | 🟡 Approval monitoring |
| Transfers | Alchemy Transfers API | 🟡 Liquidity tracking |
| Wallet | Alchemy Smart Wallets | 🟢 ERC-4337 + gas sponsorship |
| Gas | Alchemy Gas Manager | 🟢 Zero-cost agent txs |
| Bundler | Alchemy Bundler API | 🟢 Batch attestations |
| Speed | Arbitrum Nitro | 🔵 Fast block times |
| Funds | Robinhood Faucet | 🔴 Free testnet ETH |

> VEIL used only 1 sponsor component. ArbShield uses 11. Lesson learned.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Set environment
cp .env.example .env
# Fill in: ARB_RPC_URL, TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, PRIVATE_KEY

# Run agent
python -m agent.main
```

## Detection Coverage

| Pattern | Severity | Confidence Threshold |
|---------|----------|---------------------|
| Flash Loan Attack | CRITICAL | 80% |
| Oracle Manipulation | CRITICAL | 85% |
| Reentrancy | HIGH | 75% |
| Rug Pull | HIGH | 80% |
| MEV Sandwich | MEDIUM | 70% |

## Contracts (Arbitrum Sepolia)

| Contract | Purpose |
|----------|---------|
| `DetectionRegistry.sol` | Hash-commits every detection on-chain |
| `AgentRegistry.sol` | Agent identity + reputation tracking |

## Track Entry

- [ ] Overall Prize ($70K)
- [ ] Best Agentic Project ($15K)

## License

MIT — Arbitrum Open House London Buildathon, June 2026
