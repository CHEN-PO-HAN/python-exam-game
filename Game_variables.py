"""棒球遊戲共用的設定數值與可變動狀態。"""

import pygame

# ---- 視窗與資產配置 ----
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
GAME_SPEED_RATE = 152	# 遊戲速率
WINDOW_TITLE = "打擊遊戲"
FONT_NAME = "Microsoft JhengHei"	# 文字字型
FONT_SIZE = 36	# 文字大小
SCOREBOARD_FILE = "scoreboard.json"
SCOREBOARD_LIMIT = 5

BACKGROUND_IMAGE_PATH = "grass_clean.png"
BALL_IMAGE_PATH = "baseball_clean.png"

# ---- 球設定 ----
ball_radius = 18	# 球半徑
BALL_SPAWN_OFFSET_X = 50	# 球出現位置離螢幕右側的距離
BALL_BASELINE_Y = SCREEN_HEIGHT // 2	# 球的基準線 Y 座標
BALL_SPEED_RANGE = (3, 6)	# 球速範圍 (像素/幀)
BALL_DESPAWN_X = -50	# 球消失位置 X 座標

# ---- 打擊區與打者 ----
HIT_ZONE_POS = (50, SCREEN_HEIGHT // 2 - 40)	# 擊球區左上角位置
HIT_ZONE_SIZE = (80, 80)	# 擊球區尺寸
HIT_ZONE_RECT = pygame.Rect(HIT_ZONE_POS, HIT_ZONE_SIZE)	# 擊球區矩形
HITTER_OFFSET = (0, -60)	# 打者相對於擊球區的位置

# ---- 遊戲狀態 ----
swinging = False	# 是否正在揮棒
swing_time = 150   # 揮棒時間 (毫秒)
swing_start = 0
score = 0
combo = 0
lives = 3
GAME_OVER_WAIT_MS = 3000
READY_GO_DURATION_MS = 2000
scoreboard = []

# ---- 特效參數與狀態 ----
hit_effect_duration = 250	# 命中特效持續時間
hit_effect_start = -1000	# 命中特效開始時間，確保遊戲一開始「特效已經結束」
miss_effect_duration = 200	# 失誤特效持續時間
miss_effect_start = -1000	# 失誤特效開始時間，確保遊戲一開始「特效已經結束」
hit_zone_shake_magnitude = 6	# 擊球區抖動幅度
hit_zone_shake_duration = 200	# 擊球區抖動持續時間


def reset_state():
	"""將跑局中的動態變數清為預設值，方便重新開始。"""
	global swinging, swing_start, score, combo, lives
	global hit_effect_start, miss_effect_start

	swinging = False
	swing_start = 0
	score = 0
	combo = 0
	lives = 3	# 重置生命值
	hit_effect_start = -1000
	miss_effect_start = -1000
