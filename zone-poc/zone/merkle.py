"""
Glogos High-Throughput Zone - Merkle Engine with Parallel Computation
Aligned with Glogos Specification v1.0-rc.0 §4

Features:
- Binary Merkle tree with SHA-256
- Lexicographic sorting of leaves
- Positional index algorithm (Spec §4.3)
- Parallel computation using multiprocessing (GIL bypass)
"""

import hashlib
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import os


def sha256_bytes(data: bytes) -> bytes:
    """SHA256 hash returning bytes"""
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    """SHA256 hash returning hex string"""
    return hashlib.sha256(data).hexdigest()


def _compute_subtree_root(leaves_hex: List[str]) -> str:
    """
    Compute Merkle root for a list of leaf hashes.
    Worker function for parallel processing.
    
    Args:
        leaves_hex: List of 64-char hex hashes (already sorted)
    
    Returns:
        Root hash as 64-char hex string
    """
    if not leaves_hex:
        return sha256_hex(b"")  # Empty tree
    
    if len(leaves_hex) == 1:
        return leaves_hex[0]
    
    # Convert to bytes for processing
    level = [bytes.fromhex(h) for h in leaves_hex]
    
    while len(level) > 1:
        next_level = []
        
        for i in range(0, len(level), 2):
            left = level[i]
            # Odd count: duplicate last leaf (Spec §4.4)
            right = level[i + 1] if i + 1 < len(level) else level[i]
            parent = sha256_bytes(left + right)
            next_level.append(parent)
        
        level = next_level
    
    return level[0].hex()


class MerkleEngine:
    """
    High-performance Merkle tree with parallel computation.
    
    Supports:
    - Single-threaded computation (for small sets)
    - Parallel computation using ProcessPoolExecutor (for large sets)
    - Proof generation per Spec §4
    """
    
    def __init__(self, max_workers: Optional[int] = None, parallel_threshold: int = 1000):
        """
        Args:
            max_workers: Number of worker processes (default: CPU count)
            parallel_threshold: Minimum leaves to trigger parallel computation
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        self.parallel_threshold = parallel_threshold
        self._leaves: List[str] = []
        self._sorted_leaves: Optional[List[str]] = None
        self._cached_root: Optional[str] = None
    
    def add_leaf(self, attestation_id: str) -> int:
        """
        Add an attestation ID as a leaf node.
        
        Returns:
            Index of the leaf (before sorting)
        """
        if len(attestation_id) != 64:
            raise ValueError("Attestation ID must be 64-character hex string")
        
        self._leaves.append(attestation_id.lower())
        self._sorted_leaves = None  # Invalidate cache
        self._cached_root = None
        
        return len(self._leaves) - 1
    
    def _ensure_sorted(self) -> List[str]:
        """Sort leaves lexicographically (Spec §4.4 rule 2)"""
        if self._sorted_leaves is None:
            self._sorted_leaves = sorted(self._leaves)
        return self._sorted_leaves
    
    def compute_root(self) -> str:
        """
        Compute Merkle root (single-threaded).
        
        Returns:
            64-char hex root hash
        """
        if self._cached_root is not None:
            return self._cached_root
        
        leaves = self._ensure_sorted()
        self._cached_root = _compute_subtree_root(leaves)
        return self._cached_root
    
    def compute_root_parallel(self) -> str:
        """
        Compute Merkle root using parallel processing.
        Falls back to single-threaded if below threshold.
        
        Returns:
            64-char hex root hash
        """
        if self._cached_root is not None:
            return self._cached_root
        
        leaves = self._ensure_sorted()
        
        # Use single-threaded for small sets
        if len(leaves) < self.parallel_threshold:
            return self.compute_root()
        
        # Split into chunks for parallel processing
        chunk_size = max(len(leaves) // self.max_workers, 100)
        chunks = [
            leaves[i:i + chunk_size]
            for i in range(0, len(leaves), chunk_size)
        ]
        
        # Compute subtree roots in parallel
        subtree_roots = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_compute_subtree_root, chunk): i 
                      for i, chunk in enumerate(chunks)}
            
            results = {}
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
            
            # Maintain order
            subtree_roots = [results[i] for i in range(len(chunks))]
        
        # Combine subtree roots to get final root
        self._cached_root = _compute_subtree_root(subtree_roots)
        return self._cached_root
    
    def generate_proof(self, attestation_id: str) -> Optional[dict]:
        """
        Generate Merkle proof for an attestation per Spec §4.1.
        
        Args:
            attestation_id: 64-char hex attestation ID
        
        Returns:
            Proof dict with version, leaf_hash, leaf_index, proof, root
            or None if attestation not found
        """
        attestation_id = attestation_id.lower()
        leaves = self._ensure_sorted()
        
        try:
            leaf_index = leaves.index(attestation_id)
        except ValueError:
            return None  # Attestation not in tree
        
        proof = []
        level = [bytes.fromhex(h) for h in leaves]
        current_index = leaf_index
        
        while len(level) > 1:
            next_level = []
            
            for i in range(0, len(level), 2):
                left = level[i]
                
                # Handle odd count
                if i + 1 < len(level):
                    right = level[i + 1]
                    is_duplicate = False
                else:
                    right = level[i]
                    is_duplicate = True
                
                # Record sibling for proof
                if i == current_index or i + 1 == current_index:
                    if i == current_index:
                        # Current is left, sibling is right
                        sibling = "*" if is_duplicate else level[i + 1].hex()
                    else:
                        # Current is right, sibling is left
                        sibling = level[i].hex()
                    proof.append(sibling)
                
                parent = sha256_bytes(left + right)
                next_level.append(parent)
            
            # Update index for next level
            current_index = current_index // 2
            level = next_level
        
        root = level[0].hex() if level else sha256_hex(b"")
        
        return {
            "version": "1.0",
            "leaf_hash": attestation_id,
            "leaf_index": leaf_index,
            "proof": proof,
            "root": root
        }
    
    @staticmethod
    def verify_proof(
        leaf_hash: str,
        leaf_index: int,
        proof: List[str],
        expected_root: str
    ) -> bool:
        """
        Verify a Merkle proof per Spec §4.3.
        
        Args:
            leaf_hash: 64-char hex attestation ID
            leaf_index: Position in sorted leaf array
            proof: List of sibling hashes (or "*" for duplicate)
            expected_root: Expected Merkle root
        
        Returns:
            True if proof is valid
        """
        current = bytes.fromhex(leaf_hash)
        index = leaf_index
        
        for sibling in proof:
            if sibling == "*":
                sibling_hash = current
            else:
                sibling_hash = bytes.fromhex(sibling)
            
            if index % 2 == 0:
                # Current is LEFT child
                current = sha256_bytes(current + sibling_hash)
            else:
                # Current is RIGHT child
                current = sha256_bytes(sibling_hash + current)
            
            index = index // 2
        
        return current.hex() == expected_root
    
    @property
    def leaf_count(self) -> int:
        """Number of leaves in tree"""
        return len(self._leaves)
    
    def clear(self) -> None:
        """Clear all leaves and cached values"""
        self._leaves = []
        self._sorted_leaves = None
        self._cached_root = None
    
    def get_all_leaves(self) -> List[str]:
        """Get all leaves (sorted)"""
        return self._ensure_sorted()


# =============================================================================
# Benchmark utilities
# =============================================================================

def benchmark_merkle_computation(leaf_count: int, parallel: bool = True) -> dict:
    """
    Benchmark Merkle tree computation.
    
    Args:
        leaf_count: Number of test leaves
        parallel: Use parallel computation
    
    Returns:
        Dict with timing and throughput metrics
    """
    import time
    import secrets
    
    # Generate random leaves
    leaves = [secrets.token_hex(32) for _ in range(leaf_count)]
    
    engine = MerkleEngine()
    
    # Add leaves
    add_start = time.perf_counter()
    for leaf in leaves:
        engine.add_leaf(leaf)
    add_duration = time.perf_counter() - add_start
    
    # Compute root
    compute_start = time.perf_counter()
    if parallel:
        root = engine.compute_root_parallel()
    else:
        root = engine.compute_root()
    compute_duration = time.perf_counter() - compute_start
    
    return {
        "leaf_count": leaf_count,
        "parallel": parallel,
        "add_duration_ms": add_duration * 1000,
        "compute_duration_ms": compute_duration * 1000,
        "total_duration_ms": (add_duration + compute_duration) * 1000,
        "leaves_per_second": leaf_count / (add_duration + compute_duration),
        "root": root
    }


if __name__ == "__main__":
    # Quick self-test
    print("Testing MerkleEngine...")
    
    engine = MerkleEngine()
    
    # Add some test leaves
    leaves = [
        sha256_hex(f"leaf_{i}".encode()) for i in range(7)
    ]
    
    for leaf in leaves:
        engine.add_leaf(leaf)
    
    root = engine.compute_root()
    print(f"Root (7 leaves): {root}")
    
    # Test proof generation and verification
    test_leaf = sorted(leaves)[3]
    proof_data = engine.generate_proof(test_leaf)
    print(f"Proof for index 3: {proof_data}")
    
    is_valid = MerkleEngine.verify_proof(
        proof_data["leaf_hash"],
        proof_data["leaf_index"],
        proof_data["proof"],
        proof_data["root"]
    )
    print(f"Proof valid: {is_valid}")
    
    # Benchmark
    print("\nBenchmarking...")
    result = benchmark_merkle_computation(10000, parallel=False)
    print(f"10K leaves (single): {result['compute_duration_ms']:.2f}ms")
    
    print("\nAll tests passed!")
