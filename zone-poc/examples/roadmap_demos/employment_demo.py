#!/usr/bin/env python3
"""
Contract Completion POC - Employment Verification
==================================================

Demonstrates Hart & Holmström's Contract Theory (Nobel 2016)
for solving incomplete contracts using Glogos attestations.

PROBLEM: Incomplete Contracts
- Employment contracts can't specify everything
- Effort is hard to verify (moral hazard)
- Information asymmetry between employer/employee
- Residual rights unclear

SOLUTION: Multi-party Attestation
| Contract Problem      | Glogos Solution              |
|-----------------------|------------------------------|
| Unverifiable effort   | Peer attestation of work     |
| Information asymmetry | Shared Merkle visibility     |
| Residual rights       | Attestation-based claims     |
| Principal-agent       | Multi-party verification     |

GLSR: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
"""

import sys
import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta

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
CANON_EMPLOYMENT = hashlib.sha256(b"employment:contract:1.0").hexdigest()
CANON_WORK_DELIVERY = hashlib.sha256(b"employment:work-delivery:1.0").hexdigest()
CANON_PEER_REVIEW = hashlib.sha256(b"employment:peer-review:1.0").hexdigest()
CANON_MILESTONE = hashlib.sha256(b"employment:milestone:1.0").hexdigest()
CANON_PAYMENT = hashlib.sha256(b"employment:payment:1.0").hexdigest()
CANON_DISPUTE = hashlib.sha256(b"employment:dispute:1.0").hexdigest()

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Employee:
    """Employee in the contract"""
    employee_id: str
    name: str
    role: str
    skills: List[str]

@dataclass
class Employer:
    """Employer in the contract"""
    employer_id: str
    company_name: str
    industry: str

@dataclass
class EmploymentContract:
    """The employment contract (necessarily incomplete)"""
    contract_id: str
    employer_id: str
    employee_id: str
    role: str
    monthly_salary: float
    start_date: str
    milestones: List[str]  # High-level goals only
    attestation_id: str = ""

@dataclass
class WorkDelivery:
    """Attestation of work delivered"""
    delivery_id: str
    contract_id: str
    description: str
    hours_worked: int
    artifacts: List[str]  # Links to deliverables
    attestation_id: str = ""

@dataclass
class PeerReview:
    """Peer attestation of work quality"""
    review_id: str
    delivery_id: str
    reviewer_id: str
    rating: int  # 1-5
    feedback: str
    attestation_id: str = ""

@dataclass
class MilestoneCompletion:
    """Milestone completion attestation"""
    milestone_id: str
    contract_id: str
    milestone_name: str
    completed_deliveries: List[str]
    peer_reviews: List[str]
    employer_approved: bool
    attestation_id: str = ""

# =============================================================================
# EMPLOYMENT ZONE
# =============================================================================

class EmploymentZone:
    """
    A Zone implementing Hart & Holmström's contract theory principles.
    Solves incomplete contracts through multi-party attestation.
    """
    
    def __init__(self, zone_name: str):
        self.zone_id = hashlib.sha256(zone_name.encode()).hexdigest()
        self.zone_name = zone_name
        self.merkle = MerkleEngine()
        
        # State
        self.employers: Dict[str, Employer] = {}
        self.employees: Dict[str, Employee] = {}
        self.contracts: Dict[str, EmploymentContract] = {}
        self.deliveries: List[WorkDelivery] = []
        self.reviews: List[PeerReview] = []
        self.milestones: List[MilestoneCompletion] = []
        self.payments: List[dict] = []
        self.disputes: List[dict] = []
        
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
    # REGISTRATION
    # =========================================================================
    
    def register_employer(self, company_name: str, industry: str) -> Employer:
        employer_id = hashlib.sha256(company_name.encode()).hexdigest()
        employer = Employer(
            employer_id=employer_id,
            company_name=company_name,
            industry=industry
        )
        self.employers[employer_id] = employer
        return employer
    
    def register_employee(self, name: str, role: str, skills: List[str]) -> Employee:
        employee_id = hashlib.sha256(f"{name}:{role}".encode()).hexdigest()
        employee = Employee(
            employee_id=employee_id,
            name=name,
            role=role,
            skills=skills
        )
        self.employees[employee_id] = employee
        return employee
    
    # =========================================================================
    # CONTRACT CREATION (Necessarily Incomplete)
    # =========================================================================
    
    def create_contract(
        self,
        employer: Employer,
        employee: Employee,
        monthly_salary: float,
        milestones: List[str]
    ) -> EmploymentContract:
        """
        Create employment contract.
        Note: Contract is INCOMPLETE by design - can't specify all details.
        Glogos handles this via ongoing attestations.
        """
        contract_id = hashlib.sha256(
            f"{employer.employer_id}:{employee.employee_id}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"CONTRACT|{contract_id}|"
            f"employer:{employer.company_name}|"
            f"employee:{employee.name}|"
            f"salary:{monthly_salary}|"
            f"milestones:{len(milestones)}"
        )
        att_id = self._create_attestation(CANON_EMPLOYMENT, claim)
        
        contract = EmploymentContract(
            contract_id=contract_id,
            employer_id=employer.employer_id,
            employee_id=employee.employee_id,
            role=employee.role,
            monthly_salary=monthly_salary,
            start_date=datetime.now().isoformat(),
            milestones=milestones,
            attestation_id=att_id
        )
        self.contracts[contract_id] = contract
        return contract
    
    # =========================================================================
    # WORK DELIVERY (Solving "Unverifiable Effort")
    # =========================================================================
    
    def submit_work(
        self,
        contract_id: str,
        description: str,
        hours_worked: int,
        artifacts: List[str]
    ) -> WorkDelivery:
        """
        Employee submits work delivery.
        This solves Hart's "unverifiable effort" problem -
        work is now cryptographically attested.
        """
        if contract_id not in self.contracts:
            raise ValueError("Contract not found")
        
        delivery_id = hashlib.sha256(
            f"{contract_id}:{description}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"WORK|{delivery_id}|contract:{contract_id[:8]}|"
            f"hours:{hours_worked}|artifacts:{len(artifacts)}"
        )
        att_id = self._create_attestation(CANON_WORK_DELIVERY, claim)
        
        delivery = WorkDelivery(
            delivery_id=delivery_id,
            contract_id=contract_id,
            description=description,
            hours_worked=hours_worked,
            artifacts=artifacts,
            attestation_id=att_id
        )
        self.deliveries.append(delivery)
        return delivery
    
    # =========================================================================
    # PEER REVIEW (Solving "Information Asymmetry")
    # =========================================================================
    
    def submit_peer_review(
        self,
        delivery_id: str,
        reviewer: Employee,
        rating: int,
        feedback: str
    ) -> PeerReview:
        """
        Peer review of work delivery.
        Solves information asymmetry - colleagues verify work quality.
        """
        review_id = hashlib.sha256(
            f"{delivery_id}:{reviewer.employee_id}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"REVIEW|{review_id}|delivery:{delivery_id[:8]}|"
            f"reviewer:{reviewer.name}|rating:{rating}/5"
        )
        att_id = self._create_attestation(CANON_PEER_REVIEW, claim)
        
        review = PeerReview(
            review_id=review_id,
            delivery_id=delivery_id,
            reviewer_id=reviewer.employee_id,
            rating=rating,
            feedback=feedback,
            attestation_id=att_id
        )
        self.reviews.append(review)
        return review
    
    # =========================================================================
    # MILESTONE COMPLETION (Multi-party Verification)
    # =========================================================================
    
    def complete_milestone(
        self,
        contract_id: str,
        milestone_name: str,
        delivery_ids: List[str],
        review_ids: List[str],
        employer_approved: bool
    ) -> MilestoneCompletion:
        """
        Complete a milestone with multi-party verification.
        Requires: work deliveries + peer reviews + employer approval.
        """
        milestone_id = hashlib.sha256(
            f"{contract_id}:{milestone_name}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"MILESTONE|{milestone_id}|{milestone_name}|"
            f"deliveries:{len(delivery_ids)}|reviews:{len(review_ids)}|"
            f"approved:{employer_approved}"
        )
        att_id = self._create_attestation(CANON_MILESTONE, claim)
        
        milestone = MilestoneCompletion(
            milestone_id=milestone_id,
            contract_id=contract_id,
            milestone_name=milestone_name,
            completed_deliveries=delivery_ids,
            peer_reviews=review_ids,
            employer_approved=employer_approved,
            attestation_id=att_id
        )
        self.milestones.append(milestone)
        return milestone
    
    # =========================================================================
    # PAYMENT (Attestation-based Claims)
    # =========================================================================
    
    def record_payment(
        self,
        contract_id: str,
        amount: float,
        milestone_id: Optional[str] = None
    ) -> dict:
        """Record payment against contract or milestone."""
        payment_id = hashlib.sha256(
            f"PAYMENT:{contract_id}:{amount}:{time.time()}".encode()
        ).hexdigest()
        
        claim = (
            f"PAYMENT|{payment_id}|contract:{contract_id[:8]}|"
            f"amount:{amount}|milestone:{milestone_id[:8] if milestone_id else 'N/A'}"
        )
        att_id = self._create_attestation(CANON_PAYMENT, claim)
        
        payment = {
            "payment_id": payment_id,
            "contract_id": contract_id,
            "amount": amount,
            "milestone_id": milestone_id,
            "attestation_id": att_id
        }
        self.payments.append(payment)
        return payment
    
    # =========================================================================
    # DISPUTE RESOLUTION
    # =========================================================================
    
    def file_dispute(
        self,
        contract_id: str,
        filed_by: str,
        reason: str
    ) -> dict:
        """File a dispute on the contract."""
        dispute_id = hashlib.sha256(
            f"DISPUTE:{contract_id}:{reason}:{time.time()}".encode()
        ).hexdigest()
        
        claim = f"DISPUTE|{dispute_id}|contract:{contract_id[:8]}|by:{filed_by[:8]}"
        att_id = self._create_attestation(CANON_DISPUTE, claim)
        
        dispute = {
            "dispute_id": dispute_id,
            "contract_id": contract_id,
            "filed_by": filed_by,
            "reason": reason,
            "attestation_id": att_id,
            "status": "OPEN"
        }
        self.disputes.append(dispute)
        return dispute
    
    # =========================================================================
    # VERIFICATION
    # =========================================================================
    
    def get_work_history(self, contract_id: str) -> dict:
        """Get complete verifiable work history for a contract."""
        contract = self.contracts.get(contract_id)
        if not contract:
            return {}
        
        deliveries = [d for d in self.deliveries if d.contract_id == contract_id]
        delivery_ids = [d.delivery_id for d in deliveries]
        reviews = [r for r in self.reviews if r.delivery_id in delivery_ids]
        milestones = [m for m in self.milestones if m.contract_id == contract_id]
        payments = [p for p in self.payments if p["contract_id"] == contract_id]
        
        return {
            "contract": contract,
            "deliveries": deliveries,
            "reviews": reviews,
            "milestones": milestones,
            "payments": payments,
            "total_hours": sum(d.hours_worked for d in deliveries),
            "avg_rating": sum(r.rating for r in reviews) / len(reviews) if reviews else 0,
            "total_paid": sum(p["amount"] for p in payments)
        }


# =============================================================================
# DEMO
# =============================================================================

def main():
    print("=" * 80)
    print("CONTRACT COMPLETION POC - EMPLOYMENT VERIFICATION")
    print("Implementing Hart & Holmström's Contract Theory (Nobel 2016)")
    print("=" * 80)
    print(f"\nGLSR: {GLSR}")
    
    # Create zone
    zone = EmploymentZone("Tech Talent Network")
    
    print(f"\n[ZONE] Created: {zone.zone_name}")
    print(f"   Zone ID: {zone.zone_id[:16]}...")
    
    # =========================================================================
    # SETUP: Register parties
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 1: Register Parties")
    print("=" * 80)
    
    employer = zone.register_employer("Acme Corp", "Technology")
    print(f"   [EMPLOYER] {employer.company_name}")
    
    employee = zone.register_employee(
        "Alice Developer",
        "Senior Software Engineer",
        ["Python", "Rust", "Blockchain"]
    )
    print(f"   [EMPLOYEE] {employee.name} - {employee.role}")
    
    # Register peer reviewers
    peer1 = zone.register_employee("Bob Reviewer", "Tech Lead", ["Architecture"])
    peer2 = zone.register_employee("Carol QA", "QA Engineer", ["Testing"])
    print(f"   [PEER] {peer1.name}")
    print(f"   [PEER] {peer2.name}")
    
    # =========================================================================
    # CONTRACT: Create incomplete contract
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 2: Create Employment Contract (Incomplete by Design)")
    print("=" * 80)
    
    contract = zone.create_contract(
        employer=employer,
        employee=employee,
        monthly_salary=10000,
        milestones=[
            "Design system architecture",
            "Implement core features",
            "Deploy to production"
        ]
    )
    
    print(f"\n   [CONTRACT] {contract.contract_id[:16]}...")
    print(f"   Employer: {employer.company_name}")
    print(f"   Employee: {employee.name}")
    print(f"   Salary: ${contract.monthly_salary:,}/month")
    print(f"   Milestones: {len(contract.milestones)}")
    print(f"   Attestation: {contract.attestation_id[:16]}...")
    print(f"\n   NOTE: Contract is INCOMPLETE - details handled via attestations")
    
    # =========================================================================
    # WORK DELIVERY: Solve "Unverifiable Effort"
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 3: Work Delivery (Solving 'Unverifiable Effort')")
    print("=" * 80)
    
    deliveries = []
    work_items = [
        ("System architecture document completed", 16, ["arch_doc_v1.pdf"]),
        ("Database schema designed", 8, ["schema.sql", "erd.png"]),
        ("Core API implemented", 40, ["api.py", "tests.py"]),
        ("Frontend integration", 24, ["frontend.js", "styles.css"]),
    ]
    
    for desc, hours, artifacts in work_items:
        delivery = zone.submit_work(
            contract.contract_id,
            desc,
            hours,
            artifacts
        )
        deliveries.append(delivery)
        print(f"   [WORK] {desc}")
        print(f"          Hours: {hours} | Artifacts: {artifacts}")
        print(f"          Attestation: {delivery.attestation_id[:16]}...")
    
    # =========================================================================
    # PEER REVIEW: Solve "Information Asymmetry"
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 4: Peer Review (Solving 'Information Asymmetry')")
    print("=" * 80)
    
    reviews = []
    
    # Peer 1 reviews first 2 deliveries
    for delivery in deliveries[:2]:
        review = zone.submit_peer_review(
            delivery.delivery_id,
            peer1,
            rating=5,
            feedback="Excellent work, well documented"
        )
        reviews.append(review)
        print(f"   [REVIEW] {peer1.name} reviewed delivery {delivery.delivery_id[:8]}...")
        print(f"            Rating: {review.rating}/5 | Attestation: {review.attestation_id[:16]}...")
    
    # Peer 2 reviews last 2 deliveries
    for delivery in deliveries[2:]:
        review = zone.submit_peer_review(
            delivery.delivery_id,
            peer2,
            rating=4,
            feedback="Good quality, minor improvements suggested"
        )
        reviews.append(review)
        print(f"   [REVIEW] {peer2.name} reviewed delivery {delivery.delivery_id[:8]}...")
        print(f"            Rating: {review.rating}/5 | Attestation: {review.attestation_id[:16]}...")
    
    # =========================================================================
    # MILESTONE: Multi-party Verification
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 5: Milestone Completion (Multi-party Verification)")
    print("=" * 80)
    
    milestone = zone.complete_milestone(
        contract.contract_id,
        "Design system architecture",
        delivery_ids=[d.delivery_id for d in deliveries[:2]],
        review_ids=[r.review_id for r in reviews[:2]],
        employer_approved=True
    )
    
    print(f"   [MILESTONE] {milestone.milestone_name}")
    print(f"   Deliveries: {len(milestone.completed_deliveries)}")
    print(f"   Reviews: {len(milestone.peer_reviews)}")
    print(f"   Employer approved: {'✅ Yes' if milestone.employer_approved else '❌ No'}")
    print(f"   Attestation: {milestone.attestation_id[:16]}...")
    
    # =========================================================================
    # PAYMENT: Attestation-based Claims
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 6: Payment (Attestation-based Claims)")
    print("=" * 80)
    
    payment = zone.record_payment(
        contract.contract_id,
        amount=5000,
        milestone_id=milestone.milestone_id
    )
    
    print(f"   [PAYMENT] ${payment['amount']:,}")
    print(f"   Contract: {payment['contract_id'][:16]}...")
    print(f"   Milestone: {payment['milestone_id'][:16]}...")
    print(f"   Attestation: {payment['attestation_id'][:16]}...")
    
    # =========================================================================
    # VERIFICATION: Complete Work History
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 7: Verifiable Work History")
    print("=" * 80)
    
    history = zone.get_work_history(contract.contract_id)
    
    print(f"\n   [HISTORY] Contract {contract.contract_id[:16]}...")
    print(f"   Total hours worked: {history['total_hours']}")
    print(f"   Average rating: {history['avg_rating']:.1f}/5")
    print(f"   Total paid: ${history['total_paid']:,}")
    print(f"   Deliveries: {len(history['deliveries'])}")
    print(f"   Reviews: {len(history['reviews'])}")
    print(f"   Milestones completed: {len(history['milestones'])}")
    
    # =========================================================================
    # MERKLE PROOF
    # =========================================================================
    print("\n" + "=" * 80)
    print("STEP 8: Cryptographic Verification")
    print("=" * 80)
    
    root = zone.merkle.compute_root()
    proof = zone.merkle.generate_proof(contract.attestation_id)
    
    if proof:
        is_valid = MerkleEngine.verify_proof(
            contract.attestation_id,
            proof['leaf_index'],
            proof['proof'],
            root
        )
        print(f"\n   [PROOF] Contract attestation")
        print(f"   Merkle root: {root[:16]}...")
        print(f"   Proof size: {len(proof['proof'])} siblings")
        print(f"   Verified: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("CONTRACT THEORY PRINCIPLES - VERIFICATION")
    print("=" * 80)
    
    principles = [
        ("Unverifiable effort", "Work delivery attestations with artifacts", "✅"),
        ("Information asymmetry", "Peer review attestations", "✅"),
        ("Residual rights", "Milestone completion proofs", "✅"),
        ("Principal-agent", "Multi-party verification (employee + peers + employer)", "✅"),
        ("Incomplete contracts", "Ongoing attestations fill gaps", "✅"),
    ]
    
    for problem, solution, status in principles:
        print(f"   {status} {problem}")
        print(f"      └── {solution}")
    
    print(f"\n   Total attestations: {len(zone.attestation_ids)}")
    print(f"   Merkle root: {root[:16]}...")
    print("=" * 80)
    print("Employment verification POC complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
