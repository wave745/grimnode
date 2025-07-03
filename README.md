# GrimNode

Autonomous glitch agent in the cryptic chaos.

## 💀 TL;DR

GrimNode is a modular, on-chain automation system for degens, meme-lords, and stealth traders. It combines a command-line interface, secure encrypted agents, Solana smart contracts, and transaction-bundling logic into a cohesive blackbox toolkit — optimized for speed, stealth, and chaos.

## 🧩 Key Components

### 1. ⚙️ GrimPy CLI (`cli.py`)
A hacker-style command-line interface built with typer and rich.

**Commands:**
- `scan`: Realtime scan of new token creations on Pump.fun
- `meme`: (WIP) AI meme generation module
- `bundle`: (WIP) Execute stealthy multi-wallet trade bundles
- `send-job`: Dispatch encrypted jobs to local agents via ShadowNet
- `grimcast`: (WIP) Post memes or signals to Twitter/X

**Integrations:** Solana RPC, ZeroMQ, AES encryption, base58, Pump.fun

### 2. 🛰️ Shadow Agent (`shadow_agent.py`)
A local daemon that:
- Listens for incoming encrypted jobs via ZeroMQ
- Decrypts job payloads
- Processes and replies with encrypted ACKs

Think of it as a local grunt node for AI-coordinated ops.

### 3. 💰 GrimVault (Anchor Smart Contract)
A Rust-based treasury system built with Anchor on Solana.

**Features:**
- Accepts SOL-based subscriptions
- Supports access tiers (e.g., free, pro, premium)
- Time-based expiry, possible NFT-based tiering
- Serves as the gatekeeper for using advanced tools (like bundler/AI modules)

### 4. 🧃 GrimBundle Executor
A dual Rust + Python system designed to:
- Bundle Solana transactions across multiple wallets
- Add randomized delays + transaction splitting to obfuscate intent
- (Planned) integrate zk-SNARK-based proof of trade ownership
- Supports saved bundles (JSON), simulation, and execution logic

### 5. 🧰 Utility Modules (`utils/`)
Contains:
- `solana_client.py`: balance checks, supply, token info
- `pumpportal.py`: trending token fetch from pump.fun
- `crypto.py`: AES-based message encryption for ShadowNet
- (WIP) Jupiter DEX aggregator integrations and wallet risk scoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Rust & Cargo (for smart contracts)
- Solana CLI tools (optional, for direct blockchain interaction)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd grimnode
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the Shadow Agent (in background):**
```bash
python3 shadow_agent.py &
```

4. **Test the CLI:**
```bash
python3 cli.py --help
```

### Basic Usage

**Scan for new tokens on Pump.fun:**
```bash
python3 cli.py scan --limit 10
```

**Send an encrypted job to ShadowNet:**
```bash
python3 cli.py send-job "your job data here"
```

**Test agent communication:**
```bash
python3 cli.py send-job "test job from co-dev"
```

## 🧭 What It's For

GrimNode is built for:
- Onchain automation
- Stealthy trading
- Meme-fueled market manipulation
- Encrypted agent communication
- Token launches, bundle sniping, and chaos orchestration

It's Axiom meets Parasite AI, but glitchy, meme-powered, and aggressively Solana-native.

## 🛠 Current Status

- ✅ CLI scan + ShadowNet communication working
- ⚠️ Meme, bundle, and cast commands in progress
- ⚙️ Smart contract compiles, needs testing & deployment
- 🔐 Encrypted ZMQ pipeline live
- 🧪 Bundling logic in early validation phase

## 🏗️ Project Structure

```
grimnode/
├── cli.py                 # Main CLI interface
├── shadow_agent.py        # Local encrypted agent
├── requirements.txt       # Python dependencies
├── grim_vault/           # Solana smart contract (Anchor)
├── grim_bundle/          # Rust transaction bundler
├── bundle/               # Python bundling utilities
├── utils/                # Utility modules
│   ├── crypto.py         # AES encryption
│   ├── solana_client.py  # Solana RPC client
│   ├── pumpportal.py     # Pump.fun API integration
│   ├── jupiter.py        # Jupiter DEX aggregator
│   └── io.py             # File I/O utilities
└── bundles/              # Saved bundle files
```

## 🔧 Development

### Running Tests
```bash
# Test CLI commands
python3 cli.py scan
python3 cli.py send-job "test"

# Test Shadow Agent
python3 shadow_agent.py
```

### Smart Contract Development
```bash
cd grim_vault
anchor build
anchor test
```

### Bundle Development
```bash
cd grim_bundle
cargo build
```

## 🚨 Security Notes

- **ShadowNet keys are hardcoded** - For production, use environment variables
- **No authentication** on local agent communication - Add proper auth for multi-user setups
- **Smart contract needs audit** before mainnet deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Add your license here]

---

**💀 Welcome to the chaos.**