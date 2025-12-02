"""棒球遊戲共用的設定數值與可變動狀態。"""

import pygame

# ---- 視窗與資產配置 ----
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
FPS = 120
WINDOW_TITLE = "打擊遊戲"
FONT_NAME = "Microsoft JhengHei"
FONT_SIZE = 36

BACKGROUND_IMAGE_PATH = "grass.jpg"
BALL_IMAGE_PATH = "baseball.png"

# ---- 球設定 ----
ball_radius = 18
BALL_SPAWN_OFFSET_X = 50
BALL_BASELINE_Y = SCREEN_HEIGHT // 2
BALL_SPEED_RANGE = (3, 6)
BALL_DESPAWN_X = -50

# ---- 打擊區與打者 ----
HIT_ZONE_POS = (50, SCREEN_HEIGHT // 2 - 40)
HIT_ZONE_SIZE = (80, 80)
HIT_ZONE_RECT = pygame.Rect(HIT_ZONE_POS, HIT_ZONE_SIZE)
HITTER_OFFSET = (0, -60)

# ---- 遊戲狀態 ----
swinging = False
swing_time = 150   # 揮棒時間 (毫秒)
swing_start = 0
score = 0
combo = 0
lives = 3
GAME_OVER_WAIT_MS = 3000

# ---- 特效參數與狀態 ----
hit_effect_duration = 250
hit_effect_start = -1000
miss_effect_duration = 200
miss_effect_start = -1000
hit_zone_shake_magnitude = 6
hit_zone_shake_duration = 200


def reset_state():
	"""將跑局中的動態變數清為預設值，方便重新開始。"""
	global swinging, swing_start, score, combo, lives
	global hit_effect_start, miss_effect_start

	swinging = False
	swing_start = 0
	score = 0
	combo = 0
	lives = 3
	hit_effect_start = -1000
	miss_effect_start = -1000
