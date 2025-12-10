#!/usr/bin/env python3
"""Glogos Test Vectors"""

import hashlib
import json

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def test_empty():
    result = sha256_hex(b"")
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert result == expected, f"Empty mismatch: {result}"
    print("✓ Empty axiom verified")

def test_euler():
    euler_string = "e^(i\u03c0) + 1 = 0"
    euler_bytes = euler_string.encode("utf-8")

    # Verify byte representation: e^(iπ) + 1 = 0
    # 65 5e 28 69 cf 80 29 20 2b 20 31 20 3d 20 30
    assert len(euler_bytes) == 15, f"Euler byte count: {len(euler_bytes)}"

    result = sha256_hex(euler_bytes)
    expected = "15458cd30f2922ed7df3b0819d5ce0743c0913811ef1ddb03c1083f2e558d6ad"
    assert result == expected, f"Euler mismatch: {result}"
    print("✓ Euler axiom verified")

def test_merkle_proof():
    """Test Merkle proof verification with positional index."""

    def verify_merkle_proof(leaf_hash, leaf_index, proof, expected_root):
        current = bytes.fromhex(leaf_hash)
        index = leaf_index

        for sibling in proof:
            if sibling == "*":
                sibling_hash = current
            else:
                sibling_hash = bytes.fromhex(sibling)

            if index % 2 == 0:
                current = hashlib.sha256(current + sibling_hash).digest()
            else:
                current = hashlib.sha256(sibling_hash + current).digest()
            index //= 2

        return current.hex() == expected_root

    # Test case: 3 leaves
    leaf_a = sha256_hex(b"leaf_a")
    leaf_b = sha256_hex(b"leaf_b")
    leaf_c = sha256_hex(b"leaf_c")

    # Per spec, leaves MUST be sorted lexicographically before building the tree
    leaves = sorted([leaf_a, leaf_b, leaf_c])

    # Build tree
    node_ab = sha256_hex(bytes.fromhex(leaves[0]) + bytes.fromhex(leaves[1])) # node(a,b)
    node_cc = sha256_hex(bytes.fromhex(leaves[2]) + bytes.fromhex(leaves[2]))  # duplicate
    root = sha256_hex(bytes.fromhex(node_ab) + bytes.fromhex(node_cc))

    # Verify leaf_b (index 1)
    proof_b = [leaves[0], node_cc]
    assert verify_merkle_proof(leaves[1], 1, proof_b, root)
    print("✓ Merkle proof verification works")

def test_entropy_encoding():
    """
    Test entropy computation encoding.
    Verify that hex values are decoded using bytes.fromhex(), not .encode('utf-8').
    """
    # Sample inputs
    ceremony_time = "2025-12-21T15:03:00Z"
    drand_randomness = "abc123def456"  # 12 hex chars = 6 bytes
    nist_output = "AABBCCDD"  # 8 hex chars = 4 bytes  
    btc_hash = "0000000000000000000102030405060708090a0b0c0d0e0f1011121314151617"
    julian_day = "2461031.1270833333"
    
    # CORRECT: using bytes.fromhex()
    components = []
    components.append(ceremony_time.encode("utf-8"))  # timestamp: UTF-8
    components.append(bytes.fromhex(drand_randomness))  # hex → bytes
    components.append(bytes.fromhex(nist_output))  # hex → bytes
    components.append(bytes.fromhex(btc_hash))  # hex → bytes
    components.append(julian_day.encode("utf-8"))  # julian day: UTF-8
    
    correct_preimage = b"".join(components)
    correct_entropy = sha256_hex(correct_preimage)
    
    # WRONG: if we used .encode('utf-8') on hex values
    wrong_components = []
    wrong_components.append(ceremony_time.encode("utf-8"))
    wrong_components.append(drand_randomness.encode("utf-8"))  # WRONG!
    wrong_components.append(nist_output.encode("utf-8"))  # WRONG!
    wrong_components.append(btc_hash.encode("utf-8"))  # WRONG!
    wrong_components.append(julian_day.encode("utf-8"))
    
    wrong_preimage = b"".join(wrong_components)
    wrong_entropy = sha256_hex(wrong_preimage)
    
    # They must be different
    assert correct_entropy != wrong_entropy, "Entropy should differ with wrong encoding"
    assert len(correct_preimage) == 80, f"Expected 80 bytes, got {len(correct_preimage)}"
    assert len(wrong_preimage) == 122, f"Expected 122 bytes with wrong encoding, got {len(wrong_preimage)}"
    
    print("✓ Entropy encoding verified (bytes.fromhex used correctly)")

if __name__ == "__main__":
    test_empty()
    test_euler()
    test_merkle_proof()
    test_entropy_encoding()
    print("\nAll tests passed!")