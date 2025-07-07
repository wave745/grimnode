/// <reference path="./snarkjs.d.ts" />
import { Keypair } from "@solana/web3.js";
import * as fs from "fs";
import winston from "winston";
import * as snarkjs from 'snarkjs';

declare module 'snarkjs';

export function generateGrimWallets(count: number): Keypair[] {
  const wallets: Keypair[] = [];
  for (let i = 0; i < count; i++) {
    const keypair = Keypair.generate();
    wallets.push(keypair);
    fs.writeFileSync(`grim-wallet-${i}.json`, JSON.stringify(Array.from(keypair.secretKey)));
  }
  return wallets;
}

export function loadGrimWallet(filePath: string): Keypair {
  const secretKey = JSON.parse(fs.readFileSync(filePath, "utf-8"));
  return Keypair.fromSecretKey(new Uint8Array(secretKey));
}

// Winston logger setup
export const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message }: { timestamp: string; level: string; message: string }) => `${timestamp} [${level.toUpperCase()}] ${message}`)
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: "grimnode.log" })
  ]
});

// zk-SNARK utilities (using snarkjs)
export async function generateProof(input: any, wasmPath: string, zkeyPath: string) {
    // Generate a proof using snarkjs.groth16.fullProve
    return await snarkjs.groth16.fullProve(input, wasmPath, zkeyPath);
}

export async function verifyProof(vkeyPath: string, publicSignals: any, proof: any) {
    // Load verification key
    const vkey = JSON.parse(fs.readFileSync(vkeyPath, 'utf-8'));
    return await snarkjs.groth16.verify(vkey, publicSignals, proof);
}

include "../../node_modules/circomlib/circuits/sha256/sha256.circom";
include "../../node_modules/circomlib/circuits/comparators.circom";