import json
import os
import subprocess
import requests

print(" Starting Action Executor...")

# =====================================================
# EXECUTE REMEDIATION SCRIPT
# =====================================================

def execute_remediation(script_name):

    script_path = os.path.join(

        BASE,
        "remediation_scripts",

        script_name

    )

    if not os.path.exists(script_path):

        print(f"Script not found: {script_name}")

        return False

    result = subprocess.run(

        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path
        ],

        capture_output=True,
        text=True

    )

    if result.returncode == 0:

        print(f" Auto remediation executed: {script_name}")

        return True

    else:

        print(f" Auto remediation failed: {script_name}")

        print(result.stderr)

        return False

def generate_response_phi3(rca):

    prompt = f"""
You are a Windows administrator.

Return ONLY valid JSON.

Generate ONLY ONE remediation action.

Do NOT generate multiple actions.
Do NOT generate markdown.
Do NOT generate any text outside the JSON.

Format:

{{
  "explanation":"",
  "actions":[
    {{
      "action":"",
      "risk":"",
      "reason":""
    }}
  ]
}}

Event ID: {rca.get("root_cause", {}).get("primary_event_id", "")}
Severity: {rca.get("severity", "")}
Message: {rca.get("original_message", "")}
"""

    response = requests.post(
        

        "http://localhost:11434/api/generate",

        json={

            "model": "phi3:mini",

            "prompt": prompt,

            "stream": False,

            "format": "json",

            "options": {
                "num_predict": 512
            }
        }
    )
    print("Ollama Status:", response.status_code)
    
    print("Ollama Response:")
    
    print(response.text)

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

    parsed_output["actions"] = actions

    return parsed_output

# =====================================================
# BASE PATH
# =====================================================

BASE = os.path.dirname(os.path.abspath(__file__))

RCA_FILE = os.path.join(
    BASE,
    "rca_output.json"
)

ACTION_OUTPUT_FILE = os.path.join(
    BASE,
    "action_executor.json"
)

HISTORY_FILE = os.path.join(
    BASE,
    "incident_history.json"
)

APPROVED_FILE = os.path.join(
    BASE,
    "approved_actions.json"
)

AUTO_LOG_FILE = os.path.join(
    BASE,
    "auto_remediation_log.json"
)


# =====================================================
# LOAD RCA FILE
# =====================================================

if not os.path.exists(RCA_FILE):

    print(" RCA file not found")

    exit()

with open(
    RCA_FILE,
    "r",
    encoding="utf-8"
) as f:

    rca_data = json.load(f)

if isinstance(rca_data, dict):

    rca_data = [rca_data]

print(" RCA file loaded")


# =====================================================
# LOAD APPROVED REMEDIATIONS
# =====================================================

approved_actions = {}

if os.path.exists(APPROVED_FILE):

    try:

        with open(
            APPROVED_FILE,
            "r",
            encoding="utf-8-sig"
        ) as f:

            approved_actions = json.load(f)

    except Exception as e:

        print("Error loading approved_actions.json:", e)

        approved_actions = {}

print(f" Loaded {len(approved_actions)} approved remediations")


# =====================================================
# ACTION GENERATION LOGIC
# =====================================================
executed_scripts = set()

final_output = []

for incident in rca_data:

    # Skip invalid incidents
    if not incident or not incident.get("incident_id"):

        print(" Skipping invalid incident")

        continue

    severity = incident.get(
        "severity",
        "Warning"
    )

    root_cause = incident.get(
        "root_cause",
        {}
    )

    event_id = root_cause.get(
        "primary_event_id",
        0
    )

    action_data = {

        "severity":
            severity,

        "original_message":
            incident.get(
                "original_message",
                ""
            ),

        "incident_id":
            incident.get(
                "incident_id"
            ),

        "created_at":
            incident.get(
                "created_at"
            ),

        "priority_status":
            "Low Priority",

        "action_generation":
            False,

        "message":
            "Stored for monitoring only.",

        "remediation_script":
            "",

        "steps":
            "No Script",

        "status":
            "Pending",

        "approved_time":
            "-",

        "suggested_actions": [

            {
                "action":
                    "Investigate incident manually"
            }

        ],

        "rca_type":
            incident.get(
                "rca_type"
            ),

        "root_cause":
            root_cause,

        "confidence_score":
            incident.get(
                "confidence_score"
            ),

        "confidence_level":
            incident.get(
                "confidence_level"
            ),

        "impact_summary":
            incident.get(
                "impact_summary"
            ),

        "supporting_events":
            incident.get(
                "supporting_events"
            )
    }

    # =================================================
    # HIGH PRIORITY ERROR LOGIC
    # =================================================

    if severity in ["Error", "Critical"]:

        action_data["priority_status"] = "High Priority"

        action_data["action_generation"] = True

        action_data["message"] = "Automated remediation available."

        action_data["human_in_the_loop"] = True

        action_data["admin_feedback"] = {

            "status": "Pending",

            "approved_actions": [],

            "rejected_actions": [],

            "comments": ""

        }
        # =================================================
        # EVENT-ID-BASED REMEDIATION MAPPING
        # =================================================

        if event_id == 1000:

            action_data["remediation_script"] = "Error1000_ApplicationCrash.ps1"
            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

                {
                    "action": "Restart crashed application"
                },

                {
                    "action": "Collect crash dump logs"
                }

            ]


        elif event_id == 11:

            action_data["remediation_script"] = "Error11_DiskControllerError.ps1"
            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

                {
                    "action": "Check disk controller health"
                },

                {
                    "action": "Inspect storage connectivity"
                }

            ]

        elif event_id == 7:

            action_data["remediation_script"] = "Error7_BadBlocksDetected.ps1"
            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

                {
                    "action": "Run disk diagnostics and investigate bad blocks on the affected drive"
                }

            ]


        elif event_id == 41:

            action_data["remediation_script"] = "Error41_SystemRebootDueToResourceExhaustion.ps1"
            action_data["steps"] = "View Steps"


        elif event_id == 51:

            action_data["remediation_script"] = "Error51_DiskPagingIOError.ps1"
            action_data["steps"] = "View Steps"


        elif event_id == 55:

            action_data["remediation_script"] = "Error55_NTFSCorruptionDetected.ps1"
            action_data["steps"] = "View Steps"


        elif event_id == 98:

            action_data["remediation_script"] = "Error98_VolumeCorruptionDetected.ps1"
            action_data["steps"] = "View Steps"


        elif event_id == 129:

            action_data["remediation_script"] = "Error129_StorageTimeoutReset.ps1"
            action_data["steps"] = "View Steps"


        elif event_id == 153:

            action_data["remediation_script"] = "Error153_DiskIORetryIssue.ps1"
            action_data["steps"] = "View Steps"

        elif event_id == 513:

            action_data["remediation_script"] = "Restart_WSearch_Service.ps1"

            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

                {
                    "action": "Restart Windows Search Service"
                }

            ]


        elif event_id == 2013:

            action_data["remediation_script"] = "Error2013_DiskCleanup.ps1"

            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

                {
                    "action": "Clean temporary files and recover disk space"
                }

            ]

        elif event_id == 512:
            action_data["remediation_script"] = "Error512_MCPFirmwareCallHome.ps1"

            action_data["steps"] = "View Steps"

            action_data["suggested_actions"] = [

        {
            "action": "Verify MCP firmware status"
        },

        {
            "action": "Check CallHome connectivity"
        }

    ]



        elif event_id == 1014:

            action_data["remediation_script"] = "Error1014_DNSNameResolutionTimeout.ps1"
            action_data["steps"] = "View Steps"


        else:

            print(f"No remediation script found for Event ID {event_id}. Generating SLM suggestions...")

            slm_output = generate_response_phi3(action_data)

            action_data["llm_explanation"] = slm_output.get(
        "explanation",
        "No explanation generated."
            )

            suggestions = []

            for item in slm_output.get("actions", []):

                if isinstance(item, dict):

                    suggestions.append({

                "action": item.get("action", "No suggestion"),

                "risk": item.get("risk", "Medium"),

                "reason": item.get("reason", "")

        })

            if suggestions:

                action_data["suggested_actions"] = suggestions

            else:

                action_data["suggested_actions"] = [

                    {
                "action": "Perform manual investigation",
                "risk": "Medium",
                "reason": "The SLM could not generate recommendations."
                    }

            ]

            action_data["steps"] = "SLM Recommendation"
    
                    # =================================================
        # AUTO REMEDIATION IF PREVIOUSLY APPROVED
        # =================================================

        script_name = action_data.get("remediation_script", "")
        # Prevent duplicate execution in the same pipeline run
        if script_name in executed_scripts:
            print(f" Already executed in this run: {script_name}")
            action_data["status"] = "Auto Remediated"
            final_output.append(action_data)
            continue

        if script_name and script_name in approved_actions:
            executed_scripts.add(script_name)

            print(f"Previously approved: {script_name}")

            success = execute_remediation(script_name)

            from datetime import datetime

            log_entry = {

                "timestamp":
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                "incident_id":
                    action_data["incident_id"],

                "event_id":
                    event_id,

                "script":
                    script_name,

                "mode":
                    "Automatic",

                "result":
                    "Success" if success else "Failed"

            }

            logs = []

            if os.path.exists(AUTO_LOG_FILE):

                try:

                    with open(
                        AUTO_LOG_FILE,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        logs = json.load(f)

                        if not isinstance(logs, list):
                            logs = []

                except:

                    logs = []

            logs.append(log_entry)

            with open(
                AUTO_LOG_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    logs,
                    f,
                    indent=4
                )

            print(" Auto remediation logged.")

            print(" Skipping dashboard...")
            action_data["status"] = "Auto Remediated"
            action_data["approved_time"] = log_entry["timestamp"]

            final_output.append(action_data)

        else:

            final_output.append(action_data)

    else:

        print(f"Generating SLM suggestions for Event ID {event_id} ({severity})")

        slm_output = generate_response_phi3(action_data)

        action_data["llm_explanation"] = slm_output.get(
        "explanation",
        "No explanation generated."
        )

        suggestions = []

        for item in slm_output.get("actions", []):

            if isinstance(item, dict):

                suggestions.append({

                "action": item.get("action", "No suggestion"),
                "risk": item.get("risk", "Medium"),
                "reason": item.get("reason", "")

            })

        if suggestions:

            action_data["suggested_actions"] = suggestions

        else:

            action_data["suggested_actions"] = [

                {
                "action": "Perform manual investigation",
                "risk": "Medium",
                "reason": "The SLM could not generate recommendations."
                }

            ]

        action_data["steps"] = "SLM Recommendation"

        final_output.append(action_data)
        # =====================================================
# LOAD EXISTING ACTIONS
# =====================================================

existing_actions = []

if os.path.exists(ACTION_OUTPUT_FILE):

    try:

        with open(
            ACTION_OUTPUT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            existing_actions = json.load(f)

            if isinstance(existing_actions, dict):

                existing_actions = [existing_actions]

    except:

        existing_actions = []


# =====================================================
# COMBINE + REMOVE DUPLICATES
# =====================================================

combined_actions = final_output + existing_actions 

unique_actions = []

seen_ids = set()

for item in combined_actions:

    if not item.get("incident_id"):
        continue

    incident_id = item["incident_id"]

    if incident_id in seen_ids:
        continue

    seen_ids.add(incident_id)

    unique_actions.append(item)

# Keep only the latest 20 incidents
unique_actions = sorted(
    unique_actions,
    key=lambda x: x.get("created_at", ""),
    reverse=True
)[:50]


# =====================================================
# SAVE ACTION EXECUTOR OUTPUT
# =====================================================

with open(
    ACTION_OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        unique_actions,
        f,
        indent=2
    )

print(" action_executor.json updated")


# =====================================================
# SAVE INCIDENT HISTORY
# =====================================================

with open(
    HISTORY_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        unique_actions,
        f,
        indent=2
    )

print("Incident history updated")

print(json.dumps(
    unique_actions,
    indent=2
))

print(" Executor completed")
