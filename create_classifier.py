"""
HARIS - Face Classifier Training Module
Creator & Lead Developer: Sameer Abbas
"""

import numpy as np
from PIL import Image
import os
import cv2


# Method to train custom classifier to recognize face
def train_classifer(name):
    path = os.path.join("data", name)
    if not os.path.isdir(path):
        raise FileNotFoundError(f"User dataset directory '{path}' not found.")

    faces = []
    ids = []
    
    # Supported image formats
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    pictures = [f for f in sorted(os.listdir(path)) if f.lower().endswith(valid_extensions)]
    
    if not pictures:
        raise ValueError(f"No face images found in '{path}' to train classifier.")

    for i, pic in enumerate(pictures):
        # Skip QR code or badge images if stored in user folder
        if "badge" in pic.lower() or "qr" in pic.lower():
            continue

        imgpath = os.path.join(path, pic)
        try:
            img = Image.open(imgpath).convert('L')
            imageNp = np.array(img, 'uint8')

            # Safely extract numeric ID or use sequential index
            prefix = pic.split(name)[0] if name in pic else ""
            if prefix.isdigit():
                img_id = int(prefix)
            else:
                img_id = i + 1

            faces.append(imageNp)
            ids.append(img_id)
        except Exception as e:
            print(f"[Classifier] Skipping {pic}: {e}")
            continue

    if not faces:
        raise ValueError(f"No valid face images could be processed in '{path}'.")

    ids = np.array(ids, dtype=np.int32)

    # Ensure classifier output directory exists
    os.makedirs(os.path.join("data", "classifiers"), exist_ok=True)
    
    # Train and save classifier
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    output_path = os.path.join("data", "classifiers", f"{name}_classifier.xml")
    clf.write(output_path)
    return True


def train_all_classifiers():
    """
    Scans data directory and trains classifiers for all enrolled users.
    Returns dictionary with training results per user.
    """
    results = {}
    data_dir = "data"
    if not os.path.isdir(data_dir):
        return results

    # Find candidate user directories (exclude classifiers and qrcodes)
    excluded = {"classifiers", "qrcodes", "__pycache__"}
    for item in os.listdir(data_dir):
        full_p = os.path.join(data_dir, item)
        if os.path.isdir(full_p) and item not in excluded:
            try:
                success = train_classifer(item)
                results[item] = "Success" if success else "Failed"
            except Exception as e:
                results[item] = f"Error: {e}"

    return results
