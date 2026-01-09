# Database Initialization Guide

## Overview

This guide explains how to initialize the CareFlow Healthcare System database with sample data including nurses, cleaners, beds, and departments.

## Prerequisites

1. Python environment with dependencies installed
2. Firebase project configured
3. `FIREBASE_CRED_PATH` environment variable set in `.env` file

## Database Collections

The initialization script creates the following collections:

### 1. **Departments** (8 departments)
- ICU (Intensive Care Unit)
- ER (Emergency Room)
- Surgery Ward
- Pediatrics
- General Ward
- Maternity Ward
- Oncology
- Cardiology

### 2. **Nurses** (10 nurses with detailed profiles)

Each nurse has:
- **Personal Info**: Name, age, gender, contact details
- **Experience**: Years of experience (ranging from 3 to 30 years)
- **Specialties**: Specific areas of expertise (e.g., "ICU", "Critical Care", "Trauma")
- **Certifications**: Professional certifications (e.g., "RN", "CCRN", "ACLS")
- **Skills**: Numerical ratings (0-100) for various nursing skills
- **Department**: Primary department assignment
- **Shift Preference**: Day, night, or rotating
- **Languages**: Languages spoken
- **Availability**: Days of the week available
- **Patient Capacity**: Maximum patients they can handle

#### Example Nurses:
- **Sarah Johnson**: 22 years experience, ICU specialist, veteran nurse
- **Michael Chen**: 15 years experience, ER specialist, trauma expert
- **Emily Martinez**: 30 years experience, pediatric nurse with exceptional skills
- **Maria Rodriguez**: 3 years experience, recent graduate, general care

### 3. **Cleaners** (10 cleaners with detailed profiles)

Each cleaner has:
- **Personal Info**: Name, age, gender, contact details
- **Experience**: Years of experience (ranging from 2 to 25 years)
- **Specialties**: Specific cleaning expertise (e.g., "ICU Cleaning", "OR Sterilization")
- **Certifications**: Professional certifications (e.g., "Healthcare Environmental Services")
- **Skills**: Numerical ratings (0-100) for various cleaning skills
- **Clearance Level**: "standard" or "high_risk" for specialized areas
- **Equipment Certified**: Specialized equipment they can operate
- **Department Expertise**: Departments they're trained for
- **Average Room Time**: Minutes required per room
- **Max Tasks**: Maximum tasks per shift

#### Example Cleaners:
- **John Smith**: 18 years experience, ICU specialist, infection control expert
- **Patricia Brown**: 14 years experience, OR specialist, surgical suite sterilization
- **Carlos Garcia**: 11 years experience, ER specialist, rapid turnover expert
- **Linda Martinez**: 2 years experience, general cleaning, recent hire

### 4. **Doctors** (5 doctors)
- Specialized in: Cardiology, Emergency Medicine, Pediatrics, Surgery, Oncology

### 5. **Receptionists** (3 receptionists)
- Day and night shift coverage

### 6. **Beds** (20 beds)
- Different types: ICU, ER, Surgery, Pediatric, Maternity, Oncology, Cardiology, General
- Each with specific features and equipment
- Distributed across departments

### 7. **Shifts** (3 shifts)
- Day Shift: 07:00 - 15:00
- Evening Shift: 15:00 - 23:00
- Night Shift: 23:00 - 07:00

## Running the Script

### Step 1: Navigate to Backend Directory
```bash
cd careflow-gdg/CareFlowNexus/backend
```

### Step 2: Activate Virtual Environment (if using one)
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Run the Initialization Script
```bash
python init_database.py
```

### Step 4: Confirm Initialization
When prompted, type `yes` to confirm:
```
This will clear and reinitialize the database. Continue? (yes/no): yes
```

## Default Credentials

### Doctors
- **Username**: `dr.smith` | **Password**: `doc123` | **Specialty**: Cardiology
- **Username**: `dr.jones` | **Password**: `doc123` | **Specialty**: Emergency Medicine
- **Username**: `dr.patel` | **Password**: `doc123` | **Specialty**: Pediatrics
- **Username**: `dr.wong` | **Password**: `doc123` | **Specialty**: Surgery
- **Username**: `dr.kumar` | **Password**: `doc123` | **Specialty**: Oncology

### Nurses
- **Username**: `sarah.johnson` | **Password**: `nurse123` | **Department**: ICU (22 years exp)
- **Username**: `michael.chen` | **Password**: `nurse123` | **Department**: ER (15 years exp)
- **Username**: `emily.martinez` | **Password**: `nurse123` | **Department**: Pediatrics (30 years exp)
- **Username**: `david.oconnor` | **Password**: `nurse123` | **Department**: Surgery (8 years exp)
- **Username**: `priya.patel` | **Password**: `nurse123` | **Department**: General (6 years exp)
- **Username**: `jennifer.williams` | **Password**: `nurse123` | **Department**: Maternity (18 years exp)
- **Username**: `robert.thompson` | **Password**: `nurse123` | **Department**: Oncology (24 years exp)
- **Username**: `lisa.nguyen` | **Password**: `nurse123` | **Department**: Cardiology (12 years exp)
- **Username**: `james.anderson` | **Password**: `nurse123` | **Department**: General (7 years exp)
- **Username**: `maria.rodriguez` | **Password**: `nurse123` | **Department**: General (3 years exp)

### Cleaners
- **Username**: `john.smith` | **Password**: `clean123` | **Specialty**: ICU (18 years exp)
- **Username**: `patricia.brown` | **Password**: `clean123` | **Specialty**: OR (14 years exp)
- **Username**: `carlos.garcia` | **Password**: `clean123` | **Specialty**: ER (11 years exp)
- **Username**: `susan.lee` | **Password**: `clean123` | **Specialty**: Pediatrics (7 years exp)
- **Username**: `thomas.wilson` | **Password**: `clean123` | **Specialty**: General (25 years exp)
- **Username**: `angela.davis` | **Password**: `clean123` | **Specialty**: Maternity (9 years exp)
- **Username**: `raymond.kim` | **Password**: `clean123` | **Specialty**: Oncology (5 years exp)
- **Username**: `michelle.taylor` | **Password**: `clean123` | **Specialty**: Cardiology (8 years exp)
- **Username**: `robert.jackson` | **Password**: `clean123` | **Specialty**: Isolation (20 years exp)
- **Username**: `linda.martinez` | **Password**: `clean123` | **Specialty**: General (2 years exp)

### Receptionists
- **Username**: `anna.white` | **Password**: `rec123` | **Shift**: Day
- **Username**: `tom.brown` | **Password**: `rec123` | **Shift**: Night
- **Username**: `sarah.green` | **Password**: `rec123` | **Department**: ER Reception

## AI Agent Usage

The detailed profiles enable AI agents to make intelligent decisions:

### Nurse Agent Benefits
- Match patients with nurses based on **specialty** (e.g., ICU patient → ICU nurse)
- Consider **experience level** for complex cases
- Check **skill ratings** for specific requirements
- Verify **language compatibility** for non-English speakers
- Respect **availability** and **current patient load**
- Factor in **certifications** for specialized care

### Cleaner Agent Benefits
- Assign cleaners based on **department expertise** (e.g., ICU room → ICU specialist)
- Match **clearance level** for high-risk areas
- Consider **specialties** (e.g., OR cleaning, hazmat)
- Check **equipment certification** for specialized tools
- Optimize based on **average room time**
- Balance workload with **max tasks per shift**
- Respect **availability** and **shift preferences**

## Example Agent Decision Logic

### For Nurse Assignment:
```
Patient: ICU admission, ventilator needed, Spanish-speaking
Best Match: Sarah Johnson
Reasons:
- ICU specialty (95 skill rating)
- Ventilator management expertise
- Speaks Spanish
- 22 years experience
- Currently below max patient capacity
```

### For Cleaner Assignment:
```
Room: ICU bed post-discharge, requires sterilization
Best Match: John Smith
Reasons:
- ICU cleaning specialty (95 skill rating)
- High-risk clearance
- Infection control certified
- 18 years experience
- Currently below max tasks
- Certified on required equipment
```

## Database Schema

### User Collection Fields (Nurses)
```json
{
  "user_id": "string",
  "username": "string",
  "password": "string",
  "role": "nurse",
  "name": "string",
  "email": "string",
  "phone": "string",
  "active": boolean,
  "age": number,
  "gender": "string",
  "experience_years": number,
  "specialties": ["array of strings"],
  "certifications": ["array of strings"],
  "skills": {
    "skill_name": number (0-100)
  },
  "department": "string",
  "shift_preference": "string",
  "languages": ["array of strings"],
  "notes": "string",
  "availability": {
    "monday": boolean,
    "tuesday": boolean,
    ...
  },
  "max_patients": number,
  "current_patients": number
}
```

### User Collection Fields (Cleaners)
```json
{
  "user_id": "string",
  "username": "string",
  "password": "string",
  "role": "cleaner",
  "name": "string",
  "email": "string",
  "phone": "string",
  "active": boolean,
  "age": number,
  "gender": "string",
  "experience_years": number,
  "specialties": ["array of strings"],
  "certifications": ["array of strings"],
  "skills": {
    "skill_name": number (0-100)
  },
  "clearance_level": "standard" | "high_risk",
  "equipment_certified": ["array of strings"],
  "department_expertise": ["array of strings"],
  "shift_preference": "string",
  "languages": ["array of strings"],
  "notes": "string",
  "availability": {
    "monday": boolean,
    ...
  },
  "average_room_time": number (minutes),
  "current_tasks": number,
  "max_tasks_per_shift": number
}
```

## Troubleshooting

### Error: "FIREBASE_CRED_PATH is not set"
**Solution**: Create a `.env` file in the backend directory with:
```
FIREBASE_CRED_PATH=path/to/serviceAccountKey.json
```

### Error: Permission denied on Firebase
**Solution**: Check that your Firebase service account has proper permissions

### Warning: Collections already exist
**Solution**: The script will prompt you to confirm deletion before proceeding

## Next Steps

After initialization:
1. Start the backend server: `uvicorn app.main:app --reload`
2. Test authentication with provided credentials
3. Use the frontend to interact with the system
4. Monitor how AI agents use the detailed profiles for decision-making

## Notes

- **Security Warning**: Default passwords are for development only. Change them in production.
- **Data Persistence**: This script overwrites existing data. Backup before running in production.
- **Customization**: Edit the script to add more users or modify profiles as needed.
- **Skill Ratings**: Ratings are 0-100, with 90+ indicating expert level.