"""負責繪製火柴人打者並提供補間揮棒姿勢。"""

import pygame

_pose_cache = {
    "hand": None,
    "bat": None,
}


def _lerp(prev, target, factor):    
    """往目標點補間，讓姿勢轉換更平滑。"""
    if prev is None:
        return target   #初始狀態直接回傳目標點
    return (
        prev[0] + (target[0] - prev[0]) * factor,   
        prev[1] + (target[1] - prev[1]) * factor,   
    )


def _as_ints(point):
    """將浮點座標轉成整數，方便 pygame 繪圖。"""
    return int(point[0]), int(point[1])


def draw_hitter(screen, x, y, swinging, swing_start, swing_time, colors):
    """用兩段補間動作渲染打者揮棒。"""
    now = pygame.time.get_ticks()
    swing_phase = 0.0
    if swinging and swing_time > 0:
        swing_phase = min(1.0, (now - swing_start) / swing_time)

    # 頭身
    pygame.draw.circle(screen, colors.WHITE, (x, y), 15)
    pygame.draw.line(screen, colors.WHITE, (x, y), (x, y + 20), 4)

    hand_target = (x, y + 15)
    hand_pos = _lerp(_pose_cache["hand"], hand_target, 0.45)
    _pose_cache["hand"] = hand_pos

    hand_x, hand_y = hand_pos
    if swinging:
        if swing_phase < 0.5:
            t = swing_phase / 0.5
            bat_target = (hand_x - 25 + t * 25, hand_y + t * 40)
        else:
            t = (swing_phase - 0.5) / 0.5
            bat_target = (hand_x + t * 15, hand_y + 40 + t * 60)
    else:
        bat_target = (hand_x - 30, hand_y - 5)

    bat_pos = _lerp(_pose_cache["bat"], bat_target, 0.35)
    _pose_cache["bat"] = bat_pos

    # 手臂與球棒
    pygame.draw.line(screen, colors.WHITE, (x, y), _as_ints(hand_pos), 4)
    pygame.draw.line(screen, colors.BLUE, _as_ints(hand_pos), _as_ints(bat_pos), 6)