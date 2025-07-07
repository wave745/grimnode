import { Connection, Keypair, Transaction, SystemProgram, PublicKey, SimulatedTransactionResponse, RpcResponseAndContext, Commitment } from "@solana/web3.js";
import { GRIMNODE_CONFIG, getPayerKeypair } from "./config";
import { generateGrimWallets, loadGrimWallet, logger } from "./utils";
import { createGrimToken, createGrimBundleBuys, grimBumpToken, monitorGrimTokens } from "./grimbundle";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

const argv = yargs(hideBin(process.argv))
  .option("bundleSize", { type: "number", description: "Number of wallets in the bundle", default: GRIMNODE_CONFIG.BUNDLE_SIZE })
  .option("solPerBuy", { type: "number", description: "SOL per buy", default: GRIMNODE_CONFIG.MIN_SOL_PER_BUY })
  .option("slippage", { type: "number", description: "Slippage", default: GRIMNODE_CONFIG.SLIPPAGE })
  .option("txDelay", { type: "number", description: "Delay between transactions (ms)", default: Number(process.env.TX_DELAY_MS) || 500 })
  .help()
  .argv as any;

const TX_DELAY_MS = argv.txDelay;
const CONFIRMATION_COMMITMENT: Commitment = "finalized";

async function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function hasSufficientBalance(connection: Connection, pubkey: PublicKey, requiredLamports: number): Promise<boolean> {
  const balance = await connection.getBalance(pubkey);
  return balance >= requiredLamports;
}

async function confirmTx(connection: Connection, sig: string): Promise<boolean> {
  try {
    const result = await connection.confirmTransaction(sig, CONFIRMATION_COMMITMENT);
    if (result.value.err) {
      logger.error(`[CONFIRMATION FAILED] ${sig}: ${JSON.stringify(result.value.err)}`);
      return false;
    }
    logger.info(`[CONFIRMED] ${sig}`);
    return true;
  } catch (e) {
    logger.error(`[CONFIRMATION ERROR] ${sig}: ${e}`);
    return false;
  }
}

async function simulateAndSend(connection: Connection, tx: Transaction, signers: Keypair[], requiredLamports?: number): Promise<string | null> {
  try {
    if (requiredLamports && !(await hasSufficientBalance(connection, signers[0].publicKey, requiredLamports))) {
      logger.warn(`[BALANCE] Wallet ${signers[0].publicKey.toBase58()} has insufficient SOL. Required: ${requiredLamports / 1e9} SOL`);
      return null;
    }
    tx.recentBlockhash = (await connection.getLatestBlockhash()).blockhash;
    tx.feePayer = signers[0].publicKey;
    tx.sign(...signers);
    // Simulate the transaction
    const simResult: RpcResponseAndContext<SimulatedTransactionResponse> = await connection.simulateTransaction(tx);
    if (simResult.value.err) {
      logger.error(`[SIMULATION FAILED] ${JSON.stringify(simResult.value.err)}`);
      return null;
    }
    logger.info(`[SIMULATION SUCCESS]`);
    const sig = await connection.sendRawTransaction(tx.serialize());
    logger.info(`[TX SENT] ${sig}`);
    const confirmed = await confirmTx(connection, sig);
    if (!confirmed) {
      logger.error(`[TX NOT CONFIRMED] ${sig}`);
      return null;
    }
    return sig;
  } catch (e) {
    logger.error(`[SIMULATION ERROR] ${e}`);
    return null;
  }
}

async function main() {
  // Use mainnet for production
  const connection = new Connection(GRIMNODE_CONFIG.RPC_ENDPOINT, "confirmed");
  let payer: Keypair;
  try {
    payer = getPayerKeypair();
  } catch (e) {
    logger.error("Could not load payer keypair from .env. Please set PAYER_PRIVATE_KEY.");
    process.exit(1);
  }
  const subWallets = generateGrimWallets(argv.bundleSize);

  // Fund sub-wallets from payer (devnet only)
  for (const wallet of subWallets) {
    const tx = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: payer.publicKey,
        toPubkey: wallet.publicKey,
        lamports: argv.solPerBuy * 1e9,
      })
    );
    await simulateAndSend(connection, tx, [payer], argv.solPerBuy * 1e9);
    await delay(TX_DELAY_MS);
  }

  // Create token
  const { mint, transaction } = await createGrimToken(
    connection,
    payer,
    "GrimToken",
    "GRIM",
    "https://grimbundle.io/token.png"
  );
  logger.info(`Created GrimToken: ${mint.toBase58()}`);

  // Bundle buys
  const buyTxs = await createGrimBundleBuys(
    connection,
    mint,
    subWallets,
    argv.solPerBuy
  );
  for (let i = 0; i < buyTxs.length; i++) {
    const sig = await simulateAndSend(connection, buyTxs[i], [subWallets[i]], argv.solPerBuy * 1e9);
    if (sig) {
      logger.info(`GrimBundle buy sent from wallet ${i}: ${sig}`);
    } else {
      logger.warn(`[SKIPPED] Buy from wallet ${i} due to simulation failure or insufficient balance.`);
    }
    await delay(TX_DELAY_MS);
  }

  // Start bumping
  await grimBumpToken(connection, mint, subWallets, GRIMNODE_CONFIG.BUMP_INTERVAL_MS);

  // Monitor for other tokens to snipe
  monitorGrimTokens(connection, async (newMint: PublicKey) => {
    logger.info(`Sniping new token: ${newMint.toBase58()}`);
    const snipeTxs = await createGrimBundleBuys(
      connection,
      newMint,
      subWallets,
      argv.solPerBuy
    );
    for (let i = 0; i < snipeTxs.length; i++) {
      const sig = await simulateAndSend(connection, snipeTxs[i], [subWallets[i]], argv.solPerBuy * 1e9);
      if (sig) {
        logger.info(`Sniped buy sent from wallet ${i}: ${sig}`);
      } else {
        logger.warn(`[SKIPPED] Snipe from wallet ${i} due to simulation failure or insufficient balance.`);
      }
      await delay(TX_DELAY_MS);
    }
  });
}

main().catch((err) => logger.error(`GrimBundle error: ${err}`)); 