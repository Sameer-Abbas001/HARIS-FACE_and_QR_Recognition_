"""
HARIS - QR Code & Biometric ID Badge Generator
Creator & Lead Developer: Sameer Abbas
Embeds user portrait photographs inside high-error-correction QR codes
and creates cybernetic access passes for real-time verification.
"""

import os
import cv2
import numpy as np
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont


def load_font(size, bold=False):
    """
    Safely loads the cleanest available TrueType font on Windows, Linux (EC2), or Docker.
    Falls back gracefully to default PIL font if no TTF is found.
    """
    candidates_bold = [
        "arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    candidates_reg = [
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "DejaVuSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def get_user_photo_path(name):
    """
    Finds the best available reference photo for a registered user.
    Looks in ./data/<name>/ or ./data/qrcodes/
    """
    user_dir = os.path.join("data", name)
    if os.path.isdir(user_dir):
        # Preferred photos: 0<name>.jpg, 1<name>.jpg, or any .jpg/.png
        for filename in [f"0{name}.jpg", f"1{name}.jpg", f"2{name}.jpg", f"3{name}.jpg", f"photo_{name}.jpg"]:
            full_p = os.path.join(user_dir, filename)
            if os.path.isfile(full_p):
                return full_p
        
        # Fallback to any image file in user directory
        for f in sorted(os.listdir(user_dir)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                return os.path.join(user_dir, f)

    return None


def generate_photo_qr(name, photo_path=None, output_path=None, payload=None):
    """
    Generates a high-error-correction QR Code with a user photo embedded in the center.
    Payload defaults to 'HARIS:USER:<name>'
    """
    if payload is None:
        payload = f"HARIS:USER:{name}"

    os.makedirs(os.path.join("data", "qrcodes"), exist_ok=True)
    if output_path is None:
        output_path = os.path.join("data", "qrcodes", f"{name}_qr.png")

    if photo_path is None or not os.path.isfile(photo_path):
        photo_path = get_user_photo_path(name)

    # 1. Create QR code with High Error Correction (H = ~30% recovery capacity)
    qr = qrcode.QRCode(
        version=None,  # Auto size
        error_correction=ERROR_CORRECT_H,
        box_size=12,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    # QR Base Image in RGB
    qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert("RGBA")
    qr_w, qr_h = qr_img.size

    # 2. Embed user photo if available
    if photo_path and os.path.isfile(photo_path):
        try:
            face_img = Image.open(photo_path).convert("RGBA")

            # Center logo size ~ 25% of QR width for optimal scan reliability
            logo_size = int(qr_w * 0.26)
            face_img = face_img.resize((logo_size, logo_size), Image.LANCZOS)

            # Create rounded mask with glowing border
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            radius = int(logo_size * 0.25)
            draw_mask.rounded_rectangle([(0, 0), (logo_size - 1, logo_size - 1)], radius=radius, fill=255)

            # Create a stylish border container for the photo
            border_pad = 6
            container_size = logo_size + border_pad * 2
            container = Image.new("RGBA", (container_size, container_size), (15, 23, 42, 255))
            draw_con = ImageDraw.Draw(container)
            draw_con.rounded_rectangle(
                [(0, 0), (container_size - 1, container_size - 1)],
                radius=radius + 2,
                fill="#0f172a",
                outline="#38bdf8",
                width=3
            )

            # Paste face into container
            container.paste(face_img, (border_pad, border_pad), mask)

            # Paste container into center of QR code
            pos_x = (qr_w - container_size) // 2
            pos_y = (qr_h - container_size) // 2
            qr_img.paste(container, (pos_x, pos_y), container)

        except Exception as e:
            print(f"[QR] Warning: Could not embed photo: {e}")

    # Convert to RGB and save
    final_img = qr_img.convert("RGB")
    final_img.save(output_path, "PNG", quality=95)
    return output_path


def generate_id_badge(name, photo_path=None, output_path=None):
    """
    Creates a full cybernetic ID Badge Card containing the photo, QR code,
    and user verification credentials.
    """
    os.makedirs(os.path.join("data", "qrcodes"), exist_ok=True)
    if output_path is None:
        output_path = os.path.join("data", "qrcodes", f"{name}_badge.png")

    if photo_path is None or not os.path.isfile(photo_path):
        photo_path = get_user_photo_path(name)

    # First ensure Photo-QR code is generated
    qr_path = os.path.join("data", "qrcodes", f"{name}_qr.png")
    generate_photo_qr(name, photo_path=photo_path, output_path=qr_path)

    # Badge Dimensions (Sleek Cyber Card: 540 x 780)
    card_w, card_h = 540, 780
    badge = Image.new("RGB", (card_w, card_h), "#0b1120")
    draw = ImageDraw.Draw(badge)

    # 1. Outer Holographic Border & Header Gradient
    draw.rounded_rectangle([(10, 10), (card_w - 10, card_h - 10)], radius=20, outline="#38bdf8", width=3)
    draw.rounded_rectangle([(16, 16), (card_w - 16, card_h - 16)], radius=16, outline="#1e293b", width=2)
    
    # Top Header Bar
    draw.rounded_rectangle([(16, 16), (card_w - 16, 90)], radius=16, fill="#0f172a")
    draw.rectangle([(16, 75), (card_w - 16, 90)], fill="#0f172a") # Flatten bottom curve

    # Header Accent line
    draw.line([(30, 90), (card_w - 30, 90)], fill="#38bdf8", width=2)

    # Load fonts with cross-platform Linux/Windows fallbacks
    font_title = load_font(24, bold=True)
    font_sub = load_font(14, bold=False)
    font_name = load_font(26, bold=True)
    font_meta = load_font(13, bold=False)
    font_meta_b = load_font(14, bold=True)

    # Header Text
    draw.text((card_w // 2, 40), "HARIS ACCESS CONTROL", fill="#38bdf8", font=font_title, anchor="mm")
    draw.text((card_w // 2, 68), "BIOMETRIC & QR IDENTITY PASS", fill="#94a3b8", font=font_sub, anchor="mm")

    # 2. User Portrait Photo
    photo_box_size = 150
    photo_y = 115
    photo_x = (card_w - photo_box_size) // 2

    # Draw photo border
    draw.rounded_rectangle(
        [(photo_x - 4, photo_y - 4), (photo_x + photo_box_size + 4, photo_y + photo_box_size + 4)],
        radius=14, fill="#1e293b", outline="#ff4500", width=2
    )

    if photo_path and os.path.isfile(photo_path):
        try:
            face_img = Image.open(photo_path).convert("RGBA")
            face_img = face_img.resize((photo_box_size, photo_box_size), Image.LANCZOS)
            mask = Image.new("L", (photo_box_size, photo_box_size), 0)
            draw_m = ImageDraw.Draw(mask)
            draw_m.rounded_rectangle([(0, 0), (photo_box_size, photo_box_size)], radius=12, fill=255)
            badge.paste(face_img, (photo_x, photo_y), mask)
        except Exception:
            draw.text((card_w // 2, photo_y + photo_box_size // 2), "[PORTRAIT]", fill="#64748b", font=font_meta, anchor="mm")
    else:
        draw.text((card_w // 2, photo_y + photo_box_size // 2), "[PORTRAIT]", fill="#64748b", font=font_meta, anchor="mm")

    # 3. User Name & Status Badge
    name_y = photo_y + photo_box_size + 28
    draw.text((card_w // 2, name_y), name.upper(), fill="#ffffff", font=font_name, anchor="mm")

    status_pill_y = name_y + 24
    draw.rounded_rectangle(
        [(card_w // 2 - 110, status_pill_y - 12), (card_w // 2 + 110, status_pill_y + 12)],
        radius=10, fill="#064e3b", outline="#10b981", width=1
    )
    draw.text((card_w // 2, status_pill_y), "● BIOMETRIC VERIFIED", fill="#34d399", font=font_meta_b, anchor="mm")

    # 4. Embedded QR Code
    if os.path.isfile(qr_path):
        try:
            qr_img = Image.open(qr_path).convert("RGBA")
            qr_display_size = 230
            qr_img = qr_img.resize((qr_display_size, qr_display_size), Image.LANCZOS)
            qr_x = (card_w - qr_display_size) // 2
            qr_y = status_pill_y + 30

            # QR background plate
            draw.rounded_rectangle(
                [(qr_x - 6, qr_y - 6), (qr_x + qr_display_size + 6, qr_y + qr_display_size + 6)],
                radius=14, fill="#ffffff", outline="#38bdf8", width=2
            )
            badge.paste(qr_img, (qr_x, qr_y), qr_img)
        except Exception as e:
            print(f"[Badge] Error drawing QR: {e}")

    # 5. Footer Metadata
    footer_y = card_h - 45
    draw.line([(40, footer_y - 15), (card_w - 40, footer_y - 15)], fill="#1e293b", width=1)
    draw.text((card_w // 2, footer_y - 2), "OFFICIAL HARIS NEURAL RECOGNITION TOKEN", fill="#64748b", font=font_meta, anchor="mm")
    draw.text((card_w // 2, footer_y + 14), f"TOKEN ID: HARIS-SEC-{abs(hash(name)) % 1000000:06d}", fill="#38bdf8", font=font_meta, anchor="mm")

    badge.save(output_path, "PNG", quality=95)
    return output_path


def parse_qr_data(decoded_text):
    """
    Parses decoded text from a QR code.
    Extracts user name if format is 'HARIS:USER:<name>' or raw text.
    """
    if not decoded_text:
        return None
    
    text = decoded_text.strip()
    if text.startswith("HARIS:USER:"):
        return text.split("HARIS:USER:", 1)[1].strip()
    elif text.startswith("USER:"):
        return text.split("USER:", 1)[1].strip()
    return text
