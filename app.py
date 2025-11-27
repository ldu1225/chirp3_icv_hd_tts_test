# -*- coding: utf-8 -*-
import os
import time
import base64
import google.auth
import requests
from google.cloud import texttospeech, storage
from flask import Flask, render_template, request, url_for

# --- Configuration ---
PROJECT_ID = "xxx"
BUCKET_NAME = f"{PROJECT_ID}-xxx"
VOICE_KEY_FILE = "voice_key.txt"
CONSENT_SCRIPT = "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Global Variables & Key Loading ---
storage_client = None
voice_cloning_key = None

try:
    with open(VOICE_KEY_FILE, "r") as f:
        voice_cloning_key = f.read().strip()
    if not voice_cloning_key:
        raise ValueError("Voice key file is empty.")
    print("Successfully loaded voice cloning key.")
except (FileNotFoundError, ValueError) as e:
    print(f"FATAL: Could not load voice cloning key from {VOICE_KEY_FILE}. It must be included in the deployment. Error: {e}")
    # In a production environment, you might want to exit or handle this differently.
    # For Cloud Run, this will cause the container to fail startup if the key is missing, which is desired.

# --- Helper Functions (Adapted from main.py) ---

def synthesize_and_upload(text, model_name):
    """Synthesizes speech, saves locally, uploads to GCS, and returns results."""
    if not voice_cloning_key:
        return {"error": "Invalid voice cloning key. The application may not have started correctly."}

    try:
        credentials, _ = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        access_token = credentials.token
    except Exception as e:
        return {"error": f"Authentication failed: {e}"}

    url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-goog-user-project": PROJECT_ID,
    }
    if model_name == "hd":
        # Use Google's standard Korean male voice for HD
        data = {
            "input": {"text": text},
            "voice": {
                "language_code": "ko-KR",
                "name": "ko-KR-Wavenet-C",
            },
            "audioConfig": {"audioEncoding": "LINEAR16"},
        }
    else:  # For 'icv'
        # Use the user's cloned voice
        data = {
            "input": {"text": text},
            "voice": {
                "language_code": "en-US",  # Cloning was done in English
                "voice_clone": {"voice_cloning_key": voice_cloning_key},
            },
            "audioConfig": {"audioEncoding": "LINEAR16"},
        }

    print(f"Synthesizing with {model_name} model...")
    start_time = time.time()
    response = requests.post(url, headers=headers, json=data)
    end_time = time.time()
    synth_time = end_time - start_time

    if response.status_code != 200:
        error_message = f"Error synthesizing speech: {response.status_code} - {response.text}"
        return {"error": error_message}

    audio_content = base64.b64decode(response.json()["audioContent"])
    
    local_filename = f"output_{model_name}.wav"
    local_filepath = os.path.join("static", local_filename)
    with open(local_filepath, "wb") as out:
        out.write(audio_content)
    
    gcs_filename = f"generated_audio/{local_filename}"
    try:
        # Initialize client here if it's not already
        global storage_client
        if storage_client is None:
            storage_client = storage.Client(project=PROJECT_ID)
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(gcs_filename)
        blob.upload_from_filename(local_filepath)
        print(f"Uploaded {local_filename} to gs://{BUCKET_NAME}/{gcs_filename}")
    except Exception as e:
        return {"error": f"Failed to upload to GCS: {e}"}

    return {
        "time": synth_time,
        "local_url": url_for('static', filename=local_filename)
    }

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        text_to_synthesize = request.form.get("text")
        if text_to_synthesize:
            hd_result = synthesize_and_upload(text_to_synthesize, "hd")
            icv_result = synthesize_and_upload(text_to_synthesize, "icv")
            
            if "error" not in hd_result and "error" not in icv_result:
                time_diff = abs(hd_result['time'] - icv_result['time'])
                faster_model = "HD" if hd_result['time'] < icv_result['time'] else "ICV"
                results = {
                    "hd_time": f"{hd_result['time']:.4f}",
                    "icv_time": f"{icv_result['time']:.4f}",
                    "hd_url": hd_result['local_url'],
                    "icv_url": icv_result['local_url'],
                    "faster_model": faster_model,
                    "time_diff": f"{time_diff:.4f}"
                }
            else:
                results = {"error": hd_result.get("error") or icv_result.get("error")}

    return render_template("index.html", results=results)

if __name__ == "__main__":
    if not voice_cloning_key:
        print("Could not load voice cloning key. Exiting.")
        exit(1)
    
    # Initialize GCS client for local development
    try:
        storage_client = storage.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Failed to initialize GCS client: {e}")
        exit(1)

    app.run(debug=True, host="0.0.0.0", port=8080)
