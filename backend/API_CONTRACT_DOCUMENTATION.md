# CareFlow Healthcare System - API Contract Documentation

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Date:** January 2026

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Patient Management Endpoints](#patient-management-endpoints)
3. [Admission & Discharge Endpoints](#admission--discharge-endpoints)
4. [Task Management Endpoints](#task-management-endpoints)
5. [Admin Endpoints](#admin-endpoints)
6. [Response Codes](#response-codes)
7. [Data Models](#data-models)

---

## Authentication Endpoints

### 1. Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and retrieve user credentials

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (Success - 200):**
```json
{
  "user_id": "string",
  "role": "string"
}
```

**Response (Error - 401):**
```json
{
  "detail": "Invalid credentials"
}
```

**Available Roles:**
- `doctor`
- `nurse`
- `cleaner`
- `receptionist`
- `admin`

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dr.smith","password":"doc123"}'
```

---

## Patient Management Endpoints

### 2. Create Patient

**Endpoint:** `POST /patients`

**Description:** Create a new patient record (Receptionist only)

**Request Body:**
```json
{
  "user_id": "string",
  "name": "string",
  "age": "integer",
  "gender": "string",
  "medical_history": ["string"],
  "special_needs": ["string"]
}
```

**Response (Success - 200):**
```json
{
  "patient_id": "uuid",
  "status": "created"
}
```

**Required Role:** `receptionist`

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "rec_001",
    "name": "John Doe",
    "age": 45,
    "gender": "male",
    "medical_history": ["diabetes", "hypertension"],
    "special_needs": ["wheelchair access"]
  }'
```

---

### 3. List Patients

**Endpoint:** `GET /patients?user_id={user_id}`

**Description:** Get list of patients based on user role

**Query Parameters:**
| Parameter | Type   | Required | Description           |
|-----------|--------|----------|-----------------------|
| user_id   | string | Yes      | ID of requesting user |

**Response (Success - 200):**
```json
[
  {
    "patient_id": "uuid",
    "name": "string",
    "age": "integer",
    "gender": "string",
    "status": "string",
    "medical_history": ["string"],
    "special_needs": ["string"],
    "created_at": "datetime",
    "admission": {
      "diagnosis": "string",
      "special_instructions": "string",
      "confirmed_bed_id": "string",
      "assigned_nurse_id": "string"
    }
  }
]
```

**Role-Based Filtering:**
- **Receptionist:** See all patients
- **Doctor:** See patients with status `created` or `admitted`
- **Nurse:** See patients assigned to them

**Example:**
```bash
curl "http://localhost:8000/api/v1/patients?user_id=rec_001"
```

---

## Admission & Discharge Endpoints

### 4. Admit Patient

**Endpoint:** `POST /patients/{patient_id}/admission`

**Description:** Admit a patient and trigger bed assignment agent (Doctor only)

**Path Parameters:**
| Parameter  | Type   | Description       |
|------------|--------|-------------------|
| patient_id | string | UUID of patient   |

**Request Body:**
```json
{
  "user_id": "string",
  "diagnosis": "string",
  "special_instructions": "string"
}
```

**Response (Success - 200):**
```json
{
  "recommended_bed_id": "string",
  "status": "pending_confirmation",
  "reason": "string",
  "suggestion": "string"
}
```

**Required Role:** `doctor`

**AI Agent Called:** Bed Assignment Agent

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/admission \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "doc_001",
    "diagnosis": "Acute myocardial infarction",
    "special_instructions": "Requires cardiac monitoring"
  }'
```

---

### 5. Confirm Bed

**Endpoint:** `POST /patients/{patient_id}/confirm-bed`

**Description:** Confirm bed assignment and trigger cleaner agent (Receptionist only)

**Path Parameters:**
| Parameter  | Type   | Description       |
|------------|--------|-------------------|
| patient_id | string | UUID of patient   |

**Request Body:**
```json
{
  "user_id": "string",
  "bed_id": "string",
  "confirm": "boolean"
}
```

**Response (Success - 200):**
```json
{
  "status": "bed_confirmed",
  "message": "Bed confirmed. Cleaner assigned for preparation.",
  "assigned_cleaner_id": "string",
  "next_step": "string"
}
```

**Required Role:** `receptionist`

**AI Agent Called:** Cleaner Assignment Agent (pre-admission cleaning)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/confirm-bed \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "rec_001",
    "bed_id": "bed_015",
    "confirm": true
  }'
```

---

### 6. Request Discharge

**Endpoint:** `POST /patients/{patient_id}/discharge`

**Description:** Request patient discharge and trigger nurse agent (Doctor only)

**Path Parameters:**
| Parameter  | Type   | Description       |
|------------|--------|-------------------|
| patient_id | string | UUID of patient   |

**Request Body:**
```json
{
  "user_id": "string",
  "discharge_notes": "string"
}
```

**Response (Success - 200):**
```json
{
  "status": "discharge_requested",
  "assigned_nurse_id": "string"
}
```

**Required Role:** `doctor`

**AI Agent Called:** Nurse Assignment Agent (discharge preparation)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/patients/abc123/discharge \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "doc_001",
    "discharge_notes": "Patient stable, cleared for discharge"
  }'
```

---

## Task Management Endpoints

### 7. Get Tasks

**Endpoint:** `GET /tasks?user_id={user_id}`

**Description:** Get tasks assigned to a specific user (Nurse/Cleaner only)

**Query Parameters:**
| Parameter | Type   | Required | Description           |
|-----------|--------|----------|-----------------------|
| user_id   | string | Yes      | ID of nurse or cleaner|

**Response (Success - 200):**
```json
[
  {
    "task_id": "uuid",
    "type": "string",
    "status": "string",
    "role": "string",
    "patient_id": "uuid",
    "bed_id": "string",
    "assigned_to": "string",
    "created_at": "datetime",
    "completed_at": "datetime",
    "notes": "string"
  }
]
```

**Task Types:**
- `cleaning` - Pre-admission or post-discharge cleaning
- `patient_care` - Nurse patient care after bed preparation
- `discharge_nursing` - Discharge preparation by nurse

**Task Statuses:**
- `assigned` - Task created, not yet accepted
- `accepted` - Task accepted by staff member
- `completed` - Task completed

**Required Role:** `nurse` or `cleaner`

**Example:**
```bash
curl "http://localhost:8000/api/v1/tasks?user_id=nurse_001"
```

---

### 8. Accept Task

**Endpoint:** `POST /tasks/{task_id}/accept`

**Description:** Accept an assigned task (Nurse/Cleaner only)

**Path Parameters:**
| Parameter | Type   | Description    |
|-----------|--------|----------------|
| task_id   | string | UUID of task   |

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Response (Success - 200):**
```json
{
  "status": "accepted"
}
```

**Required Role:** `nurse` or `cleaner` (must be assigned to the task)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/task123/accept \
  -H "Content-Type: application/json" \
  -d '{"user_id": "nurse_001"}'
```

---

### 9. Complete Task

**Endpoint:** `POST /tasks/{task_id}/complete`

**Description:** Complete a task and trigger next workflow step (Nurse/Cleaner only)

**Path Parameters:**
| Parameter | Type   | Description    |
|-----------|--------|----------------|
| task_id   | string | UUID of task   |

**Request Body:**
```json
{
  "user_id": "string",
  "notes": "string"
}
```

**Response (Success - 200):**

**For Pre-Admission Cleaning:**
```json
{
  "status": "completed",
  "assigned_nurse_id": "string",
  "message": "Bed prepared. Nurse assigned for patient care."
}
```

**For Patient Care:**
```json
{
  "status": "completed"
}
```

**For Discharge Nursing:**
```json
{
  "status": "completed"
}
```

**Required Role:** `nurse` or `cleaner` (must be assigned to the task)

**AI Agents Triggered:**
- **Pre-admission cleaning completion** → Nurse Assignment Agent
- **Discharge nursing completion** → Cleaner Assignment Agent (post-discharge)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/task123/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "cleaner_001",
    "notes": "Room cleaned and sterilized"
  }'
```

---

## Admin Endpoints

### 10. Get All Beds

**Endpoint:** `GET /admin/beds?user_id={user_id}`

**Description:** Get all beds and their current status (Admin only)

**Query Parameters:**
| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| user_id   | string | Yes      | Admin user ID  |

**Response (Success - 200):**
```json
[
  {
    "bed_id": "string",
    "ward": "string",
    "features": ["string"],
    "occupied": "boolean",
    "current_patient_id": "string"
  }
]
```

**Required Role:** `admin`

**Example:**
```bash
curl "http://localhost:8000/api/v1/admin/beds?user_id=admin_001"
```

---

### 11. Get All Tasks

**Endpoint:** `GET /admin/tasks?user_id={user_id}`

**Description:** Get all tasks in the system (Admin only)

**Query Parameters:**
| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| user_id   | string | Yes      | Admin user ID  |

**Response (Success - 200):**
```json
[
  {
    "task_id": "string",
    "type": "string",
    "role": "string",
    "patient_id": "string",
    "bed_id": "string",
    "assigned_to": "string",
    "status": "string",
    "created_at": "datetime"
  }
]
```

**Required Role:** `admin`

**Example:**
```bash
curl "http://localhost:8000/api/v1/admin/tasks?user_id=admin_001"
```

---

### 12. Get All Nurses

**Endpoint:** `GET /admin/nurses?user_id={user_id}`

**Description:** Get all nurses with detailed profiles (Admin only)

**Query Parameters:**
| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| user_id   | string | Yes      | Admin user ID  |

**Response (Success - 200):**
```json
[
  {
    "user_id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "active": "boolean",
    "age": "integer",
    "gender": "string",
    "experience_years": "integer",
    "specialties": ["string"],
    "certifications": ["string"],
    "skills": {
      "critical_care": "integer (0-100)",
      "emergency_response": "integer (0-100)",
      "patient_monitoring": "integer (0-100)",
      "medication_administration": "integer (0-100)"
    },
    "department": "string",
    "shift_preference": "string",
    "languages": ["string"],
    "max_patients": "integer",
    "current_patients": "integer",
    "availability": {
      "monday": "boolean",
      "tuesday": "boolean",
      "wednesday": "boolean",
      "thursday": "boolean",
      "friday": "boolean",
      "saturday": "boolean",
      "sunday": "boolean"
    },
    "notes": "string"
  }
]
```

**Required Role:** `admin`

**Example:**
```bash
curl "http://localhost:8000/api/v1/admin/nurses?user_id=admin_001"
```

**Sample Response:**
```json
[
  {
    "user_id": "nurse_001",
    "name": "Sarah Johnson",
    "email": "sarah.johnson@careflow.com",
    "phone": "+1-555-0101",
    "active": true,
    "age": 45,
    "gender": "female",
    "experience_years": 22,
    "specialties": ["ICU", "Critical Care", "Ventilator Management"],
    "certifications": ["RN", "CCRN", "ACLS", "BLS"],
    "skills": {
      "critical_care": 95,
      "emergency_response": 90,
      "patient_monitoring": 95,
      "medication_administration": 92,
      "wound_care": 85,
      "iv_therapy": 93
    },
    "department": "ICU",
    "shift_preference": "day",
    "languages": ["English", "Spanish"],
    "max_patients": 4,
    "current_patients": 2,
    "availability": {
      "monday": true,
      "tuesday": true,
      "wednesday": true,
      "thursday": true,
      "friday": true,
      "saturday": false,
      "sunday": false
    },
    "notes": "Veteran ICU nurse with extensive experience"
  }
]
```

---

### 13. Get All Cleaners

**Endpoint:** `GET /admin/cleaners?user_id={user_id}`

**Description:** Get all cleaners with detailed profiles (Admin only)

**Query Parameters:**
| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| user_id   | string | Yes      | Admin user ID  |

**Response (Success - 200):**
```json
[
  {
    "user_id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "active": "boolean",
    "age": "integer",
    "gender": "string",
    "experience_years": "integer",
    "specialties": ["string"],
    "certifications": ["string"],
    "skills": {
      "icu_cleaning": "integer (0-100)",
      "sterile_technique": "integer (0-100)",
      "isolation_protocols": "integer (0-100)",
      "infection_control": "integer (0-100)"
    },
    "clearance_level": "string",
    "equipment_certified": ["string"],
    "department_expertise": ["string"],
    "shift_preference": "string",
    "languages": ["string"],
    "average_room_time": "integer (minutes)",
    "current_tasks": "integer",
    "max_tasks_per_shift": "integer",
    "availability": {
      "monday": "boolean",
      "tuesday": "boolean",
      "wednesday": "boolean",
      "thursday": "boolean",
      "friday": "boolean",
      "saturday": "boolean",
      "sunday": "boolean"
    },
    "notes": "string"
  }
]
```

**Clearance Levels:**
- `standard` - General cleaning
- `high_risk` - ICU, OR, Isolation rooms

**Required Role:** `admin`

**Example:**
```bash
curl "http://localhost:8000/api/v1/admin/cleaners?user_id=admin_001"
```

**Sample Response:**
```json
[
  {
    "user_id": "cleaner_001",
    "name": "John Smith",
    "email": "john.smith@careflow.com",
    "phone": "+1-555-0201",
    "active": true,
    "age": 43,
    "gender": "male",
    "experience_years": 18,
    "specialties": ["ICU Cleaning", "Sterile Environment", "Isolation Room Protocols"],
    "certifications": ["Healthcare Environmental Services", "Infection Control", "Hazardous Materials"],
    "skills": {
      "icu_cleaning": 95,
      "sterile_technique": 93,
      "isolation_protocols": 94,
      "chemical_handling": 90,
      "equipment_sterilization": 92,
      "infection_control": 95
    },
    "clearance_level": "high_risk",
    "equipment_certified": ["UV sterilizers", "autoclave", "foggers", "electrostatic sprayers"],
    "department_expertise": ["ICU", "ER", "Surgery"],
    "shift_preference": "day",
    "languages": ["English"],
    "average_room_time": 45,
    "current_tasks": 1,
    "max_tasks_per_shift": 8,
    "availability": {
      "monday": true,
      "tuesday": true,
      "wednesday": true,
      "thursday": true,
      "friday": true,
      "saturday": false,
      "sunday": false
    },
    "notes": "Senior ICU cleaner with expert-level knowledge"
  }
]
```

---

## Response Codes

| Code | Status                | Description                           |
|------|-----------------------|---------------------------------------|
| 200  | OK                    | Request successful                    |
| 401  | Unauthorized          | Invalid credentials or missing auth   |
| 403  | Forbidden             | User doesn't have required role       |
| 404  | Not Found             | Resource not found                    |
| 422  | Unprocessable Entity  | Invalid request body/parameters       |
| 500  | Internal Server Error | Server error                          |

---

## Data Models

### Patient Status Flow

```
created → awaiting_bed_confirmation → bed_confirmed → 
bed_prepared → under_care → discharge_requested → 
discharged → bed_available
```

### User Roles

| Role         | Permissions                                          |
|--------------|------------------------------------------------------|
| admin        | View all data, manage system                         |
| receptionist | Create patients, confirm beds, view all patients     |
| doctor       | Admit patients, request discharge                    |
| nurse        | View assigned tasks, complete patient care           |
| cleaner      | View assigned tasks, complete cleaning               |

### Skill Ratings

All skill ratings are integers from 0-100:
- **90-100:** Expert level
- **80-89:** Advanced level
- **70-79:** Proficient level
- **60-69:** Competent level
- **Below 60:** Developing level

---

## AI Agent Integration

### Bed Assignment Agent
**Triggered:** Patient admission  
**Evaluates:** Patient diagnosis, bed features, ward type  
**Returns:** Recommended bed with reasoning

### Cleaner Assignment Agent
**Triggered:** Bed confirmation (pre-admission) or discharge completion (post-discharge)  
**Evaluates:** Experience, specialties, skills, workload, clearance level  
**Returns:** Selected cleaner with reasoning

### Nurse Assignment Agent
**Triggered:** Pre-admission cleaning completion or discharge request  
**Evaluates:** Experience, specialties, certifications, skills, workload, department match  
**Returns:** Selected nurse with reasoning

---

## Complete Workflow Example

```bash
# 1. Login as receptionist
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"anna.white","password":"rec123"}'
# Response: {"user_id":"rec_001","role":"receptionist"}

# 2. Create patient
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"rec_001",
    "name":"Robert Smith",
    "age":62,
    "gender":"male",
    "medical_history":["hypertension"],
    "special_needs":[]
  }'
# Response: {"patient_id":"abc-123","status":"created"}

# 3. Login as doctor
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dr.smith","password":"doc123"}'
# Response: {"user_id":"doc_001","role":"doctor"}

# 4. Admit patient
curl -X POST http://localhost:8000/api/v1/patients/abc-123/admission \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"doc_001",
    "diagnosis":"Acute myocardial infarction",
    "special_instructions":"Requires cardiac monitoring"
  }'
# Response: {"recommended_bed_id":"bed_015","status":"pending_confirmation","reason":"Excellent match"}

# 5. Confirm bed (as receptionist)
curl -X POST http://localhost:8000/api/v1/patients/abc-123/confirm-bed \
  -H "Content-Type: application/json" \
  -d '{"user_id":"rec_001","bed_id":"bed_015","confirm":true}'
# Response: {"status":"bed_confirmed","assigned_cleaner_id":"cleaner_001"}

# 6. Get cleaner tasks
curl "http://localhost:8000/api/v1/tasks?user_id=cleaner_001"
# Response: [{"task_id":"task-456","type":"cleaning","status":"assigned",...}]

# 7. Accept task
curl -X POST http://localhost:8000/api/v1/tasks/task-456/accept \
  -H "Content-Type: application/json" \
  -d '{"user_id":"cleaner_001"}'
# Response: {"status":"accepted"}

# 8. Complete cleaning
curl -X POST http://localhost:8000/api/v1/tasks/task-456/complete \
  -H "Content-Type: application/json" \
  -d '{"user_id":"cleaner_001","notes":"Room cleaned and sterilized"}'
# Response: {"status":"completed","assigned_nurse_id":"nurse_001"}

# 9. Get nurse tasks
curl "http://localhost:8000/api/v1/tasks?user_id=nurse_001"
# Response: [{"task_id":"task-789","type":"patient_care","status":"assigned",...}]

# 10. Complete patient care
curl -X POST http://localhost:8000/api/v1/tasks/task-789/accept \
  -H "Content-Type: application/json" \
  -d '{"user_id":"nurse_001"}'

curl -X POST http://localhost:8000/api/v1/tasks/task-789/complete \
  -H "Content-Type: application/json" \
  -d '{"user_id":"nurse_001","notes":"Patient stable, vitals normal"}'
# Response: {"status":"completed"}

# Patient is now under care!
```

---

## Authentication Credentials

### Admin Users
- **Username:** `admin` | **Password:** `admin123` | **Role:** admin
- **Username:** `supervisor` | **Password:** `admin123` | **Role:** admin

### Doctors
- **Username:** `dr.smith` | **Password:** `doc123` | **Department:** Cardiology
- **Username:** `dr.jones` | **Password:** `doc123` | **Department:** Emergency
- **Username:** `dr.patel` | **Password:** `doc123` | **Department:** Pediatrics
- **Username:** `dr.wong` | **Password:** `doc123` | **Department:** Surgery
- **Username:** `dr.kumar` | **Password:** `doc123` | **Department:** Oncology

### Nurses (10 nurses with varying experience)
- **Username:** `sarah.johnson` | **Password:** `nurse123` | **ICU Specialist (22 years)**
- **Username:** `michael.chen` | **Password:** `nurse123` | **ER Specialist (15 years)**
- **Username:** `emily.martinez` | **Password:** `nurse123` | **Pediatrics (30 years)**
- And 7 more...

### Cleaners (10 cleaners with varying specialties)
- **Username:** `john.smith` | **Password:** `clean123` | **ICU Specialist (18 years)**
- **Username:** `patricia.brown` | **Password:** `clean123` | **OR Specialist (14 years)**
- **Username:** `carlos.garcia` | **Password:** `clean123` | **ER Specialist (11 years)**
- And 7 more...

### Receptionists
- **Username:** `anna.white` | **Password:** `rec123` | **Day Shift**
- **Username:** `tom.brown` | **Password:** `rec123` | **Night Shift**
- **Username:** `sarah.green` | **Password:** `rec123` | **ER Reception**

---

## Security Notes

⚠️ **Important:** All passwords shown are for development/testing only. In production:
- Use proper authentication (JWT, OAuth)
- Hash passwords with bcrypt/argon2
- Implement rate limiting
- Use HTTPS
- Add API keys for admin endpoints
- Implement role-based access control (RBAC)

---

## Support & Contact

For API support or questions:
- **Email:** api-support@careflow.com
- **Documentation:** http://localhost:8000/docs (Swagger UI)
- **Redoc:** http://localhost:8000/redoc

---

**End of API Documentation**