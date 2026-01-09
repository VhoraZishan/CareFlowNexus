"""
Prompt Templates for CareFlow Nexus AI Agents
Contains all prompt templates for State Manager, Bed Allocator, and Task Coordinator agents
"""


class StateManagerPrompts:
    """Prompt templates for State Manager Agent"""

    STATE_ANALYSIS = """
You are a State Manager AI for a hospital bed management system.

CURRENT HOSPITAL STATE:

Beds:
- Total Beds: {total_beds}
- Available: {available_beds}
- Occupied: {occupied_beds}
- In Cleaning: {cleaning_beds}
- In Maintenance: {maintenance_beds}
- Utilization Rate: {utilization_rate}%

Patients:
- Total Patients: {total_patients}
- Waiting for Admission: {waiting_patients}
- Currently Admitted: {admitted_patients}

Staff:
- Nurses On Shift: {nurses_count}
- Cleaners On Shift: {cleaners_count}
- Total Staff Available: {total_staff}

Tasks:
- Active Tasks: {active_tasks}
- Pending Tasks: {pending_tasks}
- In Progress Tasks: {in_progress_tasks}
- Overdue Tasks: {overdue_tasks}

Ward Breakdown:
{ward_summary}

TASK:
Analyze this hospital state and identify:
1. Critical issues requiring immediate attention
2. Operational bottlenecks
3. Capacity forecast for next 4-6 hours
4. Proactive recommendations

Respond ONLY with valid JSON in this exact format:
{{
  "critical_alerts": [
    {{
      "type": "alert type",
      "severity": "critical/high/medium",
      "message": "what's wrong",
      "action_needed": "what to do"
    }}
  ],
  "bottlenecks": [
    {{
      "area": "which area (cleaning, staffing, beds)",
      "description": "issue description",
      "impact": "how it affects operations",
      "recommendation": "suggested solution"
    }}
  ],
  "capacity_forecast": {{
    "next_4_hours": "forecast description",
    "bed_availability_trend": "increasing/stable/decreasing",
    "staffing_adequacy": "sufficient/stretched/insufficient"
  }},
  "recommendations": [
    "proactive action 1",
    "proactive action 2"
  ]
}}
"""

    BOTTLENECK_DETECTION = """
Analyze the following hospital operations data for bottlenecks:

{operational_data}

Identify specific bottlenecks and provide actionable recommendations.

Respond with JSON:
{{
  "bottlenecks": [
    {{
      "type": "cleaning_backlog/staff_overload/bed_shortage",
      "severity": "low/medium/high/critical",
      "count": 0,
      "description": "detailed issue",
      "recommendation": "action to take"
    }}
  ]
}}
"""


class BedAllocatorPrompts:
    """Prompt templates for Bed Allocator Agent"""

    BED_ALLOCATION = """
You are a Bed Allocator AI for a hospital. Your job is to match patients with the most suitable beds.

PATIENT INFORMATION:
- Name: {patient_name}
- Age: {age}
- Gender: {gender}
- Diagnosis: {diagnosis}
- Severity: {severity}
- Mobility Status: {mobility_status}

EXTRACTED REQUIREMENTS:
- Needs Oxygen: {needs_oxygen}
- Needs Ventilator: {needs_ventilator}
- Needs Cardiac Monitor: {needs_cardiac_monitor}
- Needs Isolation: {needs_isolation}
- Preferred Ward: {preferred_ward}

AVAILABLE BEDS (Pre-filtered by requirements):
{beds_json}

CURRENT CONTEXT:
- Time of Day: {current_time}
- Day of Week: {day_of_week}
- Overall Hospital Occupancy: {occupancy_rate}%
- Staff Availability: {staff_summary}

SCORING CRITERIA:
1. Medical Appropriateness (40 points):
   - Equipment match (oxygen, ventilator, monitors)
   - Isolation capability if needed
   - Ward specialization

2. Patient Safety & Comfort (25 points):
   - Proximity to nursing station for monitoring
   - Appropriate ward environment
   - Infection control considerations

3. Operational Efficiency (20 points):
   - Current ward workload distribution
   - Staff availability in ward
   - Bed location logistics

4. Resource Optimization (15 points):
   - Avoid over-specification (don't use ICU for minor cases)
   - Balance ward occupancy
   - Equipment availability vs future needs

TASK:
Rank the available beds and recommend the TOP 3 most suitable options.
For each bed, provide:
- Match score (0-100)
- Detailed reasoning
- Pros (advantages)
- Cons (concerns or limitations)

Respond ONLY with valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "bed_id": "bed_id_here",
      "bed_number": "bed number",
      "ward": "ward name",
      "score": 85,
      "reasoning": "This bed is ideal because it has oxygen equipment which is required for the pneumonia patient. It's located in the Respiratory ward with specialized staff and has high proximity to nursing station (8/10) for close monitoring.",
      "pros": [
        "Has required oxygen equipment",
        "In specialized Respiratory ward",
        "Close to nursing station for monitoring",
        "Currently available and clean"
      ],
      "cons": [
        "Ward is at 75% capacity - relatively busy",
        "No cardiac monitor (not required but could be useful)"
      ]
    }}
  ],
  "overall_confidence": 90,
  "considerations": "Patient has moderate severity pneumonia requiring oxygen support and close monitoring. All recommended beds meet core requirements."
}}
"""

    REQUIREMENT_EXTRACTION = """
You are a medical requirements analyzer for hospital bed allocation.

PATIENT DATA:
- Age: {age}
- Gender: {gender}
- Diagnosis: {diagnosis}
- Severity: {severity}
- Admission Type: {admission_type}
- Mobility Status: {mobility_status}

TASK:
Extract the medical care requirements needed for this patient.

Consider:
- What equipment is needed? (oxygen, ventilator, cardiac monitor)
- Is isolation required? (infectious diseases, immunocompromised)
- What ward is most appropriate? (ICU, General, Isolation, Cardiac, Respiratory)
- How much nursing attention is needed? (proximity to nursing station: 1-10)
- Any special considerations?

Respond ONLY with valid JSON:
{{
  "needs_oxygen": true,
  "needs_ventilator": false,
  "needs_cardiac_monitor": false,
  "needs_isolation": true,
  "preferred_ward": "Respiratory",
  "proximity_preference": 8,
  "special_considerations": [
    "Patient needs close monitoring due to moderate severity",
    "Infectious precautions required"
  ],
  "confidence": 95,
  "reasoning": "Pneumonia diagnosis requires oxygen support and isolation to prevent spread. Moderate severity indicates need for close monitoring."
}}
"""


class TaskCoordinatorPrompts:
    """Prompt templates for Task Coordinator Agent"""

    STAFF_ASSIGNMENT = """
You are a Task Coordinator AI for hospital operations.

TASK TO ASSIGN:
- Task ID: {task_id}
- Type: {task_type}
- Description: {description}
- Priority: {priority}
- Location: Ward {ward}, Bed {bed_number}
- Estimated Duration: {duration} minutes
- Patient: {patient_name} (if applicable)

AVAILABLE STAFF CANDIDATES:
{staff_json}

CURRENT CONTEXT:
- Current Time: {current_time}
- Ward Activity Level: {activity_level}
- Total Pending Tasks: {pending_tasks_count}

SELECTION CRITERIA:
1. Role Appropriateness (Must Match): {required_role}
2. Current Workload (Fair Distribution)
3. Ward Assignment (Preference for same ward)
4. Location Proximity (Efficiency)
5. Recent Task History (Avoid overloading)

TASK:
Select the most appropriate staff member for this task.

Consider:
- Who has the lowest current workload?
- Who is already in or near this ward?
- Who hasn't been assigned a task recently?
- Balance efficiency with fairness

Respond ONLY with valid JSON:
{{
  "recommended_staff_id": "staff_id_here",
  "staff_name": "Staff Name",
  "reasoning": "This staff member has the lowest current workload (2 tasks) and is already assigned to the same ward, making them the most efficient choice. They have the appropriate role and capacity.",
  "workload_impact": "Workload will increase from 2 to 3 tasks, still below maximum of 5.",
  "concerns": [
    "Ward is busy - staff may need support"
  ],
  "alternatives": [
    {{
      "staff_id": "alt_id",
      "staff_name": "Alt Name",
      "reason": "Second choice with 3 current tasks"
    }}
  ],
  "confidence": 85
}}
"""

    WORKFLOW_ORCHESTRATION = """
You are orchestrating a multi-step hospital workflow.

WORKFLOW TYPE: {workflow_type}

CONTEXT:
{context_json}

CURRENT STEP: {current_step}
PREVIOUS STEPS COMPLETED: {completed_steps}

AVAILABLE STAFF:
- Nurses: {nurses_available}
- Cleaners: {cleaners_available}

TASK:
Determine the next task(s) to create and assign.

Respond with JSON:
{{
  "next_tasks": [
    {{
      "task_type": "cleaning",
      "priority": "high",
      "assigned_role": "cleaner",
      "description": "Task description",
      "estimated_duration": 30
    }}
  ],
  "workflow_status": "in_progress/completed",
  "reasoning": "Why these tasks next"
}}
"""

    TASK_ESCALATION = """
You are handling a delayed hospital task that needs escalation.

TASK DETAILS:
{task_json}

DELAY INFORMATION:
- Expected Duration: {expected_duration} minutes
- Actual Time Elapsed: {actual_elapsed} minutes
- Delay: {delay_minutes} minutes
- Current Status: {status}

CONTEXT:
- Ward: {ward}
- Priority: {priority}
- Patient Waiting: {patient_waiting}

AVAILABLE OPTIONS:
1. Reassign to different staff
2. Escalate to supervisor
3. Increase priority
4. Request additional support

Available staff for reassignment:
{available_staff_json}

TASK:
Recommend the best course of action to resolve this delay.

Respond with JSON:
{{
  "action": "reassign/escalate/increase_priority/request_support",
  "reasoning": "Why this action is appropriate",
  "recommended_staff_id": "staff_id if reassigning",
  "escalation_message": "Message to supervisor if escalating",
  "priority_change": "new priority if increasing",
  "urgency": "low/medium/high/critical"
}}
"""


class CommonPrompts:
    """Common prompts used across multiple agents"""

    GENERATE_REASONING = """
Explain the following decision in simple, clear language:

DECISION: {decision}

FACTORS CONSIDERED:
{factors_json}

Provide a 2-3 sentence explanation suitable for hospital staff.
"""

    VALIDATE_DECISION = """
Validate this decision for potential issues:

{decision_json}

Check for:
- Safety concerns
- Resource conflicts
- Policy violations
- Logic errors

Respond with JSON:
{{
  "is_valid": true/false,
  "concerns": ["list of issues if any"],
  "severity": "none/low/medium/high",
  "recommendation": "proceed/review/reject"
}}
"""
