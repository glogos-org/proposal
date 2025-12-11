/// Glogos Merkle Tree Benchmark - STRESS TEST VERSION
/// Testing limits: 1M, 10M, 50M, 100M attestations
/// 
/// Aligned with Glogos proposal v1.0.0-rc.0 §4

use sha2::{Sha256, Digest};
use rand::Rng;
use rayon::prelude::*;
use std::time::Instant;

#[inline(always)]
fn sha256_bytes(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

fn to_hex(bytes: &[u8]) -> String {
    hex::encode(bytes)
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

fn compute_merkle_root_parallel(leaves: &[[u8; 32]]) -> [u8; 32] {
    if leaves.is_empty() {
        return sha256_bytes(b"");
    }
    if leaves.len() == 1 {
        return leaves[0];
    }
    
    let mut level = leaves.to_vec();
    
    while level.len() > 1 {
        let next_level: Vec<[u8; 32]> = level.par_chunks(2)
            .map(|chunk| {
                let left = &chunk[0];
                // If chunk has 2 elements, use right. If 1, duplicate left.
                let right = if chunk.len() > 1 { &chunk[1] } else { &chunk[0] };
                
                let mut combined = [0u8; 64];
                combined[..32].copy_from_slice(left);
                combined[32..].copy_from_slice(right);
                sha256_bytes(&combined)
            })
            .collect();
        
        level = next_level;
    }
    
    level[0]
}

fn run_stress_test(leaf_count: usize) -> (f64, f64, usize) {
    let start = Instant::now();
    
    // Phase 1: Parallel leaf generation
    let gen_start = Instant::now();
    let leaves: Vec<[u8; 32]> = (0..leaf_count)
        .into_par_iter()
        .map(|_| {
            let mut rng = rand::thread_rng();
            let bytes: [u8; 32] = rng.gen();
            sha256_bytes(&bytes)
        })
        .collect();
    let gen_time = gen_start.elapsed().as_secs_f64() * 1000.0;
    
    // Phase 2: Parallel sort
    let sort_start = Instant::now();
    let mut leaves = leaves;
    leaves.par_sort_unstable();
    let sort_time = sort_start.elapsed().as_secs_f64() * 1000.0;
    
    // Phase 3: Merkle root
    let merkle_start = Instant::now();
    let root = compute_merkle_root_parallel(&leaves);
    let merkle_time = merkle_start.elapsed().as_secs_f64() * 1000.0;
    
    let total = start.elapsed().as_secs_f64() * 1000.0;
    let throughput = leaf_count as f64 / (total / 1000.0);
    
    // Memory estimate (32 bytes per leaf)
    let mem_mb = (leaf_count * 32) / (1024 * 1024);
    
    println!("  Generate:  {:>10.1} ms", gen_time);
    println!("  Sort:      {:>10.1} ms", sort_time);
    println!("  Merkle:    {:>10.1} ms", merkle_time);
    println!("  Root:      {}...", to_hex(&root[..8]));
    
    (total, throughput, mem_mb)
}

fn main() {
    // Parse command line args
    let args: Vec<String> = std::env::args().collect();
    
    let custom_tests: Option<Vec<usize>> = if args.len() > 1 {
        Some(args[1..].iter()
            .filter_map(|s| s.replace("_", "").replace(",", "").parse().ok())
            .collect())
    } else {
        None
    };
    
    println!("================================================================================");
    println!("GLOGOS STRESS TEST - PUSHING THE LIMITS");
    println!("================================================================================");
    println!("CPU threads: {}", rayon::current_num_threads());
    if custom_tests.is_some() {
        println!("Custom test sizes: {:?}", custom_tests.as_ref().unwrap());
    }
    println!();
    
    // Verify GLSR
    let glsr = to_hex(&sha256_bytes(b""));
    assert_eq!(glsr, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    println!("[OK] GLSR verified");
    println!();
    
    // Warmup
    println!("Warming up...");
    let _ = run_stress_test(100_000);
    println!();
    
    let default_tests = vec![
        1_000_000,
        10_000_000,
        50_000_000,
        100_000_000,
    ];
    
    let tests = custom_tests.unwrap_or(default_tests);
    
    println!("================================================================================");
    println!("STRESS TEST RESULTS");
    println!("================================================================================");
    
    let mut results = Vec::new();
    
    for &count in &tests {
        println!();
        println!("Testing {} attestations...", format_with_commas(count));
        println!("----------------------------------------");
        let (total_ms, throughput, mem_mb) = run_stress_test(count);
        println!("----------------------------------------");
        println!("  TOTAL:     {:>10.1} ms ({:.2} sec)", total_ms, total_ms / 1000.0);
        println!("  THROUGHPUT:{:>10.0} attestations/sec", throughput);
        println!("  MEMORY:    {:>10} MB (leaves only)", mem_mb);
        results.push((count, total_ms, throughput));
    }
    
    println!();
    println!("================================================================================");
    println!("SUMMARY TABLE");
    println!("================================================================================");
    println!("| Attestations | Time (sec) | Throughput         | vs Solana (65K TPS) |");
    println!("|--------------|------------|--------------------|---------------------|");
    
    for (count, time_ms, throughput) in &results {
        let ratio = throughput / 65000.0;
        println!(
            "| {:>12} | {:>10.2} | {:>18.0} | {:>17.1}x |",
            format_with_commas(*count),
            time_ms / 1000.0,
            throughput,
            ratio
        );
    }
    
    println!();
    println!("================================================================================");
    println!("PEAK PERFORMANCE");
    println!("================================================================================");
    let best = results.iter().max_by(|a, b| a.2.partial_cmp(&b.2).unwrap()).unwrap();
    println!("  Best throughput: {:.0} attestations/sec @ {} attestations", best.2, format_with_commas(best.0));
    println!("  vs Solana: {:.1}x faster (no consensus)", best.2 / 65000.0);
    println!("  vs Python: {:.0}x faster", best.2 / 11456.0);
    println!("================================================================================");
}
