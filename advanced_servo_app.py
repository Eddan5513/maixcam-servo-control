"""
Advanced Servo Control App for MaixCAM
Supports: Color Detection, Object Detection (YOLO), Motion Detection
Features: Presets, Full Settings, ARM Mode, OSD/UI
Optimized for speed and accuracy
"""

from maix import camera, display, image, touchscreen, pinmap, pwm, err, app, nn
import time as pytime
import json
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = "/root/advanced_servo_config.json"

# Default settings
DEFAULT_CONFIG = {
    "servo_pin": "A18",
    "pwm_id": 6,
    "servo_angle_open": 90,
    "servo_angle_close": 0,
    "close_delay": 10,
    "rearm_mode": True,  # Auto rearm after object disappears
    "rearm_delay": 2,    # Seconds to wait before rearming
    "repeat_trigger": False,  # Repeat trigger every N seconds while detected
    "repeat_interval": 10,
    
    # Detection settings
    "detection_mode": "color",  # color, object, motion
    "color_preset": "Yellow",
    "object_preset": "person",
    "confidence_threshold": 0.5,
    "min_area": 500,
    "motion_sensitivity": 50,
    
    # Camera settings
    "camera_width": 640,
    "camera_height": 480,
    "fps_target": 30,
    
    # Custom color threshold (LAB)
    "custom_threshold": [[50, 80, 0, 30, 40, 80]]
}

# Color presets (LAB color space)
COLOR_PRESETS = {
    "Yellow": [[50, 80, 0, 30, 40, 80]],
    "Red": [[30, 80, 40, 80, 10, 80]],
    "Green": [[30, 80, -120, -10, 0, 30]],
    "Blue": [[30, 80, 30, 100, -120, -60]],
    "Orange": [[40, 80, 20, 60, 30, 70]],
    "Purple": [[20, 70, 20, 80, -80, -20]],
    "White": [[80, 100, -20, 20, -20, 20]],
    "Black": [[0, 30, -20, 20, -20, 20]],
    "Custom": [[50, 80, 0, 30, 40, 80]]
}

# Object detection labels (COCO dataset)
OBJECT_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class AppState:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.ui_mode = "run"  # run, menu, settings, calibrate
        self.menu_page = 0
        self.settings_page = 0
        
        # Servo state
        self.servo_opened = False
        self.open_time = 0
        self.last_trigger_time = 0
        self.armed = True
        self.last_detection_time = 0
        self.rearm_timer = 0
        
        # Detection state
        self.prev_frame = None
        self.detector = None
        
        # UI state
        self.fps = 0
        self.frame_count = 0
        self.fps_time = pytime.time()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
                print(f"[CONFIG] Loaded: {CONFIG_FILE}")
        except Exception as e:
            print(f"[CONFIG] Load error: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"[CONFIG] Saved: {CONFIG_FILE}")
        except Exception as e:
            print(f"[CONFIG] Save error: {e}")
    
    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            now = pytime.time()
            self.fps = 30 / (now - self.fps_time)
            self.fps_time = now

# ============================================================================
# SERVO CONTROL
# ============================================================================

class ServoController:
    def __init__(self, state):
        self.state = state
        self.pwm = None
        self.setup()
    
    def setup(self):
        """Initialize servo PWM"""
        try:
            pin = self.state.config["servo_pin"]
            pwm_id = self.state.config["pwm_id"]
            
            err.check_raise(
                pinmap.set_pin_function(pin, f"PWM{pwm_id}"),
                f"PWM setup failed for {pin}"
            )
            
            self.pwm = pwm.PWM(pwm_id, freq=50, duty=2.5, enable=True)
            self.set_angle(self.state.config["servo_angle_close"])
            print(f"[SERVO] Initialized: {pin} (PWM{pwm_id})")
        except Exception as e:
            print(f"[SERVO] Setup error: {e}")
    
    def set_angle(self, angle):
        """Set servo angle (0-180 degrees)"""
        if self.pwm:
            duty = 2.5 + (angle / 180.0) * 10.0
            self.pwm.duty(duty)
    
    def open(self):
        """Open servo"""
        angle = self.state.config["servo_angle_open"]
        self.set_angle(angle)
        self.state.servo_opened = True
        self.state.open_time = pytime.time()
        self.state.last_trigger_time = pytime.time()
        print(f"[SERVO] OPEN ({angle}°)")
    
    def close(self):
        """Close servo"""
        angle = self.state.config["servo_angle_close"]
        self.set_angle(angle)
        self.state.servo_opened = False
        print(f"[SERVO] CLOSE ({angle}°)")
    
    def update(self, detected):
        """Update servo based on detection and timing logic"""
        current_time = pytime.time()
        
        # Update detection time
        if detected:
            self.state.last_detection_time = current_time
        
        # Check if object disappeared and rearm mode is enabled
        if not detected and self.state.servo_opened:
            time_since_detection = current_time - self.state.last_detection_time
            if time_since_detection >= 1.0:  # Object gone for 1 second
                if self.state.config["rearm_mode"]:
                    # Start rearm timer
                    if self.state.rearm_timer == 0:
                        self.state.rearm_timer = current_time
                    
                    # Check if rearm delay passed
                    if current_time - self.state.rearm_timer >= self.state.config["rearm_delay"]:
                        self.close()
                        self.state.armed = True
                        self.state.rearm_timer = 0
                        print("[SERVO] Rearmed")
        else:
            self.state.rearm_timer = 0
        
        # Auto-close after delay
        if self.state.servo_opened:
            elapsed = current_time - self.state.open_time
            if elapsed >= self.state.config["close_delay"]:
                self.close()
                if not self.state.config["rearm_mode"]:
                    self.state.armed = False
        
        # Repeat trigger logic
        if detected and self.state.servo_opened and self.state.config["repeat_trigger"]:
            elapsed_since_trigger = current_time - self.state.last_trigger_time
            if elapsed_since_trigger >= self.state.config["repeat_interval"]:
                self.open()  # Re-trigger
        
        # Trigger on new detection
        if detected and not self.state.servo_opened and self.state.armed:
            self.open()
            if not self.state.config["rearm_mode"]:
                self.state.armed = False
    
    def cleanup(self):
        """Cleanup servo"""
        if self.pwm:
            self.close()
            self.pwm.disable()

# ============================================================================
# DETECTION ENGINES
# ============================================================================

class ColorDetector:
    def __init__(self, state):
        self.state = state
    
    def detect(self, img):
        """Detect color blobs"""
        preset = self.state.config["color_preset"]
        
        if preset == "Custom":
            threshold = self.state.config["custom_threshold"]
        else:
            threshold = COLOR_PRESETS.get(preset, COLOR_PRESETS["Yellow"])
        
        min_area = self.state.config["min_area"]
        
        blobs = img.find_blobs(
            threshold,
            pixels_threshold=min_area,
            area_threshold=min_area,
            merge=True
        )
        
        return len(blobs) > 0, blobs
    
    def calibrate(self, img, x, y, radius=30):
        """Calibrate custom color from point"""
        try:
            stats = img.get_statistics(roi=(x-radius, y-radius, radius*2, radius*2))
            l, a, b = stats.l_mean(), stats.a_mean(), stats.b_mean()
            
            # Create threshold with tolerance
            l_min = max(0, int(l - 25))
            l_max = min(100, int(l + 25))
            a_min = max(-128, int(a - 30))
            a_max = min(127, int(a + 30))
            b_min = max(-128, int(b - 30))
            b_max = min(127, int(b + 30))
            
            self.state.config["custom_threshold"] = [[l_min, l_max, a_min, a_max, b_min, b_max]]
            self.state.config["color_preset"] = "Custom"
            self.state.save_config()
            
            print(f"[COLOR] Calibrated: LAB=({l:.0f},{a:.0f},{b:.0f})")
            return True
        except Exception as e:
            print(f"[COLOR] Calibration error: {e}")
            return False

class ObjectDetector:
    def __init__(self, state):
        self.state = state
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        try:
            # Try to load YOLOv8 model (default on MaixCAM)
            self.model = nn.YOLOv8(model="/root/models/yolov8n.mud")
            print("[OBJECT] YOLOv8 model loaded")
        except Exception as e:
            print(f"[OBJECT] Model load error: {e}")
            print("[OBJECT] Falling back to color detection")
    
    def detect(self, img):
        """Detect objects using YOLO"""
        if not self.model:
            return False, []
        
        try:
            target_label = self.state.config["object_preset"]
            confidence = self.state.config["confidence_threshold"]
            
            # Run detection
            objs = self.model.detect(img, conf_th=confidence, iou_th=0.45)
            
            # Filter by target label
            filtered = []
            for obj in objs:
                label_idx = obj.class_id
                if label_idx < len(OBJECT_LABELS):
                    label = OBJECT_LABELS[label_idx]
                    if label == target_label:
                        filtered.append(obj)
            
            return len(filtered) > 0, filtered
        except Exception as e:
            print(f"[OBJECT] Detection error: {e}")
            return False, []

class MotionDetector:
    def __init__(self, state):
        self.state = state
    
    def detect(self, img):
        """Detect motion between frames"""
        if self.state.prev_frame is None:
            self.state.prev_frame = img.copy()
            return False, []
        
        try:
            # Calculate difference
            diff = img.difference(self.state.prev_frame)
            stats = diff.get_statistics()
            
            # Update previous frame
            self.state.prev_frame = img.copy()
            
            # Check if motion exceeds threshold
            sensitivity = self.state.config["motion_sensitivity"]
            detected = stats.l_mean() > sensitivity
            
            return detected, []
        except Exception as e:
            print(f"[MOTION] Detection error: {e}")
            return False, []

# ============================================================================
# UI RENDERING
# ============================================================================

class UIButton:
    def __init__(self, id, x, y, w, h, label, value=""):
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.value = value
        
    def draw(self, img):
        img.draw_rect(self.x, self.y, self.w, self.h, color=image.Color.from_rgb(50, 50, 50), thickness=-1)
        img.draw_rect(self.x, self.y, self.w, self.h, color=image.Color.from_rgb(200, 200, 200), thickness=2)
        img.draw_string(self.x + 10, self.y + (self.h // 2) - 12, self.label, color=image.Color.from_rgb(255, 255, 255), scale=1.6)
        if self.value != "":
            img.draw_string(self.x + self.w - 140, self.y + (self.h // 2) - 12, str(self.value), color=image.Color.from_rgb(0, 255, 255), scale=1.6)

    def is_clicked(self, x, y):
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

class UI:
    def __init__(self, state):
        self.state = state
        self.active_buttons = []
    
    def draw_osd(self, img, detected, detections):
        """Draw on-screen display (OSD) in run mode"""
        # Servo status - large and prominent
        status = "OPEN" if self.state.servo_opened else "CLOSED"
        status_color = image.Color.from_rgb(0, 255, 0) if self.state.servo_opened else image.Color.from_rgb(255, 255, 255)
        img.draw_string(10, 10, f"SERVO: {status}", color=status_color, scale=3)
        
        # ARM status
        arm_status = "ARMED" if self.state.armed else "DISARMED"
        arm_color = image.Color.from_rgb(0, 255, 0) if self.state.armed else image.Color.from_rgb(255, 0, 0)
        img.draw_string(10, 50, f"[{arm_status}]", color=arm_color, scale=2)
        
        # Detection mode and target
        mode = self.state.config["detection_mode"].upper()
        if mode == "COLOR":
            target = self.state.config["color_preset"]
        elif mode == "OBJECT":
            target = self.state.config["object_preset"]
        else:
            target = "MOTION"
        
        img.draw_string(10, 85, f"Mode: {mode}", color=image.Color.from_rgb(255, 255, 255), scale=2)
        img.draw_string(10, 115, f"Target: {target}", color=image.Color.from_rgb(255, 255, 255), scale=2)
        
        # FPS
        img.draw_string(10, 145, f"FPS: {self.state.fps:.0f}", color=image.Color.from_rgb(255, 255, 255), scale=2)
        
        # Timer countdown
        if self.state.servo_opened:
            current_time = pytime.time()
            remaining = int(self.state.config["close_delay"] - (current_time - self.state.open_time))
            if remaining > 0:
                img.draw_string(10, 175, f"Close: {remaining}s", color=image.Color.from_rgb(255, 255, 0), scale=2)
        
        # Rearm timer
        if self.state.rearm_timer > 0:
            current_time = pytime.time()
            rearm_remaining = int(self.state.config["rearm_delay"] - (current_time - self.state.rearm_timer))
            if rearm_remaining > 0:
                img.draw_string(10, 205, f"Rearm: {rearm_remaining}s", color=image.Color.from_rgb(255, 165, 0), scale=2)
        
        # Draw detections
        self.draw_detections(img, detections)
        
        # Hint
        img.draw_string(10, img.height() - 40, "TAP FOR MENU", 
                       color=image.Color.from_rgb(150, 150, 150), scale=2)
    
    def draw_detections(self, img, detections):
        """Draw detection boxes"""
        mode = self.state.config["detection_mode"]
        
        if mode == "color":
            for blob in detections:
                x, y, w, h = blob[0], blob[1], blob[2], blob[3]
                area = w * h
                color = image.Color.from_rgb(0, 255, 0)
                img.draw_rect(x, y, w, h, color=color, thickness=2)
                img.draw_string(x, y - 15, f"{area}", color=color, scale=1.5)
        
        elif mode == "object":
            for obj in detections:
                x, y, w, h = obj.x, obj.y, obj.w, obj.h
                label_idx = obj.class_id
                conf = obj.score
                
                if label_idx < len(OBJECT_LABELS):
                    label = OBJECT_LABELS[label_idx]
                else:
                    label = f"ID{label_idx}"
                
                color = image.Color.from_rgb(0, 255, 0)
                img.draw_rect(x, y, w, h, color=color, thickness=2)
                img.draw_string(x, y - 15, f"{label} {conf:.2f}", color=color, scale=1.5)
    
    def draw_menu(self, img):
        """Draw main menu using UIButtons"""
        self.active_buttons = []
        
        # Semi-transparent background
        img.draw_rect(0, 0, 360, img.height(), color=image.Color.from_rgb(0, 0, 0), thickness=-1)
        
        # Title
        img.draw_string(10, 10, "MAIN MENU", color=image.Color.from_rgb(255, 255, 0), scale=2.5)
        
        y = 50
        h = 45
        w = 340
        spacing = 50
        
        btn_data = [
            (0, "Detection Mode", self.state.config["detection_mode"]),
            (1, "Color Preset", self.state.config["color_preset"]),
            (2, "Object Target", self.state.config["object_preset"]),
            (3, "Settings", ""),
            (4, "Calibrate Color", ""),
            (5, "ARM/DISARM", "ARMED" if self.state.armed else "DISARMED"),
            (6, "Save & Exit", "")
        ]
        
        for id, label, value in btn_data:
            btn = UIButton(id, 10, y, w, h, label, value)
            btn.draw(img)
            self.active_buttons.append(btn)
            y += spacing
    
    def draw_calibrate(self, img):
        """Draw calibration screen"""
        img.draw_string(img.width()//2 - 150, img.height()//2, 
                       "TAP TARGET COLOR", 
                       color=image.Color.from_rgb(255, 0, 255), scale=3)
        
        img.draw_string(img.width()//2 - 100, img.height()//2 + 50, 
                       "TAP AGAIN TO CANCEL", 
                       color=image.Color.from_rgb(150, 150, 150), scale=2)
    
    def draw_settings(self, img):
        """Draw settings menu using UIButtons"""
        self.active_buttons = []
        
        # Semi-transparent background
        img.draw_rect(0, 0, 420, img.height(), color=image.Color.from_rgb(0, 0, 0), thickness=-1)
        
        # Title
        img.draw_string(10, 5, f"SETTINGS P{self.state.settings_page+1}", color=image.Color.from_rgb(255, 255, 0), scale=2.5)
        
        y = 45
        h = 40
        w = 400
        spacing = 45
        
        if self.state.settings_page == 0:
            btn_data = [
                (0, "Close Delay", f"{self.state.config['close_delay']}s"),
                (1, "Rearm Mode", "ON" if self.state.config['rearm_mode'] else "OFF"),
                (2, "Rearm Delay", f"{self.state.config['rearm_delay']}s"),
                (3, "Repeat Trigger", "ON" if self.state.config['repeat_trigger'] else "OFF"),
                (4, "Min Area", f"{self.state.config['min_area']}"),
                (5, "Confidence", f"{self.state.config['confidence_threshold']:.2f}"),
                (6, "Motion Sens", f"{self.state.config['motion_sensitivity']}"),
                (7, "Next Page ->", ""),
                (8, "Back to Menu", "")
            ]
        else:
            res = f"{self.state.config['camera_width']}x{self.state.config['camera_height']}"
            btn_data = [
                (0, "Resolution", res),
                (1, "Servo Pin", str(self.state.config.get('servo_pin', 'A18'))),
                (2, "Angle Open", f"{self.state.config.get('servo_angle_open', 90)}°"),
                (3, "Angle Close", f"{self.state.config.get('servo_angle_close', 0)}°"),
                (4, "Rep. Interval", f"{self.state.config.get('repeat_interval', 10)}s"),
                (5, "<- Prev Page", ""),
                (6, "Back to Menu", "")
            ]
            
        for id, label, value in btn_data:
            btn = UIButton(id, 10, y, w, h, label, value)
            btn.draw(img)
            self.active_buttons.append(btn)
            y += spacing

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    print("=" * 60)
    print("ADVANCED SERVO CONTROL APP")
    print("=" * 60)
    
    # Initialize state
    state = AppState()
    state.load_config()
    
    # Initialize components
    cam = camera.Camera(
        state.config["camera_width"],
        state.config["camera_height"],
        image.Format.FMT_RGB888
    )
    disp = display.Display()
    ts = touchscreen.TouchScreen()
    
    servo = ServoController(state)
    color_detector = ColorDetector(state)
    object_detector = ObjectDetector(state)
    motion_detector = MotionDetector(state)
    ui = UI(state)
    
    print(f"[INIT] Camera: {state.config['camera_width']}x{state.config['camera_height']}")
    print(f"[INIT] Mode: {state.config['detection_mode']}")
    print(f"[INIT] Ready!")
    print("=" * 60)
    
    # Main loop
    try:
        while not app.need_exit():
            img = cam.read()
            state.update_fps()
            
            # Handle touch input
            touch_data = ts.read()
            if touch_data:
                tx, ty, pressed = touch_data
                if pressed:
                    handle_touch(state, img, tx, ty, color_detector, ui)
            
            # Detection and servo control
            detected = False
            detections = []
            
            if state.ui_mode == "run":
                mode = state.config["detection_mode"]
                
                if mode == "color":
                    detected, detections = color_detector.detect(img)
                elif mode == "object":
                    detected, detections = object_detector.detect(img)
                elif mode == "motion":
                    detected, detections = motion_detector.detect(img)
                
                servo.update(detected)
            
            # Render UI
            if state.ui_mode == "run":
                ui.draw_osd(img, detected, detections)
            elif state.ui_mode == "menu":
                ui.draw_menu(img)
            elif state.ui_mode == "calibrate":
                ui.draw_calibrate(img)
            elif state.ui_mode == "settings":
                ui.draw_settings(img)
            
            disp.show(img)
    
    finally:
        # Cleanup
        servo.cleanup()
        cam.close()
        print("[EXIT] Cleanup complete")

def handle_touch(state, img, tx, ty, color_detector, ui):
    """Handle touch screen input"""
    if state.ui_mode == "run":
        # Open menu
        state.ui_mode = "menu"
        return
    
    elif state.ui_mode == "calibrate":
        # Calibrate color or cancel
        if ty < img.height() // 2:
            # Scale touch coordinates to image coordinates
            img_w, img_h = img.width(), img.height()
            disp_w, disp_h = 552, 368  # MaixCAM display size
            x = int(tx * img_w / disp_w)
            y = int(ty * img_h / disp_h)
            
            color_detector.calibrate(img, x, y)
        
        state.ui_mode = "run"
        return

    # Check which button was clicked
    clicked_btn = None
    for btn in ui.active_buttons:
        if btn.is_clicked(tx, ty):
            clicked_btn = btn
            break
            
    if not clicked_btn:
        return

    setting_item = clicked_btn.id

    if state.ui_mode == "menu":
        if setting_item == 0:  # Detection mode
            modes = ["color", "object", "motion"]
            current_idx = modes.index(state.config["detection_mode"])
            state.config["detection_mode"] = modes[(current_idx + 1) % len(modes)]
        
        elif setting_item == 1:  # Color preset
            presets = list(COLOR_PRESETS.keys())
            current_idx = presets.index(state.config["color_preset"])
            state.config["color_preset"] = presets[(current_idx + 1) % len(presets)]
        
        elif setting_item == 2:  # Object target
            # Cycle through common objects
            common_objects = ["person", "car", "dog", "cat", "bird", "bottle", "cup", "cell phone", "chair", "tv", "laptop", "book", "clock"]
            if state.config["object_preset"] in common_objects:
                current_idx = common_objects.index(state.config["object_preset"])
                state.config["object_preset"] = common_objects[(current_idx + 1) % len(common_objects)]
            else:
                state.config["object_preset"] = common_objects[0]
        
        elif setting_item == 3:  # Settings
            state.ui_mode = "settings"
            state.settings_page = 0
        
        elif setting_item == 4:  # Calibrate
            state.ui_mode = "calibrate"
        
        elif setting_item == 5:  # ARM/DISARM
            state.armed = not state.armed
        
        elif setting_item == 6:  # Save & Exit
            state.save_config()
            state.ui_mode = "run"
    
    elif state.ui_mode == "settings":
        if state.settings_page == 0:
            if setting_item == 0:  # Close delay
                delays = [3, 5, 10, 15, 20, 30, 60]
                current = state.config["close_delay"]
                state.config["close_delay"] = delays[(delays.index(current) + 1) % len(delays)] if current in delays else delays[0]
            
            elif setting_item == 1:  # Rearm mode
                state.config["rearm_mode"] = not state.config["rearm_mode"]
            
            elif setting_item == 2:  # Rearm delay
                delays = [1, 2, 3, 5, 10]
                current = state.config["rearm_delay"]
                state.config["rearm_delay"] = delays[(delays.index(current) + 1) % len(delays)] if current in delays else delays[0]
            
            elif setting_item == 3:  # Repeat trigger
                state.config["repeat_trigger"] = not state.config["repeat_trigger"]
            
            elif setting_item == 4:  # Min area
                areas = [300, 500, 800, 1000, 1500, 2000]
                current = state.config["min_area"]
                state.config["min_area"] = areas[(areas.index(current) + 1) % len(areas)] if current in areas else areas[0]
            
            elif setting_item == 5:  # Confidence threshold
                thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
                current = state.config["confidence_threshold"]
                closest_idx = min(range(len(thresholds)), key=lambda i: abs(thresholds[i] - current))
                state.config["confidence_threshold"] = thresholds[(closest_idx + 1) % len(thresholds)]
            
            elif setting_item == 6:  # Motion sensitivity
                sensitivities = [30, 40, 50, 60, 70, 80]
                current = state.config["motion_sensitivity"]
                state.config["motion_sensitivity"] = sensitivities[(sensitivities.index(current) + 1) % len(sensitivities)] if current in sensitivities else sensitivities[0]
            
            elif setting_item == 7:  # Next Page
                state.settings_page = 1
            
            elif setting_item == 8:  # Back to menu
                state.save_config()
                state.ui_mode = "menu"
                state.settings_page = 0
                
        else: # settings_page == 1
            if setting_item == 0:  # Resolution
                resolutions = [(320, 240), (640, 480), (800, 600), (1280, 720)]
                current = (state.config["camera_width"], state.config["camera_height"])
                new_res = resolutions[(resolutions.index(current) + 1) % len(resolutions)] if current in resolutions else resolutions[0]
                state.config["camera_width"] = new_res[0]
                state.config["camera_height"] = new_res[1]
                print(f"[SETTINGS] Resolution changed to {new_res[0]}x{new_res[1]}. Restart to apply.")
                
            elif setting_item == 1:  # Servo Pin
                pins = ["A14", "A15", "A16", "A17", "A18", "A19"]
                current = state.config.get("servo_pin", "A18")
                state.config["servo_pin"] = pins[(pins.index(current) + 1) % len(pins)] if current in pins else pins[0]
                
            elif setting_item == 2:  # Angle Open
                angles = [0, 45, 90, 135, 180]
                current = state.config.get("servo_angle_open", 90)
                state.config["servo_angle_open"] = angles[(angles.index(current) + 1) % len(angles)] if current in angles else angles[0]
                
            elif setting_item == 3:  # Angle Close
                angles = [0, 45, 90, 135, 180]
                current = state.config.get("servo_angle_close", 0)
                state.config["servo_angle_close"] = angles[(angles.index(current) + 1) % len(angles)] if current in angles else angles[0]
                
            elif setting_item == 4:  # Rep Interval
                intervals = [1, 2, 5, 10, 15, 30]
                current = state.config.get("repeat_interval", 10)
                state.config["repeat_interval"] = intervals[(intervals.index(current) + 1) % len(intervals)] if current in intervals else intervals[0]
                
            elif setting_item == 5:  # Prev Page
                state.settings_page = 0
                
            elif setting_item == 6:  # Back to menu
                state.save_config()
                state.ui_mode = "menu"
                state.settings_page = 0

if __name__ == "__main__":
    main()
