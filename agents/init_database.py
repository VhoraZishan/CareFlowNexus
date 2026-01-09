"""
Database Initialization Script for CareFlow Nexus
This script creates the Firestore database structure according to the API contract document
"""

import sys
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


def initialize_database(service_account_path: str):
    """
    Initialize Firestore database with sample data

    Args:
        service_account_path: Path to Firebase service account JSON file
    """
    try:
        # Initialize Firebase
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()

        print("=" * 60)
        print("CareFlow Nexus - Database Initialization")
        print("=" * 60)
        print()

        # Step 1: Create Users
        print("Step 1: Creating users...")
        users_data = [
            {
                "user_id": "u_recep_01",
                "username": "receptionist1",
                "password": "recep123",
                "role": "receptionist",
                "active": True,
            },
            {
                "user_id": "u_doc_01",
                "username": "doctor1",
                "password": "doc123",
                "role": "doctor",
                "active": True,
            },
            {
                "user_id": "u_nurse_01",
                "username": "nurse1",
                "password": "nurse123",
                "role": "nurse",
                "active": True,
            },
            {
                "user_id": "u_nurse_02",
                "username": "nurse2",
                "password": "nurse123",
                "role": "nurse",
                "active": True,
            },
            {
                "user_id": "u_cleaner_01",
                "username": "cleaner1",
                "password": "clean123",
                "role": "cleaner",
                "active": True,
            },
            {
                "user_id": "u_cleaner_02",
                "username": "cleaner2",
                "password": "clean123",
                "role": "cleaner",
                "active": True,
            },
        ]

        for user in users_data:
            db.collection("users").document(user["user_id"]).set(user)
            print(
                f"  ✓ Created {user['role']}: {user['username']} (ID: {user['user_id']})"
            )

        print(f"\n✓ Created {len(users_data)} users")

        # Step 2: Create Beds
        print("\nStep 2: Creating beds...")
        beds_data = [
            # ICU Beds
            {
                "bed_id": "bed_icu_01",
                "ward": "ICU",
                "features": ["oxygen", "monitor", "ventilator"],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_icu_02",
                "ward": "ICU",
                "features": ["oxygen", "monitor", "ventilator"],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_icu_03",
                "ward": "ICU",
                "features": ["oxygen", "monitor"],
                "occupied": False,
                "current_patient_id": None,
            },
            # General Ward Beds
            {
                "bed_id": "bed_gen_01",
                "ward": "General",
                "features": ["oxygen"],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_gen_02",
                "ward": "General",
                "features": ["oxygen"],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_gen_03",
                "ward": "General",
                "features": [],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_gen_04",
                "ward": "General",
                "features": [],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_gen_05",
                "ward": "General",
                "features": ["monitor"],
                "occupied": False,
                "current_patient_id": None,
            },
            # Private Rooms
            {
                "bed_id": "bed_pvt_01",
                "ward": "Private",
                "features": ["oxygen", "monitor"],
                "occupied": False,
                "current_patient_id": None,
            },
            {
                "bed_id": "bed_pvt_02",
                "ward": "Private",
                "features": ["oxygen", "monitor"],
                "occupied": False,
                "current_patient_id": None,
            },
        ]

        for bed in beds_data:
            db.collection("beds").document(bed["bed_id"]).set(bed)
            features_str = ", ".join(bed["features"]) if bed["features"] else "Standard"
            print(f"  ✓ Created bed {bed['bed_id']} in {bed['ward']} ({features_str})")

        print(f"\n✓ Created {len(beds_data)} beds")

        # Step 3: Create Sample Patients
        print("\nStep 3: Creating sample patients...")
        patients_data = [
            {
                "patient_id": "patient_001",
                "name": "John Doe",
                "age": 52,
                "gender": "male",
                "medical_history": ["diabetes", "hypertension"],
                "special_needs": ["wheelchair"],
                "status": "created",
                "created_by": "u_recep_01",
                "created_at": firestore.SERVER_TIMESTAMP,
                "admission": None,
            },
            {
                "patient_id": "patient_002",
                "name": "Jane Smith",
                "age": 38,
                "gender": "female",
                "medical_history": ["asthma"],
                "special_needs": [],
                "status": "created",
                "created_by": "u_recep_01",
                "created_at": firestore.SERVER_TIMESTAMP,
                "admission": None,
            },
            {
                "patient_id": "patient_003",
                "name": "Robert Johnson",
                "age": 65,
                "gender": "male",
                "medical_history": ["heart disease", "diabetes"],
                "special_needs": ["oxygen support"],
                "status": "created",
                "created_by": "u_recep_01",
                "created_at": firestore.SERVER_TIMESTAMP,
                "admission": None,
            },
        ]

        for patient in patients_data:
            db.collection("patients").document(patient["patient_id"]).set(patient)
            print(
                f"  ✓ Created patient: {patient['name']} (ID: {patient['patient_id']})"
            )

        print(f"\n✓ Created {len(patients_data)} sample patients")

        # Step 4: Create event_logs collection (for agent decisions)
        print("\nStep 4: Creating event_logs collection...")
        db.collection("event_logs").document("init").set(
            {
                "timestamp": firestore.SERVER_TIMESTAMP,
                "event": "database_initialized",
                "message": "CareFlow Nexus database initialized successfully",
            }
        )
        print("  ✓ Event logs collection created")

        print("\n" + "=" * 60)
        print("✅ DATABASE INITIALIZATION COMPLETE")
        print("=" * 60)
        print("\nDatabase Summary:")
        print(f"  - Users: {len(users_data)}")
        print(f"  - Beds: {len(beds_data)}")
        print(f"  - Sample Patients: {len(patients_data)}")
        print(f"  - Tasks: 0 (will be created by agents)")
        print("\nCollections Created:")
        print("  ✓ users")
        print("  ✓ patients")
        print("  ✓ beds")
        print("  ✓ tasks (empty)")
        print("  ✓ event_logs")

        print("\n" + "=" * 60)
        print("LOGIN CREDENTIALS")
        print("=" * 60)
        print("\nReceptionist:")
        print("  Username: receptionist1 | Password: recep123")
        print("\nDoctor:")
        print("  Username: doctor1 | Password: doc123")
        print("\nNurse:")
        print("  Username: nurse1 | Password: nurse123")
        print("  Username: nurse2 | Password: nurse123")
        print("\nCleaner:")
        print("  Username: cleaner1 | Password: clean123")
        print("  Username: cleaner2 | Password: clean123")
        print("\n" + "=" * 60)

        print("\n✅ You can now run the agents with: python main.py")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        return False


if __name__ == "__main__":
    # Get service account path from command line or use default
    if len(sys.argv) > 1:
        service_account_path = sys.argv[1]
    else:
        service_account_path = "./config/serviceAccountKey.json"

    print(f"\nUsing service account: {service_account_path}\n")

    success = initialize_database(service_account_path)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
