pragma circom 2.0.0;

include "../../node_modules/circomlib/circuits/sha256/sha256.circom";
include "../../node_modules/circomlib/circuits/comparators.circom";

template Preimage() {
    signal input preimage[256]; // 256-bit preimage as array of bits
    signal input hash[8]; // SHA-256 outputs 8 field elements (32 bytes)
    signal output valid;

    component sha256 = Sha256(256);
    sha256.in <== preimage;

    // Compare each element of the hash output
    component equals[8];
    signal eq[8];
    for (var i = 0; i < 8; i++) {
        equals[i] = IsEqual();
        equals[i].in[0] <== sha256.out[i];
        equals[i].in[1] <== hash[i];
        eq[i] <== equals[i].out;
    }
    // Chain the AND operation pairwise
    signal and01, and23, and45, and67, and0123, and4567;
    and01 <== eq[0] * eq[1];
    and23 <== eq[2] * eq[3];
    and45 <== eq[4] * eq[5];
    and67 <== eq[6] * eq[7];
    and0123 <== and01 * and23;
    and4567 <== and45 * and67;
    valid <== and0123 * and4567;
}

component main { public [hash] } = Preimage();
