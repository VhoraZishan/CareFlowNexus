# CareFlow Nexus AI Agents

## Overview

This directory contains the three AI agents that power the CareFlow Nexus hospital bed management system. The agents use a **hybrid approach: 50% rule-based algorithms and 50% AI (Gemini 2.0 Flash)** to make intelligent decisions about bed allocation and task coordination.

---

## 🔌 Backend Integration

### Quick Start

The agents run as a **separate HTTP service** that the backend calls. **No backend code changes required!**

**Step 1: Start Agent Server** (Terminal 1)
```bash
cd agents
# Windows
run_agent_server.bat

# Linux/Mac
./run_agent_server.sh
```

**Step 2: Start Backend** (Terminal 2)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### How It Works

```
Backend (Port 8000) → HTTP Requests → Agent Server (Port 9000)
                                            ↓
                                     AI Agents Process
                                            ↓
                                     Returns Results
```

The backend's `app/services/agents.py` calls these endpoints:
- `POST http://localhost:9000/agent/bed-assignment`
- `POST http://localhost:9000/agent/cleaner-assignment`
- `POST http://localhost:9000/agent/nurse-assignment`

### Configuration

**agents/.env:**
```env
FIREBASE_SERVICE_ACCOUNT_PATH=./config/serviceAccountKey.json
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp
AGENT_SERVER_PORT=9000
```

**backend/.env:**
```env
FIREBASE_CRED_PATH=./config/serviceAccountKey.json
BED_AGENT_URL=http://localhost:9000/agent/bed-assignment
CLEANER_AGENT_URL=http://localhost:9000/agent/cleaner-assignment
NURSE_AGENT_URL=http://localhost:9000/agent/nurse-assignment
```

### Files Added for Integration

- **`agent_server.py`** - HTTP server exposing agent endpoints
- **`run_agent_server.bat`** - Windows startup script
- **`run_agent_server.sh`** - Linux/Mac startup script
- **`../INTEGRATION_GUIDE.md`** - Complete integration guide

### Testing the Integration

1. **Check Agent Server Health:**
   ```bash
   curl http://localhost:9000/health
   ```

2. **View API Documentation:**
   - Agent Server: http://localhost:9000/docs
   - Backend: http://localhost:8000/docs

3. **Test Full Workflow:**
   - Follow the examples in `../INTEGRATION_GUIDE.md`

---

## 🤖 The Three Agents

### **Agent 1: Memory Agent (State Manager)**
**File:** `memory_agent.py`

**Purpose:** Knows everything about the hospital at all times

**Responsibilities:**
- Memorizes all hospital data (beds, patients, staff, tasks)
- Provides fast queries to other agents
- Monitors system state in real-time
- Detects bottlenecks and anomalies (AI-powered)
- Generates state analysis reports (AI-powered)

**Key Methods:**
- `get_available_beds(filters)` - Query available beds
- `get_patient_requirements(patient_id)` - Get patient needs
- `get_staff_availability(role, ward)` - Find available staff
- `analyze_state_with_ai()` - AI-powered state analysis
- `detect_bottlenecks()` - Hybrid bottleneck detection

---

### **Agent 2: Bed Allocator Agent**
**File:** `allocator_agent.py`

**Purpose:** Matches patients to optimal beds

**Responsibilities:**
- Extract patient requirements from diagnosis (AI)
- Score beds using rule-based algorithm (50%)
- Enhance with AI ranking and reasoning (50%)
- Generate top 3 bed recommendations
- Learn from human overrides

**Scoring Breakdown (Rule-Based):**
- Equipment Match: 40 points
- Ward Appropriateness: 25 points
- Proximity to Nursing: 15 points
- Availability: 10 points
- Workload Distribution: 10 points

**Key Methods:**
- `extract_requirements(patient)` - AI extracts medical requirements
- `score_beds_rule_based(beds, requirements)` - Rule-based scoring
- `get_ai_recommendations()` - AI ranking and reasoning
- `combine_scores()` - Hybrid 50/50 combination
- `record_allocation_feedback()` - Learning from overrides

---

### **Agent 3: Communicator Agent (Task Coordinator)**
**File:** `communicator_agent.py`

**Purpose:** Assigns tasks to staff and orchestrates workflows

**Responsibilities:**
- Create tasks for bed assignments, cleaning, etc.
- Assign tasks to optimal staff (rule-based + AI)
- Orchestrate multi-step workflows
- Monitor task progress
- Handle delays and escalations

**Workflow Types:**
1. **bed_assignment:** Cleaning → Bed Prep → Patient Transfer
2. **discharge:** Patient Discharge → Cleaning → Bed Prep
3. **bed_cleaning:** Ad-hoc cleaning request

**Key Methods:**
- `initiate_workflow(type, context)` - Start multi-step workflow
- `create_and_assign_task()` - Create and assign single task
- `assign_optimal_staff()` - Hybrid staff assignment (50/50)
- `check_task_progress()` - Monitor active tasks
- `handle_delayed_task()` - Escalation logic

---

## 🏗️ Architecture

```
agents/
├── services/
│   ├── firebase_service.py       # Firebase Firestore operations
│   └── gemini_service.py         # Gemini AI API integration
├── prompts/
│   └── prompt_templates.py       # All AI prompt templates
├── utils/
│   └── response_parser.py        # Parse and validate AI responses
├── base_agent.py                 # Base class for all agents
├── memory_agent.py               # Agent 1: State Manager
├── allocator_agent.py            # Agent 2: Bed Allocator
├── communicator_agent.py         # Agent 3: Task Coordinator
├── config.py                     # Configuration management
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variables template
```

---

## 🚀 Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- Firebase project with Firestore database
- Google Gemini API key

### 2. Installation

```bash
# Navigate to agents directory
cd careflow-gdg/CareFlowNexus/agents

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=./config/serviceAccountKey.json
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com

# Gemini AI Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Agent Configuration
AGENT_REFRESH_INTERVAL=300
RULE_WEIGHT=0.5
AI_WEIGHT=0.5
MAX_STAFF_WORKLOAD=5
```

### 4. Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore Database
3. Download service account key:
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `config/serviceAccountKey.json`

4. Create Firestore collections:
   - `beds` - Hospital beds
   - `patients` - Patient records
   - `staff` - Staff members
   - `tasks` - Tasks for staff
   - `event_logs` - Agent decision logs

### 5. Gemini API Setup

1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env` file as `GOOGLE_API_KEY`

---

## 🎯 Usage

### Running the Agents

```bash
# Run all agents
python main.py
```

### Example: Patient Admission Workflow

```python
from main import CareFlowAgentSystem

# Initialize system
system = CareFlowAgentSystem()
await system.initialize()

# Process patient admission
result = await system.handle_new_patient_admission("patient_123")

# Result contains:
# - recommended_beds: Top 3 bed recommendations
# - tasks_created: List of tasks assigned to staff
# - confidence: AI confidence score
```

### Example: Query Available Beds

```python
# Via Memory Agent
response = await memory_agent.process({
    "type": "get_available_beds",
    "filters": {
        "ward": "ICU",
        "has_oxygen": True,
        "is_isolation": True
    }
})

available_beds = response.get("data", [])
```

### Example: Analyze System State

```python
# Via Memory Agent
response = await memory_agent.process({
    "type": "analyze_state"
})

analysis = response.get("data", {})
print(analysis["critical_alerts"])
print(analysis["bottlenecks"])
print(analysis["recommendations"])
```

### Example: Create Task Workflow

```python
# Via Communicator Agent
response = await communicator_agent.process({
    "type": "initiate_workflow",
    "workflow_type": "bed_assignment",
    "context": {
        "patient_id": "patient_123",
        "bed_id": "bed_456"
    }
})

tasks = response.get("data", {}).get("tasks_created", [])
```

---

## 📊 How the Hybrid Approach Works

### 50% Rule-Based + 50% AI

**Bed Allocation Example:**

1. **Rule-Based Scoring (50%):**
   - Equipment match: 40 points
   - Ward appropriateness: 25 points
   - Proximity: 15 points
   - Availability: 10 points
   - Workload: 10 points
   - **Total: 0-100 score**

2. **AI Ranking (50%):**
   - Gemini analyzes patient needs
   - Considers context and edge cases
   - Provides detailed reasoning
   - **Returns: 0-100 score + explanation**

3. **Combined Score:**
   ```
   Final Score = (Rule Score × 0.5) + (AI Score × 0.5)
   ```

**Example Output:**

```json
{
  "bed_id": "bed_312",
  "bed_number": "312",
  "ward": "Isolation B",
  "score": 92,
  "rule_score": 89,
  "ai_score": 95,
  "reasoning": "This bed is ideal because it has oxygen equipment which is required for the pneumonia patient. It's located in the Respiratory ward with specialized staff and has high proximity to nursing station (8/10) for close monitoring.",
  "pros": [
    "Has required oxygen equipment",
    "In specialized Respiratory ward",
    "Close to nursing station"
  ],
  "cons": [
    "Ward is at 75% capacity - relatively busy"
  ]
}
```

---

## 📝 Prompt Engineering

All prompts are in `prompts/prompt_templates.py`. Each prompt is carefully crafted to:

1. Provide clear context
2. Specify exact output format (JSON)
3. Include scoring criteria
4. Request reasoning and explanations

**Example Prompt Structure:**

```python
BED_ALLOCATION_PROMPT = """
You are a Bed Allocator AI for a hospital.

PATIENT INFORMATION:
- Name: {patient_name}
- Diagnosis: {diagnosis}
- Requirements: {requirements}

AVAILABLE BEDS:
{beds_json}

TASK:
Rank the top 3 most suitable beds considering:
1. Medical appropriateness
2. Patient safety
3. Operational efficiency

Respond ONLY with valid JSON:
{
  "recommendations": [...],
  "confidence": 0-100
}
"""
```

---

## 🧪 Testing

### Run Tests

```bash
pytest tests/
```

### Test Coverage

```bash
pytest --cov=. tests/
```

### Test Individual Agents

```python
# Test Memory Agent
python -m pytest tests/test_memory_agent.py -v

# Test Bed Allocator
python -m pytest tests/test_allocator_agent.py -v

# Test Communicator
python -m pytest tests/test_communicator_agent.py -v
```

---

## 📈 Monitoring & Logging

### Log Files

Logs are written to:
- `careflow_agents_YYYYMMDD.log` - Daily log file
- Console output (stdout)

### Log Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - General information about agent operations
- `WARNING` - Warning messages
- `ERROR` - Error messages

### Event Logging

All agent decisions are logged to Firebase `event_logs` collection:

```json
{
  "entity_type": "agent_decision",
  "entity_id": "bed_allocator_001",
  "action": "bed_allocation",
  "triggered_by": "bed_allocator",
  "details": {
    "input": {...},
    "output": {...},
    "reasoning": "...",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

---

## 🔧 Configuration Options

### Agent Weights

Adjust rule-based vs AI weights in `.env`:

```env
RULE_WEIGHT=0.5  # 50% rule-based
AI_WEIGHT=0.5    # 50% AI
```

### State Refresh Interval

How often Memory Agent refreshes data (seconds):

```env
AGENT_REFRESH_INTERVAL=300  # 5 minutes
```

### Staff Workload Limit

Maximum tasks per staff member:

```env
MAX_STAFF_WORKLOAD=5
```

### Task Timeouts

```env
TASK_TIMEOUT_WARNING=1800   # 30 minutes
TASK_TIMEOUT_CRITICAL=3600  # 1 hour
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Firebase Connection Error**
```
Error: Failed to initialize Firebase
```
**Solution:** Check `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env`

**2. Gemini API Error**
```
Error: GOOGLE_API_KEY not found
```
**Solution:** Set `GOOGLE_API_KEY` in `.env`

**3. Empty Recommendations**
```
No beds match patient requirements
```
**Solution:** Check if beds exist in Firestore with required equipment

**4. No Staff Available**
```
No available nurse staff
```
**Solution:** Ensure staff members in Firestore have `is_on_shift=true`

---

## 🚧 Development

### Adding a New Agent

1. Create new agent class inheriting from `BaseAgent`
2. Implement `process()` method
3. Implement `get_capabilities()` method
4. Add to `main.py` initialization

### Adding a New Workflow

Edit `communicator_agent.py`:

```python
WORKFLOWS = {
    "your_workflow": [
        {
            "task_type": "task_name",
            "role": "nurse",
            "priority": "high",
            "estimated_duration": 30,
            "description_template": "Do something with {patient_name}"
        }
    ]
}
```

### Modifying Prompts

Edit `prompts/prompt_templates.py` to update AI prompts.

---

## 📚 API Reference

### BaseAgent

```python
class BaseAgent(ABC):
    async def process(request_data: Dict) -> Dict
    async def log_decision(action, input_data, output_data, reasoning)
    async def log_error(error_message, context, error_type)
    def format_response(success, data, message, error_type)
```

### MemoryAgent

```python
class MemoryAgent(BaseAgent):
    async def initialize() -> bool
    async def get_available_beds(filters: Dict) -> List[Dict]
    async def get_patient_requirements(patient_id: str) -> Dict
    async def get_staff_availability(role: str, ward: str) -> List[Dict]
    async def analyze_state_with_ai() -> Dict
    async def detect_bottlenecks() -> List[Dict]
```

### BedAllocatorAgent

```python
class BedAllocatorAgent(BaseAgent):
    async def extract_requirements(patient: Dict) -> Dict
    async def score_beds_rule_based(beds, patient, requirements) -> List[Dict]
    async def get_ai_recommendations(patient, requirements, beds) -> Dict
    async def combine_scores(rule_beds, ai_recs) -> Dict
    async def record_allocation_feedback(allocation_id, ...) -> bool
```

### CommunicatorAgent

```python
class CommunicatorAgent(BaseAgent):
    async def initiate_workflow(workflow_type: str, context: Dict) -> Dict
    async def create_and_assign_task(task_data: Dict) -> Dict
    async def assign_optimal_staff(task_info: Dict) -> Dict
    async def check_task_progress() -> Dict
    async def handle_delayed_task(task_id: str) -> Dict
```

---

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Add docstrings to all functions
3. Write tests for new features
4. Update this README for significant changes

---

## 📄 License

Copyright © 2025 CareFlow Nexus Development Team

---

## 📞 Support

For issues or questions, contact the development team or open an issue in the repository.

---

## 🎉 Acknowledgments

- **Google Gemini AI** - Powering intelligent decision-making
- **Firebase** - Real-time database and authentication
- **Python Community** - Amazing libraries and tools

---

**Built with ❤️ for better healthcare management**