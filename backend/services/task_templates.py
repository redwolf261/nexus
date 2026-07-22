"""Built-in task templates for common investigation types.

Defines standard task workflows for Murder, Robbery, Missing Person, Cyber Crime, and Narcotics cases.
Instantiated at system startup or on-demand.

All templates use realistic investigative procedures and SLA targets.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session

from backend.db.schema import TaskCategory, TaskPriority, DependencyType
from backend.repositories.task_repository import TaskTemplateRepository


class BuiltInTemplates:
    """Factory for built-in task templates."""

    @staticmethod
    def murder_investigation() -> Tuple[dict, List[dict], List[Tuple[int, int]]]:
        """Murder investigation workflow.

        Returns:
            (template_meta, tasks, dependencies)
        """
        template_meta = {
            "name": "Murder Investigation",
            "case_type": "MURDER",
            "description": "Standard investigative workflow for homicide cases",
        }

        tasks = [
            {
                "order": 1,
                "title": "Secure Crime Scene",
                "description": "Ensure crime scene is secured and preserved for investigation",
                "category": TaskCategory.ADMINISTRATIVE,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 2,
            },
            {
                "order": 2,
                "title": "Conduct Scene Walk-Through",
                "description": "Initial inspection of scene, document condition, identify evidence",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 4,
            },
            {
                "order": 3,
                "title": "Collect Physical Evidence",
                "description": "Collect blood, DNA, fibers, weapons, projectiles from scene",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 4,
                "title": "Arrange Autopsy",
                "description": "Coordinate with medical examiner for autopsy",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 24,
            },
            {
                "order": 5,
                "title": "Interview Witnesses",
                "description": "Conduct interviews with witnesses present at scene",
                "category": TaskCategory.INTERVIEW,
                "priority": TaskPriority.HIGH,
                "sla_hours": 72,
            },
            {
                "order": 6,
                "title": "Interview Family",
                "description": "Notify family and conduct interviews about victim's activities",
                "category": TaskCategory.INTERVIEW,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 7,
                "title": "Obtain CCTV Footage",
                "description": "Retrieve CCTV footage from scene and surrounding areas",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 168,
            },
            {
                "order": 8,
                "title": "Analyze Video Footage",
                "description": "Review footage and identify suspect movements",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 9,
                "title": "Identify Suspect",
                "description": "Synthesize evidence to identify primary suspect",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 360,
            },
            {
                "order": 10,
                "title": "Obtain Warrant for Suspect Phone Records",
                "description": "Prepare and file warrant for suspect phone records",
                "category": TaskCategory.WARRANT,
                "priority": TaskPriority.HIGH,
                "sla_hours": 72,
            },
            {
                "order": 11,
                "title": "Collect Phone Records",
                "description": "Obtain phone records from carrier and analyze timeline",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 240,
            },
            {
                "order": 12,
                "title": "Arrest and Interrogation",
                "description": "Coordinate arrest with field team and interrogate suspect",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 72,
            },
            {
                "order": 13,
                "title": "Prepare Prosecution Case",
                "description": "Compile evidence package and prepare for prosecution",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
        ]

        # Dependencies: order 2->1, 3->2, 4->2, 5->2, 6->4, 7->2, 8->7, 9->[5,6,8], 10->9, 11->10, 12->9, 13->[11,12]
        dependencies = [
            (2, 1),  # Scene walk-through depends on scene secured
            (3, 2),  # Collect evidence depends on walk-through
            (4, 2),  # Autopsy depends on scene walk-through
            (5, 2),  # Interview witnesses depends on scene walk-through
            (6, 4),  # Interview family depends on autopsy (need results to discuss)
            (7, 2),  # Get CCTV depends on scene walk-through
            (8, 7),  # Analyze CCTV depends on footage obtained
            (9, 5),  # Identify suspect depends on witness statements
            (9, 6),  # Identify suspect depends on family interview
            (9, 8),  # Identify suspect depends on video analysis
            (10, 9), # Warrant depends on suspect identification
            (11, 10),# Phone records depend on warrant
            (12, 9), # Arrest depends on suspect identification
            (13, 11),# Prosecution prep depends on phone records
            (13, 12),# Prosecution prep depends on arrest/interrogation
        ]

        return template_meta, tasks, dependencies

    @staticmethod
    def robbery_investigation() -> Tuple[dict, List[dict], List[Tuple[int, int]]]:
        """Robbery investigation workflow.

        Returns:
            (template_meta, tasks, dependencies)
        """
        template_meta = {
            "name": "Robbery Investigation",
            "case_type": "ROBBERY",
            "description": "Investigation workflow for robbery cases",
        }

        tasks = [
            {
                "order": 1,
                "title": "Visit Crime Scene",
                "description": "Visit robbery location and document scene",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 4,
            },
            {
                "order": 2,
                "title": "Collect CCTV Footage",
                "description": "Obtain CCTV from business and surrounding area",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 3,
                "title": "Witness Statements",
                "description": "Conduct interviews with victim and witnesses",
                "category": TaskCategory.INTERVIEW,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 4,
                "title": "Analyze Video",
                "description": "Review CCTV and identify suspect description",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 72,
            },
            {
                "order": 5,
                "title": "Suspect Identification",
                "description": "Identify perpetrator from video and descriptions",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 6,
                "title": "Evidence Collection",
                "description": "Collect recovered items and document",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.MEDIUM,
                "sla_hours": 72,
            },
            {
                "order": 7,
                "title": "Arrest",
                "description": "Execute arrest of identified suspect",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 8,
                "title": "Case Review",
                "description": "Finalize case and prepare for prosecution",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.MEDIUM,
                "sla_hours": 96,
            },
        ]

        dependencies = [
            (2, 1),  # CCTV after scene visit
            (3, 1),  # Witness statements after scene visit
            (4, 2),  # Video analysis after CCTV obtained
            (5, 4),  # Suspect ID after video analyzed
            (5, 3),  # Suspect ID after witness statements
            (6, 1),  # Evidence collection after scene visit
            (7, 5),  # Arrest after suspect identified
            (8, 7),  # Case review after arrest
            (8, 6),  # Case review after evidence collected
        ]

        return template_meta, tasks, dependencies

    @staticmethod
    def missing_person_investigation() -> Tuple[dict, List[dict], List[Tuple[int, int]]]:
        """Missing person investigation (< 72 hours critical).

        Returns:
            (template_meta, tasks, dependencies)
        """
        template_meta = {
            "name": "Missing Person Investigation (< 72 hours)",
            "case_type": "MISSING_PERSON",
            "description": "Time-critical investigation for missing persons",
        }

        tasks = [
            {
                "order": 1,
                "title": "Verify Missing Status",
                "description": "Contact family to confirm person actually missing",
                "category": TaskCategory.INTERVIEW,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 2,
            },
            {
                "order": 2,
                "title": "Create Missing Person Alert",
                "description": "Generate alert and media release",
                "category": TaskCategory.ADMINISTRATIVE,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 4,
            },
            {
                "order": 3,
                "title": "Hospital Records Check",
                "description": "Check hospitals for unidentified patients",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 4,
            },
            {
                "order": 4,
                "title": "Get Recent Photos",
                "description": "Obtain current photos of missing person",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 4,
            },
            {
                "order": 5,
                "title": "Obtain CCTV",
                "description": "Get CCTV from last known location",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 24,
            },
            {
                "order": 6,
                "title": "Phone Records Request",
                "description": "Request phone location and call records",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 7,
                "title": "72-Hour Status Review",
                "description": "Assess findings and escalate if needed",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 72,
            },
        ]

        dependencies = [
            (2, 1),  # Alert after confirmed missing
            (3, 1),  # Hospital check after confirmed missing
            (4, 1),  # Get photos after confirmed missing
            (5, 4),  # CCTV depends on having recent photo (location)
            (6, 4),  # Phone records depend on having phone number
            (7, 5),  # Status review depends on CCTV analysis
            (7, 6),  # Status review depends on phone records
        ]

        return template_meta, tasks, dependencies

    @staticmethod
    def cyber_crime_investigation() -> Tuple[dict, List[dict], List[Tuple[int, int]]]:
        """Cyber crime investigation workflow.

        Returns:
            (template_meta, tasks, dependencies)
        """
        template_meta = {
            "name": "Cyber Crime Investigation",
            "case_type": "CYBER",
            "description": "Investigation workflow for cyber crimes",
        }

        tasks = [
            {
                "order": 1,
                "title": "Document Initial Report",
                "description": "Record victim's account of the cyber crime",
                "category": TaskCategory.INTERVIEW,
                "priority": TaskPriority.HIGH,
                "sla_hours": 8,
            },
            {
                "order": 2,
                "title": "Preserve Digital Evidence",
                "description": "Preserve logs, backups, and system state",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 12,
            },
            {
                "order": 3,
                "title": "Forensic Analysis",
                "description": "Conduct forensic analysis of compromised systems",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 240,
            },
            {
                "order": 4,
                "title": "Identify Attack Vector",
                "description": "Determine how attacker gained access",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 168,
            },
            {
                "order": 5,
                "title": "IP Trace",
                "description": "Trace attacker IP addresses and infrastructure",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 6,
                "title": "Identify Suspect",
                "description": "Link technical evidence to suspected individual",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 240,
            },
            {
                "order": 7,
                "title": "Obtain Warrants",
                "description": "Prepare and file warrants for additional records",
                "category": TaskCategory.WARRANT,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 8,
                "title": "Case Documentation",
                "description": "Prepare technical evidence summary for prosecution",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
        ]

        dependencies = [
            (2, 1),  # Preserve evidence after victim statement
            (3, 2),  # Forensic analysis after preservation
            (4, 3),  # Attack vector after forensic analysis
            (5, 4),  # IP trace after determining attack vector
            (6, 3),  # Suspect ID after forensic analysis
            (6, 5),  # Suspect ID after IP trace
            (7, 6),  # Warrants after suspect identified
            (8, 7),  # Documentation after warrants
        ]

        return template_meta, tasks, dependencies

    @staticmethod
    def narcotics_investigation() -> Tuple[dict, List[dict], List[Tuple[int, int]]]:
        """Narcotics investigation workflow.

        Returns:
            (template_meta, tasks, dependencies)
        """
        template_meta = {
            "name": "Narcotics Investigation",
            "case_type": "NARCOTICS",
            "description": "Investigation workflow for drug-related crimes",
        }

        tasks = [
            {
                "order": 1,
                "title": "Initial Surveillance",
                "description": "Conduct initial observation and intelligence gathering",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 2,
                "title": "Evidence Collection",
                "description": "Collect controlled substance samples",
                "category": TaskCategory.EVIDENCE_COLLECTION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 24,
            },
            {
                "order": 3,
                "title": "Lab Analysis",
                "description": "Submit samples to forensic lab for analysis",
                "category": TaskCategory.EXTERNAL_COORDINATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 120,
            },
            {
                "order": 4,
                "title": "Financial Investigation",
                "description": "Trace proceeds from narcotics activity",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.MEDIUM,
                "sla_hours": 240,
            },
            {
                "order": 5,
                "title": "Network Analysis",
                "description": "Map supplier and distributor network",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.HIGH,
                "sla_hours": 168,
            },
            {
                "order": 6,
                "title": "Obtain Search Warrant",
                "description": "Prepare warrant for suspect location",
                "category": TaskCategory.WARRANT,
                "priority": TaskPriority.HIGH,
                "sla_hours": 72,
            },
            {
                "order": 7,
                "title": "Execute Search",
                "description": "Execute search warrant and seize evidence",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.CRITICAL,
                "sla_hours": 72,
            },
            {
                "order": 8,
                "title": "Arrest and Interrogation",
                "description": "Arrest suspects and conduct interrogation",
                "category": TaskCategory.FIELD_OPERATION,
                "priority": TaskPriority.HIGH,
                "sla_hours": 48,
            },
            {
                "order": 9,
                "title": "Case Finalization",
                "description": "Compile evidence and prepare for prosecution",
                "category": TaskCategory.ANALYSIS,
                "priority": TaskPriority.MEDIUM,
                "sla_hours": 120,
            },
        ]

        dependencies = [
            (2, 1),  # Evidence collection after surveillance
            (3, 2),  # Lab analysis after collection
            (4, 2),  # Financial investigation after collection
            (5, 1),  # Network analysis after initial surveillance
            (6, 5),  # Warrant after network analysis
            (7, 6),  # Execute search after warrant obtained
            (8, 7),  # Arrest after search execution
            (9, 3),  # Case finalization after lab analysis
            (9, 8),  # Case finalization after arrest
        ]

        return template_meta, tasks, dependencies

    @staticmethod
    def install_all_templates(session: Session) -> None:
        """Install all built-in templates into database.

        Called at system startup.
        """
        repo = TaskTemplateRepository(session)

        templates_data = [
            BuiltInTemplates.murder_investigation(),
            BuiltInTemplates.robbery_investigation(),
            BuiltInTemplates.missing_person_investigation(),
            BuiltInTemplates.cyber_crime_investigation(),
            BuiltInTemplates.narcotics_investigation(),
        ]

        for template_meta, tasks, dependencies in templates_data:
            # Check if template already exists
            existing = repo.get_template_by_case_type(template_meta["case_type"])
            if existing:
                continue  # Skip if already installed

            # Create template
            template = repo.create_template(
                name=template_meta["name"],
                case_type=template_meta["case_type"],
                description=template_meta.get("description", ""),
            )

            # Map order -> task ID
            order_to_task_id = {}

            # Add tasks
            for task_data in tasks:
                task = repo.add_template_task(
                    template_id=template.id,
                    order=task_data["order"],
                    title=task_data["title"],
                    description=task_data["description"],
                    category=task_data["category"],
                    priority=task_data["priority"],
                    sla_hours=task_data.get("sla_hours"),
                )
                order_to_task_id[task_data["order"]] = task.id

            # Add dependencies
            for order, depends_on_order in dependencies:
                repo.add_template_dependency(
                    template_id=template.id,
                    task_id=order_to_task_id[order],
                    depends_on_task_id=order_to_task_id[depends_on_order],
                    dependency_type=DependencyType.FINISH_TO_START,
                )

        session.commit()
