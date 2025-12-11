#!/usr/bin/env python3
"""
Unified Merkle Tree Builder
Aligned with Glogos Specification v1.0.0-rc.0 §4

Combines multiple attestation sources into a single Merkle tree.
"""

import hashlib
import json
import os
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Get script directory (works from any CWD)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ZONE_REF_DIR = os.path.dirname(SCRIPT_DIR)

# Add zone-reference to path for imports
sys.path.insert(0, ZONE_REF_DIR)
os.chdir(ZONE_REF_DIR)

try:
    from zone.merkle import MerkleEngine
except ImportError:
    print("ERROR: Could not import zone.merkle")
    sys.exit(1)


@dataclass
class MerkleTreeResult:
    root: str
    leaf_count: int
    tree_height: int
    build_time_ms: float
    leaves: List[str]


def build_unified_tree(attestation_ids: List[str], verbose: bool = True) -> MerkleTreeResult:
    """
    Build unified Merkle tree from multiple attestation sources.
    
    Args:
        attestation_ids: List of 64-char hex attestation IDs
        verbose: Print progress
    
    Returns:
        MerkleTreeResult with root and metadata
    """
    import time
    
    if verbose:
        print(f"\n{'='*60}")
        print("UNIFIED MERKLE TREE BUILDER")
        print(f"{'='*60}")
        print(f"\nInputs: {len(attestation_ids)} attestations")
    
    engine = MerkleEngine()
    
    start = time.perf_counter()
    
    # Add all leaves
    for aid in attestation_ids:
        engine.add_leaf(aid)
    
    # Compute root
    root = engine.compute_root()
    
    elapsed = (time.perf_counter() - start) * 1000
    
    # Calculate tree height
    import math
    height = math.ceil(math.log2(max(len(attestation_ids), 1))) + 1 if attestation_ids else 0
    
    if verbose:
        print(f"\n[CHART] Build Results:")
        print(f"   Leaves: {len(attestation_ids)}")
        print(f"   Tree height: {height} levels")
        print(f"   Build time: {elapsed:.2f}ms")
        print(f"   Root: {root}")
    
    return MerkleTreeResult(
        root=root,
        leaf_count=len(attestation_ids),
        tree_height=height,
        build_time_ms=elapsed,
        leaves=sorted([aid.lower() for aid in attestation_ids])
    )


def load_attestations_from_file(filepath: str) -> List[str]:
    """Load attestation IDs from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Support different formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'attestation_id' in data:
            return [data['attestation_id']]
        elif 'attestations' in data:
            return [a.get('attestation_id') for a in data['attestations'] if a.get('attestation_id')]
    
    return []


def main():
    print("""
+===============================================================+
|       GLOGOS UNIFIED MERKLE TREE BUILDER - v1.0.0-rc.0       |
+===============================================================+
    """)
    
    # Check for existing attestation files
    examples_dir = SCRIPT_DIR
    glogos_proposal_dir = os.path.join(examples_dir, 'glogos-proposal')
    
    all_attestation_ids = []
    
    # Load from glogos-proposal if exists
    proposal_attestation = os.path.join(glogos_proposal_dir, 'proposal_attestation.json')
    if os.path.exists(proposal_attestation):
        print(f"[DOC] Loading: {proposal_attestation}")
        ids = load_attestations_from_file(proposal_attestation)
        all_attestation_ids.extend(ids)
        print(f"   Found: {len(ids)} attestation(s)")
    
    # Generate some test attestations if needed
    if len(all_attestation_ids) < 3:
        print(f"\n📝 Generating test attestations to demonstrate tree...")
        import hashlib
        for i in range(5 - len(all_attestation_ids)):
            test_claim = f"Test claim #{i+1} at {datetime.now().isoformat()}"
            test_id = hashlib.sha256(test_claim.encode()).hexdigest()
            all_attestation_ids.append(test_id)
            print(f"   Generated: {test_id[:24]}...")
    
    # Build unified tree
    result = build_unified_tree(all_attestation_ids, verbose=True)
    
    # Save result
    output = {
        "version": "1.0-rc.0",
        "merkle_root": result.root,
        "leaf_count": result.leaf_count,
        "tree_height": result.tree_height,
        "build_time_ms": result.build_time_ms,
        "built_at": datetime.now().isoformat(),
        "leaves": result.leaves[:10] if result.leaf_count > 10 else result.leaves,
        "leaves_truncated": result.leaf_count > 10
    }
    
    output_path = os.path.join(examples_dir, 'unified_merkle_tree.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved to: {output_path}")
    print(f"{'='*60}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()


@dataclass
class MerkleTreeResult:
    root: str
    leaf_count: int
    tree_height: int
    build_time_ms: float
    leaves: List[str]


def build_unified_tree(attestation_ids: List[str], verbose: bool = True) -> MerkleTreeResult:
    """
    Build unified Merkle tree from multiple attestation sources.
    
    Args:
        attestation_ids: List of 64-char hex attestation IDs
        verbose: Print progress
    
    Returns:
        MerkleTreeResult with root and metadata
    """
    import time
    
    if verbose:
        print(f"\n{'='*60}")
        print("UNIFIED MERKLE TREE BUILDER")
        print(f"{'='*60}")
        print(f"\nInputs: {len(attestation_ids)} attestations")
    
    engine = MerkleEngine()
    
    start = time.perf_counter()
    
    # Add all leaves
    for aid in attestation_ids:
        engine.add_leaf(aid)
    
    # Compute root
    root = engine.compute_root()
    
    elapsed = (time.perf_counter() - start) * 1000
    
    # Calculate tree height
    import math
    height = math.ceil(math.log2(max(len(attestation_ids), 1))) + 1 if attestation_ids else 0
    
    if verbose:
        print(f"\n[CHART] Build Results:")
        print(f"   Leaves: {len(attestation_ids)}")
        print(f"   Tree height: {height} levels")
        print(f"   Build time: {elapsed:.2f}ms")
        print(f"   Root: {root}")
    
    return MerkleTreeResult(
        root=root,
        leaf_count=len(attestation_ids),
        tree_height=height,
        build_time_ms=elapsed,
        leaves=sorted([aid.lower() for aid in attestation_ids])
    )


def load_attestations_from_file(filepath: str) -> List[str]:
    """Load attestation IDs from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Support different formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'attestation_id' in data:
            return [data['attestation_id']]
        elif 'attestations' in data:
            return [a.get('attestation_id') for a in data['attestations'] if a.get('attestation_id')]
    
    return []


def main():
    print("""
+===============================================================+
|       GLOGOS UNIFIED MERKLE TREE BUILDER - v1.0.0-rc.0       |
+===============================================================+
    """)
    
    # Check for existing attestation files
    examples_dir = os.path.dirname(__file__)
    glogos_proposal_dir = os.path.join(examples_dir, 'glogos-proposal')
    
    all_attestation_ids = []
    
    # Load from glogos-proposal if exists
    proposal_attestation = os.path.join(glogos_proposal_dir, 'proposal_attestation.json')
    if os.path.exists(proposal_attestation):
        print(f"[DOC] Loading: {proposal_attestation}")
        ids = load_attestations_from_file(proposal_attestation)
        all_attestation_ids.extend(ids)
        print(f"   Found: {len(ids)} attestation(s)")
    
    # Generate some test attestations if needed
    if len(all_attestation_ids) < 3:
        print(f"\n📝 Generating test attestations to demonstrate tree...")
        for i in range(5 - len(all_attestation_ids)):
            test_claim = f"Test claim #{i+1} at {datetime.now().isoformat()}"
            test_id = hashlib.sha256(test_claim.encode()).hexdigest()
            all_attestation_ids.append(test_id)
            print(f"   Generated: {test_id[:24]}...")
    
    # Build unified tree
    result = build_unified_tree(all_attestation_ids, verbose=True)
    
    # ASCII Tree visualization
    print(f"\n{'='*60}")
    print("TREE VISUALIZATION")
    print(f"{'='*60}")
    
    if result.leaf_count <= 8:
        # Show simple tree
        sorted_leaves = result.leaves
        print("\nLeaves (sorted):")
        for i, leaf in enumerate(sorted_leaves):
            print(f"  [{i}] {leaf[:24]}...")
        
        print(f"\nTree structure:")
        print(f"  Root: {result.root[:24]}...")
        print(f"  Height: {result.tree_height} levels")
        print(f"  Rule: Each parent = SHA256(left_child || right_child)")
    else:
        print(f"\n  Tree too large to display ({result.leaf_count} leaves)")
        print(f"  Root: {result.root}")
    
    # Save result
    output = {
        "version": "1.0-rc.0",
        "merkle_root": result.root,
        "leaf_count": result.leaf_count,
        "tree_height": result.tree_height,
        "build_time_ms": result.build_time_ms,
        "built_at": datetime.now().isoformat(),
        "leaves": result.leaves[:10] if result.leaf_count > 10 else result.leaves,
        "leaves_truncated": result.leaf_count > 10
    }
    
    output_path = os.path.join(examples_dir, 'unified_merkle_tree.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved to: {output_path}")
    print(f"{'='*60}")
    
    return result


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Merkle Tree Visualization Demo
Aligned with Glogos Specification v1.0.0-rc.0 §4
"""

import hashlib
from typing import List, Tuple

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_short(data: bytes) -> str:
    """Short hash for display"""
    return sha256_hex(data)[:8]

def build_merkle_tree_visual(attestation_ids: List[str]) -> Tuple[str, List[List[str]]]:
    """
    Build Merkle tree and return root + all levels for visualization.
    
    Rules per Spec §4.4:
    1. Collect all attestation_ids as leaf nodes
    2. Sort leaves lexicographically (lowercase hex)
    3. Build binary tree: internal_node = SHA256(left || right)
    4. Odd leaf count: duplicate the last leaf
    5. Empty tree: root = SHA256("")
    """
    # Rule 5: Empty tree
    if not attestation_ids:
        return sha256_hex(b""), [[sha256_hex(b"")[:16] + "..."]]
    
    # Rule 2: Sort lexicographically
    sorted_leaves = sorted([id.lower() for id in attestation_ids])
    
    # Build tree level by level
    all_levels = []
    level = [bytes.fromhex(h) for h in sorted_leaves]
    all_levels.append([h[:8] + "..." for h in sorted_leaves])
    
    level_num = 0
    print(f"\n{'='*60}")
    print("MERKLE TREE CONSTRUCTION")
    print(f"{'='*60}")
    print(f"\nLevel 0 (Leaves - sorted):")
    for i, leaf in enumerate(sorted_leaves):
        print(f"  [{i}] {leaf[:16]}...")
    
    while len(level) > 1:
        level_num += 1
        next_level = []
        next_level_display = []
        
        print(f"\nLevel {level_num}:")
        
        for i in range(0, len(level), 2):
            left = level[i]
            
            # Rule 4: Odd count - duplicate last
            if i + 1 < len(level):
                right = level[i + 1]
                dup_marker = ""
            else:
                right = level[i]
                dup_marker = " [DUP]"
            
            # Rule 3: SHA256(left || right)
            parent = hashlib.sha256(left + right).digest()
            next_level.append(parent)
            next_level_display.append(parent.hex()[:8] + "...")
            
            print(f"  SHA256({left.hex()[:8]}... || {right.hex()[:8]}...{dup_marker})")
            print(f"    = {parent.hex()[:16]}...")
        
        level = next_level
        all_levels.append(next_level_display)
    
    root = level[0].hex()
    print(f"\n{'='*60}")
    print(f"MERKLE ROOT: {root}")
    print(f"{'='*60}")
    
    return root, all_levels


def generate_proof_visual(attestation_id: str, all_ids: List[str]) -> dict:
    """
    Generate and visualize Merkle proof per Spec §4.1-4.3
    """
    sorted_leaves = sorted([id.lower() for id in all_ids])
    target = attestation_id.lower()
    
    try:
        leaf_index = sorted_leaves.index(target)
    except ValueError:
        print(f"❌ Attestation {target[:16]}... not found")
        return None
    
    print(f"\n{'='*60}")
    print(f"MERKLE PROOF for index {leaf_index}")
    print(f"{'='*60}")
    print(f"Target: {target[:16]}...")
    
    proof = []
    level = [bytes.fromhex(h) for h in sorted_leaves]
    current_index = leaf_index
    
    step = 0
    while len(level) > 1:
        step += 1
        next_level = []
        
        for i in range(0, len(level), 2):
            left = level[i]
            
            if i + 1 < len(level):
                right = level[i + 1]
                is_duplicate = False
            else:
                right = level[i]
                is_duplicate = True
            
            # Record sibling for proof
            if i == current_index or i + 1 == current_index:
                if i == current_index:
                    # Current is LEFT child
                    sibling = "*" if is_duplicate else level[i + 1].hex()
                    direction = "LEFT"
                else:
                    # Current is RIGHT child
                    sibling = level[i].hex()
                    direction = "RIGHT"
                
                proof.append(sibling)
                sibling_display = "[DUPLICATE]" if sibling == "*" else sibling[:16] + "..."
                print(f"  Step {step}: Current is {direction}, sibling = {sibling_display}")
            
            parent = hashlib.sha256(left + right).digest()
            next_level.append(parent)
        
        current_index = current_index // 2
        level = next_level
    
    root = level[0].hex()
    
    print(f"\nProof array: {[p[:16]+'...' if p != '*' else p for p in proof]}")
    print(f"Root: {root[:16]}...")
    
    return {
        "version": "1.0",
        "leaf_hash": target,
        "leaf_index": leaf_index,
        "proof": proof,
        "root": root
    }


def verify_proof_visual(proof_data: dict) -> bool:
    """
    Verify Merkle proof using Positional Index Algorithm (Spec §4.3)
    """
    print(f"\n{'='*60}")
    print("PROOF VERIFICATION")
    print(f"{'='*60}")
    
    leaf_hash = proof_data["leaf_hash"]
    leaf_index = proof_data["leaf_index"]
    proof = proof_data["proof"]
    expected_root = proof_data["root"]
    
    current = bytes.fromhex(leaf_hash)
    index = leaf_index
    
    print(f"Starting: {current.hex()[:16]}... (index={index})")
    
    for step, sibling in enumerate(proof):
        if sibling == "*":
            sibling_hash = current
            sibling_display = "[DUPLICATE]"
        else:
            sibling_hash = bytes.fromhex(sibling)
            sibling_display = sibling[:16] + "..."
        
        if index % 2 == 0:
            # Current is LEFT
            direction = "LEFT"
            new_current = hashlib.sha256(current + sibling_hash).digest()
        else:
            # Current is RIGHT
            direction = "RIGHT"
            new_current = hashlib.sha256(sibling_hash + current).digest()
        
        print(f"  Step {step+1}: index={index} ({direction}) + {sibling_display}")
        print(f"         -> {new_current.hex()[:16]}...")
        
        current = new_current
        index = index // 2
    
    is_valid = current.hex() == expected_root
    
    print(f"\nFinal hash: {current.hex()[:16]}...")
    print(f"Expected:   {expected_root[:16]}...")
    print(f"Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    return is_valid


def main():
    print("""
+===============================================================+
|        GLOGOS MERKLE TREE DEMO - Spec v1.0.0-rc.0 §4         |
+===============================================================+
    """)
    
    # Create sample attestations
    print("Creating sample attestations...")
    attestations = []
    for i in range(5):
        claim = f"Claim #{i+1}: This is attestation number {i+1}"
        attestation_id = sha256_hex(claim.encode())
        attestations.append(attestation_id)
        print(f"  Attestation {i+1}: {attestation_id[:24]}...")
    
    # Build tree
    root, levels = build_merkle_tree_visual(attestations)
    
    # ASCII visualization
    print(f"\n{'='*60}")
    print("TREE STRUCTURE (ASCII)")
    print(f"{'='*60}")
    
    sorted_leaves = sorted(attestations)
    
    if len(sorted_leaves) == 5:
        print("""
                         [ROOT]
                        /      \\
                   [Node1]     [Node2]
                   /    \\       /    \\
              [Node3] [Node4] [Leaf4] [Leaf4*]
              /    \\    /   \\
         [Leaf0][Leaf1][Leaf2][Leaf3]
         
    * = Duplicate (odd number of leaves)
        """)
    
    # Generate and verify proof
    target_idx = 2
    target = sorted_leaves[target_idx]
    proof_data = generate_proof_visual(target, attestations)
    
    if proof_data:
        verify_proof_visual(proof_data)
    
    # Show empty tree case
    print(f"\n{'='*60}")
    print("EMPTY TREE (Rule 5)")
    print(f"{'='*60}")
    empty_root, _ = build_merkle_tree_visual([])
    print(f"Empty root = SHA256('') = {sha256_hex(b'')[:32]}...")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
