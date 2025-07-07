import { AnchorProvider, Program, Wallet } from "@coral-xyz/anchor";
import { Connection, Keypair, PublicKey, Transaction, SystemProgram } from "@solana/web3.js";
import { createAssociatedTokenAccountInstruction, getAssociatedTokenAddressSync } from "@solana/spl-token";
import { GRIMNODE_CONFIG } from "./config";
import BN from "bn.js";
import { logger } from "./utils";

// 1. Token Creation (using Anchor IDL)
export async function createGrimToken(
  connection: Connection,
  payer: Keypair,
  name: string,
  symbol: string,
  imageUri: string
): Promise<{ mint: PublicKey; transaction: Transaction }> {
  const provider = new AnchorProvider(connection, new Wallet(payer), { commitment: "confirmed" });
  const program = new Program(GRIMNODE_CONFIG.PUMP_IDL as any, GRIMNODE_CONFIG.PUMP_FUN_PROGRAM, provider);

  const mintKeypair = Keypair.generate();
  const bondingCurve = PublicKey.findProgramAddressSync(
    [Buffer.from("bonding-curve"), mintKeypair.publicKey.toBytes()],
    GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
  )[0];
  const associatedBondingCurve = getAssociatedTokenAddressSync(
    mintKeypair.publicKey,
    bondingCurve,
    true
  );

  const createIx = await program.methods
    .create(name, symbol, imageUri)
    .accounts({
      mint: mintKeypair.publicKey,
      bondingCurve,
      associatedBondingCurve,
      global: PublicKey.findProgramAddressSync([Buffer.from("global")], GRIMNODE_CONFIG.PUMP_FUN_PROGRAM)[0],
      feeRecipient: GRIMNODE_CONFIG.FEE_RECIPIENT,
      user: payer.publicKey,
      systemProgram: SystemProgram.programId,
      tokenProgram: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
      rent: new PublicKey("SysvarRent111111111111111111111111111111111"),
      eventAuthority: PublicKey.findProgramAddressSync(
        [Buffer.from("__event_authority")],
        GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
      )[0],
      program: GRIMNODE_CONFIG.PUMP_FUN_PROGRAM,
    })
    .signers([payer, mintKeypair])
    .instruction();

  const tx = new Transaction().add(createIx);
  return { mint: mintKeypair.publicKey, transaction: tx };
}

// 2. Bundled Buy Transactions (using Anchor IDL)
export async function createGrimBundleBuys(
  connection: Connection,
  mint: PublicKey,
  wallets: Keypair[],
  solAmount: number
): Promise<Transaction[]> {
  const program = new Program(GRIMNODE_CONFIG.PUMP_IDL as any, GRIMNODE_CONFIG.PUMP_FUN_PROGRAM, new AnchorProvider(connection, new Wallet(wallets[0]), { commitment: "confirmed" }));
  const transactions: Transaction[] = [];
  const bondingCurve = PublicKey.findProgramAddressSync(
    [Buffer.from("bonding-curve"), mint.toBytes()],
    GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
  )[0];
  const associatedBondingCurve = getAssociatedTokenAddressSync(mint, bondingCurve, true);

  for (const wallet of wallets) {
    const tokenAccount = getAssociatedTokenAddressSync(mint, wallet.publicKey, true);
    const ataIx = createAssociatedTokenAccountInstruction(
      wallet.publicKey,
      tokenAccount,
      wallet.publicKey,
      mint
    );
    const buyIx = await program.methods
      .buy(new BN(solAmount * 1e9), new BN(solAmount * 1e9 * (1 + GRIMNODE_CONFIG.SLIPPAGE)))
      .accounts({
        mint,
        bondingCurve,
        associatedBondingCurve,
        associatedUser: tokenAccount,
        user: wallet.publicKey,
        feeRecipient: GRIMNODE_CONFIG.FEE_RECIPIENT,
        systemProgram: SystemProgram.programId,
        tokenProgram: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
        rent: new PublicKey("SysvarRent111111111111111111111111111111111"),
        eventAuthority: PublicKey.findProgramAddressSync(
          [Buffer.from("__event_authority")],
          GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
        )[0],
        program: GRIMNODE_CONFIG.PUMP_FUN_PROGRAM,
      })
      .instruction();
    const tx = new Transaction().add(ataIx, buyIx);
    transactions.push(tx);
  }
  return transactions;
}

// 3. Bumping for Visibility (using Anchor IDL)
export async function grimBumpToken(
  connection: Connection,
  mint: PublicKey,
  wallets: Keypair[],
  intervalMs: number
) {
  const program = new Program(GRIMNODE_CONFIG.PUMP_IDL as any, GRIMNODE_CONFIG.PUMP_FUN_PROGRAM, new AnchorProvider(connection, new Wallet(wallets[0]), { commitment: "confirmed" }));
  const bondingCurve = PublicKey.findProgramAddressSync(
    [Buffer.from("bonding-curve"), mint.toBytes()],
    GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
  )[0];
  const associatedBondingCurve = getAssociatedTokenAddressSync(mint, bondingCurve, true);

  for (const wallet of wallets) {
    const tokenAccount = getAssociatedTokenAddressSync(mint, wallet.publicKey, true);
    const ataIx = createAssociatedTokenAccountInstruction(
      wallet.publicKey,
      tokenAccount,
      wallet.publicKey,
      mint
    );
    const bumpIx = await program.methods
      .buy(new BN(GRIMNODE_CONFIG.BUMP_AMOUNT * 1e9), new BN(GRIMNODE_CONFIG.BUMP_AMOUNT * 1e9 * (1 + GRIMNODE_CONFIG.SLIPPAGE)))
      .accounts({
        mint,
        bondingCurve,
        associatedBondingCurve,
        associatedUser: tokenAccount,
        user: wallet.publicKey,
        feeRecipient: GRIMNODE_CONFIG.FEE_RECIPIENT,
        systemProgram: SystemProgram.programId,
        tokenProgram: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
        rent: new PublicKey("SysvarRent111111111111111111111111111111111"),
        eventAuthority: PublicKey.findProgramAddressSync(
          [Buffer.from("__event_authority")],
          GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
        )[0],
        program: GRIMNODE_CONFIG.PUMP_FUN_PROGRAM,
      })
      .instruction();
    const tx = new Transaction().add(ataIx, bumpIx);
    await connection.sendTransaction(tx, [wallet]);
    console.log(`GrimBundle bump executed for ${mint.toBase58()}`);
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

// 4. Monitoring for new tokens (using Solana RPC)
export async function monitorGrimTokens(connection: Connection, callback: (mint: PublicKey) => void) {
  connection.onProgramAccountChange(
    GRIMNODE_CONFIG.PUMP_FUN_PROGRAM,
    async (keyedAccountInfo) => {
      const mint = keyedAccountInfo.accountId; // Simplified; parse with IDL for accuracy
      console.log(`GrimBundle detected new token: ${mint.toBase58()}`);
      callback(mint);
    },
    "confirmed",
    [{ dataSize: 165 }]
  );
}

// Sell logic
export async function grimSellToken(
  connection: Connection,
  mint: PublicKey,
  wallet: Keypair,
  amount: number
) {
  const provider = new AnchorProvider(connection, new Wallet(wallet), { commitment: "confirmed" });
  const program = new Program(GRIMNODE_CONFIG.PUMP_IDL as any, GRIMNODE_CONFIG.PUMP_FUN_PROGRAM, provider);

  const bondingCurve = PublicKey.findProgramAddressSync(
    [Buffer.from("bonding-curve"), mint.toBytes()],
    GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
  )[0];
  const associatedBondingCurve = getAssociatedTokenAddressSync(mint, bondingCurve, true);
  const tokenAccount = getAssociatedTokenAddressSync(mint, wallet.publicKey, true);

  const ataIx = createAssociatedTokenAccountInstruction(
    wallet.publicKey,
    tokenAccount,
    wallet.publicKey,
    mint
  );
  const sellIx = await program.methods
    .sell(new BN(amount * 1e6)) // 6 decimals for Pump.fun tokens
    .accounts({
      mint,
      bondingCurve,
      associatedBondingCurve,
      associatedUser: tokenAccount,
      user: wallet.publicKey,
      feeRecipient: GRIMNODE_CONFIG.FEE_RECIPIENT,
      systemProgram: SystemProgram.programId,
      tokenProgram: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
      rent: new PublicKey("SysvarRent111111111111111111111111111111111"),
      eventAuthority: PublicKey.findProgramAddressSync(
        [Buffer.from("__event_authority")],
        GRIMNODE_CONFIG.PUMP_FUN_PROGRAM
      )[0],
      program: GRIMNODE_CONFIG.PUMP_FUN_PROGRAM,
    })
    .instruction();
  const tx = new Transaction().add(ataIx, sellIx);
  try {
    const sig = await connection.sendTransaction(tx, [wallet]);
    logger.info(`GrimBundle sold ${amount} tokens for ${mint.toBase58()}: ${sig}`);
    return sig;
  } catch (e) {
    logger.error(`Sell failed for ${mint.toBase58()}: ${e}`);
    return null;
  }
} 