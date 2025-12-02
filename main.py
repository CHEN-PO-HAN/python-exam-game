import pygame
import random
import sys
import math
import array
import color
import Game_variables
from hitter import draw_hitter

pygame.mixer.pre_init(44100, -16, 1, 256)
pygame.init()


def generate_tone(freq, duration_ms, volume=0.5):
    """產生簡單的正弦波音效，用於命中與失誤的提示。"""
    sample_rate = 44100
    sample_count = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * volume)
    buffer = array.array("h")
    for i in range(sample_count):
        sample = int(amplitude * math.sin(2 * math.pi * freq * (i / sample_rate)))
        buffer.append(sample)
    return pygame.mixer.Sound(buffer=buffer.tobytes())


def load_assets():
    """載入並縮放圖片、字型，以及備用產生的音效。"""
    ball_img = pygame.image.load(Game_variables.BALL_IMAGE_PATH).convert_alpha()
    ball_img = pygame.transform.scale(
        ball_img,
        (Game_variables.ball_radius * 2, Game_variables.ball_radius * 2),
    )

    grass_img = pygame.image.load(Game_variables.BACKGROUND_IMAGE_PATH).convert()
    grass_img = pygame.transform.scale(
        grass_img,
        (Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT),
    )

    font = pygame.font.SysFont(Game_variables.FONT_NAME, Game_variables.FONT_SIZE)

    try:
        hit_sound = generate_tone(880, 80, 0.6)
        miss_sound = generate_tone(220, 150, 0.5)
    except pygame.error:
        hit_sound = None
        miss_sound = None

    return {
        "ball_img": ball_img,
        "grass_img": grass_img,
        "font": font,
        "hit_sound": hit_sound,
        "miss_sound": miss_sound,
    }


def spawn_ball():
    """在螢幕右側外生成球，讓它向打擊區飛入。"""
    return [
        Game_variables.SCREEN_WIDTH + Game_variables.BALL_SPAWN_OFFSET_X,
        Game_variables.BALL_BASELINE_Y,
        random.uniform(*Game_variables.BALL_SPEED_RANGE),
    ]


def init_state():
    """建立更新與渲染共用的遊戲狀態字典。"""
    hit_zone = Game_variables.HIT_ZONE_RECT.copy()
    hitter_x = hit_zone.centerx + Game_variables.HITTER_OFFSET[0]
    hitter_y = hit_zone.top + Game_variables.HITTER_OFFSET[1]
    return {
        "ball": spawn_ball(),
        "hit_zone": hit_zone,
        "hitter_pos": (hitter_x, hitter_y),
        "game_over": False,
        "game_over_start": 0,
        "paused": False,
    }


def reset_game(state):
    """重置狀態只重置遊戲狀態（球、分數、combo、暫停旗標等），重新開始回合。"""
    Game_variables.reset_state()
    state["ball"] = spawn_ball()
    state["game_over"] = False
    state["game_over_start"] = 0
    state["paused"] = False


def shaken_hit_zone(rect, now):
    """命中後讓打擊區短暫震動，增加手感。"""
    elapsed = now - Game_variables.hit_effect_start
    if elapsed < Game_variables.hit_zone_shake_duration:
        strength = 1 - (elapsed / Game_variables.hit_zone_shake_duration)
        offset_x = math.sin(elapsed * 0.08) * Game_variables.hit_zone_shake_magnitude * strength
        offset_y = math.cos(elapsed * 0.13) * (Game_variables.hit_zone_shake_magnitude * 0.6) * strength
        return rect.move(int(offset_x), int(offset_y))
    return rect


def update(state, current_time, assets):
    """負責處理輸入、推進遊戲計時並結算碰撞。"""
        # 集中處理事件，確保熱鍵（重開/暫停）隨時可用。
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game(state)
                continue
            if event.key == pygame.K_p and not state["game_over"]:
                    # 按下 P 時切換暫停狀態。
                state["paused"] = not state["paused"]
                continue
            if state["game_over"] or state["paused"]:
                continue
            if event.key == pygame.K_SPACE and not Game_variables.swinging:
                Game_variables.swinging = True
                Game_variables.swing_start = current_time

    if state["game_over"]:
        if current_time - state["game_over_start"] >= Game_variables.GAME_OVER_WAIT_MS:
            return False
        return True

    if state["paused"]:
            # 繼續跑迴圈等輸入，但停止模擬更新。
        return True

    if Game_variables.swinging and Game_variables.swing_time > 0:
        if current_time - Game_variables.swing_start > Game_variables.swing_time:
            Game_variables.swinging = False

    state["ball"][0] -= state["ball"][2]

    ball_rect = pygame.Rect(
        state["ball"][0] - Game_variables.ball_radius,
        state["ball"][1] - Game_variables.ball_radius,
        Game_variables.ball_radius * 2,
        Game_variables.ball_radius * 2,
    )

    if Game_variables.swinging and ball_rect.colliderect(state["hit_zone"]):
        Game_variables.score += 100 + Game_variables.combo * 20
        Game_variables.combo += 1
        Game_variables.hit_effect_start = current_time
        if assets["hit_sound"]:
            assets["hit_sound"].play()
        state["ball"] = spawn_ball()

    if state["ball"][0] < Game_variables.BALL_DESPAWN_X:
        Game_variables.lives -= 1
        Game_variables.combo = 0
        Game_variables.miss_effect_start = current_time
        if assets["miss_sound"]:
            assets["miss_sound"].play()
        state["ball"] = spawn_ball()
        if Game_variables.lives <= 0:
            state["game_over"] = True
            state["game_over_start"] = current_time

    return True


def render(screen, assets, state, current_time):
    """負責繪製畫面、覆蓋層與短暫特效。"""
    screen.blit(assets["grass_img"], (0, 0))

    display_hit_zone = shaken_hit_zone(state["hit_zone"], current_time)
    pygame.draw.rect(screen, (50, 50, 50), display_hit_zone, 2)

    screen.blit(
        assets["ball_img"],
        (
            int(state["ball"][0] - Game_variables.ball_radius),
            int(state["ball"][1] - Game_variables.ball_radius),
        ),
    )

    hitter_x, hitter_y = state["hitter_pos"]
    draw_hitter(
        screen,
        hitter_x,
        hitter_y,
        Game_variables.swinging,
        Game_variables.swing_start,
        Game_variables.swing_time,
        color,
    )

    hit_elapsed = current_time - Game_variables.hit_effect_start
    if hit_elapsed < Game_variables.hit_effect_duration:
        progress = hit_elapsed / Game_variables.hit_effect_duration
        radius = int(35 + progress * 45)
        alpha = max(0, 255 - int(progress * 255))
        ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_surface, (255, 255, 255, alpha), (radius, radius), radius, 3)
        pygame.draw.circle(
            ring_surface,
            (255, 200, 120, alpha),
            (radius, radius),
            max(5, int(radius * 0.4)),
            0,
        )
        screen.blit(ring_surface, (display_hit_zone.centerx - radius, display_hit_zone.centery - radius))

    miss_elapsed = current_time - Game_variables.miss_effect_start
    if miss_elapsed < Game_variables.miss_effect_duration:
        miss_surface = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)
        intensity = max(0, 120 - int(120 * (miss_elapsed / Game_variables.miss_effect_duration)))
        miss_surface.fill((255, 50, 50, intensity))
        screen.blit(miss_surface, (0, 0))

    font = assets["font"]
    text = font.render(
        f"分數: {Game_variables.score}  連擊: {Game_variables.combo}  生命: {Game_variables.lives}",
        True,
        color.BLACK,
    )
    screen.blit(text, (20, 20))
    hint = font.render("SPACE揮棒  P暫停/繼續  R重新開始", True, color.BLACK)
    screen.blit(hint, (20, 60))

    if state["paused"] and not state["game_over"]:
        overlay = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        paused_text = font.render("暫停中", True, color.WHITE)
        sub_text = font.render("按 P 繼續 / R 重來", True, color.WHITE)
        screen.blit(
            paused_text,
            (
                Game_variables.SCREEN_WIDTH // 2 - paused_text.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 - paused_text.get_height(),
            ),
        )
        screen.blit(
            sub_text,
            (
                Game_variables.SCREEN_WIDTH // 2 - sub_text.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 + 10,
            ),
        )

    if state["game_over"]:
        overlay = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        message = font.render(f"GAME OVER   分數: {Game_variables.score}", True, color.WHITE)
        screen.blit(
            message,
            (
                Game_variables.SCREEN_WIDTH // 2 - message.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 - message.get_height() // 2,
            ),
        )

    pygame.display.flip()


def main():
    """初始化 pygame，並執行更新/渲染迴圈直到結束。"""
    screen = pygame.display.set_mode((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT))
    pygame.display.set_caption(Game_variables.WINDOW_TITLE)
    clock = pygame.time.Clock()

    assets = load_assets()
    state = init_state()

    while True:
        clock.tick(Game_variables.FPS)
        current_time = pygame.time.get_ticks()
        if not update(state, current_time, assets):
            break
        render(screen, assets, state, current_time)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
