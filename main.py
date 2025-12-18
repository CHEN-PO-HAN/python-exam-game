import pygame
import random   
import sys  
import math 
import array
import color
import Game_variables
import scoreboard
from hitter import draw_hitter      

pygame.mixer.pre_init(44100, -16, 1, 64) #44.1kHz, 16bit, 單聲道, 64 bytes buffer，減少延遲經測試沒有雜音
pygame.init()


def generate_tone(freq, duration_ms, volume=0.5):   # 產生音調
    sample_rate = 44100 # 44.1 kHz
    sample_count = int(sample_rate * duration_ms / 1000)    #取樣率乘以音效時長(毫秒轉秒)
    amplitude = int(32767 * volume) #16位元音量範圍-32768到32767
    buffer = array.array("h")   # "h"表示16位元有符號整數陣列，用於儲存每個時間點的波形值
    for i in range(sample_count):   # 產生每個取樣點的波形值
        sample = int(amplitude * math.sin(2 * math.pi * freq * (i / sample_rate)))
        '''把第 i 個取樣點應該是什麼振幅算出來'''
        buffer.append(sample)   # 將計算出的取樣值加入陣列
    return pygame.mixer.Sound(buffer=buffer.tobytes())  # 將陣列轉成位元組丟給 pygame 建立 Sound 物件


def load_assets():  #載入遊戲資產
    ball_img = pygame.image.load(Game_variables.BALL_IMAGE_PATH).convert_alpha()    #載入並轉換球圖片以支援透明
    ball_img = pygame.transform.scale(      
        ball_img,
        (Game_variables.ball_radius * 2, Game_variables.ball_radius * 2),
    )   #調整球圖片大小為直徑

    grass_img = pygame.image.load(Game_variables.BACKGROUND_IMAGE_PATH).convert()   #載入並轉換草地背景圖片
    grass_img = pygame.transform.scale(
        grass_img,
        (Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT),
    )   #調整草地圖片大小以符合視窗

    font = pygame.font.SysFont(Game_variables.FONT_NAME, Game_variables.FONT_SIZE)  #建立系統字型物件

    try:    #嘗試產生音效
        hit_sound = generate_tone(880, 80, 0.6)
        miss_sound = generate_tone(220, 150, 0.5)
    except pygame.error:    #若產生失敗讓他沒聲音
        hit_sound = None
        miss_sound = None

    return {    
        "ball_img": ball_img,
        "grass_img": grass_img,
        "font": font,
        "hit_sound": hit_sound,
        "miss_sound": miss_sound,
    }   #回傳資產字典


def spawn_ball():   #產生新球
    ball_type = random.choice(["fastball", "curve", "changeup"])    #隨機選擇球種，直球、曲球、變速球
    speed_ranges = {
        "fastball": (10, 15),   #直球速度範圍
        "curve": Game_variables.BALL_SPEED_RANGE,
        "changeup": (6, 12),    #變速球速度範圍
    }   #不同球種的速度範圍
    min_speed, max_speed = speed_ranges.get(ball_type, Game_variables.BALL_SPEED_RANGE)  #取得該球種的速度範圍
    ball = {
        "x": Game_variables.SCREEN_WIDTH + Game_variables.BALL_SPAWN_OFFSET_X,  #球一開始出現在螢幕右側外面
        "y": Game_variables.BALL_BASELINE_Y,    #球的 Y 座標在基準線位置
        "speed": random.uniform(min_speed, max_speed),  #隨機決定球速(浮點數)
        "type": ball_type,
    }   #建立球的初始資料
    if ball_type == "curve":    
        ball["curve_freq"] = random.uniform(0.02, 0.08)  #曲球的頻率
        ball["curve_amp"] = random.uniform(1.5, 5.0)    #曲球的振幅!!!
    return ball


def init_state(scoreboard_entries):   #初始化遊戲狀態
    hit_zone = Game_variables.HIT_ZONE_RECT.copy()  #建立擊球區矩形
    hitter_x = hit_zone.centerx + Game_variables.HITTER_OFFSET[0]   #計算打者 X 座標
    hitter_y = hit_zone.top + Game_variables.HITTER_OFFSET[1]   #計算打者 Y 座標
    current_time = pygame.time.get_ticks()
    return {
        "ball": spawn_ball(),   #產生初始球
        "hit_zone": hit_zone,   #擊球區矩形
        "hitter_pos": (hitter_x, hitter_y), #打者座標
        "game_over": False, #遊戲結束標記
        "game_over_start": 0,   #遊戲結束時間
        "paused": False,    #暫停標記
        "scoreboard": list(scoreboard_entries),  #得分榜紀錄
        "score_recorded": False,    #避免重複寫入得分榜
        "ready_until": current_time + Game_variables.READY_GO_DURATION_MS,
    }


def reset_game(state):  #重置遊戲狀態
    Game_variables.reset_state()    #呼叫 Game_variables 裡的 reset_state() 重置動態變數
    state["ball"] = spawn_ball()    #產生新球
    state["game_over"] = False      #取消遊戲結束標記
    state["game_over_start"] = 0    #重置遊戲結束時間
    state["paused"] = False         #取消暫停標記
    state["score_recorded"] = False
    state["ready_until"] = pygame.time.get_ticks() + Game_variables.READY_GO_DURATION_MS


def ensure_score_recorded(state):
    if state["score_recorded"]:
        return
    state["scoreboard"] = scoreboard.record_score(
        state["scoreboard"],
        Game_variables.score,
        Game_variables.SCOREBOARD_LIMIT,
    )
    scoreboard.save_scores(Game_variables.SCOREBOARD_FILE, state["scoreboard"])
    Game_variables.scoreboard = list(state["scoreboard"])
    state["score_recorded"] = True


def shaken_hit_zone(rect, now):
    elapsed = now - Game_variables.hit_effect_start
    if elapsed < Game_variables.hit_zone_shake_duration:
        strength = 1 - (elapsed / Game_variables.hit_zone_shake_duration)
        offset_x = math.sin(elapsed * 0.08) * Game_variables.hit_zone_shake_magnitude * strength
        offset_y = math.cos(elapsed * 0.13) * (Game_variables.hit_zone_shake_magnitude * 0.6) * strength
        return rect.move(int(offset_x), int(offset_y))
    return rect


def update(state, current_time, assets):    #更新遊戲邏輯與狀態
    for event in pygame.event.get():    #處理事件
        if event.type == pygame.QUIT:   #使用者關閉視窗
            return False    #回傳 False 結束遊戲主迴圈
        if event.type == pygame.KEYDOWN:    #按下鍵盤按鍵
            if event.key == pygame.K_r:  #按 R 鍵重新開始遊戲
                reset_game(state)   #重置遊戲狀態
                continue    #忽略其他按鍵輸入
            if state["game_over"] and event.key == pygame.K_ESCAPE:  #遊戲結束時允許按 ESC 離開
                return False
            if event.key == pygame.K_p and not state["game_over"]:  #按 P 鍵暫停或繼續遊戲
                state["paused"] = not state["paused"]   #切換暫停狀態
                continue    #忽略其他按鍵輸入
            if state["game_over"] or state["paused"]:   #遊戲結束或暫停時忽略其他按鍵
                continue    #忽略其他按鍵輸入
            if event.key == pygame.K_SPACE and not Game_variables.swinging: #按空白鍵揮棒，且目前沒有在揮棒中
                Game_variables.swinging = True  #標記為正在揮棒
                Game_variables.swing_start = current_time   #記錄揮棒開始時間

    if current_time < state["ready_until"]:
        Game_variables.swinging = False
        return True

    if state["game_over"]:
        ensure_score_recorded(state)
        return True

    if state["paused"]:
        return True

    if Game_variables.swinging and Game_variables.swing_time > 0:
        if current_time - Game_variables.swing_start > Game_variables.swing_time:
            Game_variables.swinging = False

    ball = state["ball"]
    if ball["type"] == "fastball":  # 直球
        ball["x"] -= ball["speed"]  #以固定速度讓球沿 X 軸向左移動
    elif ball["type"] == "curve":  # 曲球
        ball["x"] -= ball["speed"]  #同樣先沿 X 軸減速前進
        ball["y"] += math.sin(ball["x"] * ball["curve_freq"]) * ball["curve_amp"]   #再用正弦函數乘以振幅，讓 Y 軸產生曲球晃動
    elif ball["type"] == "changeup":  # 變速球
        ball["x"] -= ball["speed"]  #先照原速往左移
        ball["speed"] = max(3, ball["speed"] * 0.995)   #然後把速度乘 0.995 做出逐漸減速，並確保最低不小於 3

    ball_rect = pygame.Rect(    #建立 球的hitbox，以球中心與半徑打造碰撞矩形
        ball["x"] - Game_variables.ball_radius, #X 座標向左偏移半徑得到矩形左邊
        ball["y"] - Game_variables.ball_radius, #Y 座標向上偏移半徑得到矩形頂端
        Game_variables.ball_radius * 2,  #寬度為直徑
        Game_variables.ball_radius * 2,  #高度一樣是直徑
    )

    if Game_variables.swinging and ball_rect.colliderect(state["hit_zone"]):#若目前正在揮棒且球矩形與擊球區相交
        Game_variables.score += 100 + Game_variables.combo * 20 #分數+100 再加上 combo數 乘 20 的加成
        Game_variables.combo += 1   #連擊數 +1
        Game_variables.hit_effect_start = current_time  #記錄命中特效啟動時間
        if assets["hit_sound"]: #若命中音效存在
            assets["hit_sound"].play()  #播放命中音效
        state["ball"] = spawn_ball()    #立即生成下一顆球

    if ball["x"] < Game_variables.BALL_DESPAWN_X:   #如果球飛出螢幕左側的 despawn X
        Game_variables.lives -= 1   #扣一條命
        Game_variables.combo = 0    #連擊歸零
        Game_variables.miss_effect_start = current_time    #記錄失誤特效開始時間
        if assets["miss_sound"]:    #若失誤音效存在
            assets["miss_sound"].play()    #播放失誤音效
        state["ball"] = spawn_ball()       #產生下一顆球繼續遊戲
        if Game_variables.lives <= 0:      #若生命降到 0 或以下
            state["game_over"] = True      #標記遊戲結束
            state["game_over_start"] = current_time    #記錄遊戲結束時間
            ensure_score_recorded(state)

    return True    #update() 成功更新就回傳 True 讓主迴圈持續


def render(screen, assets, state, current_time):    #繪製遊戲畫面
    screen.blit(assets["grass_img"], (0, 0))    #把草地背景鋪滿視窗

    display_hit_zone = shaken_hit_zone(state["hit_zone"], current_time)    #取得可能有抖動偏移的擊球區矩形
    pygame.draw.rect(screen, (0, 0, 0), display_hit_zone, 2)    #用黑色描出擊球區框線

    ball = state["ball"]    #再度取出目前球資料
    screen.blit(
        assets["ball_img"],
        (
            int(ball["x"] - Game_variables.ball_radius),
            int(ball["y"] - Game_variables.ball_radius),
        ),
    )    #把球圖片繪製在球的座標，並以半徑做偏移讓圖片中心對齊球座標

    hitter_x, hitter_y = state["hitter_pos"]    #取得打者座標
    draw_hitter(
        screen,
        hitter_x,
        hitter_y,
        Game_variables.swinging,    #是否正在揮棒
        Game_variables.swing_start,   #揮棒開始時間
        Game_variables.swing_time,    #揮棒持續時間
        color,
    )    #呼叫 draw_hitter()，把揮棒狀態與時序資訊傳給角色繪製函式

    # 特效
    hit_elapsed = current_time - Game_variables.hit_effect_start    #算命中特效已經經過多久
    if hit_elapsed < Game_variables.hit_effect_duration:    #若還在特效持續時間內
        progress = hit_elapsed / Game_variables.hit_effect_duration  #將經過時間除以總長度得到動畫進度(0.0~1.0)
        radius = int(35 + progress * 45)    #依進度線性放大外圈半徑， 35 漸增到 80
        alpha = max(0, 255 - int(progress * 255))   #依進度線性降低透明度，從 255 漸變到 0
        ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)    #建立具透明通道的表面供圓環使用
        pygame.draw.circle(ring_surface, (255, 255, 255, alpha), (radius, radius), radius, 3)   #在 surface 上畫出白色外環
        pygame.draw.circle(
            ring_surface,
            (255, 200, 120, alpha),
            (radius, radius),
            max(5, int(radius * 0.4)),
            0,
        )   #在 surface 上畫出內圈實心圓
        screen.blit(ring_surface, (display_hit_zone.centerx - radius, display_hit_zone.centery - radius))   #把圓環繪製在擊球區中心位置

    miss_elapsed = current_time - Game_variables.miss_effect_start  #算失誤特效經過時間
    if miss_elapsed < Game_variables.miss_effect_duration:  #若還在特效持續時間內
        miss_surface = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)  #建立全螢幕透明表面
        intensity = max(0, 120 - int(120 * (miss_elapsed / Game_variables.miss_effect_duration)))   #計算紅色遮罩強度，從 120 漸變到 0
        miss_surface.fill((255, 50, 50, intensity))  #用紅色填滿表面並設定透明度
        screen.blit(miss_surface, (0, 0))   #把紅色遮罩繪製到螢幕上

    # 分數與提示文字固定在右下角
    font = assets["font"]

    text = font.render(
        f"分數: {Game_variables.score}  連擊: {Game_variables.combo}  生命: {Game_variables.lives}",
        True,
        color.BLACK,
    )   #繪製分數文字
    screen.blit(
        text,
        (
            Game_variables.SCREEN_WIDTH - text.get_width() - 20,
            Game_variables.SCREEN_HEIGHT - text.get_height() - 60,
        ),  
    )   #把分數文字繪製在右下角，距離邊界 20 像素

    hint = font.render("SPACE揮棒  P暫停/繼續  R重新開始", True, color.BLACK)   #繪製提示文字
    screen.blit(
        hint,
        (
            Game_variables.SCREEN_WIDTH - hint.get_width() - 20,
            Game_variables.SCREEN_HEIGHT - hint.get_height() - 20,
        ),
    )   #把提示文字繪製在右下角，距離邊界 20 像素

    if state["paused"] and not state["game_over"]:  #暫停畫面
        overlay = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)  #建立全螢幕透明表面
        overlay.fill((0, 0, 0, 140))    #用半透明黑色填滿表面
        screen.blit(overlay, (0, 0))    #把半透明遮罩繪製到螢幕上
        paused_text = font.render("暫停中", True, color.WHITE)  #繪製暫停文字
        sub_text = font.render("按 P 繼續 / R 重來", True, color.WHITE) #繪製子提示文字
        screen.blit(
            paused_text,
            (
                Game_variables.SCREEN_WIDTH // 2 - paused_text.get_width() // 2,        
                Game_variables.SCREEN_HEIGHT // 2 - paused_text.get_height(),   
            ),
        )   #把暫停文字繪製在螢幕中央
        screen.blit(
            sub_text,
            (
                Game_variables.SCREEN_WIDTH // 2 - sub_text.get_width() // 2,   
                Game_variables.SCREEN_HEIGHT // 2 + 10,
            ),
        )   #把子提示文字繪製在暫停文字下方

    # Game Over 畫面
    if state["game_over"]:
        overlay = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)  #建立全螢幕透明表面
        overlay.fill((0, 0, 0, 170))    #用較深的半透明黑色填滿表面
        screen.blit(overlay, (0, 0))    #把半透明遮罩繪製到螢幕上
        message = font.render(f"GAME OVER   分數: {Game_variables.score}", True, color.WHITE)   #繪製遊戲結束文字
        screen.blit(
            message,
            (
                Game_variables.SCREEN_WIDTH // 2 - message.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 - message.get_height(),
            ),
        )   #把遊戲結束文字繪製在螢幕中央
        exit_hint = font.render("按 R 重來 / ESC 離開", True, color.WHITE)
        screen.blit(
            exit_hint,
            (
                Game_variables.SCREEN_WIDTH // 2 - exit_hint.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 + exit_hint.get_height() // 2,
            ),
        )

    if state["game_over"]:
        scoreboard_title = font.render("得分榜", True, color.WHITE)
        screen.blit(scoreboard_title, (20, 20))
        if state["scoreboard"]:
            for index, value in enumerate(state["scoreboard"], start=1):
                entry_text = font.render(f"{index}. {value}", True, color.WHITE)
                screen.blit(entry_text, (20, 20 + index * (font.get_linesize() + 4)))
        else:
            empty_text = font.render("尚無紀錄", True, color.WHITE)
            screen.blit(empty_text, (20, 20 + font.get_linesize() + 4))
    else:
        best = state["scoreboard"][0] if state["scoreboard"] else 0
        highlight = font.render(f"最高分: {best}", True, color.WHITE)
        screen.blit(highlight, (20, 20))

    ready_time_left = state["ready_until"] - current_time
    if ready_time_left > 0:
        overlay = pygame.Surface((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        progress = 1 - (ready_time_left / Game_variables.READY_GO_DURATION_MS)
        message = "READY" if progress < 0.5 else "GO!"
        ready_text = font.render(message, True, color.WHITE)
        screen.blit(
            ready_text,
            (
                Game_variables.SCREEN_WIDTH // 2 - ready_text.get_width() // 2,
                Game_variables.SCREEN_HEIGHT // 2 - ready_text.get_height() // 2,
            ),
        )

    pygame.display.flip()   #更新整個顯示畫面


def main():
    screen = pygame.display.set_mode((Game_variables.SCREEN_WIDTH, Game_variables.SCREEN_HEIGHT))   #建立遊戲視窗
    pygame.display.set_caption(Game_variables.WINDOW_TITLE) #設定視窗標題
    clock = pygame.time.Clock()  #建立遊戲時鐘物件

    assets = load_assets()  #載入遊戲資產
    Game_variables.scoreboard = scoreboard.load_scores(
        Game_variables.SCOREBOARD_FILE,
        Game_variables.SCOREBOARD_LIMIT,
    )
    state = init_state(Game_variables.scoreboard)    #初始化遊戲狀態

    while True: #遊戲主迴圈
        clock.tick(Game_variables.GAME_SPEED_RATE)  #控制遊戲迴圈速度以符合設定的 FPS
        current_time = pygame.time.get_ticks()  #取得目前遊戲時間(毫秒)
        if not update(state, current_time, assets): #更新遊戲狀態，若回傳 False 則結束遊戲
            break
        render(screen, assets, state, current_time)  #繪製遊戲畫面

    pygame.quit()   #結束 Pygame
    sys.exit()  #結束程式


if __name__ == "__main__":  
    main()  #執行主程式