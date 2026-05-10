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

class UI:
    def __init__(self, state):
        self.state = state
        self.buttons = []
    
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
        """Draw main menu"""
        # Semi-transparent background
        img.draw_rect(0, 0, 300, img.height(), color=image.Color.from_rgb(0, 0, 0), thickness=-1)
        
        # Title
        img.draw_string(10, 10, "MENU", color=image.Color.from_rgb(255, 255, 0), scale=3)
        
        # Menu items
        y = 70
        spacing = 50
        
        items = [
            ("1. Detection Mode", self.state.config["detection_mode"]),
            ("2. Color Preset", self.state.config["color_preset"]),
            ("3. Object Target", self.state.config["object_preset"]),
            ("4. Settings", ""),
            ("5. Calibrate Color", ""),
            ("6. ARM/DISARM", "ARMED" if self.state.armed else "DISARMED"),
            ("7. Save & Exit", "")
        ]
        
        for i, (label, value) in enumerate(items):
            color = image.Color.from_rgb(255, 255, 255)
            img.draw_string(10, y + i * spacing, label, color=color, scale=2)
            if value:
                img.draw_string(10, y + i * spacing + 25, f"  > {value}", 
                               color=image.Color.from_rgb(0, 255, 255), scale=1.5)
        
        # Hint
        img.draw_string(10, img.height() - 40, "TAP TO SELECT", 
                       color=image.Color.from_rgb(150, 150, 150), scale=2)
    
    def draw_calibrate(self, img):
        """Draw calibration screen"""
        img.draw_string(img.width()//2 - 150, img.height()//2, 
                       "TAP TARGET COLOR", 
                       color=image.Color.from_rgb(255, 0, 255), scale=3)
        
        img.draw_string(img.width()//2 - 100, img.height()//2 + 50, 
                       "TAP AGAIN TO CANCEL", 
                       color=image.Color.from_rgb(150, 150, 150), scale=2)
    
    def draw_settings(self, img):
        """Draw settings menu"""
        # Semi-transparent background
        img.draw_rect(0, 0, 350, img.height(), color=image.Color.from_rgb(0, 0, 0), thickness=-1)
        
        # Title
        img.draw_string(10, 10, "SETTINGS", color=image.Color.from_rgb(255, 255, 0), scale=3)
        
        # Settings items
        y = 70
        spacing = 45
        
        items = [
            ("Close Delay", f"{self.state.config['close_delay']}s"),
            ("Rearm Mode", "ON" if self.state.config['rearm_mode'] else "OFF"),
            ("Rearm Delay", f"{self.state.config['rearm_delay']}s"),
            ("Repeat Trigger", "ON" if self.state.config['repeat_trigger'] else "OFF"),
            ("Min Area", f"{self.state.config['min_area']}"),
            ("Confidence", f"{self.state.config['confidence_threshold']:.2f}"),
            ("Motion Sens", f"{self.state.config['motion_sensitivity']}"),
            ("Back to Menu", "")
        ]
        
        for i, (label, value) in enumerate(items):
            color = image.Color.from_rgb(255, 255, 255)
            img.draw_string(10, y + i * spacing, f"{i+1}. {label}", color=color, scale=1.8)
            if value:
                img.draw_string(200, y + i * spacing, value, 
                               color=image.Color.from_rgb(0, 255, 255), scale=1.8)
        
        # Hint
        img.draw_string(10, img.height() - 40, "TAP TO ADJUST", 
                       color=image.Color.from_rgb(150, 150, 150), scale=2)

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
                    handle_touch(state, img, tx, ty, color_detector)
            
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

def handle_touch(state, img, tx, ty, color_detector):
    """Handle touch screen input"""
    if state.ui_mode == "run":
        # Open menu
        state.ui_mode = "menu"
    
    elif state.ui_mode == "menu":
        # Menu selection based on Y position
        menu_item = ty // 50
        
        if menu_item == 1:  # Detection mode
            modes = ["color", "object", "motion"]
            current_idx = modes.index(state.config["detection_mode"])
            state.config["detection_mode"] = modes[(current_idx + 1) % len(modes)]
        
        elif menu_item == 2:  # Color preset
            presets = list(COLOR_PRESETS.keys())
            current_idx = presets.index(state.config["color_preset"])
            state.config["color_preset"] = presets[(current_idx + 1) % len(presets)]
        
        elif menu_item == 3:  # Object target
            # Cycle through common objects
            common_objects = ["person", "car", "dog", "cat", "bottle", "cup", "cell phone"]
            if state.config["object_preset"] in common_objects:
                current_idx = common_objects.index(state.config["object_preset"])
                state.config["object_preset"] = common_objects[(current_idx + 1) % len(common_objects)]
            else:
                state.config["object_preset"] = common_objects[0]
        
        elif menu_item == 4:  # Settings
            state.ui_mode = "settings"
        
        elif menu_item == 5:  # Calibrate
            state.ui_mode = "calibrate"
        
        elif menu_item == 6:  # ARM/DISARM
            state.armed = not state.armed
        
        elif menu_item == 7:  # Save & Exit
            state.save_config()
            state.ui_mode = "run"
    
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
    
    elif state.ui_mode == "settings":
        # Settings adjustment based on Y position
        setting_item = ty // 45
        
        if setting_item == 0:  # Close delay
            delays = [3, 5, 10, 15, 20, 30, 60]
            current = state.config["close_delay"]
            if current in delays:
                idx = delays.index(current)
                state.config["close_delay"] = delays[(idx + 1) % len(delays)]
            else:
                state.config["close_delay"] = delays[0]
        
        elif setting_item == 1:  # Rearm mode
            state.config["rearm_mode"] = not state.config["rearm_mode"]
        
        elif setting_item == 2:  # Rearm delay
            delays = [1, 2, 3, 5, 10]
            current = state.config["rearm_delay"]
            if current in delays:
                idx = delays.index(current)
                state.config["rearm_delay"] = delays[(idx + 1) % len(delays)]
            else:
                state.config["rearm_delay"] = delays[0]
        
        elif setting_item == 3:  # Repeat trigger
            state.config["repeat_trigger"] = not state.config["repeat_trigger"]
        
        elif setting_item == 4:  # Min area
            areas = [300, 500, 800, 1000, 1500, 2000]
            current = state.config["min_area"]
            if current in areas:
                idx = areas.index(current)
                state.config["min_area"] = areas[(idx + 1) % len(areas)]
            else:
                state.config["min_area"] = areas[0]
        
        elif setting_item == 5:  # Confidence threshold
            thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
            current = state.config["confidence_threshold"]
            # Find closest
            closest_idx = min(range(len(thresholds)), key=lambda i: abs(thresholds[i] - current))
            state.config["confidence_threshold"] = thresholds[(closest_idx + 1) % len(thresholds)]
        
        elif setting_item == 6:  # Motion sensitivity
            sensitivities = [30, 40, 50, 60, 70, 80]
            current = state.config["motion_sensitivity"]
            if current in sensitivities:
                idx = sensitivities.index(current)
                state.config["motion_sensitivity"] = sensitivities[(idx + 1) % len(sensitivities)]
            else:
                state.config["motion_sensitivity"] = sensitivities[0]
        
        elif setting_item == 7:  # Back to menu
            state.save_config()
            state.ui_mode = "menu"

if __name__ == "__main__":
    main()
