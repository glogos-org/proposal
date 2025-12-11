#!/usr/bin/env python3
"""
Commons Governance POC - Fishery Quota Tracking
================================================

Demonstrates Elinor Ostrom's 8 Principles (Nobel 2009)
for sustainable commons management using Glogos.

PROBLEM: Tragedy of the Commons
- Fishers overfish because no individual ownership
- Free riders exploit shared resources
- No verifiable tracking of catches

SOLUTION: Attestation-based quota system
1. Clear boundaries → Zone membership attestation
2. Local rules → Zone-specific Canons (catch limits)
3. Collective choice → Governance votes as attestations
4. Monitoring → Public Merkle tree of all catches
5. Graduated sanctions → Reputation staking
6. Conflict resolution → Multi-zone arbitration
7. Recognition of rights → Attestation as proof
8. Nested enterprises → Zone federation

GLSR: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
"""

import sys
import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime

# Setup path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ZONE_POC_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, ZONE_POC_DIR)
os.chdir(ZONE_POC_DIR)

from zone.merkle import MerkleEngine

# =============================================================================
# CONSTANTS
# =============================================================================

GLSR = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Canon IDs for fishery management
CANON_FISHER_MEMBERSHIP = hashlib.sha256(b"fishery:membership:1.0").hexdigest()
CANON_CATCH_REPORT = hashlib.sha256(b"fishery:catch-report:1.0").hexdigest()
CANON_QUOTA_ALLOCATION = hashlib.sha256(b"fishery:quota:1.0").hexdigest()
CANON_GOVERNANCE_VOTE = hashlib.sha256(b"fishery:governance:1.0").hexdigest()
CANON_SANCTION = hashlib.sha256(b"fishery:sanction:1.0").hexdigest()

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Fisher:
    """A fisher in the commons"""
    fisher_id: str
    name: str
    boat_registration: str
    membership_attestation: str = ""
    reputation_stake: float = 100.0  # Starts at 100%
    total_catch_kg: float = 0.0
    quota_remaining_kg: float = 0.0

@dataclass
class CatchReport:
    """A verified catch report"""
    report_id: str
    fisher_id: str
    catch_kg: float
    species: str
    location: str
    timestamp: int
    witnesses: List[str] = field(default_factory=list)  # Peer attestation

@dataclass
class QuotaAllocation:
    """Annual quota allocation"""
    allocation_id: str
    fisher_id: str
    quota_kg: float
    period: str  # e.g., "2025-Q1"
    governance_vote_id: str  # Reference to vote that approved

@dataclass
class GovernanceVote:
    """Collective governance decision"""
    vote_id: str
    proposal: str
    yes_votes: int
    no_votes: int
    voters: List[str]
    passed: bool
    
# =============================================================================
# FISHERY ZONE
# =============================================================================

class FisheryZone:
    """
    A Zone implementing Ostrom's 8 Principles for commons governance.
    """
    
    def __init__(self, zone_name: str, total_sustainable_catch_kg: float):
        self.zone_id = hashlib.sha256(zone_name.encode()).hexdigest()
        self.zone_name = zone_name
        self.total_sustainable_catch_kg = total_sustainable_catch_kg
        self.merkle = MerkleEngine()
        
        # State
        self.fishers: Dict[str, Fisher] = {}
        self.catch_reports: List[CatchReport] = []
        self.quotas: Dict[str, QuotaAllocation] = {}
        self.votes: List[GovernanceVote] = []
        self.sanctions: List[dict] = []
        
        # Attestations
        self.attestation_ids: List[str] = []
        
    def _create_attestation(self, canon_id: str, claim: str) -> str:
        """Create attestation ID per Spec §3.3"""
        timestamp = int(time.time())
        claim_hash = hashlib.sha256(claim.encode()).hexdigest()
        preimage = (
            bytes.fromhex(self.zone_id) +
            bytes.fromhex(canon_id) +
            bytes.fromhex(claim_hash) +
            timestamp.to_bytes(8, 'big')
        )
        att_id = hashlib.sha256(preimage).hexdigest()
        self.attestation_ids.append(att_id)
        self.merkle.add_leaf(att_id)
        return att_id
    
    # =========================================================================
    # PRINCIPLE 1: Clear Boundaries (Membership)
    # =========================================================================
    
    def register_fisher(self, name: str, boat_registration: str) -> Fisher:
        """Register a fisher with membership attestation"""
        fisher_id = hashlib.sha256(f"{name}:{boat_registration}".encode()).hexdigest()
        
        claim = f"MEMBERSHIP|{fisher_id}|{name}|{boat_registration}"
        att_id = self._create_attestation(CANON_FISHER_MEMBERSHIP, claim)
        
        fisher = Fisher(
            fisher_id=fisher_id,
            name=name,
            boat_registration=boat_registration,
            membership_attestation=att_id
        )
        self.fishers[fisher_id] = fisher
        return fisher
    
    # =========================================================================
    # PRINCIPLE 2 & 3: Local Rules + Collective Choice (Governance)
    # =========================================================================
    
    def propose_quota_allocation(self, period: str) -> GovernanceVote:
        """Propose quota allocation via collective vote"""
        if not self.fishers:
            raise ValueError("No fishers registered")
        
        # Equal distribution (simplified - real system would be more complex)
        quota_per_fisher = self.total_sustainable_catch_kg / len(self.fishers)
        
        proposal = f"ALLOCATE|{period}|{quota_per_fisher}kg per fisher"
        vote_id = self._create_attestation(
            CANON_GOVERNANCE_VOTE,
            f"VOTE|{proposal}|PROPOSED"
        )
        
        # Simulate voting (all fishers vote yes in this demo)
        vote = GovernanceVote(
            vote_id=vote_id,
            proposal=proposal,
            yes_votes=len(self.fishers),
            no_votes=0,
            voters=list(self.fishers.keys()),
            passed=True
        )
        self.votes.append(vote)
        
        # If passed, allocate quotas
        if vote.passed:
            for fisher_id, fisher in self.fishers.items():
                allocation_id = self._create_attestation(
                    CANON_QUOTA_ALLOCATION,
                    f"QUOTA|{fisher_id}|{quota_per_fisher}|{period}"
                )
                quota = QuotaAllocation(
                    allocation_id=allocation_id,
                    fisher_id=fisher_id,
                    quota_kg=quota_per_fisher,
                    period=period,
                    governance_vote_id=vote_id
                )
                self.quotas[fisher_id] = quota
                fisher.quota_remaining_kg = quota_per_fisher
        
        return vote
    
    # =========================================================================
    # PRINCIPLE 4: Monitoring (Catch Reports with Peer Attestation)
    # =========================================================================
    
    def report_catch(
        self, 
        fisher_id: str, 
        catch_kg: float, 
        species: str,
        location: str,
        witness_ids: List[str]
    ) -> CatchReport:
        """Report a catch with peer witnesses (Ostrom's monitoring)"""
        if fisher_id not in self.fishers:
            raise ValueError("Fisher not registered")
        
        fisher = self.fishers[fisher_id]
        
        # Verify witnesses are also fishers (peer monitoring)
        valid_witnesses = [w for w in witness_ids if w in self.fishers and w != fisher_id]
        
        claim = f"CATCH|{fisher_id}|{catch_kg}kg|{species}|{location}|witnesses:{len(valid_witnesses)}"
        report_id = self._create_attestation(CANON_CATCH_REPORT, claim)
        
        report = CatchReport(
            report_id=report_id,
            fisher_id=fisher_id,
            catch_kg=catch_kg,
            species=species,
            location=location,
            timestamp=int(time.time()),
            witnesses=valid_witnesses
        )
        self.catch_reports.append(report)
        
        # Update fisher's quota
        fisher.total_catch_kg += catch_kg
        fisher.quota_remaining_kg -= catch_kg
        
        return report
    
    # =========================================================================
    # PRINCIPLE 5: Graduated Sanctions
    # =========================================================================
    
    def apply_sanction(self, fisher_id: str, violation: str, severity: float) -> dict:
        """Apply graduated sanction based on violation severity"""
        if fisher_id not in self.fishers:
            raise ValueError("Fisher not registered")
        
        fisher = self.fishers[fisher_id]
        
        # Reduce reputation stake
        penalty = min(severity, fisher.reputation_stake)
        fisher.reputation_stake -= penalty
        
        claim = f"SANCTION|{fisher_id}|{violation}|penalty:{penalty}%"
        sanction_id = self._create_attestation(CANON_SANCTION, claim)
        
        sanction = {
            "sanction_id": sanction_id,
            "fisher_id": fisher_id,
            "violation": violation,
            "penalty": penalty,
            "remaining_stake": fisher.reputation_stake
        }
        self.sanctions.append(sanction)
        
        return sanction
    
    # =========================================================================
    # PRINCIPLE 7: Recognition of Rights (Proof Generation)
    # =========================================================================
    
    def get_membership_proof(self, fisher_id: str) -> Optional[dict]:
        """Get cryptographic proof of membership"""
        if fisher_id not in self.fishers:
            return None
        
        fisher = self.fishers[fisher_id]
        self.merkle.compute_root()
        proof = self.merkle.generate_proof(fisher.membership_attestation)
        
        return {
            "fisher": fisher,
            "proof": proof,
            "merkle_root": self.merkle.compute_root()
        }
    
    def get_catch_history(self, fisher_id: str) -> List[CatchReport]:
        """Get verifiable catch history for a fisher"""
        return [r for r in self.catch_reports if r.fisher_id == fisher_id]
    
    # =========================================================================
    # PRINCIPLE 8: Nested Enterprises (Zone Federation)
    # =========================================================================
    
    def get_zone_state(self) -> dict:
        """Get full zone state for federation"""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "merkle_root": self.merkle.compute_root(),
            "total_fishers": len(self.fishers),
            "total_catch_kg": sum(f.total_catch_kg for f in self.fishers.values()),
            "sustainable_limit_kg": self.total_sustainable_catch_kg,
            "utilization": sum(f.total_catch_kg for f in self.fishers.values()) / self.total_sustainable_catch_kg * 100
        }


# =============================================================================
# DEMO
# =============================================================================

def main():
    print("=" * 80)
    print("COMMONS GOVERNANCE POC - FISHERY QUOTA TRACKING")
    print("Implementing Elinor Ostrom's 8 Principles (Nobel 2009)")
    print("=" * 80)
    print(f"\nGLSR: {GLSR}")
    
    # Create fishery zone
    zone = FisheryZone(
        zone_name="Mekong Delta Fishery Cooperative",
        total_sustainable_catch_kg=100000  # 100 tons annual sustainable catch
    )
    
    print(f"\n[ZONE] Created: {zone.zone_name}")
    print(f"   Zone ID: {zone.zone_id[:16]}...")
    print(f"   Sustainable catch limit: {zone.total_sustainable_catch_kg:,} kg/year")
    
    # =========================================================================
    # PRINCIPLE 1: Clear Boundaries
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 1: Clear Boundaries (Membership)")
    print("=" * 80)
    
    fishers = [
        zone.register_fisher("Nguyen Van A", "BOAT-001"),
        zone.register_fisher("Tran Thi B", "BOAT-002"),
        zone.register_fisher("Le Van C", "BOAT-003"),
        zone.register_fisher("Pham Thi D", "BOAT-004"),
        zone.register_fisher("Hoang Van E", "BOAT-005"),
    ]
    
    for f in fishers:
        print(f"   [OK] Registered: {f.name} ({f.boat_registration})")
        print(f"        Membership attestation: {f.membership_attestation[:16]}...")
    
    # =========================================================================
    # PRINCIPLE 2 & 3: Local Rules + Collective Choice
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 2 & 3: Local Rules + Collective Choice")
    print("=" * 80)
    
    vote = zone.propose_quota_allocation("2025-Q1")
    
    print(f"\n   [VOTE] {vote.proposal}")
    print(f"   Result: {'PASSED' if vote.passed else 'FAILED'} ({vote.yes_votes} yes / {vote.no_votes} no)")
    print(f"   Vote attestation: {vote.vote_id[:16]}...")
    
    for fisher in fishers:
        quota = zone.quotas.get(fisher.fisher_id)
        if quota:
            print(f"   [QUOTA] {fisher.name}: {quota.quota_kg:,.0f} kg")
    
    # =========================================================================
    # PRINCIPLE 4: Monitoring (Peer-witnessed catch reports)
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 4: Monitoring (Peer-witnessed Catch Reports)")
    print("=" * 80)
    
    # Simulate catches
    catches = [
        (fishers[0], 500, "Catfish", "Zone A-1", [fishers[1].fisher_id, fishers[2].fisher_id]),
        (fishers[1], 750, "Tilapia", "Zone A-2", [fishers[0].fisher_id]),
        (fishers[2], 300, "Carp", "Zone B-1", [fishers[3].fisher_id, fishers[4].fisher_id]),
        (fishers[0], 1200, "Catfish", "Zone A-1", [fishers[1].fisher_id]),
        (fishers[3], 800, "Pangasius", "Zone C-1", [fishers[4].fisher_id]),
    ]
    
    for fisher, kg, species, location, witnesses in catches:
        report = zone.report_catch(
            fisher.fisher_id,
            kg,
            species,
            location,
            witnesses
        )
        print(f"   [CATCH] {fisher.name}: {kg} kg {species}")
        print(f"           Location: {location} | Witnesses: {len(report.witnesses)}")
        print(f"           Attestation: {report.report_id[:16]}...")
    
    # =========================================================================
    # PRINCIPLE 5: Graduated Sanctions
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 5: Graduated Sanctions")
    print("=" * 80)
    
    # Fisher 0 over-reported (simulated violation)
    sanction = zone.apply_sanction(
        fishers[0].fisher_id,
        "Exceeded daily catch limit by 20%",
        severity=10.0  # 10% reputation penalty
    )
    
    print(f"\n   [SANCTION] {fishers[0].name}")
    print(f"   Violation: {sanction['violation']}")
    print(f"   Penalty: -{sanction['penalty']}% reputation")
    print(f"   Remaining stake: {sanction['remaining_stake']}%")
    print(f"   Attestation: {sanction['sanction_id'][:16]}...")
    
    # =========================================================================
    # PRINCIPLE 7: Recognition of Rights (Merkle Proofs)
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 7: Recognition of Rights (Cryptographic Proofs)")
    print("=" * 80)
    
    proof_data = zone.get_membership_proof(fishers[1].fisher_id)
    if proof_data and proof_data['proof']:
        print(f"\n   [PROOF] Membership proof for {fishers[1].name}")
        print(f"   Leaf: {fishers[1].membership_attestation[:16]}...")
        print(f"   Proof size: {len(proof_data['proof']['proof'])} siblings")
        print(f"   Merkle root: {proof_data['merkle_root'][:16]}...")
        
        # Verify proof
        is_valid = MerkleEngine.verify_proof(
            fishers[1].membership_attestation,
            proof_data['proof']['leaf_index'],
            proof_data['proof']['proof'],
            proof_data['merkle_root']
        )
        print(f"   Verified: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # =========================================================================
    # PRINCIPLE 8: Nested Enterprises (Zone State for Federation)
    # =========================================================================
    print("\n" + "=" * 80)
    print("PRINCIPLE 8: Nested Enterprises (Zone Federation State)")
    print("=" * 80)
    
    state = zone.get_zone_state()
    print(f"\n   [ZONE STATE]")
    print(f"   Zone: {state['zone_name']}")
    print(f"   Merkle root: {state['merkle_root'][:16]}...")
    print(f"   Fishers: {state['total_fishers']}")
    print(f"   Total catch: {state['total_catch_kg']:,.0f} kg")
    print(f"   Sustainable limit: {state['sustainable_limit_kg']:,.0f} kg")
    print(f"   Utilization: {state['utilization']:.1f}%")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("OSTROM'S 8 PRINCIPLES - VERIFICATION")
    print("=" * 80)
    
    principles = [
        ("1. Clear boundaries", "Zone membership attestation", "✅"),
        ("2. Local rules", "Zone-specific Canons (catch limits)", "✅"),
        ("3. Collective choice", "Governance votes as attestations", "✅"),
        ("4. Monitoring", "Public Merkle tree of all catches", "✅"),
        ("5. Graduated sanctions", "Reputation staking + penalties", "✅"),
        ("6. Conflict resolution", "Multi-zone arbitration (TODO)", "⚠️"),
        ("7. Recognition of rights", "Cryptographic proofs", "✅"),
        ("8. Nested enterprises", "Zone federation state", "✅"),
    ]
    
    for principle, implementation, status in principles:
        print(f"   {status} {principle}")
        print(f"      └── {implementation}")
    
    print(f"\n   Total attestations: {len(zone.attestation_ids)}")
    print(f"   Merkle root: {zone.merkle.compute_root()[:16]}...")
    print("=" * 80)
    print("Commons governance POC complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
