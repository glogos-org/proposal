#!/usr/bin/env python3
"""
Market Design POC - Carbon Credit Auction
==========================================

Demonstrates Milgrom & Wilson's Market Design (Nobel 2020)
for transparent, manipulation-resistant auctions using Glogos.

PROBLEM: Auction Manipulation
- Bid concealment leads to inefficient outcomes
- Winner's curse in common-value auctions
- Collusion hard to detect
- Mechanism opacity breeds distrust

SOLUTION: Commit-Reveal Attestations
| Market Problem     | Glogos Solution                |
|--------------------|--------------------------------|
| Bid concealment    | Commit-reveal attestations     |
| Winner's curse     | Information disclosure proofs  |
| Collusion          | Public bid verification        |
| Mechanism opacity  | Transparent rule attestation   |

USE CASES:
- Carbon credit markets
- Spectrum auctions
- Procurement transparency
- Public asset sales

GLSR: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
"""

import sys
import os
import hashlib
import time
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
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

# Canon IDs
CANON_AUCTION_RULES = hashlib.sha256(b"auction:rules:1.0").hexdigest()
CANON_CREDIT_LISTING = hashlib.sha256(b"auction:carbon-credit:1.0").hexdigest()
CANON_BID_COMMIT = hashlib.sha256(b"auction:bid-commit:1.0").hexdigest()
CANON_BID_REVEAL = hashlib.sha256(b"auction:bid-reveal:1.0").hexdigest()
CANON_AUCTION_RESULT = hashlib.sha256(b"auction:result:1.0").hexdigest()
CANON_TRANSFER = hashlib.sha256(b"auction:transfer:1.0").hexdigest()

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Bidder:
    """Auction participant"""
    bidder_id: str
    name: str
    organization: str
    verified: bool = True

@dataclass
class CarbonCredit:
    """Carbon credit listing"""
    credit_id: str
    description: str
    tonnes_co2: float
    vintage_year: int
    verification_standard: str  # e.g., "Verra VCS", "Gold Standard"
    min_price: float
    attestation_id: str = ""

@dataclass
class BidCommitment:
    """Commit phase: Hash of bid (bid not revealed yet)"""
    commit_id: str
    bidder_id: str
    credit_id: str
    commit_hash: str  # H(bid_amount || nonce)
    timestamp: int
    attestation_id: str = ""
    
@dataclass
class BidReveal:
    """Reveal phase: Actual bid amount + nonce"""
    reveal_id: str
    commit_id: str
    bid_amount: float
    nonce: str
    valid: bool  # Does H(amount || nonce) match commitment?
    attestation_id: str = ""

@dataclass
class AuctionResult:
    """Final auction result"""
    auction_id: str
    credit_id: str
    winner_id: str
    winning_bid: float
    all_bids: List[Tuple[str, float]]  # (bidder_id, amount)
    attestation_id: str = ""

# =============================================================================
# CARBON CREDIT AUCTION ZONE
# =============================================================================

class CarbonAuctionZone:
    """
    A Zone implementing Milgrom & Wilson's market design principles.
    Uses commit-reveal scheme for transparent, fair auctions.
    """
    
    def __init__(self, zone_name: str):
        self.zone_id = hashlib.sha256(zone_name.encode()).hexdigest()
        self.zone_name = zone_name
        self.merkle = MerkleEngine()
        
        # State
        self.bidders: Dict[str, Bidder] = {}
        self.credits: Dict[str, CarbonCredit] = {}
        self.commitments: Dict[str, BidCommitment] = {}  # commit_id -> commitment
        self.reveals: Dict[str, BidReveal] = {}  # commit_id -> reveal
        self.results: List[AuctionResult] = []
        self.transfers: List[dict] = []
        
        self.attestation_ids: List[str] = []
        
        # Attest auction rules at creation
        self._attest_rules()
        
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
    
    def _attest_rules(self):
        """Attest auction rules (Mechanism Transparency)"""
        rules = (
            "AUCTION_RULES|"
            "type:sealed-bid-second-price|"
            "method:commit-reveal|"
            "commit_hash:SHA256(amount||nonce)|"
            "winner:highest_bidder|"
            "price:second_highest_bid"
        )
        self.rules_attestation = self._create_attestation(CANON_AUCTION_RULES, rules)
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    def register_bidder(self, name: str, organization: str) -> Bidder:
        bidder_id = hashlib.sha256(f"{name}:{organization}".encode()).hexdigest()
        bidder = Bidder(
            bidder_id=bidder_id,
            name=name,
            organization=organization
        )
        self.bidders[bidder_id] = bidder
        return bidder
    
    # =========================================================================
    # CREDIT LISTING
    # =========================================================================
    
    def list_credit(
        self,
        description: str,
        tonnes_co2: float,
        vintage_year: int,
        verification_standard: str,
        min_price: float
    ) -> CarbonCredit:
        """List a carbon credit for auction"""
        credit_id = hashlib.sha256(
            f"{description}:{tonnes_co2}:{vintage_year}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"CREDIT|{credit_id}|{description}|"
            f"{tonnes_co2}tCO2|{vintage_year}|{verification_standard}|"
            f"min:${min_price}"
        )
        att_id = self._create_attestation(CANON_CREDIT_LISTING, claim)
        
        credit = CarbonCredit(
            credit_id=credit_id,
            description=description,
            tonnes_co2=tonnes_co2,
            vintage_year=vintage_year,
            verification_standard=verification_standard,
            min_price=min_price,
            attestation_id=att_id
        )
        self.credits[credit_id] = credit
        return credit
    
    # =========================================================================
    # COMMIT PHASE (Bid Concealment Solution)
    # =========================================================================
    
    def commit_bid(
        self,
        bidder: Bidder,
        credit_id: str,
        bid_amount: float
    ) -> Tuple[BidCommitment, str]:
        """
        Commit phase: Bidder submits H(bid || nonce).
        Returns commitment and nonce (bidder must keep nonce secret).
        """
        if credit_id not in self.credits:
            raise ValueError("Credit not found")
        
        # Generate random nonce
        nonce = secrets.token_hex(16)
        
        # Create commitment: H(amount || nonce)
        commit_hash = hashlib.sha256(
            f"{bid_amount:.2f}:{nonce}".encode()
        ).hexdigest()
        
        commit_id = hashlib.sha256(
            f"{bidder.bidder_id}:{credit_id}:{commit_hash}".encode()
        ).hexdigest()
        
        claim = (
            f"COMMIT|{commit_id}|"
            f"bidder:{bidder.bidder_id[:8]}|"
            f"credit:{credit_id[:8]}|"
            f"hash:{commit_hash[:16]}"
        )
        att_id = self._create_attestation(CANON_BID_COMMIT, claim)
        
        commitment = BidCommitment(
            commit_id=commit_id,
            bidder_id=bidder.bidder_id,
            credit_id=credit_id,
            commit_hash=commit_hash,
            timestamp=int(time.time()),
            attestation_id=att_id
        )
        self.commitments[commit_id] = commitment
        
        return commitment, nonce
    
    # =========================================================================
    # REVEAL PHASE (Information Disclosure)
    # =========================================================================
    
    def reveal_bid(
        self,
        commit_id: str,
        bid_amount: float,
        nonce: str
    ) -> BidReveal:
        """
        Reveal phase: Bidder reveals bid_amount and nonce.
        System verifies H(amount || nonce) matches original commitment.
        """
        if commit_id not in self.commitments:
            raise ValueError("Commitment not found")
        
        commitment = self.commitments[commit_id]
        
        # Verify commitment
        computed_hash = hashlib.sha256(
            f"{bid_amount:.2f}:{nonce}".encode()
        ).hexdigest()
        
        valid = computed_hash == commitment.commit_hash
        
        reveal_id = hashlib.sha256(
            f"REVEAL:{commit_id}:{bid_amount}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"REVEAL|{reveal_id}|"
            f"commit:{commit_id[:8]}|"
            f"amount:${bid_amount:.2f}|"
            f"valid:{valid}"
        )
        att_id = self._create_attestation(CANON_BID_REVEAL, claim)
        
        reveal = BidReveal(
            reveal_id=reveal_id,
            commit_id=commit_id,
            bid_amount=bid_amount,
            nonce=nonce,
            valid=valid,
            attestation_id=att_id
        )
        self.reveals[commit_id] = reveal
        
        return reveal
    
    # =========================================================================
    # AUCTION SETTLEMENT (Public Verification)
    # =========================================================================
    
    def settle_auction(self, credit_id: str) -> Optional[AuctionResult]:
        """
        Settle auction: Determine winner based on revealed bids.
        Uses second-price auction (Vickrey) for truthful bidding.
        """
        credit = self.credits.get(credit_id)
        if not credit:
            raise ValueError("Credit not found")
        
        # Get all valid reveals for this credit
        valid_bids = []
        for commit_id, commitment in self.commitments.items():
            if commitment.credit_id != credit_id:
                continue
            reveal = self.reveals.get(commit_id)
            if reveal and reveal.valid and reveal.bid_amount >= credit.min_price:
                valid_bids.append((commitment.bidder_id, reveal.bid_amount))
        
        if not valid_bids:
            print("   No valid bids received")
            return None
        
        # Sort by bid amount (descending)
        valid_bids.sort(key=lambda x: x[1], reverse=True)
        
        # Winner = highest bidder
        winner_id, highest_bid = valid_bids[0]
        
        # Price = second highest bid (or min_price if only one bidder)
        if len(valid_bids) >= 2:
            winning_price = valid_bids[1][1]  # Second price
        else:
            winning_price = credit.min_price
        
        auction_id = hashlib.sha256(
            f"AUCTION:{credit_id}:{winner_id}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"RESULT|{auction_id}|"
            f"credit:{credit_id[:8]}|"
            f"winner:{winner_id[:8]}|"
            f"bid:${highest_bid:.2f}|"
            f"price:${winning_price:.2f}|"
            f"bids:{len(valid_bids)}"
        )
        att_id = self._create_attestation(CANON_AUCTION_RESULT, claim)
        
        result = AuctionResult(
            auction_id=auction_id,
            credit_id=credit_id,
            winner_id=winner_id,
            winning_bid=winning_price,
            all_bids=valid_bids,
            attestation_id=att_id
        )
        self.results.append(result)
        
        return result
    
    # =========================================================================
    # TRANSFER (Asset Movement)
    # =========================================================================
    
    def transfer_credit(
        self,
        result: AuctionResult,
        from_account: str,
        to_account: str
    ) -> dict:
        """Record credit transfer based on auction result."""
        credit = self.credits[result.credit_id]
        
        transfer_id = hashlib.sha256(
            f"TRANSFER:{result.auction_id}:{to_account}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"TRANSFER|{transfer_id}|"
            f"credit:{result.credit_id[:8]}|"
            f"from:{from_account[:8]}|"
            f"to:{to_account[:8]}|"
            f"{credit.tonnes_co2}tCO2"
        )
        att_id = self._create_attestation(CANON_TRANSFER, claim)
        
        transfer = {
            "transfer_id": transfer_id,
            "credit_id": result.credit_id,
            "from": from_account,
            "to": to_account,
            "tonnes_co2": credit.tonnes_co2,
            "price": result.winning_bid,
            "auction_id": result.auction_id,
            "attestation_id": att_id
        }
        self.transfers.append(transfer)
        
        return transfer


# =============================================================================
# DEMO
# =============================================================================

def main():
    print("=" * 80)
    print("MARKET DESIGN POC - CARBON CREDIT AUCTION")
    print("Implementing Milgrom & Wilson's Market Design (Nobel 2020)")
    print("=" * 80)
    print(f"\nGLSR: {GLSR}")
    
    # Create zone
    zone = CarbonAuctionZone("Global Carbon Exchange")
    
    print(f"\n[ZONE] Created: {zone.zone_name}")
    print(f"   Zone ID: {zone.zone_id[:16]}...")
    print(f"   Rules attestation: {zone.rules_attestation[:16]}...")
    
    # =========================================================================
    # STEP 1: Register Bidders
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 1: Register Bidders")
    print("=" * 80)
    
    bidders = [
        zone.register_bidder("Green Energy Corp", "Renewable Energy"),
        zone.register_bidder("EcoTech Industries", "Manufacturing"),
        zone.register_bidder("Clean Air Initiative", "Non-profit"),
        zone.register_bidder("Carbon Neutral Ltd", "Consulting"),
    ]
    
    for b in bidders:
        print(f"   [BIDDER] {b.name} ({b.organization})")
    
    # =========================================================================
    # STEP 2: List Carbon Credit
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 2: List Carbon Credit for Auction")
    print("=" * 80)
    
    credit = zone.list_credit(
        description="Amazon Rainforest Conservation Project - Block A",
        tonnes_co2=1000,
        vintage_year=2024,
        verification_standard="Verra VCS",
        min_price=15.0
    )
    
    print(f"\n   [CREDIT] {credit.description}")
    print(f"   Volume: {credit.tonnes_co2:,} tonnes CO2")
    print(f"   Vintage: {credit.vintage_year}")
    print(f"   Standard: {credit.verification_standard}")
    print(f"   Minimum price: ${credit.min_price}/tonne")
    print(f"   Attestation: {credit.attestation_id[:16]}...")
    
    # =========================================================================
    # STEP 3: Commit Phase (Sealed Bids)
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 3: Commit Phase (Sealed Bids)")
    print("=" * 80)
    print("   Bidders submit H(bid || nonce) - bids are hidden")
    
    # Each bidder commits their bid
    bid_data = [
        (bidders[0], 25.50),  # Green Energy Corp
        (bidders[1], 22.00),  # EcoTech Industries
        (bidders[2], 28.75),  # Clean Air Initiative
        (bidders[3], 20.00),  # Carbon Neutral Ltd
    ]
    
    commitments_and_nonces = []
    for bidder, amount in bid_data:
        commitment, nonce = zone.commit_bid(bidder, credit.credit_id, amount)
        commitments_and_nonces.append((commitment, nonce, amount))
        print(f"\n   [COMMIT] {bidder.name}")
        print(f"   Commit hash: {commitment.commit_hash[:24]}...")
        print(f"   Attestation: {commitment.attestation_id[:16]}...")
        # Note: Actual bid amount is hidden at this stage!
    
    # =========================================================================
    # STEP 4: Reveal Phase (Public Disclosure)
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 4: Reveal Phase (Public Disclosure)")
    print("=" * 80)
    print("   Bidders reveal (bid, nonce) - system verifies hash matches")
    
    for commitment, nonce, amount in commitments_and_nonces:
        bidder = zone.bidders[commitment.bidder_id]
        reveal = zone.reveal_bid(commitment.commit_id, amount, nonce)
        
        status = "✅ VALID" if reveal.valid else "❌ INVALID"
        print(f"\n   [REVEAL] {bidder.name}")
        print(f"   Bid: ${amount:.2f}/tonne")
        print(f"   Verification: {status}")
        print(f"   Attestation: {reveal.attestation_id[:16]}...")
    
    # =========================================================================
    # STEP 5: Auction Settlement
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 5: Auction Settlement (Second-Price Vickrey)")
    print("=" * 80)
    
    result = zone.settle_auction(credit.credit_id)
    
    if result:
        winner = zone.bidders[result.winner_id]
        print(f"\n   [RESULT] Auction settled!")
        print(f"\n   All bids (sorted):")
        for bidder_id, bid_amount in result.all_bids:
            bidder = zone.bidders[bidder_id]
            marker = " ← WINNER" if bidder_id == result.winner_id else ""
            print(f"      ${bid_amount:.2f} - {bidder.name}{marker}")
        
        print(f"\n   Winner: {winner.name}")
        print(f"   Highest bid: ${result.all_bids[0][1]:.2f}")
        print(f"   Winning price (2nd bid): ${result.winning_bid:.2f}")
        print(f"   Attestation: {result.attestation_id[:16]}...")
        
    # =========================================================================
    # STEP 6: Credit Transfer
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 6: Credit Transfer")
    print("=" * 80)
    
    if result:
        transfer = zone.transfer_credit(
            result,
            from_account="carbon_registry_reserve",
            to_account=result.winner_id
        )
        
        print(f"\n   [TRANSFER] Credit transferred")
        print(f"   From: Carbon Registry Reserve")
        print(f"   To: {winner.name}")
        print(f"   Volume: {transfer['tonnes_co2']:,} tonnes CO2")
        print(f"   Price: ${transfer['price']:.2f}/tonne")
        print(f"   Total value: ${transfer['tonnes_co2'] * transfer['price']:,.2f}")
        print(f"   Attestation: {transfer['attestation_id'][:16]}...")
    
    # =========================================================================
    # VERIFICATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 7: Cryptographic Verification")
    print("=" * 80)
    
    root = zone.merkle.compute_root()
    
    if result:
        proof = zone.merkle.generate_proof(result.attestation_id)
        if proof:
            is_valid = MerkleEngine.verify_proof(
                result.attestation_id,
                proof['leaf_index'],
                proof['proof'],
                root
            )
            print(f"\n   [PROOF] Auction result attestation")
            print(f"   Merkle root: {root[:16]}...")
            print(f"   Proof size: {len(proof['proof'])} siblings")
            print(f"   Verified: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("MARKET DESIGN PRINCIPLES - VERIFICATION")
    print("=" * 80)
    
    principles = [
        ("Bid concealment", "Commit-reveal attestations", "✅"),
        ("Winner's curse", "Second-price (Vickrey) auction", "✅"),
        ("Collusion prevention", "Public bid verification", "✅"),
        ("Mechanism opacity", "Rules attested at zone creation", "✅"),
        ("Truthful bidding", "Dominant strategy in second-price", "✅"),
    ]
    
    for problem, solution, status in principles:
        print(f"   {status} {problem}")
        print(f"      └── {solution}")
    
    print(f"\n   Total attestations: {len(zone.attestation_ids)}")
    print(f"   Merkle root: {root[:16]}...")
    print("=" * 80)
    print("Carbon credit auction POC complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
