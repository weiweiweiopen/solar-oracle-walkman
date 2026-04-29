# Solar Oracle Walkman - IV Voiceprint Smart Contract
A smart contract that validates and stores IV voiceprints data of DIY solar cells and keep the measurements record on chain.

## Project Brief for Reviewers

Solar Oracle Walkman is a public research prototype that connects DIY DSSC measurement practice with an IV voiceprint smart contract and oracle-signed on-chain records.

### What the V1 prototype already demonstrates
- A working Solidity contract (`SolarOracleWalkman`) for validating and storing 7-value IV voiceprint-style data.
- EIP-712 oracle signature verification, timestamp freshness checks, duplicate IV hash prevention, and on-chain record storage.
- A Sepolia deployment and visual documentation of the DIY DSSC and the I–V tester used in this research context.

### Why DSSC I–V curves are treated as material voiceprints
In this repository, patterned/handmade DSSC measurement behavior is treated as a **material voiceprint** candidate: a physical co-factor signal derived from measured I–V response, not just a software identifier.

### Why the smart contract is only one layer
The V1 smart contract is one component in a broader **material event signature** and **energy provenance evidence** research framing. A complete system also needs reproducible measurement protocols, raw data handling, registry conventions, and careful claim boundaries.

### Who this repo is for
- technical reviewers
- advisors
- collaborators
- investors
- public readers

### Quick links
- GitHub Pages briefing site (after Pages is enabled): `site/index.html`
- [V1 current prototype](docs/01_v1_current_prototype.md)
- [V1 to V4 iteration](docs/02_v1_to_v4_iteration.md)
- [Edmond Jordan briefing](docs/03_edmond_jordan_briefing.md)
- [Current progress and limitations](docs/07_current_progress_and_limitations.md)
- [Public FAQ](docs/08_public_faq.md)

> This repository is a public research prototype. It is not a legal REC / T-REC registry, not a financial product, and not a claim of actual energy equivalence.

Visit wiki for more details: https://wiki.sgmk-ssam.ch/wiki/The_Solar_Oracle_Walkman#RAVE_as_latent_oracle

## Visual Documentation

<img src="pix/DIY_DSSC_with_cyanotype_pattern.jpg" alt="DIY DSSC with cyanotype pattern" width="400">

*DIY Dye-Sensitized Solar Cell (DSSC) with cyanotype pattern - handmade solar cell demonstrating the physical basis for IV voiceprint generation*

<img src="pix/I-V_tester_made_by_Marc_Dusseiller.jpg" alt="I-V tester made by Marc Dusseiller" width="400">

*I-V characteristic tester made by Marc Dusseiller - the measurement device that generates the voiceprint data validated by this smart contract*

## Features

- **Comprehensive IV Validation**: Advanced security validation for voiceprint data of handmade DSSC.
- **EIP-712 Signatures**: Secure oracle signature verification
- **On-chain Storage**: Immutable IV voiceprint records
- **Chain Integrity**: Oracle verification of entire chain validity
- **Access Control**: Owner-managed oracle signer updates

## Security Validation Rules

1. **Range Validation**: Values must be between 0.01-3.0 (scaled by 1000 in contract)
2. **Statistical Analysis**: Variance checks for realistic IV curves
3. **Pattern Detection**: Blocks monotonic sequences
4. **Duplicate Detection**: Ensures sufficient unique values
5. **Alternation Limits**: Prevents extreme value jumps

## Installation & Setup

### Step 1: Install Dependencies
```bash
# Install dependencies (requires Node.js 18+)
npm install
```

### Step 2: Compile the Smart Contract
```bash
# This converts the Solidity code into bytecode that can run on blockchain
npx hardhat compile
```
**What this does**: Translates human-readable contract code into machine code

### Step 3: Set up Environment Variables
Create a `.env` file in the project root:
```bash
INFURA_API_KEY=your_infura_project_id
PRIVATE_KEY=your_wallet_private_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```


### Step 3b (Optional): Local LLM API key for backend use only
If you add an LLM explainer service, keep the API key in a **local-only** env file and load it from your backend runtime.

```bash
# .env.local (already gitignored)
OPENAI_API_KEY=your_server_side_key
```

Rules:
- Never commit real API keys.
- Never expose the key in frontend JavaScript or public HTML.
- Call the cloud LLM from a backend proxy/service only.

### Step 4: Deploy Contract to Sepolia Testnet
```bash
# Deploy to the live Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia
```
**What this does**: Puts your smart contract onto the real Sepolia blockchain and gives it an address

### Step 5: Test the Contract
```bash
# Run the comprehensive test suite on Sepolia testnet
npx hardhat run scripts/test-contract.js --network sepolia
```

## Usage

### Deploy Contract
```javascript
const oracle = await SolarOracleWalkman.deploy(oracleSignerAddress);
```

### Validate IV Data
```javascript
const [isValid, reason] = await oracle.validateIV7Data([1200, 800, 1500, 900, 1100, 1300, 1000]);
```

### Store IV Record
```javascript
const report = {
    identity: "user_123",
    pubkey: "0x...",
    ivHash: "0x...",
    iv7Data: [1200, 800, 1500, 900, 1100, 1300, 1000],
    timestamp: Math.floor(Date.now() / 1000)
};

const signature = await signer.signTypedData(domain, types, report);
const txId = await oracle.verifyAndStore(report, signature);
```

### Verify Chain Integrity
```javascript
const [isValid, invalidCount, status] = await oracle.verifyChainIntegrity();
```

## Configuration

- **Oracle Signer**: Address authorized to sign IV reports
- **Max Staleness**: Maximum age of reports (default: 10 minutes)
- **Validation Parameters**: All thresholds configurable via constants

## Testing

The test suite covers:
- Valid IV data acceptance
- Invalid data rejection (6 attack scenarios)
- Signature verification
- Chain integrity verification
- Access control

Run tests: `npx hardhat test`

## Deployment Networks

Configure in `hardhat.config.cjs`:
- **Hardhat**: Local testing
- **Localhost**: Local node
- **Mainnet/Testnet**: Add network configs

## Security Features

1. **EIP-712 Typed Signatures**: Prevents signature replay attacks
2. **Nonce Protection**: Each IV hash can only be used once
3. **Timestamp Validation**: Prevents stale data submission
4. **Comprehensive Validation**: Advanced security rules implemented
5. **Owner Controls**: Upgradeable oracle signer

## Gas Optimization

- Scaled integers (×1000) for precision without floating point
- Efficient validation algorithms
- Minimal storage patterns
- Event-based indexing

## Live Deployment

The SolarOracleWalkman contract is currently deployed on Sepolia testnet:

- **Contract Address**: `0xeF19a90e5786dd0e89264F38f52CF81102db938e`
- **Network**: Sepolia Testnet (Chain ID: 11155111)
- **Etherscan**: https://sepolia.etherscan.io/address/0xeF19a90e5786dd0e89264F38f52CF81102db938e
- **Status**: Active and verified

## Next Steps

1. **Run the tests** to see everything working
2. **Try modifying test data** to see security in action
3. **Deploy to testnet** for real blockchain experience
4. **Integrate with your application** using the contract address

The contract is now ready to validate and store IV voiceprint data securely on the blockchain!

## Chat backend for GitHub Pages visitors (Vercel)

A minimal deployable backend is included at `api/chat.js` for Vercel serverless runtime. The static Pages app now reads a direct API URL from meta and calls that backend so all visitors can use chat without local browser keys.

### Backend deploy steps
1. Create a Vercel project from this repository.
2. Add environment variable:
   - `DEEPSEEK_API_KEY` = your server-side key.
3. Deploy. Example production URL:
   - `https://solar-oracle-walkman-api.vercel.app/api/chat`

### Frontend wiring
- `site/index.html` includes:
  - `<meta name="sow-chat-api" content="https://solar-oracle-walkman-api.vercel.app/api/chat" />`
- `site/app.js` reads this value and posts chat requests there.

Boundary note: this remains a public research prototype, not a legal REC, not T-REC, not an energy equivalence claim, and not a financial product.
