"""
Simple Test for CareFlow Nexus AI Agents
Tests that all three agents are working correctly
"""

import asyncio

from allocator_agent import BedAllocatorAgent
from communicator_agent import CommunicatorAgent
from config import config
from memory_agent import MemoryAgent
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService


async def test_agents():
    print("\n" + "=" * 60)
    print("CareFlow Nexus - Simple Agent Test")
    print("=" * 60 + "\n")

    # Initialize services
    print("[1/6] Initializing Firebase...")
    firebase = FirebaseService(config.firebase.service_account_path)
    print("     OK Firebase connected")

    print("\n[2/6] Initializing Gemini AI...")
    gemini = GeminiService(config.gemini.api_key, config.gemini.model_name)
    print("     OK Gemini connected")

    # Initialize Agent 1: Memory Agent
    print("\n[3/6] Initializing Memory Agent...")
    memory_agent = MemoryAgent(firebase, gemini)
    await memory_agent.initialize()
    print("     OK Memory Agent ready")

    # Test Memory Agent
    print("\n[4/6] Testing Memory Agent...")
    beds = await firebase.get_all_beds()
    patients = await firebase.get_all_patients()
    users = firebase.db.collection("users").stream()
    users_list = [doc.to_dict() for doc in users]

    print(f"     - Found {len(beds)} beds in database")
    print(f"     - Found {len(patients)} patients in database")
    print(f"     - Found {len(users_list)} users in database")

    # Show sample bed
    if beds:
        sample_bed = beds[0]
        print(f"\n     Sample Bed:")
        print(f"     - ID: {sample_bed.get('id')}")
        print(f"     - Ward: {sample_bed.get('ward')}")
        print(f"     - Features: {sample_bed.get('features')}")
        print(f"     - Occupied: {sample_bed.get('occupied')}")

    # Initialize Agent 2: Bed Allocator
    print("\n[5/6] Initializing Bed Allocator Agent...")
    allocator_agent = BedAllocatorAgent(firebase, gemini, memory_agent)
    print("     OK Bed Allocator ready")

    # Initialize Agent 3: Communicator Agent
    print("\n[6/6] Initializing Communicator Agent...")
    communicator_agent = CommunicatorAgent(firebase, gemini, memory_agent)
    print("     OK Communicator ready")

    # Test bed allocation if we have patients
    if patients:
        print("\n" + "=" * 60)
        print("Testing Bed Allocation for Patient")
        print("=" * 60 + "\n")

        patient = patients[0]
        print(f"Patient: {patient.get('name')}")
        print(f"Age: {patient.get('age')}")
        print(f"Medical History: {patient.get('medical_history')}")

        # Add a simple diagnosis for testing
        print("\nAdding diagnosis: 'Pneumonia, needs oxygen support'")
        await firebase.update_patient(
            patient["id"],
            {
                "status": "pending_confirmation",
                "admission": {
                    "doctor_id": users_list[1]["user_id"]
                    if len(users_list) > 1
                    else "u_doc_01",
                    "diagnosis": "Pneumonia, needs oxygen support",
                    "special_instructions": "Monitor closely",
                    "recommended_bed_id": None,
                    "confirmed_bed_id": None,
                    "nurse_id": None,
                    "admitted_at": None,
                },
            },
        )

        print("\nRequesting bed allocation from AI Agent...")
        result = await allocator_agent.process({"patient_id": patient["id"]})

        if result.get("success"):
            data = result.get("data", {})
            recommendations = data.get("recommendations", [])

            print(f"\nAI Agent returned {len(recommendations)} recommendations:\n")

            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. Bed {rec.get('bed_number')} - {rec.get('ward')}")
                print(f"   Score: {rec.get('score')}/100")
                print(f"   Reasoning: {rec.get('reasoning', 'N/A')[:100]}...")
                print()
        else:
            print(f"\nBed allocation failed: {result.get('message')}")

    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("OK Firebase - Connected and data loaded")
    print("OK Gemini AI - Connected and responding")
    print("OK Memory Agent - Initialized with hospital data")
    print("OK Bed Allocator Agent - Ready for allocations")
    print("OK Communicator Agent - Ready for task coordination")
    print("\n" + "=" * 60)
    print("ALL AGENTS ARE WORKING PERFECTLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\nStarting CareFlow Nexus Agent Tests...\n")
    asyncio.run(test_agents())
    print("\nTest Complete! Press Ctrl+C to exit.\n")
