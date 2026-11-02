from flask import Flask, json, request, jsonify
import subprocess
import os
from flask_cors import CORS
from flask import send_from_directory

# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

CORS(app)

# =====================================================
# BASE PATH
# =====================================================

BASE = os.path.dirname(os.path.abspath(__file__))

FEEDBACK_SCRIPT = os.path.join(
    BASE,
    "feedback.ps1"
)
ACTION_FILE = os.path.join(
    BASE,
    "action_executor.json"
)
# =====================================================
# FEEDBACK API
# =====================================================

@app.route('/feedback', methods=['POST'])

def feedback():

    try:

        data = request.json

        print("FULL FEEDBACK DATA:", data)

        print(
            "ALERT:",
            data.get("alertId")
        )

        print(
            "SOLUTION:",
            data.get("solution")
        )

        print(
            "FEEDBACK:",
            data.get("feedback")
        )

        subprocess.run([

            "powershell",

            "-ExecutionPolicy",
            "Bypass",

            "-File",
            FEEDBACK_SCRIPT,

            "-alertId",
            str(data['alertId']),

            "-solution",
            str(data['solution']),

            "-feedback",
            str(data['feedback'])

        ])
        from datetime import datetime
        import json

        if os.path.exists(ACTION_FILE):

            with open(ACTION_FILE, "r", encoding="utf-8") as f:
                actions = json.load(f)

            for action in actions:

                primary = next(
                    (
                        e for e in action.get("supporting_events", [])
                        if e.get("role") == "primary"
                    ),
                    None
                )

                if primary and str(primary.get("event_id")) == str(data["alertId"]):

                    if data["feedback"] == "success":
                        action["status"] = "Approved"
                    else:
                        action["status"] = "Rejected"

                    action["approved_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(ACTION_FILE, "w", encoding="utf-8") as f:
                json.dump(actions, f, indent=2)

        return jsonify({

            "status": "success"
        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)
        })

# =====================================================
# RUN REMEDIATION SCRIPT
# =====================================================


@app.route(
    '/run-remediation',
    methods=['POST']
)
def run_remediation():

    try:

        from datetime import datetime

        data = request.json

        script_name = data.get("script")

        if not script_name:

            return jsonify({

                "status": "error",

                "message": "No script provided"

            })

        script_path = os.path.join(

            BASE,
            "remediation_scripts",

            script_name

        )
        
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

                # =====================================
        # Verification Message
        # =====================================

        details_map = {

            "Error512_MCPFirmwareCallHome.ps1":
                "MCP Firmware health verified successfully.",

            "Error1000_ApplicationCrash.ps1":
                "Application restarted successfully.",

            "Error11_DiskControllerError.ps1":
                "Disk controller health verified successfully.",

            "Error41_SystemRebootDueToResourceExhaustion.ps1":
                "System reboot completed successfully.",

            "Error2013_DiskCleanup.ps1":
                "Temporary files cleaned and disk space recovered successfully.",

            "Error51_DiskPagingIOError.ps1":
                "Disk paging I/O operation completed successfully.",

            "Error55_NTFSCorruptionDetected.ps1":
                "NTFS corruption repaired successfully.",

            "Error98_VolumeCorruptionDetected.ps1":
                "Volume corruption resolved successfully.",

            "Error129_StorageTimeoutReset.ps1":
                "Storage controller reset completed successfully.",

            "Error153_DiskIORetryIssue.ps1":
                "Disk I/O retry issue resolved successfully.",

            "Error1014_DNSNameResolutionTimeout.ps1":
                "DNS cache flushed successfully."

        }

        if result.returncode == 0:

            verification = "PASSED"

            details = details_map.get(

                script_name,

                "Remediation completed successfully."

            )

        else:

            verification = "FAILED"

            details = (

                result.stderr.strip()

                if result.stderr

                else "Remediation script execution failed."

            )

        return jsonify({

            "status":
                "success" if result.returncode == 0 else "error",

            "script":
                script_name,

            "verification":
                verification,

            "details":
                details,

            "time":
                datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        })
    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        })
    
@app.route('/RemediationScripts/<path:filename>')
def remediation_scripts(filename):

    return send_from_directory(
        'remediation_scripts',
        filename
    )

@app.route("/cleanup-result", methods=["GET"])
def cleanup_result():

    result_file = os.path.join(
        BASE,
        "remediation_scripts",
        "cleanup_result.json"
    )

    if not os.path.exists(result_file):

        return jsonify({})

    with open(result_file, "r", encoding="utf-8") as f:

        data = json.load(f)

    return jsonify(data)

@app.route("/service-result", methods=["GET"])
def service_result():

    result_file = os.path.join(
        BASE,
        "remediation_scripts",
        "service_result.json"
    )

    if not os.path.exists(result_file):
        return jsonify({})

    with open(result_file, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

# =====================================================
# START SERVER
# =====================================================

AUTO_LOG = os.path.join(
    BASE,
    "auto_remediation_log.json"
)

@app.route("/auto_remediation_log.json")
def auto_remediation_log():

    if not os.path.exists(AUTO_LOG):

        return jsonify([])

    with open(AUTO_LOG, "r", encoding="utf-8") as f:

        return jsonify(json.load(f))
    
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
