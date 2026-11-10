"""
HARIS - Fast Face Dataset Capture Module
Creator & Lead Developer: Sameer Abbas
"""

import cv2
import os
import qr_generator

def start_capture(name, target_frames=4):
    path = os.path.join("data", name)
    num_of_images = 0
    cascade_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "haarcascade_frontalface_default.xml")
    detector = cv2.CascadeClassifier(cascade_p)
    os.makedirs(path, exist_ok=True)
    
    vid = cv2.VideoCapture(0)
    if not vid.isOpened():
        print("[Dataset] Error: Could not open webcam.")
        return 0

    while True:
        ret, img = vid.read()
        if not ret:
            break
            
        new_img = None
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face = detector.detectMultiScale(image=grayimg, scaleFactor=1.1, minNeighbors=5)
        
        for x, y, w, h in face:
            # Cyberpunk target brackets
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 242, 254), 2)
            cv2.putText(img, f"Face Detected: {name}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 242, 254), 2)
            
            # Save cropped face
            new_img = img[y:y+h, x:x+w]

        # Top HUD Status Bar
        cv2.rectangle(img, (10, 10), (320, 60), (15, 23, 42), -1)
        cv2.rectangle(img, (10, 10), (320, 60), (56, 189, 248), 1)
        cv2.putText(img, f"Target: {num_of_images} / {target_frames} frames", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(img, "Press 'Q' or ESC to stop", (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1)

        cv2.imshow("HARIS - Real-Time Dataset Capture (4 Frames)", img)
        key = cv2.waitKey(1) & 0xFF

        if new_img is not None and new_img.size > 0:
            try:
                cv2.imwrite(os.path.join(path, f"{num_of_images}{name}.jpg"), new_img)
                num_of_images += 1
            except Exception as e:
                pass

        if key == ord("q") or key == 27 or num_of_images >= target_frames:
            break

    vid.release()
    cv2.destroyAllWindows()

    # Automatically generate Photo-QR code if images were captured
    if num_of_images > 0:
        try:
            qr_generator.generate_photo_qr(name)
            qr_generator.generate_id_badge(name)
        except Exception as e:
            print(f"[Dataset] QR auto-generation notice: {e}")

    return num_of_images


def take_video(name, video, target_frames=4):
    path = os.path.join("data", name)
    num_of_images = 0
    cascade_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "haarcascade_frontalface_default.xml")
    detector = cv2.CascadeClassifier(cascade_p)
    os.makedirs(path, exist_ok=True)
    
    vid = cv2.VideoCapture(video)
    if not vid.isOpened():
        print("Error: Could not open video file.")
        return 0

    while True:
        ret, img = vid.read()
        if not ret:
            break
            
        new_img = None
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face = detector.detectMultiScale(image=grayimg, scaleFactor=1.1, minNeighbors=5)
        
        for x, y, w, h in face:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 242, 254), 2)
            cv2.putText(img, f"Face Detected: {name}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 242, 254), 2)
            new_img = img[y:y+h, x:x+w]

        cv2.imshow("HARIS - Video Extraction", img)
        key = cv2.waitKey(1) & 0xFF
        
        if new_img is not None and new_img.size > 0:
            try:
                cv2.imwrite(os.path.join(path, f"{num_of_images}{name}.jpg"), new_img)
                num_of_images += 1
            except Exception:
                pass

        if key == ord("q") or key == 27 or num_of_images >= target_frames:
            break

    vid.release()
    cv2.destroyAllWindows()
    return num_of_images

