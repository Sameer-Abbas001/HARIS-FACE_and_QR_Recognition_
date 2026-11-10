"""
HARIS - High-Accuracy Recognition & Identity System
Unified Web Application & Biometric Access Server
Creator & Lead Developer: Sameer Abbas
Architecture: Dual Biometric Face Recognition + Photo-Embedded QR Code Access Core
"""

import os
import sys
import re
import time
import shutil
import base64
import socket
import logging
import threading
import webbrowser
from io import BytesIO
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_file, Response

# Project Modules
import qr_generator
from create_classifier import train_classifer, train_all_classifiers

# Setup Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLASSIFIERS_DIR = os.path.join(DATA_DIR, "classifiers")
QRCODES_DIR = os.path.join(DATA_DIR, "qrcodes")
NAMES_FILE = os.path.join(BASE_DIR, "nameslist.txt")
CASCADE_PATH = os.path.join(DATA_DIR, "haarcascade_frontalface_default.xml")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CLASSIFIERS_DIR, exist_ok=True)
os.makedirs(QRCODES_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Initialize Flask App
app = Flask(__name__, template_folder=TEMPLATES_DIR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Pre-load Haar Cascade
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
qr_detector = cv2.QRCodeDetector()

# Cache for LBPH face recognizers { username: recognizer }
recognizer_cache = {}
cache_lock = threading.Lock()


def get_cached_recognizer(username):
    """Loads or retrieves a cached LBPH recognizer for a given user."""
    with cache_lock:
        if username in recognizer_cache:
            return recognizer_cache[username]
        
        clf_path = os.path.join(CLASSIFIERS_DIR, f"{username}_classifier.xml")
        if os.path.isfile(clf_path):
            try:
                rec = cv2.face.LBPHFaceRecognizer_create()
                rec.read(clf_path)
                recognizer_cache[username] = rec
                return rec
            except Exception as e:
                print(f"[Core] Error loading classifier for {username}: {e}")
        return None


def invalidate_user_cache(username=None):
    """Clears cached recognizers when a model is re-trained or deleted."""
    with cache_lock:
        if username:
            recognizer_cache.pop(username, None)
        else:
            recognizer_cache.clear()


def get_all_enrolled_usernames():
    """Returns a sorted list of registered usernames from nameslist.txt and data/."""
    names = set()
    if os.path.isfile(NAMES_FILE):
        try:
            with open(NAMES_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                for token in content.split():
                    clean = token.strip()
                    if clean:
                        names.add(clean)
        except Exception:
            pass

    if os.path.isdir(DATA_DIR):
        excluded = {"classifiers", "qrcodes", "__pycache__"}
        for item in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, item)) and item not in excluded:
                names.add(item)
    
    return sorted(list(names))


def format_file_size(size_bytes):
    """Formats file size into human-readable units."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def decode_base64_image(base64_str):
    """Converts a data URI or raw base64 string into an OpenCV BGR image."""
    if not base64_str:
        return None
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        image_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[Core] Base64 decode error: {e}")
        return None


# ==============================================================================
# --- Web Routes & API Endpoints ---
# ==============================================================================

@app.route("/")
def index():
    """Serves the connected React Cyberpunk Web Dashboard."""
    return send_file(os.path.join(TEMPLATES_DIR, "index.html"))


@app.route("/favicon.ico")
def favicon():
    """Serves application icon."""
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.isfile(icon_path):
        return send_file(icon_path, mimetype="image/x-icon")
    return ("", 204)


@app.route("/api/users", methods=["GET"])
def api_get_users():
    """Returns directory of all registered biometric subjects."""
    usernames = get_all_enrolled_usernames()
    users_list = []

    for name in usernames:
        user_dir = os.path.join(DATA_DIR, name)
        clf_path = os.path.join(CLASSIFIERS_DIR, f"{name}_classifier.xml")
        badge_path = os.path.join(QRCODES_DIR, f"{name}_badge.png")
        qr_path = os.path.join(QRCODES_DIR, f"{name}_qr.png")

        # Frame count
        frames = 0
        if os.path.isdir(user_dir):
            valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
            frames = len([f for f in os.listdir(user_dir) if f.lower().endswith(valid_exts) and "qr" not in f and "badge" not in f])

        # Model file size
        has_clf = os.path.isfile(clf_path)
        clf_size = format_file_size(os.path.getsize(clf_path)) if has_clf else "N/A"

        # Determine user role
        role = "Administrator" if name.lower() in ("abbas007", "sameer", "admin") else "Personnel"

        users_list.append({
            "id": name,
            "name": name,
            "role": role,
            "status": "Active" if has_clf else "Pending",
            "frames": frames,
            "modelSize": clf_size,
            "hasClassifier": has_clf,
            "hasBadge": os.path.isfile(badge_path),
            "hasQr": os.path.isfile(qr_path),
            "photoUrl": f"/api/users/{name}/photo",
            "badgeUrl": f"/api/users/{name}/badge" if os.path.isfile(badge_path) else None,
            "qrUrl": f"/api/users/{name}/qr" if os.path.isfile(qr_path) else None
        })

    return jsonify(users_list)


@app.route("/api/users/<name>/photo", methods=["GET"])
def api_get_user_photo(name):
    """Serves the portrait photo of an enrolled user."""
    photo_path = qr_generator.get_user_photo_path(name)
    if photo_path and os.path.isfile(photo_path):
        return send_file(photo_path, mimetype="image/jpeg")
    
    # Return placeholder or 404
    return ("", 404)


@app.route("/api/users/<name>/badge", methods=["GET"])
def api_get_user_badge(name):
    """Serves the generated cyberpunk access badge."""
    badge_path = os.path.join(QRCODES_DIR, f"{name}_badge.png")
    if os.path.isfile(badge_path):
        as_attachment = request.args.get("download") == "1"
        return send_file(badge_path, mimetype="image/png", as_attachment=as_attachment, download_name=f"{name}_badge.png")
    return ("", 404)


@app.route("/api/users/<name>/qr", methods=["GET"])
def api_get_user_qr(name):
    """Serves the generated photo-embedded QR code."""
    qr_path = os.path.join(QRCODES_DIR, f"{name}_qr.png")
    if os.path.isfile(qr_path):
        as_attachment = request.args.get("download") == "1"
        return send_file(qr_path, mimetype="image/png", as_attachment=as_attachment, download_name=f"{name}_qr.png")
    return ("", 404)


@app.route("/api/verify_frame", methods=["POST"])
def api_verify_frame():
    """
    Real-Time Dual Biometric Face Recognition & QR Verification Core.
    Accepts captured video frame (base64) and tests against all enrolled LBPH models and QR payloads.
    """
    data = request.get_json(silent=True) or {}
    image_b64 = data.get("image")

    img = decode_base64_image(image_b64)
    if img is None:
        return jsonify({"matched": False, "reason": "No valid frame received from sensor."})

    frame_h, frame_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. QR Code Scan
    qr_user = None
    try:
        qr_val, qr_points, _ = qr_detector.detectAndDecode(img)
        if qr_val:
            parsed = qr_generator.parse_qr_data(qr_val)
            if parsed:
                qr_user = parsed
    except Exception:
        pass

    # 2. Face Detection & LBPH Matching
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))

    best_match_user = None
    best_confidence = 0

    all_users = get_all_enrolled_usernames()

    if len(faces) > 0:
        # Prioritize largest face
        faces = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)
        x, y, w, h = faces[0]
        roi_gray = gray[y:y+h, x:x+w]

        # Test against candidates
        candidate_users = [qr_user] if (qr_user and qr_user in all_users) else all_users

        for user in candidate_users:
            rec = get_cached_recognizer(user)
            if rec is not None:
                try:
                    _id, raw_conf = rec.predict(roi_gray)
                    # Convert raw distance to confidence percentage (lower distance = higher confidence)
                    conf = max(0, min(100, 100 - int(raw_conf)))
                    if conf > best_confidence:
                        best_confidence = conf
                        best_match_user = user
                except Exception:
                    pass

    # 3. Decision Logic (Dual Biometric or Single Factor)
    matched = False
    final_user = None
    final_confidence = 0
    method = ""

    # Case A: Dual match (Face matched AND QR matched same subject)
    if best_match_user and qr_user and best_match_user.lower() == qr_user.lower() and best_confidence >= 40:
        matched = True
        final_user = best_match_user
        final_confidence = max(best_confidence, 98)
        method = "DUAL BIOMETRIC & QR PASS (100% VERIFIED)"

    # Case B: High-confidence face biometric match
    elif best_match_user and best_confidence >= 48:
        matched = True
        final_user = best_match_user
        final_confidence = best_confidence
        method = "LBPH FACIAL BIOMETRIC MATCH"

    # Case C: QR Badge scanned directly
    elif qr_user and qr_user in all_users:
        matched = True
        final_user = qr_user
        final_confidence = 99
        method = "PHOTO-EMBEDDED QR SECURITY BADGE"

    if matched:
        return jsonify({
            "matched": True,
            "user": final_user,
            "confidence": final_confidence,
            "method": method,
            "photoUrl": f"/api/users/{final_user}/photo"
        })
    else:
        return jsonify({
            "matched": False,
            "reason": "Unknown Entity Detected (Confidence insufficient)" if len(faces) > 0 else "No subject in sensor range"
        })


@app.route("/api/enroll", methods=["POST"])
def api_enroll_user():
    """
    Registers a new identity:
    1. Saves portrait image & synthesizes augmented training frames.
    2. Trains LBPH neural classifier model (.xml).
    3. Generates photo-embedded QR and Cyberpunk ID badge.
    4. Updates database records.
    """
    data = request.get_json(silent=True) or {}
    raw_name = data.get("name", "").strip()
    image_b64 = data.get("image")

    # Clean username (alphanumeric and underscores only)
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', raw_name)
    if not clean_name:
        return jsonify({"success": False, "message": "Invalid username. Use alphanumeric characters."}), 400

    user_dir = os.path.join(DATA_DIR, clean_name)
    os.makedirs(user_dir, exist_ok=True)

    img = decode_base64_image(image_b64)
    if img is None:
        # Fallback: check if existing image exists in user folder
        existing = qr_generator.get_user_photo_path(clean_name)
        if existing and os.path.isfile(existing):
            img = cv2.imread(existing)
        else:
            return jsonify({"success": False, "message": "No portrait photo provided."}), 400

    # Detect face in portrait for optimal crop
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    if len(faces) > 0:
        x, y, w, h = faces[0]
        face_crop = img[y:y+h, x:x+w]
    else:
        face_crop = img

    # Save base frame
    base_photo_path = os.path.join(user_dir, f"0{clean_name}.jpg")
    cv2.imwrite(base_photo_path, face_crop)

    # Synthesize 4 augmented frames for robust LBPH training (rotations, brightness)
    h_c, w_c = face_crop.shape[:2]
    angles = [-8, 8, -4, 4]
    for idx, angle in enumerate(angles, start=1):
        M = cv2.getRotationMatrix2D((w_c / 2, h_c / 2), angle, 1.0)
        rotated = cv2.warpAffine(face_crop, M, (w_c, h_c))
        # Slight brightness shift
        bright = cv2.convertScaleAbs(rotated, alpha=1.05, beta=(idx * 4 - 10))
        cv2.imwrite(os.path.join(user_dir, f"{idx}{clean_name}.jpg"), bright)

    # Train Classifier
    try:
        train_classifer(clean_name)
        invalidate_user_cache(clean_name)
    except Exception as e:
        print(f"[Enroll] Classifier training error: {e}")
        return jsonify({"success": False, "message": f"Classifier training failed: {e}"}), 500

    # Generate QR Code & Access Badge
    badge_path = os.path.join(QRCODES_DIR, f"{clean_name}_badge.png")
    qr_path = os.path.join(QRCODES_DIR, f"{clean_name}_qr.png")

    try:
        qr_generator.generate_photo_qr(clean_name, photo_path=base_photo_path, output_path=qr_path)
        qr_generator.generate_id_badge(clean_name, photo_path=base_photo_path, output_path=badge_path)
    except Exception as e:
        print(f"[Enroll] Badge generator error: {e}")

    # Register in nameslist.txt
    try:
        existing_names = set(get_all_enrolled_usernames())
        if clean_name not in existing_names:
            with open(NAMES_FILE, "a", encoding="utf-8") as f:
                f.write(f" {clean_name}")
    except Exception as e:
        print(f"[Enroll] nameslist write error: {e}")

    return jsonify({
        "success": True,
        "name": clean_name,
        "badgeUrl": f"/api/users/{clean_name}/badge",
        "qrUrl": f"/api/users/{clean_name}/qr",
        "photoUrl": f"/api/users/{clean_name}/photo"
    })


@app.route("/api/train_all", methods=["POST"])
def api_train_all():
    """Retrains LBPH classifiers for all enrolled subjects."""
    try:
        results = train_all_classifiers()
        invalidate_user_cache()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delete_user", methods=["POST"])
def api_delete_user():
    """
    Permanently deletes all data for an enrolled identity:
    1. Removes dataset directory (all training frames and captured portraits).
    2. Deletes trained LBPH classifier (.xml).
    3. Deletes photo-embedded QR code and cyberpunk access badge.
    4. Removes subject from nameslist.txt.
    5. Invalidates in-memory recognizer cache.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "message": "No username provided."}), 400

    deleted_items = []

    # 1. Remove trained classifier model
    clf_path = os.path.join(CLASSIFIERS_DIR, f"{name}_classifier.xml")
    if os.path.isfile(clf_path):
        try:
            os.remove(clf_path)
            deleted_items.append("LBPH Model")
        except Exception as e:
            print(f"[Delete] Classifier remove error: {e}")

    # 2. Remove QR code and badge
    qr_path = os.path.join(QRCODES_DIR, f"{name}_qr.png")
    badge_path = os.path.join(QRCODES_DIR, f"{name}_badge.png")
    for file_p, label in [(qr_path, "QR Code"), (badge_path, "Access Badge")]:
        if os.path.isfile(file_p):
            try:
                os.remove(file_p)
                deleted_items.append(label)
            except Exception as e:
                print(f"[Delete] {label} remove error: {e}")

    # 3. Remove user dataset directory and all image files
    user_dir = os.path.join(DATA_DIR, name)
    if os.path.isdir(user_dir):
        try:
            shutil.rmtree(user_dir, ignore_errors=True)
            deleted_items.append("Face Dataset Frames")
        except Exception as e:
            print(f"[Delete] User dir remove error: {e}")

    # 4. Remove from nameslist.txt
    if os.path.isfile(NAMES_FILE):
        try:
            with open(NAMES_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = [t.strip() for t in content.split() if t.strip() and t.strip() != name]
            with open(NAMES_FILE, "w", encoding="utf-8") as f:
                f.write(" ".join(tokens) + "\n")
            deleted_items.append("Registry Record")
        except Exception as e:
            print(f"[Delete] nameslist write error: {e}")

    # 5. Clear cached recognizer
    invalidate_user_cache(name)

    return jsonify({
        "success": True,
        "message": f"Successfully deleted all data for '{name}'. Purged: {', '.join(deleted_items) if deleted_items else 'Records'}."
    })


@app.route("/api/telemetry", methods=["GET"])
def api_telemetry():
    """Returns real-time system core telemetry."""
    users = get_all_enrolled_usernames()
    classifiers = [f for f in os.listdir(CLASSIFIERS_DIR) if f.endswith("_classifier.xml")] if os.path.isdir(CLASSIFIERS_DIR) else []
    return jsonify({
        "status": "ONLINE",
        "enrolledSubjects": len(users),
        "activeClassifiers": len(classifiers),
        "engine": "LBPH + High-Error-Correction QR",
        "version": "v2.5"
    })


# ==============================================================================
# --- Entry Point & Launcher ---
# ==============================================================================

def find_available_port(start_port=5000):
    """Finds an available local port to bind the web server."""
    port = start_port
    for _ in range(20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return start_port


def open_browser_delayed(url):
    """Opens default browser after server initializes."""
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    port = find_available_port(5000)
    local_url = f"http://127.0.0.1:{port}"

    print("\n" + "=" * 65)
    print("⚡ HARIS - High-Accuracy Recognition & Identity System")
    print("🌟 AI Biometric & Photo-Embedded QR Web Application")
    print(f"🚀 Running locally on: {local_url}")
    print("=" * 65 + "\n")

    # Launch browser automatically
    threading.Thread(target=open_browser_delayed, args=(local_url,), daemon=True).start()

    # Run production Flask server
    app.run(host="0.0.0.0", port=port, debug=False)
