import { PublicKey, Keypair } from "@solana/web3.js";
import * as IDL from "./pump-fun-idl.json";
import * as dotenv from "dotenv";
dotenv.config();

export const GRIMNODE_CONFIG = {
  NAME: "GrimBundle",
  RPC_ENDPOINT: process.env.RPC_ENDPOINT || "https://api.devnet.solana.com",
  WS_ENDPOINT: process.env.WS_ENDPOINT || "wss://api.devnet.solana.com",
  PUMP_FUN_PROGRAM: new PublicKey("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"),
  FEE_RECIPIENT: new PublicKey("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM"),
  JITO_ENDPOINT: process.env.JITO_ENDPOINT || "https://mainnet.block-engine.jito.wtf",
  SLIPPAGE: Number(process.env.SLIPPAGE) || 0.1,
  MIN_SOL_PER_BUY: Number(process.env.MIN_SOL_PER_BUY) || 0.02,
  BUNDLE_SIZE: Number(process.env.BUNDLE_SIZE) || 16,
  BUMP_AMOUNT: Number(process.env.BUMP_AMOUNT) || 0.01,
  BUMP_INTERVAL_MS: Number(process.env.BUMP_INTERVAL_MS) || 60000,
  PUMP_IDL: IDL,
};

export function getPayerKeypair(): Keypair {
  if (process.env.PAYER_PRIVATE_KEY) {
    const secret = JSON.parse(process.env.PAYER_PRIVATE_KEY);
    return Keypair.fromSecretKey(new Uint8Array(secret));
  }
  throw new Error("PAYER_PRIVATE_KEY not set in .env");
} 