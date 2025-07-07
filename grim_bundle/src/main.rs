use solana_sdk::{transaction::Transaction, instruction::Instruction, message::Message, signature::Signer, signer::keypair::Keypair, hash::Hash, pubkey::Pubkey, system_instruction};
use solana_client::rpc_client::RpcClient;
use std::env;
use std::fs;
use serde::{Deserialize};
use bs58;
use std::str::FromStr;

#[derive(Deserialize)]
struct BundleInput {
    wallets: Vec<String>, // base58-encoded keypairs
    instructions: Vec<TransferInstruction>,
}

#[derive(Deserialize)]
struct TransferInstruction {
    from: usize, // index in wallets array
    to_pubkey: String, // base58 pubkey
    lamports: u64,
}

fn bundle_trades(wallets: &Vec<Keypair>, instructions: Vec<Instruction>) -> Transaction {
    let payer = &wallets[0];
    let message = Message::new(&instructions, Some(&payer.pubkey()));
    Transaction::new(&[payer], message, Hash::new_unique())
}

fn parse_keypair(base58_str: &str) -> Keypair {
    let bytes = bs58::decode(base58_str).into_vec().expect("Invalid base58");
    Keypair::from_bytes(&bytes).expect("Invalid keypair bytes")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("Usage: grim_bundle <input_json> [--send] [--rpc <url>]");
        return;
    }
    let input_path = &args[1];
    let send = args.contains(&"--send".to_string());
    let rpc_url = args.iter().position(|x| x == "--rpc").and_then(|i| args.get(i+1)).cloned().unwrap_or_else(|| "https://api.devnet.solana.com".to_string());

    let input_data = fs::read_to_string(input_path).expect("Failed to read input file");
    let bundle_input: BundleInput = serde_json::from_str(&input_data).expect("Invalid JSON");
    println!("Loaded wallets: {}", bundle_input.wallets.len());
    println!("Loaded instructions: {}", bundle_input.instructions.len());

    // Parse keypairs
    let keypairs: Vec<Keypair> = bundle_input.wallets.iter().map(|s| parse_keypair(s)).collect();
    println!("Parsed {} keypairs.", keypairs.len());

    // Parse transfer instructions
    let mut instructions: Vec<Instruction> = Vec::new();
    for (i, ti) in bundle_input.instructions.iter().enumerate() {
        if ti.from >= keypairs.len() {
            println!("Error: instruction {} refers to invalid wallet index {}", i, ti.from);
            continue;
        }
        let from_pubkey = keypairs[ti.from].pubkey();
        let to_pubkey = match Pubkey::from_str(&ti.to_pubkey) {
            Ok(pk) => pk,
            Err(_) => {
                println!("Error: instruction {} has invalid to_pubkey {}", i, ti.to_pubkey);
                continue;
            }
        };
        let ix = system_instruction::transfer(&from_pubkey, &to_pubkey, ti.lamports);
        instructions.push(ix);
    }

    let mut tx = bundle_trades(&keypairs, instructions);
    println!("Created transaction with {} signers.", tx.signatures.len());
    println!("Message hash: {:?}", tx.message.hash());

    if send {
        println!("Sending transaction to {}...", rpc_url);
        let client = RpcClient::new(rpc_url);
        let recent_blockhash = client.get_latest_blockhash().expect("Failed to get blockhash");
        // Prepare a vector of references
        let keypair_refs: Vec<&Keypair> = keypairs.iter().collect();
        tx.sign(&keypair_refs, recent_blockhash);
        match client.send_and_confirm_transaction(&tx) {
            Ok(sig) => println!("Transaction sent! Signature: {}", sig),
            Err(e) => println!("Error sending transaction: {}", e),
        }
    } else {
        println!("Not sending transaction. Use --send to broadcast.");
    }
}