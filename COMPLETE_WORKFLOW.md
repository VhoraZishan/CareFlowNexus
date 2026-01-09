# CareFlow Nexus - Complete Workflow Documentation

**Version:** 2.0 (Specification Compliant)  
**Last Updated:** 2025  
**Status:** ✅ FULLY COMPLIANT WITH SPECIFICATION

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent System Architecture](#agent-system-architecture)
3. [Complete Admission Workflow](#complete-admission-workflow)
4. [Complete Discharge Workflow](#complete-discharge-workflow)
5. [API Reference](#api-reference)
6. [Testing Guide](#testing-guide)

---

## Overview

CareFlow Nexus implements a **4-agent system** for hospital bed management:

| Agent | Purpose | When Called |
|-------|---------|-------------|
| **Bed Agent** | Recommend optimal bed | Doctor requests admission |
| **Cleaner Agent** | Assign cleaner for bed prep/cleaning | Bed confirmed OR patient discharged |
| **Nurse Agent** | Assign nurse for patient care | Bed prepared OR discharge requested |

**Key Principle:** Agents ONLY return recommendations. Backend handles ALL database writes.

---

## Agent System Architecture

```
┌─────────────┐
│  Frontend   │ User interactions
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  Backend    │ Orchestrates workflow, writes to DB
│ (Port 8000) │
└──────┬──────┘
       │ HTTP (recommendations only)
       ▼
┌─────────────┐
│   Agents    │ Pure computation, NO database access
│ (Port 9000) │ Returns: bed_id, cleaner_id, nurse_id
└─────────────┘
```

---

## Complete Admission Workflow

### Phase 1: Patient Registration

**Endpoint:** `POST /api/v1/patients`  
**Role:** Receptionist

```bash
curl -X POST http://localhost:8000/api/v1/patients \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_recep_01",
  "name": "John Doe",
  "age": 52,
  "gender": "male",
  "medical_history": ["diabetes"],
  "special_needs": ["oxygen", "isolation"]
}'
```

**Response:**
```json
{
  "patient_id": "abc123",
  "status": "created"
}
```

**Patient Status:** `"created"`

---

### Phase 2: Doctor Requests Admission

**Endpoint:** `POST /api/v1/patients/{patient_id}/admission`  
**Role:** Doctor

```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/admission \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_doc_01",
  "diagnosis": "Pneumonia",
  "special_instructions": "Needs oxygen + isolation"
}'
```

**What Happens:**
1. Backend fetches patient data
2. Backend fetches available beds
3. **Backend calls BED AGENT** 🤖
   - Agent Input: patient, diagnosis, available beds
   - Agent Output: `recommended_bed_id` + `reason`
4. Backend saves recommendation

**Response:**
```json
{
  "recommended_bed_id": "bed_iso_01",
  "status": "pending_confirmation",
  "reason": "Excellent match for patient requirements. Ward: Isolation."
}
```

**Patient Status:** `"pending_confirmation"`  
**Bed Status:** Still `occupied: false` (not locked yet)

---

### Phase 3: Receptionist Confirms Bed

**Endpoint:** `POST /api/v1/patients/{patient_id}/confirm-bed`  
**Role:** Receptionist

```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/confirm-bed \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_recep_01",
  "bed_id": "bed_iso_01",
  "confirm": true
}'
```

**What Happens:**
1. Backend locks the bed (`occupied: true`)
2. Backend updates patient status
3. Backend fetches available cleaners
4. **Backend calls CLEANER AGENT** 🤖 (context: `"pre_admission"`)
   - Agent Input: bed_id, available cleaners, context
   - Agent Output: `selected_cleaner_id` + `reason`
5. Backend creates **cleaning task** for cleaner
6. Backend assigns task to cleaner

**Response:**
```json
{
  "status": "bed_confirmed",
  "message": "Bed confirmed. Cleaner assigned for preparation.",
  "assigned_cleaner_id": "u_cleaner_01",
  "next_step": "Cleaner must prepare bed, then nurse will be assigned"
}
```

**Patient Status:** `"bed_confirmed"`  
**Bed Status:** `occupied: true`  
**Task Created:** Cleaning task (pre-admission) → assigned to cleaner

---

### Phase 4: Cleaner Accepts Task

**Endpoint:** `GET /api/v1/tasks?user_id={cleaner_id}`  
**Role:** Cleaner

```bash
# Get tasks
curl -X GET "http://localhost:8000/api/v1/tasks?user_id=u_cleaner_01"
```

**Response:**
```json
[
  {
    "task_id": "task_123",
    "type": "cleaning",
    "patient_id": "abc123",
    "bed_id": "bed_iso_01",
    "status": "assigned",
    "description": "Pre-admission bed preparation"
  }
]
```

**Cleaner accepts task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_123/accept \
-H "Content-Type: application/json" \
-d '{"user_id": "u_cleaner_01"}'
```

**Task Status:** `"accepted"`

---

### Phase 5: Cleaner Completes Bed Preparation

**Endpoint:** `POST /api/v1/tasks/{task_id}/complete`  
**Role:** Cleaner

```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_123/complete \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_cleaner_01",
  "notes": "Bed cleaned and prepared for isolation patient"
}'
```

**What Happens:**
1. Backend marks cleaning task as complete
2. Backend updates patient status to `"bed_prepared"`
3. Backend fetches available nurses
4. **Backend calls NURSE AGENT** 🤖
   - Agent Input: patient, bed, available nurses
   - Agent Output: `selected_nurse_id` + `reason`
5. Backend creates **patient_care task** for nurse
6. Backend assigns nurse to patient

**Response:**
```json
{
  "status": "completed",
  "assigned_nurse_id": "u_nurse_01",
  "message": "Bed prepared. Nurse assigned for patient care."
}
```

**Patient Status:** `"bed_prepared"`  
**Task Created:** Patient care task → assigned to nurse

---

### Phase 6: Nurse Accepts Patient Care

**Endpoint:** `GET /api/v1/tasks?user_id={nurse_id}`  
**Role:** Nurse

```bash
# Get tasks
curl -X GET "http://localhost:8000/api/v1/tasks?user_id=u_nurse_01"
```

**Response:**
```json
[
  {
    "task_id": "task_456",
    "type": "patient_care",
    "patient_id": "abc123",
    "bed_id": "bed_iso_01",
    "status": "assigned",
    "description": "Admit patient to bed and provide care"
  }
]
```

**Nurse accepts task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_456/accept \
-H "Content-Type: application/json" \
-d '{"user_id": "u_nurse_01"}'
```

**Task Status:** `"accepted"`

---

### Phase 7: Nurse Completes Patient Admission

**Endpoint:** `POST /api/v1/tasks/{task_id}/complete`  
**Role:** Nurse

```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_456/complete \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_nurse_01",
  "notes": "Patient admitted and settled in bed"
}'
```

**What Happens:**
1. Backend marks patient care task as complete
2. Backend updates patient status to `"admitted"`
3. Nurse is now assigned to patient for ongoing care

**Response:**
```json
{
  "status": "completed"
}
```

**Patient Status:** `"admitted"` ✅ **ADMISSION COMPLETE!**  
**Bed Status:** `occupied: true`, assigned to patient  
**Nurse:** Assigned to patient for care

---

## Complete Discharge Workflow

### Phase 8: Doctor Requests Discharge

**Endpoint:** `POST /api/v1/patients/{patient_id}/discharge`  
**Role:** Doctor

```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/discharge \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_doc_01",
  "discharge_notes": "Patient recovered, ready for discharge"
}'
```

**What Happens:**
1. Backend fetches patient and bed info
2. Backend fetches available nurses
3. **Backend calls NURSE AGENT** 🤖
   - Agent Input: patient, bed, available nurses
   - Agent Output: `selected_nurse_id` + `reason`
4. Backend creates **discharge_nursing task**
5. Backend updates patient status

**Response:**
```json
{
  "status": "discharge_requested",
  "assigned_nurse_id": "u_nurse_01"
}
```

**Patient Status:** `"discharge_requested"`  
**Task Created:** Discharge nursing task → assigned to nurse

---

### Phase 9: Nurse Completes Discharge

**Endpoint:** `POST /api/v1/tasks/{task_id}/complete`  
**Role:** Nurse

```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_789/complete \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_nurse_01",
  "notes": "Patient discharged safely with instructions"
}'
```

**What Happens:**
1. Backend marks discharge task as complete
2. Backend updates patient status to `"discharged"`
3. Backend fetches available cleaners
4. **Backend calls CLEANER AGENT** 🤖 (context: `"post_discharge"`)
   - Agent Input: bed_id, available cleaners, context
   - Agent Output: `selected_cleaner_id` + `reason`
5. Backend creates **cleaning task** (post-discharge)

**Response:**
```json
{
  "status": "completed"
}
```

**Patient Status:** `"discharged"`  
**Task Created:** Cleaning task (post-discharge) → assigned to cleaner

---

### Phase 10: Cleaner Completes Post-Discharge Cleaning

**Endpoint:** `POST /api/v1/tasks/{task_id}/complete`  
**Role:** Cleaner

```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_999/complete \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_cleaner_02",
  "notes": "Bed sanitized and ready for next patient"
}'
```

**What Happens:**
1. Backend marks cleaning task as complete
2. Backend frees the bed (`occupied: false`)
3. Bed is now available for next patient

**Response:**
```json
{
  "status": "completed"
}
```

**Bed Status:** `occupied: false` ✅ **BED AVAILABLE AGAIN!**

---

## Complete Workflow Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│ ADMISSION PHASE                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Receptionist creates patient                                 │
│    Status: "created"                                            │
│                                                                 │
│ 2. Doctor requests admission → BED AGENT called                 │
│    Status: "pending_confirmation"                               │
│                                                                 │
│ 3. Receptionist confirms bed → CLEANER AGENT called             │
│    Status: "bed_confirmed"                                      │
│    Context: "pre_admission"                                     │
│    Task: Cleaning (pre-admission)                               │
│                                                                 │
│ 4. Cleaner prepares bed → NURSE AGENT called                    │
│    Status: "bed_prepared"                                       │
│    Task: Patient care                                           │
│                                                                 │
│ 5. Nurse admits patient                                         │
│    Status: "admitted" ✅                                        │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                    (Patient stays)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ DISCHARGE PHASE                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 6. Doctor requests discharge → NURSE AGENT called               │
│    Status: "discharge_requested"                                │
│    Task: Discharge nursing                                      │
│                                                                 │
│ 7. Nurse completes discharge → CLEANER AGENT called             │
│    Status: "discharged"                                         │
│    Context: "post_discharge"                                    │
│    Task: Cleaning (post-discharge)                              │
│                                                                 │
│ 8. Cleaner cleans bed                                           │
│    Bed: occupied = false ✅                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Invocation Summary

| Step | User Action | Agent Called | Agent Context | Task Created |
|------|-------------|--------------|---------------|--------------|
| 2 | Doctor requests admission | **Bed Agent** | - | None |
| 3 | Receptionist confirms bed | **Cleaner Agent** | `pre_admission` | Cleaning (prep) |
| 4 | Cleaner completes prep | **Nurse Agent** | - | Patient care |
| 5 | Nurse admits patient | - | - | None |
| 6 | Doctor requests discharge | **Nurse Agent** | - | Discharge nursing |
| 7 | Nurse completes discharge | **Cleaner Agent** | `post_discharge` | Cleaning (sanitize) |
| 8 | Cleaner completes cleaning | - | - | None |

---

## API Reference

### User Roles

| User ID | Username | Role | Capabilities |
|---------|----------|------|--------------|
| `u_recep_01` | receptionist1 | Receptionist | Create patients, confirm beds |
| `u_doc_01` | doctor1 | Doctor | Request admission, request discharge |
| `u_nurse_01` | nurse1 | Nurse | Complete patient care tasks |
| `u_nurse_02` | nurse2 | Nurse | Complete patient care tasks |
| `u_cleaner_01` | cleaner1 | Cleaner | Complete cleaning tasks |
| `u_cleaner_02` | cleaner2 | Cleaner | Complete cleaning tasks |

### Patient Status Flow

```
created
  ↓
pending_confirmation (bed recommended)
  ↓
bed_confirmed (receptionist confirmed)
  ↓
bed_prepared (cleaner completed prep)
  ↓
admitted (nurse completed admission) ✅
  ↓
discharge_requested (doctor requested)
  ↓
discharged (nurse completed discharge)
```

### Task Types

| Task Type | Created When | Assigned To | Completion Triggers |
|-----------|--------------|-------------|---------------------|
| `cleaning` (pre) | Bed confirmed | Cleaner | Nurse agent called |
| `patient_care` | Bed prepared | Nurse | Patient admitted |
| `discharge_nursing` | Discharge requested | Nurse | Cleaner agent called |
| `cleaning` (post) | Discharge completed | Cleaner | Bed freed |

---

## Testing Guide

### Prerequisites

1. **Start Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

2. **Start Agent Server:**
```bash
cd agents
python agent_server_pure.py
# Runs on port 9000
```

3. **Verify Health:**
```bash
curl http://localhost:8000/health  # Backend
curl http://localhost:9000/health  # Agents
```

---

### Complete Test Sequence

**Save this as `test_workflow.sh`:**

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================"
echo "CareFlow Nexus - Complete Workflow Test"
echo "============================================"

# Step 1: Create patient
echo -e "\n${BLUE}Step 1: Creating patient...${NC}"
PATIENT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/patients \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_recep_01",
  "name": "John Doe",
  "age": 52,
  "gender": "male",
  "medical_history": ["diabetes"],
  "special_needs": ["oxygen", "isolation"]
}')
PATIENT_ID=$(echo $PATIENT_RESPONSE | jq -r '.patient_id')
echo -e "${GREEN}✅ Patient created: $PATIENT_ID${NC}"

# Step 2: Doctor requests admission (Bed Agent)
echo -e "\n${BLUE}Step 2: Doctor requesting admission (Bed Agent)...${NC}"
curl -s -X POST http://localhost:8000/api/v1/patients/$PATIENT_ID/admission \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_doc_01",
  "diagnosis": "Pneumonia",
  "special_instructions": "Needs oxygen + isolation"
}' | jq '.'
echo -e "${GREEN}✅ Bed recommended${NC}"

# Step 3: Receptionist confirms bed (Cleaner Agent - pre_admission)
echo -e "\n${BLUE}Step 3: Receptionist confirming bed (Cleaner Agent - pre_admission)...${NC}"
curl -s -X POST http://localhost:8000/api/v1/patients/$PATIENT_ID/confirm-bed \
-H "Content-Type: application/json" \
-d '{
  "user_id": "u_recep_01",
  "bed_id": "bed_iso_01",
  "confirm": true
}' | jq '.'
echo -e "${GREEN}✅ Bed confirmed, cleaner assigned${NC}"

# Wait for user to complete cleaner task manually
echo -e "\n${BLUE}Step 4: Get cleaner tasks...${NC}"
curl -s -X GET "http://localhost:8000/api/v1/tasks?user_id=u_cleaner_01" | jq '.'

echo -e "\n⏳ Please complete the cleaner task using:"
echo "curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/accept -H 'Content-Type: application/json' -d '{\"user_id\":\"u_cleaner_01\"}'"
echo "curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/complete -H 'Content-Type: application/json' -d '{\"user_id\":\"u_cleaner_01\",\"notes\":\"Bed prepared\"}'"
echo -e "\n${GREEN}This will trigger Nurse Agent and create patient_care task${NC}"

echo -e "\n============================================"
echo "Test workflow initiated successfully!"
echo "Continue manually to complete remaining steps"
echo "============================================"
```

---

## Specification Compliance Checklist

✅ **Bed Agent:**
- Endpoint: `/agent/bed-assignment`
- Called when: Doctor requests admission
- Returns: `recommended_bed_id` + `reason`

✅ **Cleaner Agent:**
- Endpoint: `/agent/cleaner-assignment`
- Called when: Bed confirmed (pre) OR patient discharged (post)
- Context: `"pre_admission"` or `"post_discharge"`
- Returns: `selected_cleaner_id` + `reason`

✅ **Nurse Agent:**
- Endpoint: `/agent/nurse-assignment`
- Called when: Bed prepared (admission) OR discharge requested
- Returns: `selected_nurse_id` + `reason`

✅ **Contract Enforcement:**
- Response keys match exactly
- Null values indicate no recommendation
- Agents never write to database
- Agents are stateless

---

## Status: ✅ FULLY COMPLIANT

**Last Verified:** 2025  
**Specification Version:** 1.0  
**Implementation Version:** 2.0

All agents follow the specification exactly. The workflow implements the complete admission and discharge cycle with proper agent invocations at each step.

**Ready for Production! 🚀**