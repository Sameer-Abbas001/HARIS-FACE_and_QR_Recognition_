"""
HARIS - High-Accuracy Recognition & Identity System
Creator & Lead Developer: Sameer Abbas
Architecture: Dual Biometric Face Recognition + Photo-Embedded QR Code Access Control Core
"""

import math
import os
import random
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk

# Project Modules
from Detector import main_app
from create_classifier import train_classifer
from create_dataset import start_capture
import qr_generator

# Global set of registered names
names = set()


# ==============================================================================
# --- Utility Functions for Color and Math ---
# ==============================================================================

def hex_to_rgb(hex_color):
    """Converts HEX string (e.g. '#1a2b3c') to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_tuple):
    """Converts RGB tuple to HEX string."""
    r = max(0, min(255, int(rgb_tuple[0])))
    g = max(0, min(255, int(rgb_tuple[1])))
    b = max(0, min(255, int(rgb_tuple[2])))
    return f"#{r:02x}{g:02x}{b:02x}"


def interpolate_color(color1, color2, factor):
    """Interpolates between color1 and color2 by factor (0.0 to 1.0)."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    r = rgb1[0] + (rgb2[0] - rgb1[0]) * factor
    g = rgb1[1] + (rgb2[1] - rgb1[1]) * factor
    b = rgb1[2] + (rgb2[2] - rgb1[2]) * factor
    return rgb_to_hex((r, g, b))


def center_grid_widgets(frame, rows, columns):
    """Configures rows/columns to center widgets in a grid layout."""
    for i in range(rows):
        frame.grid_rowconfigure(i, weight=1)
    for j in range(columns):
        frame.grid_columnconfigure(j, weight=1)


# ==============================================================================
# --- Animation Engine: Smooth Widget Color Transitions & Tactile Physics ---
# ==============================================================================

def animate_color_fade(widget, property_name, start_hex, end_hex, duration_ms=160, steps=10, current_step=0, callback_id_holder=None):
    """
    Smoothly fades widget color (bg or fg) from start_hex to end_hex.
    Non-blocking, uses widget.after(), safely handles destroyed widgets.
    """
    if not widget.winfo_exists():
        return

    factor = current_step / float(steps)
    curr_color = interpolate_color(start_hex, end_hex, factor)

    try:
        if property_name == 'bg':
            widget.config(bg=curr_color, activebackground=curr_color)
        elif property_name == 'fg':
            widget.config(fg=curr_color, activeforeground=curr_color)
    except tk.TclError:
        return

    if current_step < steps:
        delay = max(10, duration_ms // steps)
        after_id = widget.after(
            delay,
            animate_color_fade,
            widget,
            property_name,
            start_hex,
            end_hex,
            duration_ms,
            steps,
            current_step + 1,
            callback_id_holder
        )
        if callback_id_holder is not None:
            callback_id_holder['id'] = after_id


def add_advanced_button_effects(widget, default_bg, hover_bg, default_fg="#FFFFFF", hover_fg="#FFFFFF", active_bg=None):
    """
    Adds smooth color fading on hover, glowing text color, and tactile click physics.
    """
    if active_bg is None:
        active_bg = interpolate_color(hover_bg, "#000000", 0.25)

    holder_bg = {'id': None}
    holder_fg = {'id': None}

    def on_enter(e):
        if not widget.winfo_exists():
            return
        if holder_bg['id']:
            widget.after_cancel(holder_bg['id'])
        if holder_fg['id']:
            widget.after_cancel(holder_fg['id'])
        current_bg = widget.cget('bg')
        animate_color_fade(widget, 'bg', current_bg, hover_bg, duration_ms=140, steps=8, callback_id_holder=holder_bg)
        if default_fg != hover_fg:
            current_fg = widget.cget('fg')
            animate_color_fade(widget, 'fg', current_fg, hover_fg, duration_ms=140, steps=8, callback_id_holder=holder_fg)

    def on_leave(e):
        if not widget.winfo_exists():
            return
        if holder_bg['id']:
            widget.after_cancel(holder_bg['id'])
        if holder_fg['id']:
            widget.after_cancel(holder_fg['id'])
        current_bg = widget.cget('bg')
        animate_color_fade(widget, 'bg', current_bg, default_bg, duration_ms=180, steps=10, callback_id_holder=holder_bg)
        if default_fg != hover_fg:
            current_fg = widget.cget('fg')
            animate_color_fade(widget, 'fg', current_fg, default_fg, duration_ms=180, steps=10, callback_id_holder=holder_fg)

    def on_press(e):
        if not widget.winfo_exists():
            return
        widget.config(relief="sunken", bg=active_bg)

    def on_release(e):
        if not widget.winfo_exists():
            return
        widget.config(relief="flat", bg=hover_bg)

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")
    widget.bind("<ButtonPress-1>", on_press, add="+")
    widget.bind("<ButtonRelease-1>", on_release, add="+")


def animate_glowing_text(widget, palette, delay=45, step=0, color_idx=0, steps_per_transition=24):
    """
    Creates a continuous smooth breathing/glowing color cycle on text labels.
    """
    if not widget.winfo_exists():
        return

    try:
        curr_color = palette[color_idx]
        next_color = palette[(color_idx + 1) % len(palette)]
        factor = step / float(steps_per_transition)
        color = interpolate_color(curr_color, next_color, factor)
        widget.config(fg=color)

        if step < steps_per_transition:
            widget.after(delay, animate_glowing_text, widget, palette, delay, step + 1, color_idx, steps_per_transition)
        else:
            widget.after(delay, animate_glowing_text, widget, palette, delay, 0, (color_idx + 1) % len(palette), steps_per_transition)
    except (tk.TclError, RuntimeError):
        pass


# ==============================================================================
# --- Animation Engine: Animated Cyber Particle Background ---
# ==============================================================================

class CyberParticleBackground(tk.Canvas):
    """
    High-tech interactive animated particle network background.
    Draws floating nodes, connecting cyber-lines, and subtle mouse-reactive ripples.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#060911", highlightthickness=0, bd=0, **kwargs)
        self.particles = []
        self.num_particles = 48
        self.width = 1200
        self.height = 800
        self.mouse_x = -1000
        self.mouse_y = -1000
        self.is_animating = True

        self.color_palette = ["#00f2fe", "#4facfe", "#6366f1", "#a855f7", "#ec4899", "#38bdf8", "#10b981"]
        self.bind("<Configure>", self.on_resize)
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Leave>", self.on_mouse_leave)

    def init_particles(self):
        self.particles.clear()
        w = max(400, self.width)
        h = max(300, self.height)
        for _ in range(self.num_particles):
            p = {
                'x': random.uniform(20, w - 20),
                'y': random.uniform(20, h - 20),
                'vx': random.uniform(-0.75, 0.75),
                'vy': random.uniform(-0.75, 0.75),
                'radius': random.uniform(2.0, 4.2),
                'base_radius': random.uniform(2.0, 4.2),
                'color': random.choice(self.color_palette),
                'pulse_speed': random.uniform(0.02, 0.05),
                'pulse_val': random.uniform(0, math.pi * 2)
            }
            self.particles.append(p)

    def on_resize(self, event):
        if event.width > 50 and event.height > 50:
            self.width = event.width
            self.height = event.height
            if not self.particles:
                self.init_particles()

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_mouse_leave(self, event):
        self.mouse_x = -1000
        self.mouse_y = -1000

    def start_animation(self):
        self.is_animating = True
        self.animate_frame()

    def stop_animation(self):
        self.is_animating = False

    def animate_frame(self):
        if not self.is_animating or not self.winfo_exists():
            return

        self.delete("particle")
        self.delete("line")
        self.delete("grid")

        w = self.width
        h = self.height

        # 1. Subtle Cyber Grid dots
        grid_spacing = 75
        for gx in range(0, w, grid_spacing):
            for gy in range(0, h, grid_spacing):
                self.create_oval(gx, gy, gx + 1.5, gy + 1.5, fill="#111c2e", outline="", tags="grid")

        # 2. Update & Draw Particles
        for i, p in enumerate(self.particles):
            p['x'] += p['vx']
            p['y'] += p['vy']

            if p['x'] <= 10 or p['x'] >= w - 10:
                p['vx'] *= -1
            if p['y'] <= 10 or p['y'] >= h - 10:
                p['vy'] *= -1

            # Mouse interaction (subtle gravity / repulsion)
            dx = self.mouse_x - p['x']
            dy = self.mouse_y - p['y']
            dist = math.hypot(dx, dy)
            if 1 < dist < 150:
                force = (150 - dist) / 150.0 * 0.4
                p['x'] -= (dx / dist) * force * 3
                p['y'] -= (dy / dist) * force * 3

            # Pulse radius
            p['pulse_val'] += p['pulse_speed']
            r = p['base_radius'] + math.sin(p['pulse_val']) * 1.0

            # Outer glow
            self.create_oval(
                p['x'] - r * 1.8, p['y'] - r * 1.8,
                p['x'] + r * 1.8, p['y'] + r * 1.8,
                fill="", outline=p['color'], width=1, tags="particle"
            )
            # Core
            self.create_oval(
                p['x'] - r, p['y'] - r,
                p['x'] + r, p['y'] + r,
                fill=p['color'], outline="", tags="particle"
            )

            # Connecting lines
            for j in range(i + 1, len(self.particles)):
                p2 = self.particles[j]
                pdist = math.hypot(p['x'] - p2['x'], p['y'] - p2['y'])
                if pdist < 115:
                    line_color = "#162842" if pdist > 70 else "#2563eb"
                    width = 1 if pdist > 55 else 1.5
                    self.create_line(p['x'], p['y'], p2['x'], p2['y'], fill=line_color, width=width, tags="line")

        # Next frame (~33 FPS)
        self.after(30, self.animate_frame)


# ==============================================================================
# --- Custom Styled Animated Progress Bar (4 Frames Target) ---
# ==============================================================================

class AnimatedProgressBar(tk.Canvas):
    """
    Sleek modern animated progress bar with smooth filling and glow text.
    Target frames adjusted to 4 for lightweight, memory-efficient enrollment.
    """
    def __init__(self, parent, width=420, height=26, max_value=4, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#111827", highlightthickness=1, highlightbackground="#374151", bd=0, **kwargs)
        self.w = width
        self.h = height
        self.max_val = max_value
        self.current_val = 0
        self.target_val = 0
        self.draw_bar()

    def set_value(self, val):
        self.target_val = min(self.max_val, max(0, val))
        self.smooth_update()

    def smooth_update(self):
        if not self.winfo_exists():
            return
        if self.current_val < self.target_val:
            self.current_val = min(self.target_val, self.current_val + max(1, (self.target_val - self.current_val) // 4))
            self.draw_bar()
            self.after(20, self.smooth_update)
        elif self.current_val > self.target_val:
            self.current_val = max(self.target_val, self.current_val - 1)
            self.draw_bar()
            self.after(20, self.smooth_update)
        else:
            self.draw_bar()

    def draw_bar(self):
        self.delete("all")
        self.create_rectangle(0, 0, self.w, self.h, fill="#0f172a", outline="")
        
        fill_w = int((self.current_val / float(self.max_val)) * self.w)
        if fill_w > 0:
            ratio = self.current_val / float(self.max_val)
            color = interpolate_color("#ff4500", "#10b981", ratio)
            self.create_rectangle(0, 0, fill_w, self.h, fill=color, outline="")
            self.create_line(fill_w - 2, 0, fill_w - 2, self.h, fill="#ffffff", width=2)

        percent = int((self.current_val / float(self.max_val)) * 100)
        self.create_text(
            self.w // 2, self.h // 2,
            text=f"{self.current_val} / {self.max_val} frames ({percent}%)",
            fill="#ffffff",
            font=('Helvetica', 10, 'bold')
        )


# ==============================================================================
# --- Top Real-Time Cyber Navigation & Telemetry Bar ---
# ==============================================================================

class CyberTopNavHeader(tk.Frame):
    """
    Top floating navigation and live telemetry header.
    Features live digital clock, online status badge, and quick page navigation pills.
    """
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, bg="#0b1120", bd=0, highlightthickness=1, highlightbackground="#1e293b", padx=20, pady=8, **kwargs)
        self.controller = controller

        # Left Section: Brand Logo & Title
        left_box = tk.Frame(self, bg="#0b1120")
        left_box.pack(side="left")

        brand_logo = tk.Label(left_box, text="⚡ HARIS", font=('Helvetica', 14, 'bold'), fg="#38bdf8", bg="#0b1120")
        brand_logo.pack(side="left")

        core_tag = tk.Label(left_box, text="AI CORE", font=('Helvetica', 9, 'bold'), fg="#a855f7", bg="#1e1b4b", padx=6, pady=2)
        core_tag.pack(side="left", padx=8)

        author_tag = tk.Label(left_box, text="BY SAMEER ABBAS", font=('Helvetica', 8, 'bold'), fg="#38bdf8", bg="#0f172a", padx=4)
        author_tag.pack(side="left", padx=4)

        # Center Section: Navigation Pills
        nav_box = tk.Frame(self, bg="#0b1120")
        nav_box.pack(side="left", expand=True)

        nav_items = [
            ("🏠 Home", "StartPage"),
            ("➕ Register (4F)", "PageOne"),
            ("🔍 Check User", "PageTwo"),
            ("🪪 QR Identity Hub", "PageQR"),
            ("⚡ Detection Core", "PageFour"),
        ]

        for label, page in nav_items:
            btn = tk.Button(
                nav_box,
                text=label,
                font=('Helvetica', 10, 'bold'),
                bg="#1e293b",
                fg="#f1f5f9",
                relief="flat",
                bd=0,
                padx=12,
                pady=4,
                cursor="hand2",
                command=lambda p=page: self.controller.show_frame(p)
            )
            add_advanced_button_effects(btn, "#1e293b", "#38bdf8", default_fg="#f1f5f9", hover_fg="#0f172a", active_bg="#0284c7")
            btn.pack(side="left", padx=4)

        # Right Section: Live Telemetry & Digital Clock
        right_box = tk.Frame(self, bg="#0b1120")
        right_box.pack(side="right")

        self.status_dot = tk.Label(right_box, text="● ONLINE", font=('Helvetica', 9, 'bold'), fg="#10b981", bg="#0b1120")
        self.status_dot.pack(side="left", padx=8)

        self.clock_lbl = tk.Label(right_box, text="", font=('Consolas', 10, 'bold'), fg="#94a3b8", bg="#0b1120")
        self.clock_lbl.pack(side="left", padx=4)

        self.update_clock()
        self.pulse_status()

    def update_clock(self):
        if not self.winfo_exists():
            return
        now_str = time.strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_lbl.config(text=now_str)
        self.after(1000, self.update_clock)

    def pulse_status(self, state=True):
        if not self.winfo_exists():
            return
        col = "#10b981" if state else "#34d399"
        self.status_dot.config(fg=col)
        self.after(800, self.pulse_status, not state)


# ==============================================================================
# --- Main Application Controller Class ---
# ==============================================================================

class HARIS_App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        global names

        # Load names from file safely
        try:
            with open("nameslist.txt", "r") as f:
                content = f.read()
                tokens = content.rstrip().split(" ")
                for item in tokens:
                    item_clean = item.strip()
                    if item_clean:
                        names.add(item_clean)
        except FileNotFoundError:
            open("nameslist.txt", "w").close()

        self.title_font = tkfont.Font(family='Helvetica', size=24, weight="bold")
        self.subtitle_font = tkfont.Font(family='Helvetica', size=13, weight="normal")
        self.title("HARIS - AI Facial & QR Code Access Control | Built by Sameer Abbas")

        # Full Screen / Zoomed setup
        try:
            self.state('zoomed')
        except tk.TclError:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.active_name = None
        self.num_of_images = 0
        self.is_running = True

        # Root Background Canvas for Particle Animation
        self.bg_canvas = CyberParticleBackground(self)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bg_canvas.start_animation()

        # Top Navigation Bar
        self.top_nav = CyberTopNavHeader(self.bg_canvas, controller=self)
        self.top_nav.pack(side="top", fill="x", padx=15, pady=(10, 0))

        # Center Floating Card Container (Glassmorphic look)
        self.card_container = tk.Frame(
            self.bg_canvas,
            bg="#0f172a",
            bd=2,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#38bdf8"
        )
        
        self.card_window = self.bg_canvas.create_window(
            self.winfo_screenwidth() // 2,
            (self.winfo_screenheight() // 2) + 20,
            window=self.card_container,
            anchor="center"
        )

        self.bg_canvas.bind("<Configure>", self.recenter_card)

        self.card_container.grid_rowconfigure(0, weight=1)
        self.card_container.grid_columnconfigure(0, weight=1)

        # Initialize Frames / Pages
        self.frames = {}
        for F in (StartPage, PageOne, PageTwo, PageThree, PageQR, PageFour):
            page_name = F.__name__
            frame = F(parent=self.card_container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def recenter_card(self, event):
        """Keeps the glassmorphic content card centered on the screen."""
        self.bg_canvas.coords(self.card_window, event.width // 2, (event.height // 2) + 20)

    def show_frame(self, page_name):
        """Switches frames with a smooth visual transition."""
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def on_closing(self):
        if messagebox.askokcancel("Quit HARIS", "Are you sure you want to exit?"):
            self.is_running = False
            self.bg_canvas.stop_animation()
            global names
            try:
                with open("nameslist.txt", "w") as f:
                    f.write(" ".join(filter(None, names)))
            except Exception as e:
                print(f"Error saving names: {e}")
            self.destroy()


# ==============================================================================
# --- StartPage (Home Dashboard) ---
# ==============================================================================

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#0f172a", padx=45, pady=30)
        self.controller = controller

        # Neon animated Title Label
        self.title_label = tk.Label(
            self,
            text="HARIS ACCESS INTELLIGENCE",
            font=('Helvetica', 22, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(5, 5), sticky="n")
        animate_glowing_text(self.title_label, ["#ffffff", "#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#38bdf8"], delay=40)

        subtitle = tk.Label(
            self,
            text="Real-Time Facial Recognition & Photo-Embedded QR Verification Core",
            font=('Helvetica', 11, 'italic'),
            fg="#94a3b8",
            bg="#0f172a"
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky="n")

        # Center Visual / Image
        try:
            render = PhotoImage(file='homepagepic.png')
            self.img_label = tk.Label(self, image=render, bg="#0f172a")
            self.img_label.image = render
            self.img_label.grid(row=2, column=0, columnspan=2, pady=10, sticky="n")
        except Exception:
            self.img_canvas = tk.Canvas(self, width=160, height=120, bg="#0f172a", highlightthickness=0)
            self.img_canvas.grid(row=2, column=0, columnspan=2, pady=10, sticky="n")
            self.draw_hologram_face()

        # Theme Colors
        PRIMARY_BG = "#ff4500"
        PRIMARY_HOVER = "#ff6347"
        PRIMARY_ACTIVE = "#d63000"
        
        CYAN_BG = "#0284c7"
        CYAN_HOVER = "#38bdf8"
        CYAN_ACTIVE = "#0369a1"

        PURPLE_BG = "#7c3aed"
        PURPLE_HOVER = "#a855f7"
        PURPLE_ACTIVE = "#6d28d9"

        SEC_BG = "#334155"
        SEC_HOVER = "#475569"
        SEC_ACTIVE = "#1e293b"

        # Action Buttons
        button1 = tk.Button(
            self, text="➕  Sign Up User (4 Frames)",
            fg="#FFFFFF", bg=PRIMARY_BG,
            relief="flat", cursor="hand2",
            command=lambda: self.controller.show_frame("PageOne"),
            width=24, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=PRIMARY_ACTIVE
        )
        add_advanced_button_effects(button1, PRIMARY_BG, PRIMARY_HOVER, active_bg=PRIMARY_ACTIVE)

        button2 = tk.Button(
            self, text="🔍  Check a User",
            fg="#FFFFFF", bg=CYAN_BG,
            relief="flat", cursor="hand2",
            command=lambda: self.controller.show_frame("PageTwo"),
            width=24, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=CYAN_ACTIVE
        )
        add_advanced_button_effects(button2, CYAN_BG, CYAN_HOVER, active_bg=CYAN_ACTIVE)

        button_qr = tk.Button(
            self, text="🪪  QR Identity & Badge Hub",
            fg="#FFFFFF", bg=PURPLE_BG,
            relief="flat", cursor="hand2",
            command=lambda: self.controller.show_frame("PageQR"),
            width=24, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=PURPLE_ACTIVE
        )
        add_advanced_button_effects(button_qr, PURPLE_BG, PURPLE_HOVER, active_bg=PURPLE_ACTIVE)

        button3 = tk.Button(
            self, text="✕  Quit Application",
            fg="#f8fafc", bg=SEC_BG,
            relief="flat", cursor="hand2",
            command=self.controller.on_closing,
            width=24, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=SEC_ACTIVE
        )
        add_advanced_button_effects(button3, SEC_BG, SEC_HOVER, active_bg=SEC_ACTIVE)

        # Place buttons
        button1.grid(row=3, column=0, columnspan=2, pady=6)
        button2.grid(row=4, column=0, columnspan=2, pady=6)
        button_qr.grid(row=5, column=0, columnspan=2, pady=6)
        button3.grid(row=6, column=0, columnspan=2, pady=6)

        # Developer Credit
        builder_lbl = tk.Label(
            self,
            text="⚡ System Architect & Builder: Sameer Abbas",
            font=('Helvetica', 9, 'bold'),
            fg="#64748b",
            bg="#0f172a"
        )
        builder_lbl.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="n")

        center_grid_widgets(self, 8, 2)

    def draw_hologram_face(self):
        """Draws a futuristic holographic face icon placeholder."""
        self.img_canvas.delete("all")
        self.img_canvas.create_oval(30, 10, 130, 110, outline="#00f2fe", width=2)
        self.img_canvas.create_oval(45, 25, 115, 95, outline="#38bdf8", width=1, dash=(4, 4))
        self.img_canvas.create_oval(55, 45, 65, 55, fill="#00f2fe", outline="")
        self.img_canvas.create_oval(95, 45, 105, 55, fill="#00f2fe", outline="")
        self.img_canvas.create_line(40, 70, 120, 70, fill="#ff4500", width=2)


# ==============================================================================
# --- PageOne (Sign Up - Enter Name) ---
# ==============================================================================

class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#0f172a", padx=45, pady=35)
        self.controller = controller

        PRIMARY_BG = "#ff4500"
        PRIMARY_HOVER = "#ff6347"
        PRIMARY_ACTIVE = "#d63000"

        CLEAR_BG = "#d97706"
        CLEAR_HOVER = "#f59e0b"
        CLEAR_ACTIVE = "#b45309"

        CANCEL_BG = "#334155"
        CANCEL_HOVER = "#475569"
        CANCEL_ACTIVE = "#1e293b"

        self.title_lbl = tk.Label(
            self,
            text="REGISTER NEW USER PROFILE",
            font=('Helvetica', 20, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_lbl.grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="n")
        animate_glowing_text(self.title_lbl, ["#ffffff", "#ff4500", "#fb923c", "#f43f5e", "#ffffff"], delay=45)

        tk.Label(
            self,
            text="Rapid 4-frame dataset capture & instant Photo-QR generation",
            font=('Helvetica', 11),
            fg="#94a3b8",
            bg="#0f172a"
        ).grid(row=1, column=0, columnspan=3, pady=(0, 25), sticky="n")

        # Name Entry Group
        entry_frame = tk.Frame(self, bg="#1e293b", bd=1, relief="solid", padx=12, pady=12)
        entry_frame.grid(row=2, column=0, columnspan=3, pady=15)

        tk.Label(
            entry_frame,
            text="User Name:",
            fg="#38bdf8",
            bg="#1e293b",
            font=('Helvetica', 14, 'bold')
        ).pack(side="left", padx=10)

        self.user_name = tk.Entry(
            entry_frame,
            borderwidth=0,
            bg="#0f172a",
            fg="#ffffff",
            insertbackground="#00f2fe",
            font=('Helvetica', 14, 'bold'),
            width=18
        )
        self.user_name.pack(side="left", padx=10, ipady=5)
        self.user_name.focus_set()

        # Action Buttons
        self.buttoncanc = tk.Button(
            self, text="✕  Cancel",
            bg=CANCEL_BG, fg="#f8fafc",
            relief="flat", cursor="hand2",
            command=lambda: controller.show_frame("StartPage"),
            width=13, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=CANCEL_ACTIVE
        )
        add_advanced_button_effects(self.buttoncanc, CANCEL_BG, CANCEL_HOVER, active_bg=CANCEL_ACTIVE)

        self.buttonclear = tk.Button(
            self, text="⟲  Clear",
            command=self.clear,
            fg="#ffffff", bg=CLEAR_BG,
            relief="flat", cursor="hand2",
            width=13, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=CLEAR_ACTIVE
        )
        add_advanced_button_effects(self.buttonclear, CLEAR_BG, CLEAR_HOVER, active_bg=CLEAR_ACTIVE)

        self.buttonext = tk.Button(
            self, text="Next  ➔",
            fg="#FFFFFF", bg=PRIMARY_BG,
            relief="flat", cursor="hand2",
            command=self.start_training,
            width=13, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=PRIMARY_ACTIVE
        )
        add_advanced_button_effects(self.buttonext, PRIMARY_BG, PRIMARY_HOVER, active_bg=PRIMARY_ACTIVE)

        self.buttoncanc.grid(row=3, column=0, pady=30, padx=8)
        self.buttonclear.grid(row=3, column=1, pady=30, padx=8)
        self.buttonext.grid(row=3, column=2, pady=30, padx=8)

        center_grid_widgets(self, 4, 3)

    def on_show(self):
        self.user_name.focus_set()

    def start_training(self):
        global names
        name_input = self.user_name.get().strip()
        if not name_input or name_input.lower() == "none":
            messagebox.showerror("Validation Error", "Name cannot be empty or 'None'!")
            return
        elif name_input in names:
            messagebox.showerror("Duplicate Error", f"User '{name_input}' is already registered!")
            return

        names.add(name_input)
        self.controller.active_name = name_input
        self.controller.frames["PageTwo"].refresh_names()
        self.controller.frames["PageQR"].refresh_names()
        self.controller.show_frame("PageThree")

    def clear(self):
        self.user_name.delete(0, 'end')


# ==============================================================================
# --- PageTwo (Check User - Dropdown Selection) ---
# ==============================================================================

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#0f172a", padx=45, pady=40)
        self.controller = controller

        SELECT_BG = "#0284c7"
        SELECT_HOVER = "#38bdf8"
        SELECT_ACTIVE = "#0369a1"

        CANCEL_BG = "#334155"
        CANCEL_HOVER = "#475569"
        CANCEL_ACTIVE = "#1e293b"

        self.title_lbl = tk.Label(
            self,
            text="CHECK USER ACCESS PROFILE",
            font=('Helvetica', 20, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_lbl.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="n")
        animate_glowing_text(self.title_lbl, ["#ffffff", "#00f5d4", "#00bbf9", "#38bdf8", "#ffffff"], delay=45)

        tk.Label(
            self,
            text="Select an authorized user identity to initiate dual recognition",
            font=('Helvetica', 11),
            fg="#94a3b8",
            bg="#0f172a"
        ).grid(row=1, column=0, columnspan=2, pady=(0, 25), sticky="n")

        select_card = tk.Frame(self, bg="#1e293b", bd=1, relief="solid", padx=22, pady=16)
        select_card.grid(row=2, column=0, columnspan=2, pady=20)

        tk.Label(
            select_card,
            text="Select Registered User:",
            fg="#38bdf8",
            bg="#1e293b",
            font=('Helvetica', 13, 'bold')
        ).pack(anchor="w", pady=(0, 8))

        self.menuvar = tk.StringVar(self)
        self.dropdown = tk.OptionMenu(select_card, self.menuvar, "No Users Registered")
        self.dropdown.config(
            bg="#0f172a",
            fg="#ffffff",
            activebackground="#1e3a5f",
            activeforeground="#00f2fe",
            font=('Helvetica', 13, 'bold'),
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground="#38bdf8",
            cursor="hand2",
            width=22
        )
        self.dropdown["menu"].config(
            bg="#0f172a",
            fg="#ffffff",
            activebackground="#0284c7",
            activeforeground="#ffffff",
            font=('Helvetica', 12)
        )
        self.dropdown.pack(fill="x", ipady=4)

        self.buttoncanc = tk.Button(
            self, text="✕  Cancel",
            command=lambda: controller.show_frame("StartPage"),
            bg=CANCEL_BG, fg="#f8fafc",
            relief="flat", cursor="hand2",
            width=14, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=CANCEL_ACTIVE
        )
        add_advanced_button_effects(self.buttoncanc, CANCEL_BG, CANCEL_HOVER, active_bg=CANCEL_ACTIVE)

        self.button_select = tk.Button(
            self, text="✓  Select User",
            command=self.next_foo_dropdown,
            fg="#FFFFFF", bg=SELECT_BG,
            relief="flat", cursor="hand2",
            width=14, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=SELECT_ACTIVE
        )
        add_advanced_button_effects(self.button_select, SELECT_BG, SELECT_HOVER, active_bg=SELECT_ACTIVE)

        self.buttoncanc.grid(row=3, column=0, pady=30, padx=12, sticky="e")
        self.button_select.grid(row=3, column=1, pady=30, padx=12, sticky="w")

        center_grid_widgets(self, 4, 2)
        self.refresh_names()

    def on_show(self):
        self.refresh_names()

    def next_foo_dropdown(self):
        selected_name = self.menuvar.get().strip()
        if not selected_name or selected_name == "No Users Registered":
            messagebox.showerror("Selection Error", "Please select a valid user from the dropdown.")
            return

        self.controller.active_name = selected_name
        self.controller.show_frame("PageFour")

    def refresh_names(self):
        global names
        self.menuvar.set('')
        menu = self.dropdown['menu']
        menu.delete(0, 'end')

        if not names:
            menu.add_command(label="No Users Registered", state="disabled")
            self.menuvar.set("No Users Registered")
            return

        sorted_names = sorted(list(names))
        if sorted_names:
            self.menuvar.set(sorted_names[0])

        for name in sorted_names:
            menu.add_command(label=name, command=tk._setit(self.menuvar, name))


# ==============================================================================
# --- PageThree (Fast 50-Frame Dataset Capture & Model Training) ---
# ==============================================================================

class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#0f172a", padx=35, pady=30)
        self.controller = controller

        CAPTURE_BG = "#ff4500"
        CAPTURE_HOVER = "#ff6347"
        CAPTURE_ACTIVE = "#d63000"

        TRAIN_BG = "#059669"
        TRAIN_HOVER = "#10b981"
        TRAIN_ACTIVE = "#047857"

        BACK_BG = "#334155"
        BACK_HOVER = "#475569"
        BACK_ACTIVE = "#1e293b"

        self.title_lbl = tk.Label(
            self,
            text="DATASET CAPTURE & NEURAL SETUP",
            font=('Helvetica', 20, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_lbl.grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="n")
        animate_glowing_text(self.title_lbl, ["#ffffff", "#ff4500", "#ff8c00", "#38bdf8", "#ffffff"], delay=45)

        self.user_badge = tk.Label(
            self,
            text="Active Profile: None",
            font=('Helvetica', 12, 'bold'),
            fg="#38bdf8",
            bg="#0f172a"
        )
        self.user_badge.grid(row=1, column=0, columnspan=3, pady=(0, 15), sticky="n")

        # 4 Frames Target Progress Bar
        self.progress_bar = AnimatedProgressBar(self, width=440, height=24, max_value=4)
        self.progress_bar.grid(row=2, column=0, columnspan=3, pady=10)

        self.numimglabel = tk.Label(
            self,
            text="Status: Ready to capture 4 face frames",
            font=('Helvetica', 12),
            fg="#e2e8f0",
            bg="#0f172a"
        )
        self.numimglabel.grid(row=3, column=0, columnspan=3, pady=(5, 20), sticky="n")

        # Buttons
        self.backbutton = tk.Button(
            self, text="⬅  Back",
            fg="#f8fafc", bg=BACK_BG,
            relief="flat", cursor="hand2",
            command=lambda: self.controller.show_frame("PageOne"),
            width=12, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=BACK_ACTIVE
        )
        add_advanced_button_effects(self.backbutton, BACK_BG, BACK_HOVER, active_bg=BACK_ACTIVE)

        self.capturebutton = tk.Button(
            self, text="📷  Capture 4 Frames",
            fg="#FFFFFF", bg=CAPTURE_BG,
            relief="flat", cursor="hand2",
            command=self.capimg,
            width=18, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=CAPTURE_ACTIVE
        )
        add_advanced_button_effects(self.capturebutton, CAPTURE_BG, CAPTURE_HOVER, active_bg=CAPTURE_ACTIVE)

        self.trainbutton = tk.Button(
            self, text="⚙  Train The Model",
            fg="#FFFFFF", bg=TRAIN_BG,
            relief="flat", cursor="hand2",
            command=self.trainmodel,
            width=18, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=TRAIN_ACTIVE
        )
        add_advanced_button_effects(self.trainbutton, TRAIN_BG, TRAIN_HOVER, active_bg=TRAIN_ACTIVE)

        self.backbutton.grid(row=4, column=0, padx=8, pady=20)
        self.capturebutton.grid(row=4, column=1, padx=8, pady=20)
        self.trainbutton.grid(row=4, column=2, padx=8, pady=20)

        center_grid_widgets(self, 5, 3)

    def on_show(self):
        user = self.controller.active_name or "Unknown"
        self.user_badge.config(text=f"Active Profile: {user}")
        self.progress_bar.set_value(self.controller.num_of_images)
        self.numimglabel.config(text=f"Status: {self.controller.num_of_images} / 4 frames captured")

    def capimg(self):
        user = self.controller.active_name
        if not user:
            messagebox.showerror("Error", "No active user selected!")
            return

        self.numimglabel.config(text="Status: Capturing face frames... Please look at the camera.")
        messagebox.showinfo("Instructions", f"We will capture 4 pictures of {user}'s face.\nPress 'q' or ESC in the camera feed to stop early.")

        try:
            x = start_capture(user, target_frames=4)
            self.controller.num_of_images = x
            self.progress_bar.set_value(x)
            self.numimglabel.config(text=f"Status: Captured {x} / 4 images successfully!")
            if x >= 4:
                messagebox.showinfo("Capture Complete", f"Successfully captured {x} images!\nPhoto-QR code has also been automatically generated.\nYou can now train the model.")
        except Exception as e:
            messagebox.showerror("Capture Error", f"An error occurred while capturing images: {e}")

    def trainmodel(self):
        user = self.controller.active_name
        if self.controller.num_of_images < 1:
            messagebox.showerror("Data Incomplete", f"Not enough data ({self.controller.num_of_images}/4 frames). Capture face frames first!")
            return

        self.numimglabel.config(text="Status: Training neural classifier model...")
        self.update_idletasks()

        try:
            train_classifer(user)
            # Ensure QR code is also prepared
            qr_generator.generate_photo_qr(user)
            qr_generator.generate_id_badge(user)
            
            messagebox.showinfo("Success", f"The model and Photo-QR badge for '{user}' have been successfully trained and prepared!")
            self.controller.frames["PageQR"].refresh_names()
            self.controller.show_frame("PageQR")
        except Exception as e:
            messagebox.showerror("Training Error", f"An error occurred during model training: {e}")


# ==============================================================================
# --- PageQR (Dedicated QR Identity & Badge Hub) ---
# ==============================================================================

class PageQR(tk.Frame):
    """
    Dedicated Futuristic QR Code & Biometric Identity Hub.
    Allows generating Photo-embedded QR Codes, full ID Badge Cards, and previewing them live.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0f172a", padx=40, pady=25)
        self.controller = controller
        self.current_preview_image = None

        # Theme Colors
        PURPLE_BG = "#7c3aed"
        PURPLE_HOVER = "#a855f7"
        PURPLE_ACTIVE = "#6d28d9"

        CYAN_BG = "#0284c7"
        CYAN_HOVER = "#38bdf8"
        CYAN_ACTIVE = "#0369a1"

        HOME_BG = "#334155"
        HOME_HOVER = "#475569"
        HOME_ACTIVE = "#1e293b"

        # Title
        self.title_lbl = tk.Label(
            self,
            text="PHOTO-EMBEDDED QR IDENTITY HUB",
            font=('Helvetica', 20, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_lbl.grid(row=0, column=0, columnspan=2, pady=(5, 5), sticky="n")
        animate_glowing_text(self.title_lbl, ["#ffffff", "#a855f7", "#ec4899", "#38bdf8", "#ffffff"], delay=45)

        tk.Label(
            self,
            text="Generate high-error-correction QR codes with integrated user portrait photos",
            font=('Helvetica', 11),
            fg="#94a3b8",
            bg="#0f172a"
        ).grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky="n")

        # Left Column: Controls & User Selection
        left_panel = tk.Frame(self, bg="#1e293b", bd=1, relief="solid", padx=20, pady=18)
        left_panel.grid(row=2, column=0, padx=12, pady=10, sticky="nsew")

        tk.Label(left_panel, text="Select User Profile:", fg="#38bdf8", bg="#1e293b", font=('Helvetica', 12, 'bold')).pack(anchor="w", pady=(0, 6))

        self.menuvar = tk.StringVar(self)
        self.dropdown = tk.OptionMenu(left_panel, self.menuvar, "No Users Registered")
        self.dropdown.config(
            bg="#0f172a", fg="#ffffff",
            activebackground="#1e3a5f", activeforeground="#00f2fe",
            font=('Helvetica', 12, 'bold'), relief="flat", bd=1,
            highlightthickness=1, highlightbackground="#38bdf8", cursor="hand2", width=18
        )
        self.dropdown["menu"].config(bg="#0f172a", fg="#ffffff", activebackground="#7c3aed", activeforeground="#ffffff", font=('Helvetica', 11))
        self.dropdown.pack(fill="x", ipady=3, pady=(0, 15))

        btn_gen_qr = tk.Button(
            left_panel, text="🪪  Generate Photo-QR",
            fg="#FFFFFF", bg=PURPLE_BG,
            relief="flat", cursor="hand2",
            command=self.create_photo_qr,
            width=20, height=2, font=('Helvetica', 11, 'bold'),
            bd=0, activebackground=PURPLE_ACTIVE
        )
        add_advanced_button_effects(btn_gen_qr, PURPLE_BG, PURPLE_HOVER, active_bg=PURPLE_ACTIVE)
        btn_gen_qr.pack(fill="x", pady=6)

        btn_gen_badge = tk.Button(
            left_panel, text="🏷️  Generate Full ID Badge",
            fg="#FFFFFF", bg=CYAN_BG,
            relief="flat", cursor="hand2",
            command=self.create_id_badge,
            width=20, height=2, font=('Helvetica', 11, 'bold'),
            bd=0, activebackground=CYAN_ACTIVE
        )
        add_advanced_button_effects(btn_gen_badge, CYAN_BG, CYAN_HOVER, active_bg=CYAN_ACTIVE)
        btn_gen_badge.pack(fill="x", pady=6)

        btn_open = tk.Button(
            left_panel, text="📂  Open Badge File",
            fg="#f8fafc", bg=HOME_BG,
            relief="flat", cursor="hand2",
            command=self.open_badge_file,
            width=20, height=2, font=('Helvetica', 11, 'bold'),
            bd=0, activebackground=HOME_ACTIVE
        )
        add_advanced_button_effects(btn_open, HOME_BG, HOME_HOVER, active_bg=HOME_ACTIVE)
        btn_open.pack(fill="x", pady=6)

        btn_detect = tk.Button(
            left_panel, text="⚡  Test in Detection",
            fg="#FFFFFF", bg="#059669",
            relief="flat", cursor="hand2",
            command=lambda: self.controller.show_frame("PageFour"),
            width=20, height=2, font=('Helvetica', 11, 'bold'),
            bd=0, activebackground="#047857"
        )
        add_advanced_button_effects(btn_detect, "#059669", "#10b981", active_bg="#047857")
        btn_detect.pack(fill="x", pady=6)

        # Right Column: High-Res Interactive Canvas Preview
        right_panel = tk.Frame(self, bg="#0b1120", bd=1, relief="solid", highlightthickness=1, highlightbackground="#38bdf8", padx=10, pady=10)
        right_panel.grid(row=2, column=1, padx=12, pady=10, sticky="nsew")

        self.preview_lbl = tk.Label(right_panel, text="QR & PASS PREVIEW", fg="#38bdf8", bg="#0b1120", font=('Helvetica', 11, 'bold'))
        self.preview_lbl.pack(pady=(0, 6))

        self.preview_canvas = tk.Canvas(right_panel, width=280, height=280, bg="#0f172a", highlightthickness=0)
        self.preview_canvas.pack(pady=5)

        self.preview_canvas.create_text(
            140, 140,
            text="Select user and click\n'Generate Photo-QR' to preview",
            fill="#64748b", font=('Helvetica', 11), justify="center"
        )

        # Bottom Bar: Back Button
        btn_back = tk.Button(
            self, text="🏠  Return to Home",
            fg="#f8fafc", bg=HOME_BG,
            relief="flat", cursor="hand2",
            command=lambda: controller.show_frame("StartPage"),
            width=20, height=2, font=('Helvetica', 11, 'bold'),
            bd=0, activebackground=HOME_ACTIVE
        )
        add_advanced_button_effects(btn_back, HOME_BG, HOME_HOVER, active_bg=HOME_ACTIVE)
        btn_back.grid(row=3, column=0, columnspan=2, pady=(15, 5))

        center_grid_widgets(self, 4, 2)
        self.refresh_names()

    def on_show(self):
        self.refresh_names()
        if self.controller.active_name and self.controller.active_name in names:
            self.menuvar.set(self.controller.active_name)
            self.create_photo_qr()

    def refresh_names(self):
        global names
        current = self.menuvar.get()
        menu = self.dropdown['menu']
        menu.delete(0, 'end')

        if not names:
            menu.add_command(label="No Users Registered", state="disabled")
            self.menuvar.set("No Users Registered")
            return

        sorted_names = sorted(list(names))
        if current in sorted_names:
            self.menuvar.set(current)
        elif sorted_names:
            self.menuvar.set(sorted_names[0])

        for name in sorted_names:
            menu.add_command(label=name, command=tk._setit(self.menuvar, name))

    def create_photo_qr(self):
        user = self.menuvar.get().strip()
        if not user or user == "No Users Registered":
            messagebox.showerror("Error", "Please select a registered user first.")
            return

        try:
            qr_path = qr_generator.generate_photo_qr(user)
            self.display_image_on_canvas(qr_path)
            self.controller.active_name = user
            self.preview_lbl.config(text=f"PHOTO-QR PASS: {user.upper()}")
        except Exception as e:
            messagebox.showerror("QR Error", f"Failed to generate Photo-QR: {e}")

    def create_id_badge(self):
        user = self.menuvar.get().strip()
        if not user or user == "No Users Registered":
            messagebox.showerror("Error", "Please select a registered user first.")
            return

        try:
            badge_path = qr_generator.generate_id_badge(user)
            self.display_image_on_canvas(badge_path)
            self.controller.active_name = user
            self.preview_lbl.config(text=f"CYBER ID BADGE: {user.upper()}")
        except Exception as e:
            messagebox.showerror("Badge Error", f"Failed to generate ID Badge: {e}")

    def display_image_on_canvas(self, image_path):
        if not os.path.isfile(image_path):
            return

        try:
            pil_img = Image.open(image_path)
            # Resize image to fit nicely within 280x280 preview canvas
            pil_img.thumbnail((270, 270), Image.LANCZOS)
            self.current_preview_image = ImageTk.PhotoImage(pil_img)

            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(140, 140, image=self.current_preview_image, anchor="center")
        except Exception as e:
            print(f"[PageQR] Preview error: {e}")

    def open_badge_file(self):
        user = self.menuvar.get().strip()
        if not user or user == "No Users Registered":
            messagebox.showerror("Error", "No user selected.")
            return

        badge_p = os.path.join("data", "qrcodes", f"{user}_badge.png")
        qr_p = os.path.join("data", "qrcodes", f"{user}_qr.png")
        
        target = badge_p if os.path.isfile(badge_p) else qr_p
        if os.path.isfile(target):
            try:
                os.startfile(target)
            except Exception as e:
                messagebox.showerror("Open Error", f"Could not open file: {e}")
        else:
            messagebox.showinfo("Not Found", "Please generate the QR or Badge first!")


# ==============================================================================
# --- PageFour (Real-Time Detection & Access Core) ---
# ==============================================================================

class PageFour(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#0f172a", padx=45, pady=35)
        self.controller = controller

        PRIMARY_BG = "#ff4500"
        PRIMARY_HOVER = "#ff6347"
        PRIMARY_ACTIVE = "#d63000"

        PURPLE_BG = "#7c3aed"
        PURPLE_HOVER = "#a855f7"
        PURPLE_ACTIVE = "#6d28d9"

        HOME_BG = "#334155"
        HOME_HOVER = "#475569"
        HOME_ACTIVE = "#1e293b"

        self.title_lbl = tk.Label(
            self,
            text="REAL-TIME RECOGNITION & ACCESS CORE",
            font=('Helvetica', 20, 'bold'),
            bg="#0f172a",
            fg="#ffffff"
        )
        self.title_lbl.grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="n")
        animate_glowing_text(self.title_lbl, ["#ffffff", "#00f2fe", "#4facfe", "#818cf8", "#ffffff"], delay=45)

        self.status_sub = tk.Label(
            self,
            text="Active Profile: Ready for live recognition",
            font=('Helvetica', 12, 'bold'),
            fg="#38bdf8",
            bg="#0f172a"
        )
        self.status_sub.grid(row=1, column=0, columnspan=3, pady=(0, 20), sticky="n")

        # Action Buttons
        button1 = tk.Button(
            self, text="⚡  Start Face & QR Recognition",
            command=self.openwebcam,
            fg="#FFFFFF", bg=PRIMARY_BG,
            relief="flat", cursor="hand2",
            width=26, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=PRIMARY_ACTIVE
        )
        add_advanced_button_effects(button1, PRIMARY_BG, PRIMARY_HOVER, active_bg=PRIMARY_ACTIVE)

        button_qr = tk.Button(
            self, text="🪪  View User's Photo-QR",
            command=lambda: self.controller.show_frame("PageQR"),
            fg="#FFFFFF", bg=PURPLE_BG,
            relief="flat", cursor="hand2",
            width=22, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=PURPLE_ACTIVE
        )
        add_advanced_button_effects(button_qr, PURPLE_BG, PURPLE_HOVER, active_bg=PURPLE_ACTIVE)

        button4 = tk.Button(
            self, text="🏠  Return to Home",
            command=lambda: self.controller.show_frame("StartPage"),
            bg=HOME_BG, fg="#f8fafc",
            relief="flat", cursor="hand2",
            width=18, height=2, font=('Helvetica', 12, 'bold'),
            bd=0, activebackground=HOME_ACTIVE
        )
        add_advanced_button_effects(button4, HOME_BG, HOME_HOVER, active_bg=HOME_ACTIVE)

        button1.grid(row=2, column=0, columnspan=3, pady=12)
        button_qr.grid(row=3, column=0, columnspan=3, pady=10)
        button4.grid(row=4, column=0, columnspan=3, pady=12)

        center_grid_widgets(self, 5, 3)

    def on_show(self):
        user = self.controller.active_name or "General Mode"
        self.status_sub.config(text=f"Active Profile: {user}")

    def openwebcam(self):
        user = self.controller.active_name
        if not user:
            messagebox.showwarning("Notice", "No user profile active. Launching in general QR + Face scan mode.")
        try:
            main_app(user)
        except Exception as e:
            messagebox.showerror("Detection Error", f"Error opening recognition stream: {e}")


# ==============================================================================
# --- Application Execution ---
# ==============================================================================

if __name__ == "__main__":
    app = HARIS_App()
    try:
        app.iconphoto(True, PhotoImage(file='icon.ico'))
    except Exception:
        pass

    app.mainloop()