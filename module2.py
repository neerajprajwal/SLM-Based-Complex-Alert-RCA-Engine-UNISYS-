
import json
import pandas as pd
import joblib
import numpy as np
import subprocess
import os
import sys
import warnings
warnings.filterwarnings("ignore")

print("Module 2 is running")


# =====================================================
# BASE PATH
# =====================================================

BASE = os.path.dirname(os.path.abspath(__file__))

ALERTS_FILE = os.path.join(
    BASE,
    "alerts.json"
)

MODEL_FILE = os.path.join(
    BASE,
    "rf_model.pkl"
)

TFIDF_FILE = os.path.join(
    BASE,
    "tfidf_vectorizer.pkl"
)

ENCODER_FILE = os.path.join(
    BASE,
    "source_encoder.pkl"
)

OUTPUT_FILE = os.path.join(
    BASE,
    "classified_alerts.json"
)

RCA_FILE = os.path.join(
    BASE,
    "rca1.py"
)


# =====================================================
# STEP 1: LOAD ALERTS
# =====================================================

with open(
    ALERTS_FILE,
    "r",
    encoding="utf-8-sig"
) as f:

    data = json.load(f)



# Ensure list format
if isinstance(data, dict):

    data = [data]

print("Loaded alerts:")
for alert in data:
    print(alert["event_id"], alert["source"])
df = pd.DataFrame(data)


if df.empty:

    print("No alerts found. Exiting.")

    exit()


# =====================================================
# STEP 2: LOAD MODEL FILES
# =====================================================

model = joblib.load(MODEL_FILE)

tfidf = joblib.load(TFIDF_FILE)

source_encoder = joblib.load(ENCODER_FILE)


# =====================================================
# STEP 3: TEXT FEATURE
# =====================================================

X_text = tfidf.transform(
    df['message'].astype(str)
).toarray()


# =====================================================
# STEP 4: ENCODE SOURCE
# =====================================================

def encode_source(val):

    if val in source_encoder.classes_:

        return source_encoder.transform([val])[0]

    return -1


source_encoded = df[
    'source'
].astype(str).apply(encode_source)


# =====================================================
# STEP 5: COMBINE FEATURES
# =====================================================

X = np.hstack((
    X_text,
    source_encoded.values.reshape(-1, 1)
))


# =====================================================
# STEP 6: PREDICT
# =====================================================

predictions = model.predict(X)


# =====================================================
# STEP 7: ADD ALERT TYPE
# =====================================================

df['alert_type'] = [

    'Simple'
    if p == 0
    else 'Complex'

    for p in predictions
]


# =====================================================
# STEP 8: SAVE OUTPUT
# =====================================================

df.to_json(
    OUTPUT_FILE,
    orient='records',
    indent=4
)

print("Classification complete - classified_alerts.json")


# =====================================================
# STEP 9: RUN RCA ENGINE
# =====================================================

print("Launching RCA Engine...")


subprocess.run([
    sys.executable,
    RCA_FILE
])

print("RCA Engine completed")
