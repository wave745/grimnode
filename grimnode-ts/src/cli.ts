import { program } from "commander";
const snarkjs = require("snarkjs");
import { createHash } from "crypto";
import fs from "fs";

program
  .name("GrimBundle CLI")
  .description("CLI for GrimBundle zk-SNARK operations");

// Helper: Convert string to 256-bit array
function stringToBits(str: string, length: number): number[] {
  const bits: number[] = [];
  for (let i = 0; i < str.length && bits.length < length; i++) {
    const charCode = str.charCodeAt(i);
    for (let j = 7; j >= 0 && bits.length < length; j--) {
      bits.push((charCode >> j) & 1);
    }
  }
  while (bits.length < length) bits.push(0);
  return bits.slice(0, length);
}

// Helper: Convert Buffer to 8 field elements (32 bytes total)
function bufferToFieldElements(buffer: Buffer): number[] {
  const elements: number[] = [];
  // SHA-256 produces 32 bytes, we need 8 field elements of 4 bytes each
  for (let i = 0; i < 8; i++) {
    const start = i * 4;
    const end = start + 4;
    const bytes = buffer.slice(start, end);
    // Convert 4 bytes to a 32-bit integer
    const element = bytes.readUInt32BE(0);
    elements.push(element);
  }
  return elements;
}

program
  .command("generate-proof")
  .description("Generate a zk-SNARK proof for knowledge of preimage")
  .requiredOption("--preimage <string>", "Secret preimage (e.g., '12345')")
  .action(async (options) => {
    try {
      const preimageStr = options.preimage;
      console.log(`Generating proof for preimage: "${preimageStr}"`);
      
      const preimageBits = stringToBits(preimageStr, 256);
      const hash = createHash("sha256").update(preimageStr).digest();
      const hashElements = bufferToFieldElements(hash);
      
      console.log(`Preimage bits length: ${preimageBits.length}`);
      console.log(`Hash elements length: ${hashElements.length}`);
      console.log(`Hash elements: [${hashElements.join(', ')}]`);
      
      console.log("Loading circuit files...");
      const { proof, publicSignals } = await snarkjs.groth16.fullProve(
        { preimage: preimageBits, hash: hashElements },
        "src/circuits/preimage_js/preimage.wasm",
        "src/circuits/preimage_zkkey.zkey"
      );
      
      console.log("GrimBundle Proof Generated:", JSON.stringify(proof, null, 2));
      console.log("Public Signals:", publicSignals);
      
      // Ensure directories exist
      const dir = "src/circuits";
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      fs.writeFileSync("src/circuits/proof.json", JSON.stringify(proof));
      fs.writeFileSync("src/circuits/public.json", JSON.stringify(publicSignals));
      console.log("Proof saved to src/circuits/proof.json");
      console.log("Public signals saved to src/circuits/public.json");
    } catch (error) {
      console.error("Error generating proof:", error);
      console.error("Make sure the circuit files exist:");
      console.error("- src/circuits/preimage_js/preimage.wasm");
      console.error("- src/circuits/preimage_zkkey.zkey");
      console.error("Note: You may need to generate the .zkey file first using snarkjs");
    }
  });

program
  .command("verify-proof")
  .description("Verify a zk-SNARK proof")
  .action(async () => {
    try {
      const proof = JSON.parse(fs.readFileSync("src/circuits/proof.json", "utf-8"));
      const publicSignals = JSON.parse(fs.readFileSync("src/circuits/public.json", "utf-8"));
      const verificationKey = JSON.parse(fs.readFileSync("src/circuits/verification_key.json", "utf-8"));
      const isValid = await snarkjs.groth16.verify(verificationKey, publicSignals, proof);
      console.log(`GrimBundle Proof Verification: ${isValid ? "Valid" : "Invalid"}`);
    } catch (error) {
      console.error("Error verifying proof:", error);
      console.error("Make sure the proof files exist:");
      console.error("- src/circuits/proof.json");
      console.error("- src/circuits/public.json");
      console.error("- src/circuits/verification_key.json");
    }
  });

program.parse(); 