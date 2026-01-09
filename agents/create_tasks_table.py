#!/usr/bin/env python3
"""
Create Tasks Collection in Firestore
Simple script to initialize the tasks table/collection
"""

import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred_path = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "./config/serviceAccountKey.json"
)
cred = credentials.Certificate(cred_path)

# Check if already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


def create_tasks_collection():
    """Create tasks collection with sample document"""

    print("Creating 'tasks' collection in Firestore...")

    # Create a sample task to initialize the collection
    sample_task = {
        "task_id": "task_sample",
        "type": "cleaning",
        "role": "cleaner",
        "patient_id": "patient_001",
        "bed_id": "bed_101",
        "assigned_to": "user_001",
        "status": "assigned",
        "created_at": datetime.now(),
        "completed_at": None,
    }

    # Create the collection by adding a document
    db.collection("tasks").document("task_sample").set(sample_task)

    print("✓ Tasks collection created successfully!")
    print(f"✓ Sample task added: {sample_task['task_id']}")

    # Verify it was created
    doc = db.collection("tasks").document("task_sample").get()
    if doc.exists:
        print("✓ Verification: Collection exists and is accessible")
    else:
        print("✗ Error: Could not verify collection creation")


if __name__ == "__main__":
    create_tasks_collection()
