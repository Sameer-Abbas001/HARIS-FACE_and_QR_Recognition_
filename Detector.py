"""
HARIS - Real-Time AI Biometric & QR Access Detector
Creator & Lead Developer: Sameer Abbas
"""

import cv2
import os
import numpy as np
from time import time
try:
    from tkinter import messagebox
except (ImportError, ModuleNotFoundError):
    messagebox = None
from PIL import Image
import qr_generator


def load_cached_user_photo(name, size=(110, 110)):
    """
    Loads and resizes user reference photo as an OpenCV BGR image for HUD overlay.
    """
    photo_path = qr_generator.get_user_photo_path(name)
    if photo_path and os.path.isfile(photo_path):
        try:
            img = cv2.imread(photo_path)
            if img is not None:
                return cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        except Exception:
            pass
    return None


def overlay_image(background, foreground, x, y):
    """Safely overlays a smaller BGR/BGRA image onto background at (x, y)."""
    h_bg, w_bg = background.shape[:2]
    h_fg, w_fg = foreground.shape[:2]

    if x >= w_bg or y >= h_bg:
        return background

    # Clip dimensions if out of bounds
    w = min(w_fg, w_bg - x)
    h = min(h_fg, h_bg - y)

    if foreground.shape[2] == 4:
        # Alpha blending
        alpha = foreground[:h, :w, 3] / 255.0
        for c in range(3):
            background[y:y+h, x:x+w, c] = (
                alpha * foreground[:h, :w, c] +
                (1.0 - alpha) * background[y:y+h, x:x+w, c]
            )
    else:
        background[y:y+h, x:x+w] = foreground[:h, :w]

    return background


def main_app(name=None, timeout=8):
    """
    Real-time Access Control Detector:
    Simultaneously runs LBPH Face Recognition and QR Code Detection.
    Renders live cyberpunk HUD, confidence indicators, and displays matched user photo.
    """
    base_p = os.path.dirname(os.path.abspath(__file__))
    face_cascade = cv2.CascadeClassifier(os.path.join(base_p, 'data', 'haarcascade_frontalface_default.xml'))
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Load classifier for active user if available
    classifier_loaded = False
    if name:
        classifier_path = os.path.join(base_p, 'data', 'classifiers', f"{name}_classifier.xml")
        if os.path.isfile(classifier_path):
            try:
                recognizer.read(classifier_path)
                classifier_loaded = True
            except Exception as e:
                print(f"[Detector] Classifier read error: {e}")

    # Load QR detector
    qr_detector = cv2.QRCodeDetector()

    # Pre-cache target user photo for HUD overlay
    cached_photo = load_cached_user_photo(name) if name else None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        if messagebox:
            messagebox.showerror("Camera Error", "Could not open camera stream.")
        else:
            print("[Detector Error] Could not open camera stream.")
        return

    face_matched = False
    qr_matched = False
    detected_qr_user = None
    start_time = time()
    consecutive_matches = 0
    REQUIRED_MATCHES = 15  # ~0.5s of stable detection before auto check-in

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_h, frame_w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Real-Time Face Detection & Recognition
        faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
        current_face_matched = False

        for (x, y, w, h) in faces:
            confidence = 0
            if classifier_loaded and name:
                roi_gray = gray[y:y+h, x:x+w]
                try:
                    _id, raw_conf = recognizer.predict(roi_gray)
                    confidence = max(0, min(100, 100 - int(raw_conf)))
                except Exception:
                    confidence = 0

            if confidence > 45:
                current_face_matched = True
                face_matched = True
                box_color = (0, 255, 128)  # Emerald green
                label_text = f"FACE: {name.upper()} ({confidence}%)"
            else:
                box_color = (0, 165, 255)  # Cyber orange
                label_text = f"FACE SCANNING ({confidence}%)" if name else "FACE DETECTED"

            # Draw Cyber Corner Brackets
            d = 20
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 1)
            # Top-left corner
            cv2.line(frame, (x, y), (x + d, y), box_color, 3)
            cv2.line(frame, (x, y), (x, y + d), box_color, 3)
            # Top-right corner
            cv2.line(frame, (x + w, y), (x + w - d, y), box_color, 3)
            cv2.line(frame, (x + w, y), (x + w, y + d), box_color, 3)
            # Bottom-left corner
            cv2.line(frame, (x, y + h), (x + d, y + h), box_color, 3)
            cv2.line(frame, (x, y + h), (x, y + h - d), box_color, 3)
            # Bottom-right corner
            cv2.line(frame, (x + w, y + h), (x + w - d, y + h), box_color, 3)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - d), box_color, 3)

            # Label banner
            cv2.rectangle(frame, (x, y - 26), (x + w, y), (15, 23, 42), -1)
            cv2.putText(frame, label_text, (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.52, box_color, 2)

        # 2. Real-Time QR Code Detection & Decoding
        current_qr_matched = False
        try:
            qr_val, qr_points, _ = qr_detector.detectAndDecode(frame)
            if qr_val and qr_points is not None:
                parsed_name = qr_generator.parse_qr_data(qr_val)
                detected_qr_user = parsed_name
                qr_color = (255, 242, 0)  # Bright Cyan

                if name and parsed_name and parsed_name.lower() == name.lower():
                    current_qr_matched = True
                    qr_matched = True
                    qr_color = (0, 255, 0)
                    qr_label = f"QR BADGE VERIFIED: {name.upper()}"
                else:
                    qr_label = f"QR DECODED: {parsed_name}"

                # Draw QR Bounding Polygon
                pts = qr_points[0].astype(int)
                for j in range(len(pts)):
                    cv2.line(frame, tuple(pts[j]), tuple(pts[(j + 1) % len(pts)]), qr_color, 3)
                
                qr_top = min(p[1] for p in pts)
                qr_left = min(p[0] for p in pts)
                cv2.rectangle(frame, (qr_left, qr_top - 28), (qr_left + 280, qr_top), (15, 23, 42), -1)
                cv2.putText(frame, qr_label, (qr_left + 6, qr_top - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.52, qr_color, 2)
                
                # Dynamically load photo for this QR user if different
                if not cached_photo and parsed_name:
                    cached_photo = load_cached_user_photo(parsed_name)
        except Exception:
            pass

        # Check consecutive matches for seamless auto check-in
        if (face_matched and qr_matched) or (face_matched and not name) or (current_face_matched or current_qr_matched):
            consecutive_matches += 1
        else:
            consecutive_matches = max(0, consecutive_matches - 1)

        # 3. Heads-Up Display (HUD) Overlays
        # Top HUD Bar
        cv2.rectangle(frame, (10, 10), (frame_w - 10, 75), (15, 23, 42), -1)
        cv2.rectangle(frame, (10, 10), (frame_w - 10, 75), (56, 189, 248), 1)

        cv2.putText(frame, "HARIS DUAL BIOMETRIC & QR DETECTOR", (25, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (56, 189, 248), 2)

        face_stat = f"FACE ID: {'MATCHED' if face_matched else 'SCANNING...'}"
        face_col = (0, 255, 128) if face_matched else (148, 163, 184)
        cv2.putText(frame, face_stat, (25, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, face_col, 1)

        qr_stat = f"QR PASS: {detected_qr_user.upper() if detected_qr_user else ('MATCHED' if qr_matched else 'SCANNING...')}"
        qr_col = (0, 255, 0) if qr_matched else (148, 163, 184)
        cv2.putText(frame, qr_stat, (260, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, qr_col, 1)

        # Right Side HUD - Reference Photo Overlay
        if cached_photo is not None:
            hud_photo_x = frame_w - 130
            hud_photo_y = 85
            cv2.rectangle(frame, (hud_photo_x - 4, hud_photo_y - 4), (hud_photo_x + 114, hud_photo_y + 114), (15, 23, 42), -1)
            cv2.rectangle(frame, (hud_photo_x - 4, hud_photo_y - 4), (hud_photo_x + 114, hud_photo_y + 114), (0, 242, 254), 2)
            overlay_image(frame, cached_photo, hud_photo_x, hud_photo_y)
            cv2.putText(frame, "REF PHOTO", (hud_photo_x + 10, hud_photo_y + 130), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 242, 254), 1)

        # Bottom HUD Controls Prompt
        cv2.rectangle(frame, (10, frame_h - 40), (frame_w - 10, frame_h - 10), (15, 23, 42), -1)
        cv2.putText(frame, "Press 'Q' or ESC to Exit | Place Face and/or QR Code in View", (25, frame_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (203, 213, 225), 1)

        # 4. Access Granted Banner Overlay
        if (face_matched and qr_matched) or consecutive_matches >= REQUIRED_MATCHES:
            cv2.rectangle(frame, (frame_w // 2 - 200, frame_h // 2 - 45), (frame_w // 2 + 200, frame_h // 2 + 45), (6, 78, 59), -1)
            cv2.rectangle(frame, (frame_w // 2 - 200, frame_h // 2 - 45), (frame_w // 2 + 200, frame_h // 2 + 45), (16, 185, 129), 3)
            cv2.putText(frame, "ACCESS GRANTED", (frame_w // 2 - 140, frame_h // 2 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(frame, "IDENTITY VERIFIED 100%", (frame_w // 2 - 120, frame_h // 2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (52, 211, 153), 2)

        cv2.imshow("HARIS - Real-Time AI Detection & Access Core", frame)
        key = cv2.waitKey(20) & 0xFF

        elapsed_time = time() - start_time
        if consecutive_matches >= REQUIRED_MATCHES or (elapsed_time >= timeout and (face_matched or qr_matched)):
            cap.release()
            cv2.destroyAllWindows()
            user_title = name or detected_qr_user or "User"
            if messagebox:
                messagebox.showinfo("Access Granted", f"Congratulations {user_title}!\nYou have been successfully verified and checked in.")
            else:
                print(f"[Detector] Access Granted for {user_title}!")
            return True

        if elapsed_time >= timeout and not (face_matched or qr_matched):
            cap.release()
            cv2.destroyAllWindows()
            if messagebox:
                messagebox.showwarning("Verification Notice", "Face or QR Code not confidently detected. Please try again.")
            else:
                print("[Detector] Verification timeout: Face or QR Code not confidently detected.")
            return False

        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return False

        
        
