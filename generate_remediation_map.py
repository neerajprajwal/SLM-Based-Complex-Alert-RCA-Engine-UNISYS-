import os
import re
import json

BASE = os.path.dirname(os.path.abspath(__file__))

SCRIPT_FOLDER = os.path.join(
    BASE,
    "RemediationScripts",
    "remediation_scripts"
)

OUTPUT_FILE = os.path.join(
    BASE,
    "remediation_map.json"
)

mapping = {}

for file in os.listdir(SCRIPT_FOLDER):

    if file.endswith(".ps1"):

        match = re.search(
            r'Error(\d+)',
            file
        )

        if match:

            event_id = match.group(1)

            mapping[event_id] = file

with open(OUTPUT_FILE, "w") as f:

    json.dump(
        mapping,
        f,
        indent=2
    )

print(" remediation_map.json generated")