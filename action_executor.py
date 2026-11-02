import json
import requests
import os


# =====================================================
# BASE PATH
# =====================================================

BASE = os.path.dirname(os.path.abspath(__file__))

FEEDBACK_FILE = os.path.join(
    BASE,
    "feedback_data.json"
)

MAP_FILE = os.path.join(
    BASE,
    "remediation_map.json"
)

with open(MAP_FILE, "r") as f:

    REMEDIATION_MAP = json.load(f)


# =====================================================
# PRIORITY CHECK
# =====================================================

def is_high_priority(rca):

    confidence = rca.get(
        "confidence_score",
        0
    )

    severity = (
        rca.get(
            "impact_summary",
            {}
        )
        .get(
            "severity",
            ""
        )
        .lower()
    )

    if confidence >= 0.9:
        return True

    if severity in [
        "critical",
        "error"
    ]:
        return True

    return False


# =====================================================
# GENERATE SLM RESPONSE
# =====================================================

def generate_response_phi3(rca):

    prompt = f"""
You are an enterprise IT operations assistant.

Analyze the incident and return ONLY valid JSON.

Format:

{{
  "explanation": "string",
  "actions": [
    {{
      "action": "string",
      "risk": "Low",
      "reason": "string"
    }}
  ]
}}

Incident:

Category:
{rca['root_cause']['category']}

Reason:
{rca['root_cause']['reason_code']}

Severity:
{rca['impact_summary']['severity']}

Confidence:
{rca['confidence_level']}
"""

    response = requests.post(

        "http://localhost:11434/api/generate",

        json={

            "model": "phi3:mini",

            "prompt": prompt,

            "stream": False,

            "format": "json",

            "options": {
                "num_predict": 120
            }
        }
    )

    try:

        data = response.json()

    except:

        return {

            "explanation":
                "Failed to parse model response.",

            "actions": []
        }


    try:

        parsed_output = json.loads(
            data.get(
                "response",
                "{}"
            )
        )

    except:

        return {

            "explanation":
                "Failed to parse model response.",

            "actions": []
        }


    actions = parsed_output.get(
        "actions",
        []
    )


    if not isinstance(actions, list):

        actions = []


    # =====================================================
    # LOAD FEEDBACK HISTORY
    # =====================================================

    feedback_data = {}

    try:

        with open(FEEDBACK_FILE, "r") as f:

            feedback_data = json.load(f)

    except:

        feedback_data = {}


    event_id = str(
        rca["root_cause"].get(
            "primary_event_id",
            "unknown"
        )
    )


    scored_actions = []


    for action in actions:

        action_name = action.get(
            "action",
            ""
        )

        success = 0

        failure = 0


        if (
            event_id in feedback_data
            and
            action_name in feedback_data[event_id]
        ):

            success = (
                feedback_data[event_id]
                [action_name]
                .get("success", 0)
            )

            failure = (
                feedback_data[event_id]
                [action_name]
                .get("failure", 0)
            )


        score = success - failure


        action["historical_success"] = success

        action["historical_failure"] = failure

        action["historical_score"] = score


        scored_actions.append(action)


    scored_actions = sorted(

        scored_actions,

        key=lambda x:
            x["historical_score"],

        reverse=True
    )


    parsed_output["actions"] = scored_actions


    return parsed_output


# =====================================================
# MAIN ACTION EXECUTOR
# =====================================================

def automated_action_executor(rca):

    high_priority = is_high_priority(rca)


    # =====================================================
    # HIGH PRIORITY INCIDENT
    # =====================================================

    if high_priority:

        slm_output = generate_response_phi3(
            rca
        )
        

        final_output = {

            "severity":
                rca.get(
                    "severity",
                    rca.get(
                        "impact_summary",
                        {}
                    ).get(
                        "severity",
                        "Unknown"
                    )
                ),

            "original_message":
                rca.get(
                    "original_message",
                    ""
                ),

            "remediation_script":
                REMEDIATION_MAP.get(
                    str(
                        rca["root_cause"].get(
                            "primary_event_id"
                        )
                    ),
                    None
                ),

            "incident_id":
                rca["incident_id"],
            "created_at":
    rca.get(
        "created_at",
        ""
    ),
            "priority_status":
                "High Priority",

            "action_generation":
                True,

            "rca_type":
                rca["rca_type"],

            "root_cause":
                rca["root_cause"],

            "confidence_score":
                rca["confidence_score"],

            "confidence_level":
                rca["confidence_level"],

            "impact_summary":
                rca["impact_summary"],

            "supporting_events":
                rca["supporting_events"],

            "llm_explanation":
                slm_output.get(
                    "explanation",
                    ""
                ),

            "suggested_actions":
                slm_output.get(
                    "actions",
                    []
                ),

            "human_in_the_loop":
                True,

            "admin_feedback": {

                "status": "Pending",

                "approved_actions": [],

                "rejected_actions": [],

                "comments": ""
            }
        }


    # =====================================================
    # LOW PRIORITY INCIDENT
    # =====================================================

    else:

        final_output = {

            "severity":
                rca.get(
                    "severity",
                    rca.get(
                        "impact_summary",
                        {}
                    ).get(
                        "severity",
                        "Unknown"
                    )
                ),

            "original_message":
                rca.get(
                    "original_message",
                    ""
                ),

            "incident_id":
                rca["incident_id"],
            "created_at":
    rca.get(
        "created_at",
        ""
    ),
            "priority_status":
                "Low Priority",

            "action_generation":
                False,

            "message":
                "Stored for monitoring only.",

            "suggested_actions": [
                {
                    "action":
                        "Investigate incident manually"
                }
            ],

            "rca_type":
                rca["rca_type"],

            "root_cause":
                rca["root_cause"],

            "confidence_score":
                rca["confidence_score"],

            "confidence_level":
                rca["confidence_level"],

            "impact_summary":
                rca["impact_summary"],

            "supporting_events":
                rca["supporting_events"]
        }


    return final_output