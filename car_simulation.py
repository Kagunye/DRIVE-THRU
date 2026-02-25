"""
Drive-through car simulation - full flow:
  Car on sensor → loop triggers → base station → menu read out → customer picks →
  order on screen → staff process → car to collection/payment.
Run: python car_simulation.py
"""

import tkinter as tk
from tkinter import font as tkfont
import time
import json
import os

# Optional: use real TTS so you can hear the menu and order
_voice_system = None
try:
    from drive_thru_system import DriveThruSystem
    _voice_system = DriveThruSystem()
    if not getattr(_voice_system, "tts_method", None):
        _voice_system = None
except Exception as e:
    print("Voice disabled in simulation:", e)

# Scale factor (bigger = larger window and drawing frame)
SCALE = 2.8
def s(v):
    return int(v * SCALE)

# Lane and layout (scaled)
LANE_WIDTH = s(100)
CAR_LENGTH = s(78)
CAR_HEIGHT = s(36)
# Loop (sensor), speaker, base station — placed so full car fits before loop (car not hidden)
LOOP_TO_SPEAKER_GAP = s(18)
LOOP_W, LOOP_H = s(42), s(48)
# LOOP_X so car (starting at lane s(35)) fits fully before loop: LOOP_X >= s(35) + CAR_LENGTH + gap
LOOP_X, LOOP_Y = s(35) + CAR_LENGTH + s(10), s(58)
SPEAKER_X, SPEAKER_Y = LOOP_X + LOOP_W + LOOP_TO_SPEAKER_GAP, s(60)
SPEAKER_W, SPEAKER_H = s(48), s(50)
BASE_X, BASE_Y = s(118), s(20)
BASE_W, BASE_H = s(62), s(36)
ORDER_BOOTH_X = s(252)
COLLECTION_X = s(362)
BOOTH_W, BOOTH_H = s(55), s(75)
CANVAS_W, CANVAS_H = s(420), s(220)

# Car progress: 0=before sensor, 0.2=on sensor, 0.45=at order booth, 0.85=at collection
POS_SENSOR = 0.18
POS_ORDER = 0.45
POS_COLLECTION = 0.85

# Menu: choices 1-4; say 0 to repeat menu, 6 to cancel order
MENU_CHOICES = 4
MENU_ITEMS = [
    "Streetwise 2 plus coleslaw - 350 KES",
    "Mango crusher - 450 KES",
    "Zinger burger with 350ml coke - 500 KES",
    "Speak to Cashier",
]


def load_menu_from_config():
    try:
        path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(path) as f:
            data = json.load(f)
        offers = data.get("special_offers", [])
        if offers:
            out = []
            for o in offers[:MENU_CHOICES]:
                if " - " in o:
                    parts = o.split(" - ")
                    out.append(parts[0] + " - " + parts[-1] if len(parts) >= 2 else o[:45])
                else:
                    out.append(o[:45])
            return out
    except Exception:
        pass
    return MENU_ITEMS


class DriveThruSimulation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KFC Drive-Through - Full Flow Simulation")
        self.root.geometry(f"{s(800)}x{s(560)}")
        self.root.configure(bg="#2d2d2d")

        self.menu_items = load_menu_from_config()

        # State
        self.car_progress = -0.05  # off screen to start
        self.loop_triggered = False
        self.base_station_on = False
        self.menu_read = False
        self.order_items = []  # list of (index, name)
        self.order_confirmed = False
        self.car_at_collection = False
        self.client_response = ""  # what the client said (e.g. "Number 1")
        self.car_number = 0  # Car #1, #2 for order screen

        # Top row: drawing (canvas) + right controls
        top = tk.Frame(self.root, bg="#2d2d2d")
        top.pack(fill="x", padx=10, pady=(10, 4))

        left = tk.Frame(top, bg="#2d2d2d", width=CANVAS_W)
        left.pack(side="left", fill="y", padx=(0, 8))
        self.canvas = tk.Canvas(
            left, width=CANVAS_W, height=CANVAS_H,
            bg="#1e3d2e", highlightthickness=0
        )
        self.canvas.pack()
        self.timer_start = None
        self.timer_running = False
        self._draw_static()
        self._draw_timer()
        self._draw_car()

        right = tk.Frame(top, bg="#2d2d2d", width=s(280))
        right.pack(side="right", fill="y")
        bs_frame = tk.Frame(right, bg="#1a1a1a", relief="ridge", bd=2)
        bs_frame.pack(fill="x", pady=(0, 6))
        tk.Label(bs_frame, text="BASE STATION", bg="#1a1a1a", fg="#888", font=("Segoe UI", 8)).pack(anchor="w", padx=6, pady=2)
        self.base_station_label = tk.Label(bs_frame, text="OFF — waiting for loop", bg="#1a1a1a", fg="#666", font=("Segoe UI", 10))
        self.base_station_label.pack(anchor="w", padx=6, pady=(0, 6))
        resp_frame = tk.Frame(right, bg="#1a2a1a", relief="ridge", bd=1)
        resp_frame.pack(fill="x", pady=(0, 6))
        tk.Label(resp_frame, text="CLIENT RESPONSE", bg="#1a2a1a", fg="#7fff7f", font=("Segoe UI", 8)).pack(anchor="w", padx=6, pady=2)
        self.client_response_label = tk.Label(resp_frame, text="—", bg="#1a2a1a", fg="#aaa", font=("Segoe UI", 10))
        self.client_response_label.pack(anchor="w", padx=6, pady=(0, 6))
        tk.Label(right, text="Customer picks (simulate voice):", bg="#2d2d2d", fg="#aaa", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 2))
        menu_btns = tk.Frame(right, bg="#2d2d2d")
        menu_btns.pack(fill="x", pady=(0, 6))
        for i, name in enumerate(self.menu_items[:MENU_CHOICES]):
            short = name[:24] + "…" if len(name) > 24 else name
            btn = tk.Button(menu_btns, text=f"{i+1}. {short}", command=lambda idx=i: self.add_to_order(idx),
                           bg="#3d5a3d", fg="white", font=("Segoe UI", 8), relief="flat", cursor="hand2")
            btn.pack(fill="x", pady=2)
        btn_frame = tk.Frame(right, bg="#2d2d2d")
        btn_frame.pack(fill="x", pady=8)
        self.start_btn = tk.Button(btn_frame, text="START — Full run", command=self.run_full_flow,
                                   bg="#c4a035", fg="#1a1a1a", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2")
        self.start_btn.pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Reset", command=self.reset,
                  bg="#444", fg="white", font=("Segoe UI", 9), relief="flat", padx=8, pady=4, cursor="hand2").pack(side="left", padx=4)

        # Below the drawing: order display and menu read-out (so you can read when you can't hear)
        below = tk.Frame(self.root, bg="#2d2d2d")
        below.pack(fill="both", expand=True, padx=10, pady=(4, 6))
        tk.Label(below, text="Order display (below drawing — read here if you can't hear the menu)", bg="#2d2d2d", fg="#888", font=("Segoe UI", 9)).pack(anchor="w")
        order_frame = tk.LabelFrame(below, text=" ORDER CONFIRMED / Car # / Order list ", bg="#0a0a0a", fg="#c4a035", font=("Segoe UI", 9))
        order_frame.pack(fill="both", expand=True, pady=(2, 4))
        self.order_display = tk.Text(order_frame, height=5, bg="#0d1f12", fg="#7fff7f", font=("Consolas", 11),
                                    wrap="word", state="disabled")
        self.order_display.pack(fill="both", expand=True, padx=6, pady=6)
        self.order_display.insert("1.0", "No order yet. When the menu is read out, you can also read it here if you cannot hear.\n")
        self.order_display.config(state="disabled")
        tk.Label(below, text="Menu read-out (when base station reads the menu, text appears above)", bg="#2d2d2d", fg="#666", font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        self.status = tk.Label(self.root, text="Click START — Full run. Order display is below the drawing so you can read when you can't hear.",
                              bg="#2d2d2d", fg="#aaa", font=("Segoe UI", 9))
        self.status.pack(pady=6)

    def _speak_in_sim(self, text: str):
        """Speak text in simulation if TTS is available."""
        if _voice_system and getattr(_voice_system, "tts_method", None):
            try:
                _voice_system.speak(text)
            except Exception as e:
                print("TTS in sim:", e)

    def _speak_menu_sync(self):
        """Speak the full menu (welcome + 5 items). Say 1-5 to order, 0 to repeat, 6 to cancel."""
        if not _voice_system or not getattr(_voice_system, "tts_method", None):
            return
        self._speak_in_sim("Welcome to KFC Westlands. This is our specials today.")
        for i, name in enumerate(self.menu_items[:MENU_CHOICES], 1):
            # Speak item only (no "Number X" prefix to avoid repetition)
            clean = name.strip()
            if clean.lower().startswith("number ") and ": " in clean:
                clean = clean.split(": ", 1)[1]
            self._speak_in_sim(clean)
        self._speak_in_sim("Say 1, 2, 3, 4, or 5 for your choice. Say 0 to hear the menu again. Say 6 to cancel your order. I am listening now.")

    def _tick_timer(self):
        """Schedule timer updates while running."""
        if not self.timer_running:
            return
        self._update_timer()
        self.root.after(200, self._tick_timer)

    def run_full_flow(self):
        """One button: car goes through entire ordering by itself; timer runs in real time."""
        self.reset()
        self.timer_start = time.time()
        self.timer_running = True
        self._tick_timer()
        self.start_btn.config(state="disabled")
        self.status.config(text="Running full flow…")

        def step():
            # 1) Car onto sensor → loop → base station
            self.status.config(text="Car on sensor → loop → base station ON")
            for step_i in range(1, 15):
                self.car_progress = (step_i / 15) * POS_SENSOR
                self._draw_car()
                self._update_timer()
                self.root.update()
                time.sleep(0.04)
            self.car_progress = POS_SENSOR
            self.loop_triggered = True
            self.base_station_on = True
            self.menu_read = True
            self._draw_car()
            self._update_base_station()
            self._update_timer()
            self.root.update()
            self.status.config(text="Car on sensor — timer started. Speaker: welcome and menu by voice (1–5 order, 0 repeat, 6 cancel).")
            self.root.update()
            # Show menu text below drawing (so you can read when you can't hear)
            self._show_menu_read_out_below()
            # Speak the menu so you can hear it
            self._speak_menu_sync()
            for _ in range(12):
                time.sleep(0.1)
                self._update_timer()
                self.root.update()
            # 2) Client picks a number → Order confirmed, Car #1, order on screen, human prepares
            self.client_response = "Number 1"
            self.car_number = 1
            self.order_items.append((0, self.menu_items[0]))
            self.order_confirmed = True
            self._update_order_display()
            # Speak order confirmation so you can hear it
            self._speak_in_sim("Order confirmed. Car number one.")
            self.status.config(text="Order confirmed. Car #1. Order on screen. Human preparing — drive to pick up.")
            self._update_timer()
            self.root.update()
            time.sleep(1.0)

            # 3) Drive to order window (then to pick up)
            for step_i in range(1, 28):
                t = step_i / 28
                self.car_progress = POS_SENSOR + (POS_ORDER - POS_SENSOR) * t
                self._draw_car()
                self._update_timer()
                self.root.update()
                time.sleep(0.035)
            self.car_progress = POS_ORDER
            self._draw_car()
            self._update_timer()
            self.root.update()
            for _ in range(10):
                time.sleep(0.1)
                self._update_timer()
                self.root.update()
            # 4) Car moves to pick up — collect order and pay
            self.status.config(text="Car moving to pick up — collect order and pay.")
            for step_i in range(1, 35):
                t = step_i / 35
                self.car_progress = POS_ORDER + (POS_COLLECTION - POS_ORDER) * t
                self._draw_car()
                self._update_timer()
                self.root.update()
                time.sleep(0.035)
            self.car_progress = POS_COLLECTION
            self.car_at_collection = True
            self._draw_car()
            self._update_timer()
            self.timer_running = False
            self.status.config(text="Done. Car at pick up — customer collects order and pays.")
            self.start_btn.config(state="normal")

        # Run in a short delay so UI updates
        self.root.after(10, step)

    def _draw_static(self):
        """Simple, clean 2D scene: sky, ground, lane, building, ORDER, PICK UP, KFC, order screen."""
        c = self.canvas
        # Sky — flat
        c.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill="#b0d4e8", outline="")
        # Ground
        c.create_rectangle(0, s(148), CANVAS_W, CANVAS_H, fill="#3a5c32", outline="")
        # Lane — simple grey, white edges, yellow curb
        c.create_rectangle(s(25), s(48), s(415), s(152), fill="#444", outline="#333", width=1)
        c.create_rectangle(s(35), s(55), s(405), s(145), fill="#3a3a3a", outline="")
        for i in range(3):
            y = s(72 + i * 28)
            c.create_line(s(50), y, s(390), y, fill="#666", dash=(6, 8), width=1)
        c.create_line(s(35), s(55), s(405), s(55), fill="#fff", width=2)
        c.create_line(s(35), s(145), s(405), s(145), fill="#d4a020", width=2)
        # Building — starts after SPEAKER so it doesn't cover it; flat grey, red roof
        b_x, b_y = s(232), s(25)
        b_w, b_h = s(165), s(125)
        c.create_rectangle(b_x, b_y + s(30), b_x + b_w, b_y + b_h, fill="#555", outline="#444", width=1)
        c.create_rectangle(b_x - s(2), b_y, b_x + b_w + s(2), b_y + s(28), fill="#a02020", outline="#801818", width=1)
        # ORDER / MENU — clear spacing from road elements
        ow_x = ORDER_BOOTH_X + s(4)
        c.create_rectangle(ow_x, s(54), ow_x + s(44), s(96), fill="#2a3540", outline="#d4a020", width=1)
        c.create_text(ORDER_BOOTH_X + BOOTH_W//2, s(72), text="ORDER", fill="#d4a020", font=("Segoe UI", s(10), "bold"))
        c.create_text(ORDER_BOOTH_X + BOOTH_W//2, s(104), text="Menu · speaker at loop", fill="#8a9a9a", font=("Segoe UI", s(7)))
        c.create_rectangle(ORDER_BOOTH_X - s(4), s(34), ORDER_BOOTH_X + BOOTH_W + s(4), s(46), fill="#222", outline="#d4a020", width=1)
        c.create_text(ORDER_BOOTH_X + BOOTH_W//2, s(40), text="MENU", fill="#d4a020", font=("Segoe UI", s(9), "bold"))
        # PICK UP
        cw_x = COLLECTION_X + s(4)
        c.create_rectangle(cw_x, s(54), cw_x + s(44), s(96), fill="#1a2a1a", outline="#5a8a5a", width=1)
        c.create_text(COLLECTION_X + BOOTH_W//2, s(72), text="PICK UP", fill="#8acc8a", font=("Segoe UI", s(10), "bold"))
        c.create_text(COLLECTION_X + BOOTH_W//2, s(104), text="Collect & Pay", fill="#6a8a6a", font=("Segoe UI", s(7)))
        # KFC sign — clear position, full text visible
        kfc_left, kfc_top = s(368), s(10)
        kfc_w, kfc_h = s(48), s(40)
        kfc_cx = kfc_left + kfc_w // 2
        c.create_rectangle(kfc_left, kfc_top, kfc_left + kfc_w, kfc_top + kfc_h, fill="#d4a020", outline="#a07818", width=1)
        c.create_text(kfc_cx, kfc_top + s(12), text="KFC", fill="#1a1a1a", font=("Segoe UI", s(10), "bold"))
        c.create_text(kfc_cx, kfc_top + s(28), text="DRIVE THRU", fill="#5c4a18", font=("Segoe UI", 6, "bold"))
        # Order screen — aligned with building, clear border
        os_left, os_top = s(242), s(112)
        os_w, os_h = s(148), s(32)
        c.create_rectangle(os_left, os_top, os_left + os_w, os_top + os_h, fill="#0c1810", outline="#d4a020", width=1, tags="order_screen_bg")
        c.create_text(os_left + os_w//2, os_top + os_h//2, text="No order yet", fill="#8acc8a", font=("Consolas", 9), width=os_w - s(12), tags="order_screen_text")

    def _draw_timer(self):
        """Simple timer box."""
        self.canvas.create_rectangle(s(28), s(6), s(102), s(28), fill="#222", outline="#d4a020", width=1, tags="timer_bg")
        self.canvas.create_text(s(65), s(17), text="0:00", fill="#d4a020", font=("Consolas", s(12), "bold"), tags="timer_text")

    def _update_timer(self):
        """Refresh timer on canvas with real elapsed time."""
        try:
            if self.timer_start is None or not self.timer_running:
                self.canvas.itemconfig("timer_text", text="0:00")
                return
            elapsed = time.time() - self.timer_start
            m = int(elapsed) // 60
            s = int(elapsed) % 60
            self.canvas.itemconfig("timer_text", text=f"{m}:{s:02d}")
        except tk.TclError:
            pass

    def _car_position(self):
        """Car position in 2D (x, y). Car starts fully before LOOP sensor (left of it), then drives right."""
        t = max(0, min(1, self.car_progress))
        # Start so car's right edge is left of the loop (car is before loop)
        car_before_loop = LOOP_X - CAR_LENGTH - s(8)
        lane_end = s(405) - CAR_LENGTH
        x = car_before_loop + t * (lane_end - car_before_loop)
        y = s(100) - CAR_HEIGHT // 2
        return x, y

    def _draw_car(self):
        """Draw car as 2D sedan (body, cabin, windows, wheels) on the lane."""
        self.canvas.delete("car")
        x, y = self._car_position()
        c = self.canvas
        # Body — cleaner red with subtle outline
        c.create_rectangle(x, y + s(14), x + CAR_LENGTH, y + CAR_HEIGHT, fill="#b00", outline="#5a0000", width=1, tags="car")
        c.create_rectangle(x + s(4), y + s(18), x + CAR_LENGTH - s(4), y + CAR_HEIGHT - s(4), fill="#c00", outline="#800", width=1, tags="car")
        # Cabin / windshield
        c.create_rectangle(x + s(38), y + s(18), x + CAR_LENGTH - s(12), y + s(28), fill="#3a5068", outline="#2a4050", tags="car")
        c.create_rectangle(x + s(42), y + s(20), x + CAR_LENGTH - s(16), y + s(26), fill="#5a7088", outline="#3a5068", width=1, tags="car")
        # Roof
        c.create_rectangle(x + s(32), y + s(8), x + CAR_LENGTH - s(8), y + s(20), fill="#a00", outline="#600", width=1, tags="car")
        # Wheels
        c.create_oval(x + s(6), y + CAR_HEIGHT - s(8), x + s(22), y + CAR_HEIGHT + s(4), fill="#111", outline="#444", width=1, tags="car")
        c.create_oval(x + CAR_LENGTH - s(22), y + CAR_HEIGHT - s(8), x + CAR_LENGTH - s(6), y + CAR_HEIGHT + s(4), fill="#111", outline="#444", width=1, tags="car")
        # Lights
        c.create_oval(x + s(2), y + s(22), x + s(8), y + s(28), fill="#fff8b0", outline="#666", width=1, tags="car")
        c.create_oval(x + CAR_LENGTH - s(8), y + s(22), x + CAR_LENGTH - s(2), y + s(28), fill="#cc2222", outline="#666", width=1, tags="car")
        # Draw loop, speaker, base station on top so car never hides them
        self._draw_equipment_overlay()

    def _draw_equipment_overlay(self):
        """Simple overlay: LOOP Sensor, Speaker, Base Station; minimal connection lines. Car stays right of these."""
        c = self.canvas
        c.delete("equipment")
        line_color = "#5a6a6a"
        # LOOP Sensor — single green box
        c.create_rectangle(LOOP_X, LOOP_Y, LOOP_X + LOOP_W, LOOP_Y + LOOP_H,
                          fill="#244a24", outline="#3a6a3a", width=1, tags=("equipment", "sensor_rect"))
        c.create_text(LOOP_X + LOOP_W//2, LOOP_Y + LOOP_H//2, text="LOOP\nSensor", fill="#8acc8a", font=("Segoe UI", s(8), "bold"), tags="equipment")
        # Speaker — single orange box + simple icon
        sx, sy = SPEAKER_X, SPEAKER_Y
        c.create_rectangle(sx, sy, sx + SPEAKER_W, sy + SPEAKER_H, fill="#b05820", outline="#8a4018", width=1, tags="equipment")
        icon_cx, icon_cy = sx + SPEAKER_W//2, sy + s(16)
        c.create_oval(icon_cx - s(8), icon_cy - s(5), icon_cx + s(8), icon_cy + s(5), fill="#fff", outline="#aaa", width=1, tags="equipment")
        c.create_text(sx + SPEAKER_W//2, sy + SPEAKER_H - s(8), text="SPEAKER", fill="#fff", font=("Segoe UI", s(7), "bold"), tags="equipment")
        # Base Station — single green box (left of MENU so no overlap)
        bx, by = BASE_X, BASE_Y
        c.create_rectangle(bx, by, bx + BASE_W, by + BASE_H, fill="#1a3a1a", outline="#3a6a3a", width=1, tags="equipment")
        c.create_text(bx + BASE_W//2, by + BASE_H//2, text="BASE", fill="#7acc7a", font=("Segoe UI", s(8), "bold"), tags="equipment")
        # Minimal connections: thin dashed lines, no labels
        c.create_line(sx + SPEAKER_W, sy + SPEAKER_H//2, bx + BASE_W, by + BASE_H//2, fill=line_color, width=1, dash=(4, 4), tags="equipment")
        c.create_line(bx + BASE_W//2, by, s(65), s(17), fill=line_color, width=1, dash=(4, 4), tags="equipment")
        # Base → order screen (screen center: os_left + os_w//2, os_top + os_h//2)
        os_cx = s(242) + s(148)//2
        os_cy = s(112) + s(32)//2
        c.create_line(bx + BASE_W, by + BASE_H//2, os_cx, os_cy, fill=line_color, width=1, dash=(4, 4), tags="equipment")

    def _update_base_station(self):
        if self.base_station_on:
            self.base_station_label.config(text="ON — reading menu", fg="#7fff7f")
        elif self.loop_triggered:
            self.base_station_label.config(text="Triggered by loop", fg="#c4a035")
        else:
            self.base_station_label.config(text="OFF — waiting for loop", fg="#666")
        # Highlight LOOP Sensor when triggered
        try:
            if self.loop_triggered:
                self.canvas.itemconfig("sensor_rect", fill="#2a5a2a", outline="#5aaa5a")
            else:
                self.canvas.itemconfig("sensor_rect", fill="#244a24", outline="#3a6a3a")
        except tk.TclError:
            pass

    def _update_order_display(self):
        self.order_display.config(state="normal")
        self.order_display.delete("1.0", "end")
        if not self.order_items:
            self.order_display.insert("1.0", "No order yet. When the menu is read out, you can read it here if you cannot hear.\n")
            self._draw_order_screen_on_canvas("No order yet")
        else:
            car_id = f"Car #{self.car_number}" if self.car_number else "Order"
            self.order_display.insert("1.0", f"ORDER CONFIRMED — {car_id}\n\n")
            lines = []
            for _, name in self.order_items:
                self.order_display.insert("end", f"  • {name}\n")
                # Short line for on-canvas screen (no price, truncate so it fits)
                short = (name.split(" - ")[0].strip() if " - " in name else name)[:28]
                if len(name) > 28:
                    short = short.rstrip() + "…"
                lines.append(short)
            if self.order_confirmed:
                self.order_display.insert("end", "\n[ Human preparing — drive to pick up to collect & pay ]\n")
            canvas_text = f"ORDER CONFIRMED\n{car_id}\n" + "\n".join("• " + L for L in lines)
            self._draw_order_screen_on_canvas(canvas_text)
        self.order_display.config(state="disabled")
        # Update client response label
        if hasattr(self, "client_response_label"):
            self.client_response_label.config(text=self.client_response if self.client_response else "—")

    def _draw_order_screen_on_canvas(self, text: str):
        """Update the order screen drawing on the canvas with current order."""
        try:
            self.canvas.itemconfig("order_screen_text", text=text)
        except tk.TclError:
            pass

    def _show_menu_read_out_below(self):
        """Show the menu text below the drawing (say 1-5 to order, 0 repeat, 6 cancel)."""
        self.order_display.config(state="normal")
        self.order_display.delete("1.0", "end")
        self.order_display.insert("1.0", "Reading out menu (read here if you can't hear):\n\n")
        self.order_display.insert("end", "Welcome to KFC Westlands. This is our specials today.\n\n")
        for i, name in enumerate(self.menu_items[:MENU_CHOICES], 1):
            display_name = name.strip()
            if display_name.lower().startswith("number ") and ": " in display_name:
                display_name = display_name.split(": ", 1)[1]
            self.order_display.insert("end", f"  {i}. {display_name}\n")
        self.order_display.insert("end", "\nSay 1, 2, 3, 4, or 5 for your choice. Say 0 to hear the menu again. Say 6 to cancel your order.")
        self.order_display.config(state="disabled")

    def car_on_sensor(self):
        """Car moves onto sensor → loop triggers → base station → menu read out."""
        self.status.config(text="Car on sensor… loop triggered → base station ON → reading menu.")
        self.root.update()
        # Animate car to sensor
        for step in range(1, 12):
            self.car_progress = (step / 12) * POS_SENSOR
            self._draw_car()
            self.root.update()
            time.sleep(0.04)
        self.car_progress = POS_SENSOR
        self.loop_triggered = True
        self.base_station_on = True
        self.menu_read = True
        self._draw_car()
        self._update_base_station()
        self.status.config(text="Base station reading menu. Customer picks above, then click 'Drive to order'.")

    def drive_to_order(self):
        """Car drives to order window (after menu / picking)."""
        self.status.config(text="Car driving to order window…")
        self.root.update()
        start = self.car_progress
        for step in range(1, 25):
            t = step / 25
            self.car_progress = start + (POS_ORDER - start) * t
            self._draw_car()
            self.root.update()
            time.sleep(0.03)
        self.car_progress = POS_ORDER
        self._draw_car()
        self._update_order_display()
        self.status.config(text="At order window. Add items above. Order shows on screen. Then 'Drive to collection'.")

    def add_to_order(self, index: int):
        name = self.menu_items[index] if index < len(self.menu_items) else f"Item {index+1}"
        self.client_response = f'"{name}"' if len(name) <= 30 else f'"Number {index+1}"'
        self.car_number = self.car_number or 1
        self.order_items.append((index, name))
        self.order_confirmed = True  # human prepares order
        self._update_order_display()
        self.status.config(text=f"Order confirmed. Car #{self.car_number}. Order on screen. Drive to pick up to collect and pay.")

    def drive_to_collection(self):
        """Car moves to pick-up window to collect order and pay."""
        self.status.config(text="Car moving to pick up — collect order and pay.")
        self.root.update()
        start = self.car_progress
        for step in range(1, 30):
            t = step / 30
            self.car_progress = start + (POS_COLLECTION - start) * t
            self._draw_car()
            self.root.update()
            time.sleep(0.03)
        self.car_progress = POS_COLLECTION
        self.car_at_collection = True
        self._draw_car()
        self.status.config(text="Car at pick up — customer collects order and pays.")

    def reset(self):
        self.car_progress = -0.05
        self.loop_triggered = False
        self.base_station_on = False
        self.menu_read = False
        self.order_items = []
        self.order_confirmed = False
        self.car_at_collection = False
        self.client_response = ""
        self.car_number = 0
        self.timer_running = False
        self.timer_start = None
        self._draw_car()
        self._update_base_station()
        self._update_order_display()
        self._update_timer()
        self.status.config(text="Click START — Full run. Car does the full flow; timer on canvas.")
        if hasattr(self, 'start_btn'):
            self.start_btn.config(state="normal")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DriveThruSimulation()
    app.run()
