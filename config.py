# config.py

# 🔌 IR sensor settings
IR_PIN = 12
IR_ACTIVE_LOW = True  # True إذا الحساس يفعّل على LOW

# 🔌 Relay settings
RELAY_PIN = 16

# 🔌 Micro SW settings
MICRO_PIN = 26

#  Paths
DB_FILE = "book_database.csv"
FEATURES_PATH = "features/"
CAM_WIDTH = 1920
CAM_HEIGHT = 1080
                                            
# ⚙️ AKAZE and FLANN settings
AKAZE_THRESHOLD = 0.005
FLANN_TREES = 5
FLANN_CHECKS = 50
