#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Glogos Mainnet Launch Ceremony
==============================

Target: December 21, 2025 at 15:03:00 UTC (Winter Solstice)

PURPOSE:
This ceremony marks the MAINNET LAUNCH of the Glogos Protocol.
The GLSR is already fixed as SHA256("") - this ceremony does NOT compute it.

Instead, this ceremony:
  1. Confirms the fixed GLSR = SHA256("")
  2. Collects Euler + Entropy as ceremonial witnesses
  3. Creates the WITNESS ZONE: glogos-witness
  4. Attests proposal.md as the official specification
  5. Anchors everything to Winter Solstice timestamp

IMPORTANT - Two Layers:

TECHNICAL LAYER (Protocol):
  - GLSR = SHA256("") is FIXED, immutable
  - Anyone can create a Zone at ANY time
  - No ceremony is REQUIRED
  - No permission is NEEDED
  - This script is ONE example, not THE example

SOCIAL LAYER (Community):
  - Winter Solstice = Shared moment for coordination
  - witness_zone = First example, not required
  - Citations = Optional social graph
  - "From emptiness, all light is welcome"

You may:
  - Run this ceremony at 15:03:00 UTC and cite witness_zone (join the moment)
  - Create your own Zone independently at any time (true decentralization)
  - Both are valid! Both are welcome!

Ceremonial Elements:
  - Empty Axiom: SHA256("") = GLSR (immutable foundation)
  - Euler Identity: e^(i\u03c0) + 1 = 0 (philosophical meaning)
  - Entropy Sources: drand, NIST, Bitcoin (witness the moment)
  - World Context: CO2, ISS, blockchain heights (historical record)

Author: Le Manh Thanh
License: CC-BY-4.0 (doc), MIT (code)
"""

import hashlib
import json
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import time
import sys, os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# =============================================================================
# CONSTANTS
# =============================================================================

SPEC_VERSION = "1.0.0"

# The FIXED, IMMUTABLE GLSR - SHA256 of empty string
# This is NOT computed during ceremony - it is a mathematical constant
GLSR = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Ceremony timing
CEREMONY_TIME = "2025-12-21T15:03:00Z"
CEREMONY_TIMESTAMP = int(datetime.fromisoformat(CEREMONY_TIME.replace("Z", "+00:00")).timestamp())
JULIAN_DAY = "2461031.1270833333"

# Multi-calendar time formats (display only, symbolic)
TIME_VIGESIMAL = "13.0.13.3.8"  # Maya Long Count
TIME_SEXAGESIMAL = "11;23,37,11;7,37,30"  # Babylonian base-60

# Witness Zone configuration will be prompted at runtime
# (See prompt_zone_info() function below)

# drand quicknet parameters
DRAND_GENESIS = 1692802167
DRAND_PERIOD = 3
DRAND_CHAIN_HASH = "52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971"
DRAND_ENDPOINTS = [
    f"https://api.drand.sh/{DRAND_CHAIN_HASH}",
    f"https://api2.drand.sh/{DRAND_CHAIN_HASH}",
    f"https://api3.drand.sh/{DRAND_CHAIN_HASH}",
    f"https://drand.cloudflare.com/{DRAND_CHAIN_HASH}",
]

NIST_BEACON_BASE_URL = "https://beacon.nist.gov/beacon/2.0"
BITCOIN_API = "https://blockstream.info/api/blocks/tip/hash"


# =============================================================================
# ZONE CONFIGURATION
# =============================================================================

def prompt_zone_info() -> Tuple[str, str, str, str]:
    """
    Prompt user for zone name and operator.
    Returns: (zone_name, operator, zone_id, canon_id)
    """
    print()
    print("Zone Configuration:")
    print("-" * 60)
    
    zone_name = input("Enter your zone name [glogos-witness]: ").strip()
    if not zone_name:
        zone_name = "glogos-witness"
    
    operator = input("Enter your name [A witness]: ").strip()
    if not operator:
        operator = "A witness"
    
    # Compute zone_id and canon_id
    zone_id = hashlib.sha256(f"{zone_name}:{GLSR}".encode()).hexdigest()
    canon_id = hashlib.sha256("timestamp:1.0".encode()).hexdigest()
    
    print(f"\n  Zone: {zone_name}")
    print(f"  Operator: {operator}")
    print()
    
    return zone_name, operator, zone_id, canon_id

# =============================================================================
# GLSR VERIFICATION (NOT COMPUTATION)
# =============================================================================

def verify_glsr() -> bool:
    """
    Verify that GLSR matches SHA256("").
    
    IMPORTANT: This does NOT compute GLSR - GLSR is fixed.
    This only CONFIRMS that the constant is correct.
    """
    computed = hashlib.sha256(b"").hexdigest()
    return computed == GLSR

# =============================================================================
# CEREMONIAL WITNESSES
# =============================================================================

def compute_euler_witness() -> Dict[str, Any]:
    """
    Euler identity as philosophical witness.
    
    e^(i\u03c0) + 1 = 0
    
    "The most beautiful equation becomes part of the ceremony."
    """
    euler_string = "e^(i\u03c0) + 1 = 0"  # \u03c0 is the Unicode for π
    euler_hash = hashlib.sha256(euler_string.encode("utf-8")).hexdigest()
    return {
        "expression": euler_string,
        "hash": euler_hash,
        "meaning": "The most beautiful equation witnesses the genesis."
    }

def calculate_drand_round(timestamp: int) -> int:
    """Calculate drand round for timestamp"""
    if timestamp < DRAND_GENESIS:
        return 0
    return ((timestamp - DRAND_GENESIS) // DRAND_PERIOD) + 1

def fetch_drand_beacon(round_number: Optional[int] = None) -> Dict[str, Any]:
    """Fetch drand quicknet beacon"""
    for endpoint in DRAND_ENDPOINTS:
        try:
            url = f"{endpoint}/public/{round_number}" if round_number else f"{endpoint}/public/latest"
            headers = {"User-Agent": "Glogos-Ceremony/2.0"}
            with httpx.Client(headers=headers, timeout=10) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                return { "source": "drand_quicknet", **data }
        except Exception as e:
            print(f"  Warning: {endpoint} failed: {e}")
            continue
    raise Exception("All drand endpoints failed")

def fetch_nist_beacon(target_timestamp: Optional[int] = None) -> Dict[str, Any]:
    """Fetch NIST Beacon"""
    try:
        url = (f"{NIST_BEACON_BASE_URL}/pulse/time/{target_timestamp}" 
               if target_timestamp else f"{NIST_BEACON_BASE_URL}/pulse/last")
        headers = {"User-Agent": "Glogos-Ceremony/2.0"}
        with httpx.Client(headers=headers, timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            pulse = data.get("pulse", {})
            return {
                "source": "nist_beacon",
                "output_value": pulse.get("outputValue"),
                "pulse_index": pulse.get("pulseIndex"),
            }
    except Exception as e:
        return {"source": "nist_beacon", "error": str(e)}

def fetch_bitcoin_block() -> Dict[str, Any]:
    """Fetch Bitcoin block hash"""
    try:
        headers = {"User-Agent": "Glogos-Ceremony/2.0"}
        response = httpx.get(BITCOIN_API, headers=headers, timeout=10)
        response.raise_for_status()
        return {"source": "bitcoin", "block_hash": response.text.strip()}
    except Exception as e:
        return {"source": "bitcoin", "error": str(e)}

def fetch_world_context() -> Dict[str, Any]:
    """Fetch world context as historical record"""
    print("\n[*] Fetching World Context...")
    context = {
        "note": "Historical record only - does NOT affect GLSR",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Bitcoin height
    try:
        headers = {"User-Agent": "Glogos-Ceremony/2.0"}
        response = httpx.get("https://blockstream.info/api/blocks/tip/height", headers=headers, timeout=10)
        context["bitcoin_height"] = int(response.text.strip())
        print(f"   [OK] Bitcoin height: {context['bitcoin_height']}")
    except:
        pass
    
    return context

# =============================================================================
# WITNESS ZONE CREATION
# =============================================================================

def create_witness_zone_attestation(zone_name: str, operator: str, zone_id: str, canon_id: str) -> Tuple[Dict[str, Any], str]:
    """
    Create an attestation by the Witness Zone.
    
    This attestation verifies proposal.md as the official specification.
    Returns the attestation data and the hex-encoded data to be signed.
    """
    # Find proposal.md
    script_dir = Path(__file__).parent
    proposal_paths = [
        script_dir.parent / "proposal.md",
        script_dir.parent.parent / "proposal.md",
    ]
    
    proposal_path = None
    for path in proposal_paths:
        if path.exists():
            proposal_path = path.resolve()
            break
    
    if not proposal_path:
        return {"error": "proposal.md not found"}, ""
    
    # Compute hashes
    with open(proposal_path, 'rb') as f:
        proposal_hash = hashlib.sha256(f.read()).hexdigest()
    
    claim = f"The operator ({operator}) attests that proposal.md is the official Glogos Proposal {SPEC_VERSION}"
    claim_hash = hashlib.sha256(claim.encode()).hexdigest()
    
    evidence = f"SHA256 of proposal.md: {proposal_hash}"
    evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()
    
    timestamp = CEREMONY_TIMESTAMP
    timestamp_bytes = timestamp.to_bytes(8, byteorder='big')
    
    # Compute attestation_id per spec Section 3.3
    preimage = (
        bytes.fromhex(zone_id) +
        bytes.fromhex(canon_id) +
        bytes.fromhex(claim_hash) +
        timestamp_bytes
    )
    attestation_id = hashlib.sha256(preimage).hexdigest()
    
    # Compute sign_preimage per spec Section 3.4
    # sign_data = attestation_id || claim_hash || evidence_hash || timestamp_bytes || citations_hash
    # Citations are empty for this genesis attestation.
    citations_hash = hashlib.sha256(b"").hexdigest()
    
    sign_preimage_bytes = (
        bytes.fromhex(attestation_id) +
        bytes.fromhex(claim_hash) +
        bytes.fromhex(evidence_hash) +
        timestamp_bytes +
        bytes.fromhex(citations_hash)
    )
    sign_preimage_hex = sign_preimage_bytes.hex()
    
    attestation_data = {
        "zone": {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "zone_type": "genesis",
        },
        "attestation": {
            "attestation_id": attestation_id,
            "zone_id": zone_id,
            "canon_id": canon_id,
            "canon_name": "timestamp:1.0",
            "claim": claim,
            "claim_hash": claim_hash,
            "signature_type": "gpg_detached",
            "signature_file": "artifact.json.asc",
            "signature_note": "Sign with: gpg --armor --detach-sign artifact.json",
            "evidence": evidence,
            "evidence_hash": evidence_hash,
            "proposal_hash": proposal_hash,
            "timestamp": timestamp,
            "timestamp_iso": CEREMONY_TIME,
        },
        "anchor": {
            "type": "astronomical",
            "event": "Winter Solstice 2025",
            "timestamp": CEREMONY_TIME,
            "julian_day": float(JULIAN_DAY),
            "glsr": GLSR,
        }
    }
    
    return attestation_data, sign_preimage_hex

# =============================================================================
# CEREMONY EXECUTION
# =============================================================================

def wait_for_ceremony_time():
    """Wait until ceremony time"""
    target = datetime(2025, 12, 21, 15, 3, 0, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    if now < target:
        print(f"\n[WAIT] Ceremony time: {target.isoformat()}")
        print(f"       Current time:  {now.isoformat()}")
        print(f"       (Press Ctrl+C to cancel)\n")
        
        # Wait until the final minute
        try:
            while (remaining := target - datetime.now(timezone.utc)).total_seconds() > 60:
                days, seconds = remaining.days, remaining.seconds
                hours, minutes = seconds // 3600, (seconds % 3600) // 60
                print(f"   Waiting... {days}d {hours:02d}h {minutes:02d}m remaining", flush=True)
                time.sleep(60)
            
            # Countdown the final minute
            while (remaining := target - datetime.now(timezone.utc)).total_seconds() > 0:
                print(f"   Countdown: {remaining.total_seconds():.0f} seconds remaining...", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)
        
        print("\n[!] CEREMONY TIME!")

def run_ceremony(mode: str = "test") -> Dict[str, Any]:
    """
    Execute the Mainnet Launch Ceremony.
    
    Modes:
        - "test": Current data, no waiting
        - "live": Wait for ceremony time, fetch live data
        - "simulation": Offline test with simulated data
    """
    print("\n" + "=" * 60)
    print("       GLOGOS MAINNET LAUNCH CEREMONY")
    print("=" * 60)
    print()
    print("  Target: December 21, 2025 at 15:03:00 UTC")
    print("  Event:  Winter Solstice (Astronomical Anchor)")
    print()
    print(f"  Mode: {mode.upper()}")
    print()
    
    # Prompt for zone configuration
    zone_name, operator, zone_id, canon_id = prompt_zone_info()
    
    if mode == "live":
        wait_for_ceremony_time()

    
    # Step 1: Verify GLSR
    print("\n[1] Verifying GLSR (Fixed Value)...")
    assert verify_glsr(), "GLSR verification failed!"
    print(f"   GLSR = SHA256('') = {GLSR[:32]}...")
    print("   [OK] GLSR is correct (mathematical constant)")
    
    
    # Step 2: Collect Euler witness
    print("\n[2] Euler Identity Witness...")
    euler = compute_euler_witness()
    print(f"   {euler['expression']}")
    print(f"   Hash: {euler['hash'][:32]}...")
    
    # Step 3: Collect Entropy witnesses
    print("\n[3] Entropy Witnesses...")
    
    if mode == "simulation":
        drand = {"source": "simulation", "round": 24509072, "randomness": "sim_" + "a" * 60}
        nist = {"source": "simulation", "output_value": "sim_" + "b" * 60}
        bitcoin = {"source": "simulation", "block_hash": "0" * 64}
        print("   [OK] Using simulation data")
    else:
        target_round = calculate_drand_round(CEREMONY_TIMESTAMP) if mode == "live" else None
        drand = fetch_drand_beacon(target_round)
        nist = fetch_nist_beacon(CEREMONY_TIMESTAMP if mode == "live" else None)
        bitcoin = fetch_bitcoin_block()
        
        print(f"   [OK] drand: Round {drand.get('round')}")
        print(f"   [OK] NIST: {'OK' if 'error' not in nist else 'unavailable'}")
        print(f"   [OK] Bitcoin: {bitcoin.get('block_hash', 'N/A')[:16]}...")
    
    # Step 4: Create Witness Zone
    print(f"\n[4] Creating Witness Zone: {zone_name}...")
    witness_zone, sign_preimage_hex = create_witness_zone_attestation(zone_name, operator, zone_id, canon_id)
    
    if not witness_zone:
        print(f"   ✗ Error creating witness zone data.")
    else:
        zone = witness_zone["zone"]
        attestation = witness_zone["attestation"]
        print(f"   Zone ID: {zone['zone_id'][:32]}...")
        print(f"   Attestation ID: {attestation['attestation_id'][:32]}...")
        print(f"   Document: proposal.md → {attestation['proposal_hash'][:16]}...")
        

    
    # Step 5: Fetch world context
    world_context = fetch_world_context() if mode != "simulation" else {"note": "simulation"}
    
    # Add world context to witness_zone as snapshot
    witness_zone["world_snapshot"] = world_context
    
    # Build ceremony record
    ceremony_record = {
        "version": SPEC_VERSION,
        "ceremony_type": "mainnet_launch",
        "time": {
            "iso": CEREMONY_TIME,
            "julian_day": float(JULIAN_DAY),
            "unix": CEREMONY_TIMESTAMP,
            "vigesimal": TIME_VIGESIMAL,
            "sexagesimal": TIME_SEXAGESIMAL,
        },
        "event": "Winter Solstice 2025",
        
        # The fixed GLSR - NOT computed, just confirmed
        "glsr": {
            "value": GLSR,
            "computation": "SHA256('')",
            "status": "fixed_immutable",
        },
        
        # Ceremonial witnesses
        "witnesses": {
            "euler": euler,
            "entropy": {
                "drand": drand,
                "nist": nist,
                "bitcoin": bitcoin,
            },
        },
        
        # Witness Zone (includes world snapshot)
        "witness_zone": witness_zone,
    }
    
    # Save
    output_file = "artifact.json"
    with open(output_file, "w") as f:
        json.dump(ceremony_record, f, indent=2, ensure_ascii=True)
    
    # Summary
    print("\n" + "=" * 60)
    print("           MAINNET LAUNCH CEREMONY COMPLETE")
    print("=" * 60)
    print(f"""
  GLSR (Fixed): {GLSR}
  
  Witness Zone: glogos-witness
  Genesis Attestation: proposal.md
  
  Witnesses:
    - Euler: e^(i\u03c0) + 1 = 0
    - drand: Round {drand.get('round', 'N/A')}
    - NIST: {'OK' if 'error' not in nist else 'N/A'}
    - Bitcoin: {'OK' if 'error' not in bitcoin else 'N/A'}
  
  Artifact saved to: {output_file}

  "From emptiness, all light is welcome."
""")
    
    return ceremony_record

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           GLOGOS MAINNET LAUNCH CEREMONY                      ║
║                                                               ║
║      GLSR = SHA256("") = e3b0c44298fc1c14...                  ║
║                                                               ║
║      Target: December 21, 2025 — 15:03:00 UTC                 ║
║      Event:  Winter Solstice                                  ║
║                                                               ║
║          "From emptiness, all light is welcome."              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("Options:")
    print("  [1] Run SIMULATION (offline test)")
    print("  [2] Run LIVE ceremony (wait for Dec 21)")
    print("  [3] Verify GLSR only")
    print()
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        run_ceremony(mode="simulation")
    elif choice == "2":
        run_ceremony(mode="live")
    elif choice == "3":
        print(f"\n  GLSR = SHA256('') = {GLSR}")
        print(f"  Verified: {verify_glsr()}")
    else:
        print("Invalid option")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
