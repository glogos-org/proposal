/// Cross-Zone Demo with RocksDB Storage Benchmark - Rust Edition
/// 
/// Aligned with Glogos Specification v1.0.0-rc.0
///
/// This demo:
/// 1. Creates 4 Zones with RocksDB storage
/// 2. Creates 1,000,000 attestations
/// 3. Builds Merkle trees with anchoring cycles (Spec §7.4)
/// 4. Verifies proofs
/// 5. Outputs benchmark results

use sha2::{Sha256, Digest};
use rayon::prelude::*;
use rocksdb::{DB, Options};
use serde::{Serialize, Deserialize};
use std::time::Instant;
use std::collections::HashMap;
use std::path::Path;
use std::fs;

// =============================================================================
// CONFIG
// =============================================================================

const STRESS_COUNT: usize = 1_000_000;
const ANCHOR_INTERVAL: usize = 1000;
const SAMPLE_VERIFY: usize = 1000;

// =============================================================================
// TYPES
// =============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Attestation {
    attestation_id: String,
    zone_id: String,
    canon_id: String,
    claim_hash: String,
    evidence_hash: String,
    timestamp: u64,
    signature: String,
    citations: Vec<String>,
}

struct Zone {
    name: String,
    db: DB,
    merkle: MerkleEngine,
}

// =============================================================================
// MERKLE ENGINE
// =============================================================================

struct MerkleEngine {
    leaves: Vec<[u8; 32]>,
    sorted_leaves: Option<Vec<[u8; 32]>>,
    leaf_index_map: Option<HashMap<[u8; 32], usize>>,
    tree_levels: Option<Vec<Vec<[u8; 32]>>>,
}

impl MerkleEngine {
    fn new() -> Self {
        Self {
            leaves: Vec::new(),
            sorted_leaves: None,
            leaf_index_map: None,
            tree_levels: None,
        }
    }
    
    fn add_leaf(&mut self, attestation_id: &str) {
        let bytes = hex::decode(attestation_id).unwrap();
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&bytes);
        self.leaves.push(arr);
        self.sorted_leaves = None;
        self.leaf_index_map = None;
        self.tree_levels = None;
    }
    
    fn ensure_sorted(&mut self) -> &Vec<[u8; 32]> {
        if self.sorted_leaves.is_none() {
            let mut sorted = self.leaves.clone();
            sorted.par_sort_unstable();
            
            let index_map: HashMap<[u8; 32], usize> = sorted.iter()
                .enumerate()
                .map(|(i, leaf)| (*leaf, i))
                .collect();
            
            self.leaf_index_map = Some(index_map);
            self.sorted_leaves = Some(sorted);
        }
        self.sorted_leaves.as_ref().unwrap()
    }
    
    fn build_tree_levels(&mut self) {
        if self.tree_levels.is_some() {
            return;
        }
        
        let sorted = self.ensure_sorted().clone();
        if sorted.is_empty() {
            self.tree_levels = Some(vec![]);
            return;
        }
        
        let mut levels: Vec<Vec<[u8; 32]>> = Vec::new();
        levels.push(sorted);
        
        while levels.last().unwrap().len() > 1 {
            let current = levels.last().unwrap();
            
            let next_level: Vec<[u8; 32]> = current.par_chunks(2)
                .map(|chunk| {
                    let left = &chunk[0];
                    let right = if chunk.len() > 1 { &chunk[1] } else { &chunk[0] };
                    
                    let mut combined = [0u8; 64];
                    combined[..32].copy_from_slice(left);
                    combined[32..].copy_from_slice(right);
                    sha256_bytes(&combined)
                })
                .collect();
            
            levels.push(next_level);
        }
        
        self.tree_levels = Some(levels);
    }
    
    fn compute_root(&mut self) -> String {
        self.build_tree_levels();
        
        if let Some(levels) = &self.tree_levels {
            if !levels.is_empty() && !levels.last().unwrap().is_empty() {
                return hex::encode(levels.last().unwrap()[0]);
            }
        }
        
        hex::encode(sha256_bytes(b""))
    }
    
    fn generate_proof(&mut self, attestation_id: &str) -> Option<(usize, Vec<String>)> {
        self.build_tree_levels();
        
        let bytes = hex::decode(attestation_id).ok()?;
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&bytes);
        
        let leaf_index = *self.leaf_index_map.as_ref()?.get(&arr)?;
        let levels = self.tree_levels.as_ref()?;
        
        let mut proof = Vec::new();
        let mut current_index = leaf_index;
        
        for level in levels.iter().take(levels.len().saturating_sub(1)) {
            let sibling_index = if current_index % 2 == 0 {
                if current_index + 1 < level.len() {
                    current_index + 1
                } else {
                    current_index
                }
            } else {
                current_index - 1
            };
            
            proof.push(hex::encode(level[sibling_index]));
            current_index /= 2;
        }
        
        Some((leaf_index, proof))
    }
    
    fn verify_proof(leaf_hash: &str, leaf_index: usize, proof: &[String], expected_root: &str) -> bool {
        let current_bytes = hex::decode(leaf_hash).unwrap();
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&current_bytes);
        let mut current = arr;
        
        let mut index = leaf_index;
        
        for sibling_hex in proof {
            let sibling = if sibling_hex == "*" {
                current
            } else {
                let sibling_bytes = hex::decode(sibling_hex).unwrap();
                let mut s = [0u8; 32];
                s.copy_from_slice(&sibling_bytes);
                s
            };
            
            let mut combined = [0u8; 64];
            if index % 2 == 0 {
                combined[..32].copy_from_slice(&current);
                combined[32..].copy_from_slice(&sibling);
            } else {
                combined[..32].copy_from_slice(&sibling);
                combined[32..].copy_from_slice(&current);
            }
            
            current = sha256_bytes(&combined);
            index /= 2;
        }
        
        hex::encode(current) == expected_root
    }
}

// =============================================================================
// HELPERS
// =============================================================================

#[inline(always)]
fn sha256_bytes(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

fn sha256_hex(data: &[u8]) -> String {
    hex::encode(sha256_bytes(data))
}

fn format_with_commas(n: usize) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result.chars().rev().collect()
}

fn create_attestation(zone_name: &str, index: usize, timestamp: u64) -> Attestation {
    let data = format!("{}:{}:{}", zone_name, index, timestamp);
    let attestation_id = sha256_hex(data.as_bytes());
    
    Attestation {
        attestation_id,
        zone_id: sha256_hex(zone_name.as_bytes()),
        canon_id: sha256_hex(b"document:1.0"),
        claim_hash: sha256_hex(format!("claim_{}", index).as_bytes()),
        evidence_hash: sha256_hex(format!("evidence_{}", index).as_bytes()),
        timestamp,
        signature: "mock_signature".to_string(),
        citations: vec![],
    }
}

// =============================================================================
// MAIN BENCHMARK
// =============================================================================

fn run_benchmark() {
    println!("{}", "=".repeat(80));
    println!("CROSS-ZONE DEMO WITH ROCKSDB - RUST EDITION");
    println!("{}", "=".repeat(80));
    println!("Attestations: {}", format_with_commas(STRESS_COUNT));
    println!("Anchoring interval: {}", ANCHOR_INTERVAL);
    println!("Verification sample: {}", SAMPLE_VERIFY);
    println!("CPU threads: {}", rayon::current_num_threads());
    println!("{}", "=".repeat(80));
    
    // Verify GLSR
    let glsr = sha256_hex(b"");
    assert_eq!(glsr, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    println!("[OK] GLSR verified: {}...", &glsr[..16]);
    
    // Clean up old data
    let data_dir = Path::new("./data_rocksdb");
    if data_dir.exists() {
        fs::remove_dir_all(data_dir).ok();
    }
    fs::create_dir_all(data_dir).ok();
    
    // =========================================================================
    // PHASE 1: Create Zones with RocksDB
    // =========================================================================
    
    println!("\n[PHASE 1] Creating Zones with RocksDB storage...");
    
    let zone_configs = [
        ("Open Source Zone", 100usize),
        ("Research Zone", STRESS_COUNT - 200),
        ("Government Data Zone", 50),
        ("Healthcare Zone", 50),
    ];
    
    let mut zones: Vec<Zone> = Vec::new();
    
    for (name, _) in &zone_configs {
        let db_path = format!("./data_rocksdb/zone_{}.db", name.to_lowercase().replace(" ", "_"));
        let mut opts = Options::default();
        opts.create_if_missing(true);
        opts.set_max_open_files(100);
        opts.set_write_buffer_size(64 * 1024 * 1024); // 64MB write buffer
        opts.set_max_write_buffer_number(3);
        
        let db = DB::open(&opts, &db_path).expect("Failed to open RocksDB");
        
        zones.push(Zone {
            name: name.to_string(),
            db,
            merkle: MerkleEngine::new(),
        });
        
        println!("   [OK] {}: {}", name, db_path);
    }
    
    // =========================================================================
    // PHASE 2: Create Attestations
    // =========================================================================
    
    println!("\n[PHASE 2] Creating {} attestations...", format_with_commas(STRESS_COUNT));
    
    let write_start = Instant::now();
    let mut total_created = 0usize;
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    for (idx, (_, count)) in zone_configs.iter().enumerate() {
        let zone = &mut zones[idx];
        let zone_start = Instant::now();
        
        // Generate attestations in parallel
        let attestations: Vec<Attestation> = (0..*count)
            .into_par_iter()
            .map(|i| create_attestation(&zone.name, i, timestamp))
            .collect();
        
        // Write to RocksDB and add to Merkle tree
        for att in &attestations {
            let json = serde_json::to_vec(att).unwrap();
            zone.db.put(att.attestation_id.as_bytes(), json).unwrap();
            zone.merkle.add_leaf(&att.attestation_id);
        }
        
        total_created += count;
        
        let zone_time = zone_start.elapsed().as_secs_f64() * 1000.0;
        let writes_per_sec = *count as f64 / (zone_time / 1000.0);
        
        println!("   [OK] {}: {} attestations in {:.0}ms ({:.0}/sec)", 
                 zone.name, format_with_commas(*count), zone_time, writes_per_sec);
    }
    
    let write_time = write_start.elapsed().as_secs_f64() * 1000.0;
    let write_per_sec = total_created as f64 / (write_time / 1000.0);
    
    println!("\n   TOTAL: {} attestations in {:.0}ms", format_with_commas(total_created), write_time);
    println!("   Throughput: {:.0} writes/sec", write_per_sec);
    
    // =========================================================================
    // PHASE 3: Build Merkle Trees
    // =========================================================================
    
    println!("\n[PHASE 3] Building Merkle trees (anchor every {})...", ANCHOR_INTERVAL);
    
    let merkle_start = Instant::now();
    let mut total_cycles = 0usize;
    
    for (idx, (_, count)) in zone_configs.iter().enumerate() {
        let zone = &mut zones[idx];
        let cycles = (*count + ANCHOR_INTERVAL - 1) / ANCHOR_INTERVAL;
        total_cycles += cycles;
        
        let root = zone.merkle.compute_root();
        
        println!("   [OK] {}: {} cycles, root={}...", zone.name, cycles, &root[..16]);
    }
    
    let merkle_time = merkle_start.elapsed().as_secs_f64() * 1000.0;
    
    println!("\n   Total anchoring cycles: {} (per Spec §7.4)", total_cycles);
    println!("   Merkle build time: {:.2}ms", merkle_time);
    
    // =========================================================================
    // PHASE 4: Verify Proofs
    // =========================================================================
    
    println!("\n[PHASE 4] Verifying {} proofs from Research Zone...", SAMPLE_VERIFY);
    
    let research_zone = &mut zones[1]; // Research Zone
    let research_root = research_zone.merkle.compute_root();
    
    // Get sample IDs
    let sample_ids: Vec<String> = research_zone.db.iterator(rocksdb::IteratorMode::Start)
        .take(SAMPLE_VERIFY)
        .filter_map(|r| r.ok())
        .map(|(k, _)| String::from_utf8(k.to_vec()).unwrap())
        .collect();
    
    let verify_start = Instant::now();
    let mut verified = 0usize;
    
    for att_id in &sample_ids {
        if let Some((leaf_index, proof)) = research_zone.merkle.generate_proof(att_id) {
            if MerkleEngine::verify_proof(att_id, leaf_index, &proof, &research_root) {
                verified += 1;
            }
        }
    }
    
    let verify_time = verify_start.elapsed().as_secs_f64() * 1000.0;
    let verify_per_sec = sample_ids.len() as f64 / (verify_time / 1000.0);
    
    println!("   Verified: {}/{}", verified, sample_ids.len());
    println!("   Time: {:.2}ms", verify_time);
    println!("   Throughput: {:.0} proofs/sec", verify_per_sec);
    
    // =========================================================================
    // PHASE 5: Read Benchmark
    // =========================================================================
    
    println!("\n[PHASE 5] Read benchmark (1000 random reads)...");
    
    let read_count = 1000;
    let read_ids: Vec<String> = zones[1].db.iterator(rocksdb::IteratorMode::Start)
        .take(read_count)
        .filter_map(|r| r.ok())
        .map(|(k, _)| String::from_utf8(k.to_vec()).unwrap())
        .collect();
    
    let read_start = Instant::now();
    
    for att_id in &read_ids {
        let _ = zones[1].db.get(att_id.as_bytes());
    }
    
    let read_time = read_start.elapsed().as_secs_f64() * 1000.0;
    let reads_per_sec = read_count as f64 / (read_time / 1000.0);
    
    println!("   Read {} attestations in {:.2}ms", read_count, read_time);
    println!("   Throughput: {:.0} reads/sec", reads_per_sec);
    
    // =========================================================================
    // SUMMARY
    // =========================================================================
    
    println!("\n{}", "=".repeat(80));
    println!("BENCHMARK RESULTS");
    println!("{}", "=".repeat(80));
    println!("   Writes:  {:.0}/sec", write_per_sec);
    println!("   Reads:   {:.0}/sec", reads_per_sec);
    println!("   Verify:  {:.0}/sec", verify_per_sec);
    println!("{}", "=".repeat(80));
    
    // Compare with Python
    println!("\nCOMPARISON WITH PYTHON:");
    println!("  Operation  | Python       | Rust         | Speedup");
    println!("  -----------|--------------|--------------|--------");
    println!("  Writes/sec | ~11,456      | {:>12.0} | ~{:.0}x", write_per_sec, write_per_sec / 11456.0);
    println!("  Reads/sec  | ~7,035       | {:>12.0} | ~{:.0}x", reads_per_sec, reads_per_sec / 7035.0);
    println!("  Verify/sec | ~1,478       | {:>12.0} | ~{:.0}x", verify_per_sec, verify_per_sec / 1478.0);
    println!("{}", "=".repeat(80));
}

fn main() {
    run_benchmark();
}
