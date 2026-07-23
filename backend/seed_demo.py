"""
NEXUS Demo Data Generator & One-Command Database Seeder
Populates synthetic Karnataka State Police Datathon dataset.
"""

import sys
import os
import json
import uuid
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import engine, Base
import backend.db.schema as db_schema
from backend.audit.schema import AuditLedgerRecord, AuditAggregateRecord
from backend.audit.service import AuditService
from backend.compliance.schema import ComplianceRuleRecord, ComplianceViolationRecord
from backend.compliance.rule_repository import RuleRepository
from backend.events.event_types import EventType


def seed_database():
    print("🌱 Initializing NEXUS Database Tables & Seeding Demo Dataset...")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Seed Compliance Rules
        RuleRepository.seed_default_rules(db)

        # 2. Check if investigations already seeded
        inv_count = db.query(db_schema.Investigation).count()
        if inv_count > 0:
            print("✅ Database already populated with demo dataset.")
            return

        # 3. Seed Investigations
        investigations = [
            ("INV-2026-001", "Operation Cyber Shield - Syndicate Ring", "HIGH", "ACTIVE", "BANGALORE_CENTRAL"),
            ("INV-2026-002", "Mysuru Heritage Theft Case", "CRITICAL", "ACTIVE", "MYSURU"),
            ("INV-2026-003", "Coastal Highway Smuggling Interception", "HIGH", "ACTIVE", "MANGALURU"),
            ("INV-2026-004", "Belagavi Cross-Border Fraud Trail", "MEDIUM", "ACTIVE", "BELAGAVI"),
            ("INV-2026-005", "Hubballi Cargo Interception Investigation", "LOW", "CLOSED", "HUBBALLI"),
        ]

        for inv_id, title, priority, status, dist in investigations:
            inv = db_schema.Investigation(
                id=inv_id,
                title=title,
                priority=priority,
                status=status,
                assigned_team=dist,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
                version=1,
                last_sequence=5
            )
            db.add(inv)

        # 4. Seed Tasks with Dependencies
        tasks = [
            ("TSK-101", "INV-2026-001", "Analyze Phone CDR Data", "IN_PROGRESS", "CRITICAL", 24),
            ("TSK-102", "INV-2026-001", "Trace Cryptocurrency Transfer", "PENDING", "HIGH", 48),
            ("TSK-103", "INV-2026-002", "Secure CCTV Footage Heritage Site", "COMPLETED", "HIGH", 12),
            ("TSK-104", "INV-2026-002", "Interrogate Primary Suspect", "BLOCKED", "CRITICAL", 24),
            ("TSK-105", "INV-2026-003", "Inspect Coastal Vessel Manifests", "IN_PROGRESS", "MEDIUM", 36),
        ]

        for t_id, case_id, title, status, priority, sla_hours in tasks:
            task = db_schema.InvestigationTask(
                id=t_id,
                investigation_id=case_id,
                title=title,
                status=status,
                priority=priority,
                sla_hours=sla_hours,
                created_at=datetime.datetime.utcnow(),
                due_date=datetime.datetime.utcnow() + datetime.timedelta(hours=sla_hours)
            )
            db.add(task)

        db.commit()

        # 5. Seed Audit Ledger & Compliance Violations
        print("🔐 Initializing SHA-256 Immutable Audit Ledger & Compliance Violations...")
        for i in range(1, 15):
            AuditService.log_event(
                db=db,
                event_type="TASK_CREATED" if i % 2 == 0 else "APPROVAL_SUBMITTED",
                entity_type="Task" if i % 2 == 0 else "Approval",
                entity_id=f"TSK-10{(i % 5) + 1}",
                actor_id=f"officer_{(i % 4) + 1}",
                payload={"case_id": "INV-2026-001", "step": i, "district_id": "BANGALORE_CENTRAL"}
            )

        RuleRepository.save_violation(
            db=db,
            rule_id="RULE_ASSIGN_01",
            rule_name="Officer Over Capacity",
            category="ASSIGNMENT",
            severity="MEDIUM",
            explanation="Officer assigned to 12 active tasks exceeding capacity limits.",
            evidence={"active_workload": 12, "capacity_limit": 10},
            remediation="Rebalance active workload or reassign task.",
            violated_entity_type="Officer",
            violated_entity_id="officer_1",
            actor_id="officer_1",
            district_id="BANGALORE_CENTRAL"
        )

        db.commit()
        print("✅ NEXUS Demo Dataset Seeded Successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
