"""
Firebase Service for CareFlow Nexus
Handles all Firebase Firestore operations for beds, patients, staff, and tasks
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service class for all Firebase Firestore operations"""

    def __init__(self, service_account_path: str = None):
        """
        Initialize Firebase service

        Args:
            service_account_path: Path to Firebase service account JSON file
        """
        try:
            if not firebase_admin._apps:
                if service_account_path and os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials
                    firebase_admin.initialize_app()

            self.db = firestore.client()
            logger.info("Firebase service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise

    # ==================== BED OPERATIONS ====================

    async def get_bed(self, bed_id: str) -> Optional[Dict]:
        """Get a specific bed by ID"""
        try:
            doc = self.db.collection("beds").document(bed_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting bed {bed_id}: {e}")
            return None

    async def get_all_beds(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get all beds with optional filters

        Args:
            filters: Dict with keys like 'status', 'ward', 'has_oxygen', etc.
        """
        try:
            query = self.db.collection("beds")

            if filters:
                if "status" in filters:
                    query = query.where(
                        filter=FieldFilter("status", "==", filters["status"])
                    )
                if "ward" in filters:
                    query = query.where(
                        filter=FieldFilter("ward", "==", filters["ward"])
                    )

            docs = query.stream()
            beds = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id

                # Apply equipment filters (not indexed in Firestore)
                if filters:
                    equipment = data.get("equipment", {})
                    if (
                        "has_oxygen" in filters
                        and equipment.get("has_oxygen") != filters["has_oxygen"]
                    ):
                        continue
                    if (
                        "has_ventilator" in filters
                        and equipment.get("has_ventilator") != filters["has_ventilator"]
                    ):
                        continue
                    if (
                        "is_isolation" in filters
                        and equipment.get("is_isolation") != filters["is_isolation"]
                    ):
                        continue

                beds.append(data)

            logger.info(f"Retrieved {len(beds)} beds")
            return beds
        except Exception as e:
            logger.error(f"Error getting beds: {e}")
            return []

    async def get_available_beds(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all beds with status 'ready'"""
        filter_dict = filters or {}
        filter_dict["status"] = "ready"
        return await self.get_all_beds(filter_dict)

    async def update_bed_status(
        self, bed_id: str, status: str, notes: Optional[str] = None
    ) -> bool:
        """
        Update bed status

        Args:
            bed_id: Bed document ID
            status: New status (ready, reserved, occupied, cleaning, maintenance)
            notes: Optional notes
        """
        try:
            update_data = {"status": status, "last_updated": firestore.SERVER_TIMESTAMP}
            if notes:
                update_data["notes"] = notes

            self.db.collection("beds").document(bed_id).update(update_data)
            logger.info(f"Updated bed {bed_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating bed status: {e}")
            return False

    async def assign_bed_to_patient(self, bed_id: str, patient_id: str) -> bool:
        """Assign a bed to a patient"""
        try:
            self.db.collection("beds").document(bed_id).update(
                {
                    "assigned_patient_id": patient_id,
                    "status": "reserved",
                    "last_updated": firestore.SERVER_TIMESTAMP,
                }
            )

            self.db.collection("patients").document(patient_id).update(
                {
                    "assigned_bed_id": bed_id,
                    "status": "admitted",
                    "admission_time": firestore.SERVER_TIMESTAMP,
                }
            )

            logger.info(f"Assigned bed {bed_id} to patient {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Error assigning bed: {e}")
            return False

    # ==================== PATIENT OPERATIONS ====================

    async def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get a specific patient by ID"""
        try:
            doc = self.db.collection("patients").document(patient_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting patient {patient_id}: {e}")
            return None

    async def get_all_patients(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all patients with optional filters"""
        try:
            query = self.db.collection("patients")

            if filters and "status" in filters:
                query = query.where(
                    filter=FieldFilter("status", "==", filters["status"])
                )

            docs = query.stream()
            patients = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                patients.append(data)

            logger.info(f"Retrieved {len(patients)} patients")
            return patients
        except Exception as e:
            logger.error(f"Error getting patients: {e}")
            return []

    async def create_patient(self, patient_data: Dict) -> Optional[str]:
        """Create a new patient record"""
        try:
            patient_data["created_at"] = firestore.SERVER_TIMESTAMP
            patient_data["status"] = patient_data.get("status", "waiting")

            doc_ref = self.db.collection("patients").add(patient_data)
            patient_id = doc_ref[1].id

            logger.info(f"Created patient with ID: {patient_id}")
            return patient_id
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return None

    async def update_patient(self, patient_id: str, updates: Dict) -> bool:
        """Update patient information"""
        try:
            updates["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("patients").document(patient_id).update(updates)
            logger.info(f"Updated patient {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            return False

    # ==================== STAFF OPERATIONS ====================

    async def get_staff(self, staff_id: str) -> Optional[Dict]:
        """Get a specific staff member by ID"""
        try:
            doc = self.db.collection("staff").document(staff_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting staff {staff_id}: {e}")
            return None

    async def get_all_staff(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all staff with optional filters"""
        try:
            query = self.db.collection("staff")

            if filters:
                if "role" in filters:
                    query = query.where(
                        filter=FieldFilter("role", "==", filters["role"])
                    )
                if "is_on_shift" in filters:
                    query = query.where(
                        filter=FieldFilter("is_on_shift", "==", filters["is_on_shift"])
                    )

            docs = query.stream()
            staff_list = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id

                # Apply ward filter if specified
                if filters and "assigned_ward" in filters:
                    if data.get("assigned_ward") != filters["assigned_ward"]:
                        continue

                staff_list.append(data)

            logger.info(f"Retrieved {len(staff_list)} staff members")
            return staff_list
        except Exception as e:
            logger.error(f"Error getting staff: {e}")
            return []

    async def get_available_staff(
        self, role: str, ward: Optional[str] = None, max_workload: int = 5
    ) -> List[Dict]:
        """Get available staff by role with workload filtering"""
        filters = {"role": role, "is_on_shift": True}
        if ward:
            filters["assigned_ward"] = ward

        staff_list = await self.get_all_staff(filters)

        # Filter by workload
        available = [s for s in staff_list if s.get("current_load", 0) < max_workload]

        # Sort by current load (least busy first)
        available.sort(key=lambda x: x.get("current_load", 0))

        return available

    async def get_staff_workload(self, staff_id: str) -> int:
        """Get current workload count for a staff member"""
        try:
            doc = self.db.collection("staff").document(staff_id).get()
            if doc.exists:
                return doc.to_dict().get("current_load", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting staff workload: {e}")
            return 0

    async def update_staff_workload(self, staff_id: str, increment: int) -> bool:
        """
        Update staff workload

        Args:
            staff_id: Staff document ID
            increment: Amount to increment (positive or negative)
        """
        try:
            staff_ref = self.db.collection("staff").document(staff_id)
            staff_doc = staff_ref.get()

            if staff_doc.exists:
                current_load = staff_doc.to_dict().get("current_load", 0)
                new_load = max(0, current_load + increment)

                staff_ref.update(
                    {"current_load": new_load, "updated_at": firestore.SERVER_TIMESTAMP}
                )
                logger.info(
                    f"Updated staff {staff_id} workload: {current_load} -> {new_load}"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating staff workload: {e}")
            return False

    # ==================== TASK OPERATIONS ====================

    async def create_task(self, task_data: Dict) -> Optional[str]:
        """Create a new task"""
        try:
            task_data["created_at"] = firestore.SERVER_TIMESTAMP
            task_data["status"] = task_data.get("status", "pending")

            doc_ref = self.db.collection("tasks").add(task_data)
            task_id = doc_ref[1].id

            # Increment staff workload if assigned
            if "assigned_to" in task_data:
                await self.update_staff_workload(task_data["assigned_to"], 1)

            logger.info(f"Created task with ID: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID"""
        try:
            doc = self.db.collection("tasks").document(task_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    async def get_tasks(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get tasks with optional filters"""
        try:
            query = self.db.collection("tasks")

            if filters:
                if "status" in filters:
                    if isinstance(filters["status"], list):
                        # Multiple statuses - filter in memory
                        pass
                    else:
                        query = query.where(
                            filter=FieldFilter("status", "==", filters["status"])
                        )

                if "assigned_to" in filters:
                    query = query.where(
                        filter=FieldFilter("assigned_to", "==", filters["assigned_to"])
                    )

                if "priority" in filters:
                    query = query.where(
                        filter=FieldFilter("priority", "==", filters["priority"])
                    )

            # Order by creation time
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING)

            docs = query.stream()
            tasks = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id

                # Apply multi-status filter if needed
                if (
                    filters
                    and "status" in filters
                    and isinstance(filters["status"], list)
                ):
                    if data.get("status") not in filters["status"]:
                        continue

                tasks.append(data)

            logger.info(f"Retrieved {len(tasks)} tasks")
            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    async def update_task_status(
        self, task_id: str, status: str, notes: Optional[str] = None
    ) -> bool:
        """Update task status"""
        try:
            update_data = {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}

            if status == "in_progress" and notes is None:
                update_data["started_at"] = firestore.SERVER_TIMESTAMP
            elif status == "completed":
                update_data["completed_at"] = firestore.SERVER_TIMESTAMP

                # Decrease staff workload
                task = await self.get_task(task_id)
                if task and "assigned_to" in task:
                    await self.update_staff_workload(task["assigned_to"], -1)

            if notes:
                update_data["notes"] = notes

            self.db.collection("tasks").document(task_id).update(update_data)
            logger.info(f"Updated task {task_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False

    # ==================== EVENT LOGGING ====================

    async def log_event(self, event_data: Dict) -> Optional[str]:
        """Log an event to the event_logs collection"""
        try:
            event_data["timestamp"] = firestore.SERVER_TIMESTAMP

            doc_ref = self.db.collection("event_logs").add(event_data)
            event_id = doc_ref[1].id

            logger.debug(f"Logged event with ID: {event_id}")
            return event_id
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return None

    # ==================== ANALYTICS ====================

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            beds = await self.get_all_beds()
            patients = await self.get_all_patients()
            staff = await self.get_all_staff({"is_on_shift": True})
            tasks = await self.get_tasks({"status": ["pending", "in_progress"]})

            total_beds = len(beds)
            available_beds = len([b for b in beds if b["status"] == "ready"])
            occupied_beds = len([b for b in beds if b["status"] == "occupied"])
            cleaning_beds = len([b for b in beds if b["status"] == "cleaning"])

            metrics = {
                "beds": {
                    "total": total_beds,
                    "available": available_beds,
                    "occupied": occupied_beds,
                    "cleaning": cleaning_beds,
                    "utilization_rate": (occupied_beds / total_beds * 100)
                    if total_beds > 0
                    else 0,
                },
                "patients": {
                    "total": len(patients),
                    "waiting": len(
                        [p for p in patients if p.get("status") == "waiting"]
                    ),
                    "admitted": len(
                        [p for p in patients if p.get("status") == "admitted"]
                    ),
                },
                "staff": {
                    "on_shift": len(staff),
                    "nurses": len([s for s in staff if s["role"] == "nurse"]),
                    "cleaners": len([s for s in staff if s["role"] == "cleaner"]),
                },
                "tasks": {
                    "active": len(tasks),
                    "pending": len([t for t in tasks if t["status"] == "pending"]),
                    "in_progress": len(
                        [t for t in tasks if t["status"] == "in_progress"]
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }

            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
