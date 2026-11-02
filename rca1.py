import json
import uuid
import requests
from collections import Counter
from datetime import datetime
import subprocess
import sys
import os


# =====================================================
# BASE PATH
# =====================================================

BASE = os.path.dirname(os.path.abspath(__file__))

CLASSIFIED_FILE = os.path.join(
    BASE,
    "classified_alerts.json"
)

RCA_OUTPUT_FILE = os.path.join(
    BASE,
    "rca_output.json"
)


# =====================================================
# LOAD CLASSIFIED ALERTS
# =====================================================

with open(
    CLASSIFIED_FILE,
    "r",
    encoding="utf-8-sig"
) as f:

    alerts = json.load(f)

if not alerts:

    print(" No alerts found")

    exit()

print(f" Loaded {len(alerts)} alerts")


# =====================================================
# INCIDENT GROUPING
# =====================================================

TIME_WINDOW_SECONDS = 180

alerts.sort(
    key=lambda x: x.get("timestamp", "")
)

incident_groups = []

current_group = []


for alert in alerts:

    try:

        current_time = datetime.fromisoformat(
            alert["timestamp"]
        )

    except:

        continue


    if not current_group:

        current_group.append(alert)

        continue


    previous_alert = current_group[-1]

    try:

        previous_time = datetime.fromisoformat(
            previous_alert["timestamp"]
        )

    except:

        previous_time = current_time


    time_diff = abs(
        (current_time - previous_time).total_seconds()
    )

    same_host = (
    alert.get("host") ==
    previous_alert.get("host")
    )
    
    same_source = (
        alert.get("source") ==
        previous_alert.get("source")
    )

    same_severity = (
        alert.get("severity") ==
        previous_alert.get("severity")
    )

    correlation_score = 0

    if same_host:
        correlation_score += 1
    
    if same_source:
        correlation_score += 1

    if same_severity:
        correlation_score += 1

    if time_diff <= TIME_WINDOW_SECONDS:
        correlation_score += 1


    if correlation_score >= 3:

        current_group.append(alert)

    else:

        incident_groups.append(current_group)

        current_group = [alert]


if current_group:

    incident_groups.append(current_group)

print(f" Incident groups created: {len(incident_groups)}")


# =====================================================
# RCA PROCESSING
# =====================================================

all_rca_outputs = []


for incident_alerts in incident_groups:

    compact_alerts = []

    for alert in incident_alerts[:3]:

        compact_alerts.append({

            "event_id":
                alert.get("event_id"),

            "source":
                alert.get("source"),

            "severity":
                alert.get("severity"),

            "message":
                str(
                    alert.get(
                        "message",
                        ""
                    )
                )[:250]
        })

    alerts_text = json.dumps(
        compact_alerts,
        indent=2
    )

    prompt = f"""
You are an expert Windows RCA engine.

Return ONLY valid JSON.

Format:

{{
  "root_cause": {{
    "category": "string",
    "reason_code": "string",
    "primary_event_id": number
  }},
  "supporting_events": [
    {{
      "event_id": number,
      "count": number
    }}
  ],
  "impact_summary": {{
    "severity": "string",
    "affected_components": ["string"]
  }}
}}

Analyze these alerts:

{alerts_text}
"""

    print("\n Running RCA on incident group...")

    # =====================================================
    # OLLAMA REQUEST
    # =====================================================

    try:
        
        response = requests.post(

            "http://localhost:11434/api/generate",

            json={

                "model": "phi3:latest",

                "prompt": prompt,

                "stream": False,

                "format": "json",

                "options": {

                    "temperature": 0.2,

                    "num_predict": 180,

                    "top_p": 0.9
                }
            },

            timeout=120
        )
        

    except Exception as e:

        print(f" Ollama connection failed: {e}")

        response = None


    # =====================================================
    # FALLBACK RCA
    # =====================================================

    fallback_rca = {

        "root_cause": {

            "category":
                incident_alerts[0].get(
                    "source",
                    "System Event"
                ),

            "reason_code":
                "Fallback RCA Generated",

            "primary_event_id":
                incident_alerts[0].get(
                    "event_id",
                    0
                )
        },

        "supporting_events": [],

        "impact_summary": {

            "severity":
                incident_alerts[0].get(
                    "severity",
                    "Warning"
                ),

            "affected_components": [
                incident_alerts[0].get(
                    "source",
                    "Unknown"
                )
            ]
        }
    }


    # =====================================================
    # HANDLE RESPONSE
    # =====================================================

    if response is None:

        print(" Using fallback RCA")

        rca_data = fallback_rca

    else:

        try:
            
            data = response.json()

        except Exception as e:

            print(f"Failed parsing Ollama response: {e}")

            rca_data = fallback_rca

        else:

            result = data.get("response", "").strip()

            if not result:

                print(" Empty model response - Using fallback RCA")

                rca_data = fallback_rca

            else:

                try:

                    rca_data = json.loads(result)

                    print(" AI RCA generated successfully")

                except Exception as e:

                    print(f" Invalid JSON from model: {e}")

                    print(" Using fallback RCA")

                    rca_data = fallback_rca


    # =====================================================
    # EVENT COUNTS
    # =====================================================

    event_counter = Counter()

    for alert in incident_alerts:

        event_id = alert.get("event_id")

        if event_id:

            event_counter[event_id] += 1


    primary_id = (
        rca_data
        .get("root_cause", {})
        .get("primary_event_id")
    )

    supporting_events = []


    for event_id, count in event_counter.items():

        role = (
            "primary"
            if event_id == primary_id
            else "secondary"
        )

        supporting_events.append({

            "event_id": event_id,

            "count": count,

            "role": role
        })


    # =====================================================
    # SEVERITY HANDLING
    # =====================================================

    original_severity = (
        incident_alerts[0]
        .get("severity", "Warning")
    )


    if original_severity.lower() == "error":
        severity = "Error"

    elif original_severity.lower() == "warning":
        severity = "Warning"

    elif original_severity.lower() == "critical":
        severity = "Critical"

    else:
        severity = "Warning"


    # =====================================================
    # HYBRID HEURISTIC CONFIDENCE SCORE
    # =====================================================

    # Severity Score

    severity_weight = {

        "Warning": 0.60,

        "Error": 0.80,

        "Critical": 0.95

    }

    severity_score = severity_weight.get(
        severity,
        0.60
    )


    # Event Frequency Score

    event_frequency = min(
        len(incident_alerts) / 10,
        1.0
    )


    # Diversity Score

    unique_event_ids = len(

        set(

            alert.get("event_id")

            for alert in incident_alerts

        )

    )

    diversity_score = min(

        unique_event_ids / 5,

        1.0

    )


    # =====================================================
    # CORRELATION STRENGTH
    # =====================================================

    correlation_scores = []

    for previous_alert, current_alert in zip(
        incident_alerts,
        incident_alerts[1:]
    ):

        pair_score = 0

        if previous_alert.get("host") == current_alert.get("host"):
            pair_score += 1

        if previous_alert.get("source") == current_alert.get("source"):
            pair_score += 1

        if previous_alert.get("severity") == current_alert.get("severity"):
            pair_score += 1

        try:

            previous_time = datetime.fromisoformat(
                previous_alert.get("timestamp", "")
            )

            current_time = datetime.fromisoformat(
                current_alert.get("timestamp", "")
            )

            if abs(
                (current_time - previous_time).total_seconds()
            ) <= TIME_WINDOW_SECONDS:

                pair_score += 1

        except (TypeError, ValueError):

            pass

        correlation_scores.append(pair_score / 4)


    correlation_strength = (

        sum(correlation_scores) / len(correlation_scores)

        if correlation_scores

        else 0.0

    )


    # =====================================================
    # STABILITY
    # =====================================================

    stability_score = 1.0


    # =====================================================
    # SINGLE ALERT BOOST
    # =====================================================

    if len(incident_alerts) == 1:

        confidence_score = severity_score

    else:

        confidence_score = round(

            (

                severity_score * 0.50 +

                correlation_strength * 0.20 +

                event_frequency * 0.15 +

                diversity_score * 0.10 +

                stability_score * 0.05

            ),

            2

        )


    # =====================================================
    # CONFIDENCE LEVEL
    # =====================================================

    if confidence_score >= 0.85:

        confidence_level = "High"

    elif confidence_score >= 0.60:

        confidence_level = "Medium"

    else:

        confidence_level = "Low"


    # =====================================================
    # FINAL RCA OUTPUT
    # =====================================================
    incident_timestamp = incident_alerts[0].get("timestamp", "")
    original_message = incident_alerts[0].get("message", "")
    
    rca_output = {

        "incident_id":
            f"INC-{incident_alerts[0].get('event_id')}-{incident_alerts[0].get('timestamp')}",

        "original_message":
            original_message,

        "severity":
            severity,

        "created_at":
            incident_timestamp,

        "root_cause":
            rca_data.get(
                "root_cause",
                {}
            ),

        "confidence_score":
            confidence_score,

        "confidence_level":
            confidence_level,

        "supporting_events":
            supporting_events,

        "impact_summary": {

            "severity":
                severity,

            "affected_components":
                rca_data.get(
                    "impact_summary",
                    {}
                ).get(
                    "affected_components",
                    []
                )
        },

        "total_alerts":
            len(incident_alerts),

        "rca_type":
            "SLM-Based (Hybrid Heuristic)"
    }

    
    all_rca_outputs.append(rca_output)

    print("\n RCA GENERATED")

    print(json.dumps(rca_output, indent=2))


# =====================================================
# SAVE OUTPUT
# =====================================================

with open(RCA_OUTPUT_FILE, "w") as f:

    json.dump(
        all_rca_outputs,
        f,
        indent=2
    )

print("\n RCA output saved")


# =====================================================
# RUN ACTION EXECUTOR
# =====================================================

print("\n Running Module 4...")

subprocess.run([

    sys.executable,

    os.path.join(
        BASE,
        "run_executor.py"
    )
])

print(" Module 4 completed")

