"""
Database Initialization Script for CareFlow Healthcare System
This script populates Firebase Firestore with initial data including:
- Users (doctors, nurses, cleaners, receptionists)
- Beds with different types and facilities
- Skills and specialties for staff members
"""

import os
import uuid
from datetime import datetime

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# Initialize Firebase
cred_path = os.getenv("FIREBASE_CRED_PATH")
if not cred_path:
    raise RuntimeError("FIREBASE_CRED_PATH is not set")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()


def clear_collections():
    """Clear existing collections (optional - use with caution)"""
    collections = ["users", "beds", "departments", "shifts"]

    print("Clearing existing collections...")
    for collection_name in collections:
        docs = db.collection(collection_name).stream()
        for doc in docs:
            doc.reference.delete()
    print("Collections cleared.")


def init_departments():
    """Initialize hospital departments"""
    departments = [
        {
            "department_id": "dept_icu",
            "name": "Intensive Care Unit",
            "code": "ICU",
            "description": "Critical care for severely ill patients",
            "floor": 3,
            "capacity": 20,
        },
        {
            "department_id": "dept_er",
            "name": "Emergency Room",
            "code": "ER",
            "description": "Emergency and trauma care",
            "floor": 1,
            "capacity": 15,
        },
        {
            "department_id": "dept_surgery",
            "name": "Surgery Ward",
            "code": "SUR",
            "description": "Post-operative care and recovery",
            "floor": 4,
            "capacity": 30,
        },
        {
            "department_id": "dept_pediatric",
            "name": "Pediatrics",
            "code": "PED",
            "description": "Child and infant care",
            "floor": 2,
            "capacity": 25,
        },
        {
            "department_id": "dept_general",
            "name": "General Ward",
            "code": "GEN",
            "description": "General medical care",
            "floor": 2,
            "capacity": 40,
        },
        {
            "department_id": "dept_maternity",
            "name": "Maternity Ward",
            "code": "MAT",
            "description": "Maternity and neonatal care",
            "floor": 3,
            "capacity": 20,
        },
        {
            "department_id": "dept_oncology",
            "name": "Oncology",
            "code": "ONC",
            "description": "Cancer treatment and care",
            "floor": 5,
            "capacity": 15,
        },
        {
            "department_id": "dept_cardio",
            "name": "Cardiology",
            "code": "CARD",
            "description": "Heart and cardiovascular care",
            "floor": 4,
            "capacity": 18,
        },
    ]

    print("Initializing departments...")
    for dept in departments:
        db.collection("departments").document(dept["department_id"]).set(dept)
    print(f"Added {len(departments)} departments.")


def init_nurses():
    """Initialize nurses with detailed skills and specialties"""
    nurses = [
        {
            "user_id": "nurse_001",
            "username": "sarah.johnson",
            "password": "nurse123",
            "role": "nurse",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@careflow.com",
            "phone": "+1-555-0101",
            "active": True,
            "age": 45,
            "gender": "female",
            "experience_years": 22,
            "specialties": ["ICU", "Critical Care", "Ventilator Management"],
            "certifications": ["RN", "CCRN", "ACLS", "BLS", "Critical Care Certified"],
            "skills": {
                "critical_care": 95,
                "emergency_response": 90,
                "patient_monitoring": 95,
                "medication_administration": 92,
                "wound_care": 85,
                "iv_therapy": 93,
            },
            "department": "ICU",
            "shift_preference": "day",
            "languages": ["English", "Spanish"],
            "notes": "Veteran ICU nurse with extensive experience in managing critically ill patients. Expert in ventilator management and hemodynamic monitoring.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "max_patients": 4,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_002",
            "username": "michael.chen",
            "password": "nurse123",
            "role": "nurse",
            "name": "Michael Chen",
            "email": "michael.chen@careflow.com",
            "phone": "+1-555-0102",
            "active": True,
            "age": 38,
            "gender": "male",
            "experience_years": 15,
            "specialties": ["Emergency Medicine", "Trauma Care", "Triage"],
            "certifications": ["RN", "CEN", "TNCC", "ACLS", "PALS"],
            "skills": {
                "emergency_response": 95,
                "trauma_care": 93,
                "triage": 94,
                "critical_thinking": 90,
                "wound_care": 88,
                "patient_assessment": 92,
            },
            "department": "ER",
            "shift_preference": "night",
            "languages": ["English", "Mandarin"],
            "notes": "ER specialist with rapid response capabilities. Excellent under pressure.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "max_patients": 6,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_003",
            "username": "emily.martinez",
            "password": "nurse123",
            "role": "nurse",
            "name": "Emily Martinez",
            "email": "emily.martinez@careflow.com",
            "phone": "+1-555-0103",
            "active": True,
            "age": 52,
            "gender": "female",
            "experience_years": 30,
            "specialties": ["Pediatrics", "Neonatal Care", "Child Development"],
            "certifications": ["RN", "CPN", "PALS", "NRP", "BLS"],
            "skills": {
                "pediatric_care": 98,
                "neonatal_care": 95,
                "family_communication": 96,
                "developmental_assessment": 92,
                "medication_administration": 94,
                "comfort_care": 97,
            },
            "department": "Pediatrics",
            "shift_preference": "day",
            "languages": ["English", "Spanish", "Portuguese"],
            "notes": "Senior pediatric nurse with three decades of experience. Exceptional with children and families.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "max_patients": 5,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_004",
            "username": "david.oconnor",
            "password": "nurse123",
            "role": "nurse",
            "name": "David O'Connor",
            "email": "david.oconnor@careflow.com",
            "phone": "+1-555-0104",
            "active": True,
            "age": 33,
            "gender": "male",
            "experience_years": 8,
            "specialties": [
                "Post-Surgical Care",
                "Pain Management",
                "Mobility Assistance",
            ],
            "certifications": ["RN", "CMSRN", "BLS", "ACLS"],
            "skills": {
                "post_surgical_care": 88,
                "pain_management": 85,
                "wound_care": 90,
                "mobility_assistance": 87,
                "patient_education": 83,
                "medication_administration": 86,
            },
            "department": "Surgery",
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Skilled in post-operative care and recovery monitoring.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": False,
            },
            "max_patients": 6,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_005",
            "username": "priya.patel",
            "password": "nurse123",
            "role": "nurse",
            "name": "Priya Patel",
            "email": "priya.patel@careflow.com",
            "phone": "+1-555-0105",
            "active": True,
            "age": 29,
            "gender": "female",
            "experience_years": 6,
            "specialties": [
                "General Medicine",
                "Chronic Disease Management",
                "Patient Education",
            ],
            "certifications": ["RN", "BLS", "Medical-Surgical Certified"],
            "skills": {
                "general_care": 85,
                "chronic_disease_management": 83,
                "patient_education": 88,
                "medication_administration": 84,
                "vital_monitoring": 86,
                "documentation": 90,
            },
            "department": "General",
            "shift_preference": "rotating",
            "languages": ["English", "Hindi", "Gujarati"],
            "notes": "Excellent communicator with focus on patient education and chronic disease management.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "max_patients": 7,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_006",
            "username": "jennifer.williams",
            "password": "nurse123",
            "role": "nurse",
            "name": "Jennifer Williams",
            "email": "jennifer.williams@careflow.com",
            "phone": "+1-555-0106",
            "active": True,
            "age": 41,
            "gender": "female",
            "experience_years": 18,
            "specialties": [
                "Maternity",
                "Labor and Delivery",
                "Postpartum Care",
                "Lactation",
            ],
            "certifications": ["RN", "RNC-OB", "NRP", "IBCLC", "BLS"],
            "skills": {
                "maternity_care": 94,
                "labor_delivery": 92,
                "postpartum_care": 93,
                "lactation_support": 95,
                "newborn_care": 91,
                "family_support": 94,
            },
            "department": "Maternity",
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Certified lactation consultant with extensive maternity experience. Compassionate care for mothers and newborns.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "max_patients": 4,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_007",
            "username": "robert.thompson",
            "password": "nurse123",
            "role": "nurse",
            "name": "Robert Thompson",
            "email": "robert.thompson@careflow.com",
            "phone": "+1-555-0107",
            "active": True,
            "age": 47,
            "gender": "male",
            "experience_years": 24,
            "specialties": [
                "Oncology",
                "Chemotherapy Administration",
                "Palliative Care",
            ],
            "certifications": ["RN", "OCN", "CHPN", "BLS", "Chemotherapy Certified"],
            "skills": {
                "oncology_care": 96,
                "chemotherapy_admin": 94,
                "palliative_care": 93,
                "symptom_management": 92,
                "patient_counseling": 90,
                "port_care": 95,
            },
            "department": "Oncology",
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Veteran oncology nurse specializing in chemotherapy and palliative care. Strong patient advocacy.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "max_patients": 5,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_008",
            "username": "lisa.nguyen",
            "password": "nurse123",
            "role": "nurse",
            "name": "Lisa Nguyen",
            "email": "lisa.nguyen@careflow.com",
            "phone": "+1-555-0108",
            "active": True,
            "age": 35,
            "gender": "female",
            "experience_years": 12,
            "specialties": [
                "Cardiology",
                "Cardiac Monitoring",
                "Heart Failure Management",
            ],
            "certifications": ["RN", "CCRN-CMC", "ACLS", "BLS"],
            "skills": {
                "cardiac_care": 91,
                "ecg_interpretation": 89,
                "heart_failure_management": 90,
                "patient_monitoring": 92,
                "medication_administration": 88,
                "patient_education": 87,
            },
            "department": "Cardiology",
            "shift_preference": "night",
            "languages": ["English", "Vietnamese"],
            "notes": "Cardiac care specialist with strong monitoring and assessment skills.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "max_patients": 5,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_009",
            "username": "james.anderson",
            "password": "nurse123",
            "role": "nurse",
            "name": "James Anderson",
            "email": "james.anderson@careflow.com",
            "phone": "+1-555-0109",
            "active": True,
            "age": 31,
            "gender": "male",
            "experience_years": 7,
            "specialties": ["General Medicine", "Geriatric Care", "Fall Prevention"],
            "certifications": ["RN", "BLS", "Geriatric Nursing Certified"],
            "skills": {
                "geriatric_care": 87,
                "fall_prevention": 85,
                "medication_management": 83,
                "mobility_assistance": 86,
                "cognitive_assessment": 82,
                "patient_safety": 88,
            },
            "department": "General",
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Focused on elderly patient care with emphasis on safety and mobility.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "max_patients": 6,
            "current_patients": 0,
        },
        {
            "user_id": "nurse_010",
            "username": "maria.rodriguez",
            "password": "nurse123",
            "role": "nurse",
            "name": "Maria Rodriguez",
            "email": "maria.rodriguez@careflow.com",
            "phone": "+1-555-0110",
            "active": True,
            "age": 26,
            "gender": "female",
            "experience_years": 3,
            "specialties": ["General Medicine", "Patient Care", "Basic Nursing"],
            "certifications": ["RN", "BLS"],
            "skills": {
                "basic_care": 78,
                "vital_monitoring": 80,
                "medication_administration": 76,
                "patient_hygiene": 82,
                "documentation": 79,
                "communication": 85,
            },
            "department": "General",
            "shift_preference": "night",
            "languages": ["English", "Spanish"],
            "notes": "Recent graduate with enthusiasm and strong work ethic. Growing clinical skills.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "max_patients": 5,
            "current_patients": 0,
        },
    ]

    print("Initializing nurses...")
    for nurse in nurses:
        db.collection("users").document(nurse["user_id"]).set(nurse)
    print(f"Added {len(nurses)} nurses.")


def init_cleaners():
    """Initialize cleaners with detailed skills and specialties"""
    cleaners = [
        {
            "user_id": "cleaner_001",
            "username": "john.smith",
            "password": "clean123",
            "role": "cleaner",
            "name": "John Smith",
            "email": "john.smith@careflow.com",
            "phone": "+1-555-0201",
            "active": True,
            "age": 43,
            "gender": "male",
            "experience_years": 18,
            "specialties": [
                "ICU Cleaning",
                "Sterile Environment",
                "Isolation Room Protocols",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Infection Control",
                "Hazardous Materials",
            ],
            "skills": {
                "icu_cleaning": 95,
                "sterile_technique": 93,
                "isolation_protocols": 94,
                "chemical_handling": 90,
                "equipment_sterilization": 92,
                "infection_control": 95,
            },
            "clearance_level": "high_risk",
            "equipment_certified": [
                "UV sterilizers",
                "autoclave",
                "foggers",
                "electrostatic sprayers",
            ],
            "department_expertise": ["ICU", "ER", "Surgery"],
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Senior ICU cleaner with expert-level knowledge of infection control. Specialized in critical care environments.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "average_room_time": 45,  # minutes
            "current_tasks": 0,
            "max_tasks_per_shift": 8,
        },
        {
            "user_id": "cleaner_002",
            "username": "patricia.brown",
            "password": "clean123",
            "role": "cleaner",
            "name": "Patricia Brown",
            "email": "patricia.brown@careflow.com",
            "phone": "+1-555-0202",
            "active": True,
            "age": 38,
            "gender": "female",
            "experience_years": 14,
            "specialties": [
                "Operating Room Cleaning",
                "Surgical Suite Sterilization",
                "Biohazard Handling",
            ],
            "certifications": [
                "Sterile Processing",
                "OR Cleaning Specialist",
                "Bloodborne Pathogens",
            ],
            "skills": {
                "or_cleaning": 94,
                "surgical_sterilization": 96,
                "biohazard_handling": 93,
                "equipment_cleaning": 92,
                "chemical_safety": 90,
                "terminal_cleaning": 94,
            },
            "clearance_level": "high_risk",
            "equipment_certified": [
                "autoclave",
                "surgical equipment cleaners",
                "sterilization indicators",
            ],
            "department_expertise": ["Surgery", "OR"],
            "shift_preference": "day",
            "languages": ["English", "French"],
            "notes": "OR specialist with extensive surgical suite cleaning experience. Meticulous and detail-oriented.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": False,
            },
            "average_room_time": 60,
            "current_tasks": 0,
            "max_tasks_per_shift": 6,
        },
        {
            "user_id": "cleaner_003",
            "username": "carlos.garcia",
            "password": "clean123",
            "role": "cleaner",
            "name": "Carlos Garcia",
            "email": "carlos.garcia@careflow.com",
            "phone": "+1-555-0203",
            "active": True,
            "age": 35,
            "gender": "male",
            "experience_years": 11,
            "specialties": ["Emergency Room", "Rapid Turnover", "Trauma Cleanup"],
            "certifications": [
                "Healthcare Environmental Services",
                "Bloodborne Pathogens",
                "Crisis Cleaning",
            ],
            "skills": {
                "er_cleaning": 92,
                "rapid_turnover": 94,
                "trauma_cleanup": 90,
                "biohazard_handling": 89,
                "speed_efficiency": 95,
                "stress_management": 91,
            },
            "clearance_level": "high_risk",
            "equipment_certified": [
                "emergency cleanup kits",
                "spill response equipment",
                "portable sterilizers",
            ],
            "department_expertise": ["ER", "Trauma"],
            "shift_preference": "night",
            "languages": ["English", "Spanish"],
            "notes": "ER specialist known for quick and thorough turnover. Excellent under pressure.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "average_room_time": 30,
            "current_tasks": 0,
            "max_tasks_per_shift": 12,
        },
        {
            "user_id": "cleaner_004",
            "username": "susan.lee",
            "password": "clean123",
            "role": "cleaner",
            "name": "Susan Lee",
            "email": "susan.lee@careflow.com",
            "phone": "+1-555-0204",
            "active": True,
            "age": 29,
            "gender": "female",
            "experience_years": 7,
            "specialties": [
                "Pediatric Ward",
                "Family-Friendly Cleaning",
                "Toy Sterilization",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Child-Safe Cleaning",
            ],
            "skills": {
                "pediatric_cleaning": 88,
                "toy_sterilization": 90,
                "family_friendly": 92,
                "general_cleaning": 85,
                "safety_protocols": 87,
                "gentle_techniques": 89,
            },
            "clearance_level": "standard",
            "equipment_certified": [
                "UV sanitizers",
                "steam cleaners",
                "child-safe chemicals",
            ],
            "department_expertise": ["Pediatrics", "Maternity"],
            "shift_preference": "day",
            "languages": ["English", "Korean"],
            "notes": "Specializes in pediatric environments. Uses child-safe cleaning products and methods.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "average_room_time": 35,
            "current_tasks": 0,
            "max_tasks_per_shift": 10,
        },
        {
            "user_id": "cleaner_005",
            "username": "thomas.wilson",
            "password": "clean123",
            "role": "cleaner",
            "name": "Thomas Wilson",
            "email": "thomas.wilson@careflow.com",
            "phone": "+1-555-0205",
            "active": True,
            "age": 51,
            "gender": "male",
            "experience_years": 25,
            "specialties": [
                "General Ward",
                "High-Volume Cleaning",
                "Efficiency Expert",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Supervisor Training",
                "Quality Control",
            ],
            "skills": {
                "general_cleaning": 93,
                "high_volume": 95,
                "efficiency": 94,
                "quality_control": 92,
                "team_coordination": 90,
                "equipment_maintenance": 88,
            },
            "clearance_level": "standard",
            "equipment_certified": [
                "floor cleaners",
                "pressure washers",
                "all standard equipment",
            ],
            "department_expertise": ["General", "All departments"],
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Veteran cleaner with supervisory experience. Can handle any department and high workload.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": False,
            },
            "average_room_time": 25,
            "current_tasks": 0,
            "max_tasks_per_shift": 15,
        },
        {
            "user_id": "cleaner_006",
            "username": "angela.davis",
            "password": "clean123",
            "role": "cleaner",
            "name": "Angela Davis",
            "email": "angela.davis@careflow.com",
            "phone": "+1-555-0206",
            "active": True,
            "age": 33,
            "gender": "female",
            "experience_years": 9,
            "specialties": ["Maternity Ward", "Newborn Safety", "Gentle Cleaning"],
            "certifications": [
                "Healthcare Environmental Services",
                "Maternity Cleaning Specialist",
            ],
            "skills": {
                "maternity_cleaning": 90,
                "newborn_safety": 92,
                "gentle_cleaning": 91,
                "family_sensitivity": 93,
                "infection_prevention": 88,
                "equipment_sterilization": 87,
            },
            "clearance_level": "standard",
            "equipment_certified": [
                "steam cleaners",
                "UV sanitizers",
                "bassinet cleaners",
            ],
            "department_expertise": ["Maternity", "Pediatrics"],
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Specializes in maternity environments with focus on newborn safety protocols.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "average_room_time": 40,
            "current_tasks": 0,
            "max_tasks_per_shift": 9,
        },
        {
            "user_id": "cleaner_007",
            "username": "raymond.kim",
            "password": "clean123",
            "role": "cleaner",
            "name": "Raymond Kim",
            "email": "raymond.kim@careflow.com",
            "phone": "+1-555-0207",
            "active": True,
            "age": 27,
            "gender": "male",
            "experience_years": 5,
            "specialties": [
                "Oncology Ward",
                "Chemotherapy Spill Response",
                "Hazardous Materials",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Hazmat Level 1",
                "Chemotherapy Spill",
            ],
            "skills": {
                "oncology_cleaning": 86,
                "hazmat_response": 88,
                "chemo_spill_cleanup": 90,
                "ppe_protocols": 89,
                "safety_compliance": 87,
                "contamination_control": 88,
            },
            "clearance_level": "high_risk",
            "equipment_certified": [
                "hazmat kits",
                "chemo spill kits",
                "specialized PPE",
            ],
            "department_expertise": ["Oncology", "Chemotherapy"],
            "shift_preference": "rotating",
            "languages": ["English", "Korean"],
            "notes": "Trained in handling chemotherapy spills and oncology-specific cleaning protocols.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "average_room_time": 50,
            "current_tasks": 0,
            "max_tasks_per_shift": 8,
        },
        {
            "user_id": "cleaner_008",
            "username": "michelle.taylor",
            "password": "clean123",
            "role": "cleaner",
            "name": "Michelle Taylor",
            "email": "michelle.taylor@careflow.com",
            "phone": "+1-555-0208",
            "active": True,
            "age": 31,
            "gender": "female",
            "experience_years": 8,
            "specialties": [
                "Cardiology",
                "Medical Equipment Cleaning",
                "Patient Room Turnover",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Medical Equipment Cleaning",
            ],
            "skills": {
                "cardiology_cleaning": 87,
                "equipment_cleaning": 89,
                "room_turnover": 88,
                "infection_control": 86,
                "detail_oriented": 90,
                "time_management": 88,
            },
            "clearance_level": "standard",
            "equipment_certified": [
                "cardiac equipment cleaners",
                "medical device sanitizers",
            ],
            "department_expertise": ["Cardiology", "General"],
            "shift_preference": "day",
            "languages": ["English"],
            "notes": "Experienced in cleaning cardiac monitoring equipment and cardiology patient rooms.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False,
            },
            "average_room_time": 35,
            "current_tasks": 0,
            "max_tasks_per_shift": 10,
        },
        {
            "user_id": "cleaner_009",
            "username": "robert.jackson",
            "password": "clean123",
            "role": "cleaner",
            "name": "Robert Jackson",
            "email": "robert.jackson@careflow.com",
            "phone": "+1-555-0209",
            "active": True,
            "age": 45,
            "gender": "male",
            "experience_years": 20,
            "specialties": [
                "Isolation Rooms",
                "Infectious Disease Protocols",
                "PPE Expert",
            ],
            "certifications": [
                "Healthcare Environmental Services",
                "Infection Control",
                "Isolation Protocols",
            ],
            "skills": {
                "isolation_cleaning": 96,
                "infectious_disease": 94,
                "ppe_expertise": 95,
                "contamination_control": 93,
                "negative_pressure_rooms": 92,
                "protocol_adherence": 96,
            },
            "clearance_level": "high_risk",
            "equipment_certified": [
                "isolation room equipment",
                "negative pressure systems",
                "advanced PPE",
            ],
            "department_expertise": ["Isolation", "ICU", "Infectious Disease"],
            "shift_preference": "night",
            "languages": ["English"],
            "notes": "Expert in isolation room protocols and infectious disease cleaning. Strict adherence to safety procedures.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "average_room_time": 55,
            "current_tasks": 0,
            "max_tasks_per_shift": 7,
        },
        {
            "user_id": "cleaner_010",
            "username": "linda.martinez",
            "password": "clean123",
            "role": "cleaner",
            "name": "Linda Martinez",
            "email": "linda.martinez@careflow.com",
            "phone": "+1-555-0210",
            "active": True,
            "age": 24,
            "gender": "female",
            "experience_years": 2,
            "specialties": ["General Cleaning", "Basic Protocols"],
            "certifications": ["Healthcare Environmental Services Basic"],
            "skills": {
                "general_cleaning": 75,
                "basic_protocols": 78,
                "time_management": 76,
                "attention_to_detail": 80,
                "equipment_handling": 74,
                "safety_awareness": 79,
            },
            "clearance_level": "standard",
            "equipment_certified": ["basic cleaning equipment", "floor cleaners"],
            "department_expertise": ["General"],
            "shift_preference": "night",
            "languages": ["English", "Spanish"],
            "notes": "Recent hire with good work ethic. Building experience and skills in healthcare cleaning.",
            "availability": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
            "average_room_time": 40,
            "current_tasks": 0,
            "max_tasks_per_shift": 10,
        },
    ]

    print("Initializing cleaners...")
    for cleaner in cleaners:
        db.collection("users").document(cleaner["user_id"]).set(cleaner)
    print(f"Added {len(cleaners)} cleaners.")


def init_doctors():
    """Initialize doctors"""
    doctors = [
        {
            "user_id": "doc_001",
            "username": "dr.smith",
            "password": "doc123",
            "role": "doctor",
            "name": "Dr. Elizabeth Smith",
            "email": "dr.smith@careflow.com",
            "phone": "+1-555-0301",
            "active": True,
            "specialization": "Cardiology",
            "experience_years": 15,
            "department": "Cardiology",
        },
        {
            "user_id": "doc_002",
            "username": "dr.jones",
            "password": "doc123",
            "role": "doctor",
            "name": "Dr. Michael Jones",
            "email": "dr.jones@careflow.com",
            "phone": "+1-555-0302",
            "active": True,
            "specialization": "Emergency Medicine",
            "experience_years": 12,
            "department": "ER",
        },
        {
            "user_id": "doc_003",
            "username": "dr.patel",
            "password": "doc123",
            "role": "doctor",
            "name": "Dr. Anika Patel",
            "email": "dr.patel@careflow.com",
            "phone": "+1-555-0303",
            "active": True,
            "specialization": "Pediatrics",
            "experience_years": 10,
            "department": "Pediatrics",
        },
        {
            "user_id": "doc_004",
            "username": "dr.wong",
            "password": "doc123",
            "role": "doctor",
            "name": "Dr. David Wong",
            "email": "dr.wong@careflow.com",
            "phone": "+1-555-0304",
            "active": True,
            "specialization": "Surgery",
            "experience_years": 18,
            "department": "Surgery",
        },
        {
            "user_id": "doc_005",
            "username": "dr.kumar",
            "password": "doc123",
            "role": "doctor",
            "name": "Dr. Raj Kumar",
            "email": "dr.kumar@careflow.com",
            "phone": "+1-555-0305",
            "active": True,
            "specialization": "Oncology",
            "experience_years": 14,
            "department": "Oncology",
        },
    ]

    print("Initializing doctors...")
    for doctor in doctors:
        db.collection("users").document(doctor["user_id"]).set(doctor)
    print(f"Added {len(doctors)} doctors.")


def init_receptionists():
    """Initialize receptionists"""
    receptionists = [
        {
            "user_id": "rec_001",
            "username": "anna.white",
            "password": "rec123",
            "role": "receptionist",
            "name": "Anna White",
            "email": "anna.white@careflow.com",
            "phone": "+1-555-0401",
            "active": True,
            "department": "Main Reception",
            "shift": "day",
        },
        {
            "user_id": "rec_002",
            "username": "tom.brown",
            "password": "rec123",
            "role": "receptionist",
            "name": "Tom Brown",
            "email": "tom.brown@careflow.com",
            "phone": "+1-555-0402",
            "active": True,
            "department": "Main Reception",
            "shift": "night",
        },
        {
            "user_id": "rec_003",
            "username": "sarah.green",
            "password": "rec123",
            "role": "receptionist",
            "name": "Sarah Green",
            "email": "sarah.green@careflow.com",
            "phone": "+1-555-0403",
            "active": True,
            "department": "ER Reception",
            "shift": "day",
        },
    ]

    print("Initializing receptionists...")
    for receptionist in receptionists:
        db.collection("users").document(receptionist["user_id"]).set(receptionist)
    print(f"Added {len(receptionists)} receptionists.")


def init_beds():
    """Initialize beds with different types and features"""
    bed_types = [
        {
            "type": "ICU",
            "features": ["ventilator", "cardiac monitor", "IV pump"],
            "department": "ICU",
        },
        {
            "type": "ICU",
            "features": ["ventilator", "cardiac monitor", "IV pump"],
            "department": "ICU",
        },
        {
            "type": "ICU",
            "features": ["ventilator", "cardiac monitor", "IV pump"],
            "department": "ICU",
        },
        {"type": "ER", "features": ["monitor", "oxygen"], "department": "ER"},
        {"type": "ER", "features": ["monitor", "oxygen"], "department": "ER"},
        {
            "type": "Surgery",
            "features": ["adjustable", "IV pump", "monitor"],
            "department": "Surgery",
        },
        {
            "type": "Surgery",
            "features": ["adjustable", "IV pump", "monitor"],
            "department": "Surgery",
        },
        {
            "type": "Surgery",
            "features": ["adjustable", "IV pump", "monitor"],
            "department": "Surgery",
        },
        {
            "type": "Pediatric",
            "features": ["child-safe", "monitor", "adjustable"],
            "department": "Pediatrics",
        },
        {
            "type": "Pediatric",
            "features": ["child-safe", "monitor", "adjustable"],
            "department": "Pediatrics",
        },
        {
            "type": "Maternity",
            "features": ["adjustable", "baby bassinet", "monitor"],
            "department": "Maternity",
        },
        {
            "type": "Maternity",
            "features": ["adjustable", "baby bassinet", "monitor"],
            "department": "Maternity",
        },
        {
            "type": "Oncology",
            "features": ["adjustable", "IV pump", "comfort features"],
            "department": "Oncology",
        },
        {
            "type": "Oncology",
            "features": ["adjustable", "IV pump", "comfort features"],
            "department": "Oncology",
        },
        {
            "type": "Cardiology",
            "features": ["cardiac monitor", "telemetry", "adjustable"],
            "department": "Cardiology",
        },
        {
            "type": "Cardiology",
            "features": ["cardiac monitor", "telemetry", "adjustable"],
            "department": "Cardiology",
        },
        {
            "type": "General",
            "features": ["adjustable", "basic monitor"],
            "department": "General",
        },
        {
            "type": "General",
            "features": ["adjustable", "basic monitor"],
            "department": "General",
        },
        {
            "type": "General",
            "features": ["adjustable", "basic monitor"],
            "department": "General",
        },
        {
            "type": "General",
            "features": ["adjustable", "basic monitor"],
            "department": "General",
        },
    ]

    beds = []
    for i, bed_config in enumerate(bed_types, 1):
        bed_id = f"bed_{i:03d}"
        beds.append(
            {
                "bed_id": bed_id,
                "bed_number": f"{bed_config['department']}-{i:02d}",
                "type": bed_config["type"],
                "department": bed_config["department"],
                "floor": (i % 5) + 1,
                "room_number": f"{((i % 5) + 1) * 100 + (i % 20) + 1}",
                "features": bed_config["features"],
                "occupied": False,
                "requires_cleaning": False,
                "last_cleaned": None,
                "status": "available",
            }
        )

    print("Initializing beds...")
    for bed in beds:
        db.collection("beds").document(bed["bed_id"]).set(bed)
    print(f"Added {len(beds)} beds.")


def init_shifts():
    """Initialize shift schedules"""
    shifts = [
        {
            "shift_id": "shift_day",
            "name": "Day Shift",
            "start_time": "07:00",
            "end_time": "15:00",
            "duration_hours": 8,
        },
        {
            "shift_id": "shift_evening",
            "name": "Evening Shift",
            "start_time": "15:00",
            "end_time": "23:00",
            "duration_hours": 8,
        },
        {
            "shift_id": "shift_night",
            "name": "Night Shift",
            "start_time": "23:00",
            "end_time": "07:00",
            "duration_hours": 8,
        },
    ]

    print("Initializing shifts...")
    for shift in shifts:
        db.collection("shifts").document(shift["shift_id"]).set(shift)
    print(f"Added {len(shifts)} shifts.")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("CareFlow Healthcare System - Database Initialization")
    print("=" * 60)
    print()

    response = input(
        "This will clear and reinitialize the database. Continue? (yes/no): "
    )
    if response.lower() != "yes":
        print("Initialization cancelled.")
        return

    print()
    print("Starting initialization...")
    print()

    # Clear existing data
    clear_collections()
    print()

    # Initialize collections
    init_departments()
    print()

    init_doctors()
    print()

    init_nurses()
    print()

    init_cleaners()
    print()

    init_receptionists()
    print()

    init_beds()
    print()

    init_shifts()
    print()

    print("=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- 8 Departments")
    print("- 5 Doctors")
    print("- 10 Nurses (with detailed skills and specialties)")
    print("- 10 Cleaners (with detailed skills and specialties)")
    print("- 3 Receptionists")
    print("- 20 Beds (various types)")
    print("- 3 Shifts")
    print()
    print("You can now use the system with these credentials:")
    print()
    print("Doctors:")
    print("  - dr.smith / doc123 (Cardiology)")
    print("  - dr.jones / doc123 (Emergency)")
    print("  - dr.patel / doc123 (Pediatrics)")
    print()
    print("Nurses:")
    print("  - sarah.johnson / nurse123 (ICU - 22 years exp)")
    print("  - michael.chen / nurse123 (ER - 15 years exp)")
    print("  - emily.martinez / nurse123 (Pediatrics - 30 years exp)")
    print()
    print("Cleaners:")
    print("  - john.smith / clean123 (ICU Specialist - 18 years exp)")
    print("  - patricia.brown / clean123 (OR Specialist - 14 years exp)")
    print("  - carlos.garcia / clean123 (ER Specialist - 11 years exp)")
    print()
    print("Receptionists:")
    print("  - anna.white / rec123")
    print("  - tom.brown / rec123")
    print()


if __name__ == "__main__":
    main()
