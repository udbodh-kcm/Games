
import math
import random
import sys
import pygame

# --------------------------------------------------------------------------
# Config / palette
# --------------------------------------------------------------------------

WIDTH, HEIGHT = 900, 640
FPS = 60

BG_TOP = (23, 32, 45)
BG_BOTTOM = (10, 14, 20)
LINE = (35, 43, 56)
INK = (231, 236, 243)
INK_DIM = (141, 151, 168)
GOLD = (232, 176, 75)
GOLD_LIGHT = (244, 200, 119)
GOLD_DIM = (138, 106, 46)
TEAL = (73, 214, 196)
VIOLET = (176, 132, 232)
DANGER = (224, 86, 76)

ORB_COLORS = [GOLD, TEAL, VIOLET]
ORB_VALUES = {GOLD: 10, TEAL: 15, VIOLET: 25}

LIVES_MAX = 3
PADDLE_H = 16
PADDLE_SPEED = 620  # px/sec, keyboard control


def level_params(level: int) -> dict:
    """Difficulty curve: more concurrent orbs, faster falls, tighter spawns."""
    max_concurrent = min(2 + int((level - 1) * 0.8), 7)
    fall_speed = 150 + (level - 1) * 26       # px/sec baseline
    spawn_interval = max(950 - (level - 1) * 70, 320)  # ms
    catches_needed = 8 + (level - 1) * 3
    paddle_w = max(84, 118 - level * 2)
    return {
        "max_concurrent": max_concurrent,
        "fall_speed": fall_speed,
        "spawn_interval": spawn_interval,
        "catches_needed": catches_needed,
        "paddle_w": paddle_w,
    }


def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def lerp(a, b, t):
    return a + (b - a) * t


# --------------------------------------------------------------------------
# Game objects
# --------------------------------------------------------------------------

class Orb:
    __slots__ = ("x", "y", "r", "vy", "color", "value", "wobble")

    def __init__(self, x, y, r, vy, color):
        self.x = x
        self.y = y
        self.r = r
        self.vy = vy
        self.color = color
        self.value = ORB_VALUES[color]
        self.wobble = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.y += self.vy * dt
        self.wobble += dt * 2

    def draw(self, surf):
        wob = math.sin(self.wobble) * 1.5
        cx, cy = int(self.x + wob), int(self.y)
        glow = pygame.Surface((self.r * 4, self.r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 60), (self.r * 2, self.r * 2), int(self.r * 1.8))
        surf.blit(glow, (cx - self.r * 2, cy - self.r * 2), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surf, shade(self.color, -30), (cx, cy), int(self.r))
        pygame.draw.circle(surf, self.color, (cx, cy), int(self.r * 0.82))
        highlight = shade(self.color, 90)
        pygame.draw.circle(surf, highlight, (cx - int(self.r * 0.3), cy - int(self.r * 0.3)), max(2, int(self.r * 0.25)))


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "color")

    def __init__(self, x, y, vx, vy, color):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = 1.0
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 260 * dt
        self.life -= dt * 1.6

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(self.life * 255)))
        s = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (3, 3), 3)
        surf.blit(s, (int(self.x) - 3, int(self.y) - 3))


def spawn_burst(particles, x, y, color):
    for i in range(10):
        ang = (math.pi * 2 / 10) * i + random.uniform(0, 0.3)
        speed = random.uniform(60, 150)
        particles.append(Particle(x, y, math.cos(ang) * speed, math.sin(ang) * speed, color))


# --------------------------------------------------------------------------
# Game
# --------------------------------------------------------------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Freefall — Catch the Orbs")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = self._font(48, bold=True)
        self.font_sub = self._font(18)
        self.font_hud_label = self._font(13, bold=True)
        self.font_hud_value = self._font(30, bold=True)
        self.font_btn = self._font(20, bold=True)
        self.font_flash = self._font(40, bold=True)

        self.bg = self._make_background()
        self.best_score = 0
        self.reset_state()
        self.state = "idle"  # idle | playing | levelup | over

    @staticmethod
    def _font(size, bold=False):
        name = pygame.font.match_font("arial,helvetica,sans-serif", bold=bold)
        return pygame.font.Font(name, size)

    @staticmethod
    def _make_background():
        surf = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            color = tuple(int(lerp(BG_TOP[i], BG_BOTTOM[i], t)) for i in range(3))
            pygame.draw.line(surf, color, (0, y), (WIDTH, y))
        return surf

    def reset_state(self):
        self.score = 0
        self.level = 1
        self.lives = LIVES_MAX
        self.catches = 0
        self.orbs = []
        self.particles = []
        self.spawn_timer = 0.0
        self.levelup_timer = 0.0
        self.flash_timer = 0.0
        params = level_params(self.level)
        self.spawn_interval = params["spawn_interval"]
        self.catches_needed = params["catches_needed"]
        self.paddle_w = params["paddle_w"]
        self.paddle_x = WIDTH / 2 - self.paddle_w / 2
        self.paddle_target_x = self.paddle_x
        self.paddle_y = HEIGHT - 60

    def start_game(self):
        self.reset_state()
        self.state = "playing"

    def end_game(self):
        self.state = "over"
        if self.score > self.best_score:
            self.best_score = self.score

    def advance_level(self):
        self.level += 1
        self.catches = 0
        params = level_params(self.level)
        self.spawn_interval = params["spawn_interval"]
        self.catches_needed = params["catches_needed"]
        self.paddle_w = params["paddle_w"]
        self.paddle_x = min(max(self.paddle_x, 0), WIDTH - self.paddle_w)
        self.paddle_target_x = self.paddle_x
        self.flash_timer = 1.1

    # ---- update ----

    def handle_input(self, dt, keys):
        if self.state != "playing":
            return
        mx, _ = pygame.mouse.get_pos()
        if pygame.mouse.get_rel() != (0, 0) or True:
            # follow mouse directly when it moves; keys nudge target too
            pass
        moved_by_key = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle_target_x -= PADDLE_SPEED * dt
            moved_by_key = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle_target_x += PADDLE_SPEED * dt
            moved_by_key = True
        if not moved_by_key:
            self.paddle_target_x = mx - self.paddle_w / 2
        self.paddle_target_x = min(max(self.paddle_target_x, 0), WIDTH - self.paddle_w)
        self.paddle_x += (self.paddle_target_x - self.paddle_x) * min(1.0, dt * 14)

    def spawn_orb(self):
        r = random.uniform(13, 20)
        roll = random.random()
        color = VIOLET if roll < 0.14 else (TEAL if roll < 0.32 else GOLD)
        params = level_params(self.level)
        vy = params["fall_speed"] * random.uniform(0.85, 1.15)
        x = r + random.uniform(0, WIDTH - 2 * r)
        self.orbs.append(Orb(x, -r - 10, r, vy, color))

    def update(self, dt, keys):
        if self.state == "playing":
            self.handle_input(dt, keys)

            params = level_params(self.level)
            self.spawn_timer += dt * 1000
            if self.spawn_timer >= self.spawn_interval and len(self.orbs) < params["max_concurrent"]:
                self.spawn_timer = 0
                self.spawn_orb()

            for orb in self.orbs[:]:
                orb.update(dt)
                within_x = (orb.x + orb.r * 0.6 > self.paddle_x) and (orb.x - orb.r * 0.6 < self.paddle_x + self.paddle_w)
                within_y = (orb.y + orb.r >= self.paddle_y) and (orb.y - orb.r <= self.paddle_y + PADDLE_H)
                if within_x and within_y and orb.y < self.paddle_y + PADDLE_H:
                    self.score += orb.value
                    self.catches += 1
                    spawn_burst(self.particles, orb.x, self.paddle_y, orb.color)
                    self.orbs.remove(orb)
                    if self.catches >= self.catches_needed:
                        self.state = "levelup"
                        self.levelup_timer = 0.55
                        self.advance_level()
                    continue
                if orb.y - orb.r > HEIGHT:
                    self.orbs.remove(orb)
                    self.lives -= 1
                    if self.lives <= 0:
                        self.end_game()
                        break

        elif self.state == "levelup":
            self.levelup_timer -= dt
            for orb in self.orbs[:]:
                orb.update(dt)
                if orb.y - orb.r > HEIGHT:
                    self.orbs.remove(orb)
            if self.levelup_timer <= 0:
                self.state = "playing"

        if self.flash_timer > 0:
            self.flash_timer -= dt

        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

    # ---- draw ----

    def draw_hud(self):
        pygame.draw.line(self.screen, LINE, (0, HEIGHT - 34), (WIDTH, HEIGHT - 34), 1)

        label = self.font_hud_label.render("SCORE", True, INK_DIM)
        value = self.font_hud_value.render(str(self.score), True, GOLD)
        self.screen.blit(label, (24, 20))
        self.screen.blit(value, (24, 36))

        lvl_label = self.font_hud_label.render(f"LEVEL {self.level}", True, INK_DIM)
        self.screen.blit(lvl_label, (WIDTH - lvl_label.get_width() - 24, 20))

        for i in range(LIVES_MAX):
            cx = WIDTH - 24 - (LIVES_MAX - 1 - i) * 20
            cy = 52
            if i < self.lives:
                pygame.draw.circle(self.screen, GOLD, (cx, cy), 5)
            else:
                pygame.draw.circle(self.screen, LINE, (cx, cy), 5, 2)

        # level progress bar
        bar_x, bar_y, bar_w, bar_h = 24, 84, WIDTH - 48, 4
        pygame.draw.rect(self.screen, LINE, (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        pct = min(1.0, self.catches / self.catches_needed) if self.catches_needed else 0
        if pct > 0:
            pygame.draw.rect(self.screen, GOLD, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=2)

        hint = self.font_sub.render("Mouse or  ←  →  to catch · Esc to quit", True, INK_DIM)
        self.screen.blit(hint, (WIDTH / 2 - hint.get_width() / 2, HEIGHT - 26))

    def draw_paddle(self):
        rect = pygame.Rect(int(self.paddle_x), int(self.paddle_y), int(self.paddle_w), PADDLE_H)
        glow = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*GOLD, 70), (20, 20, rect.width, rect.height), border_radius=8)
        self.screen.blit(glow, (rect.x - 20, rect.y - 20), special_flags=pygame.BLEND_RGBA_ADD)
        for i in range(rect.width):
            t = i / max(1, rect.width)
            c = tuple(int(lerp(GOLD_LIGHT[j], GOLD[j], t)) for j in range(3))
            pygame.draw.line(self.screen, c, (rect.x + i, rect.y), (rect.x + i, rect.y + rect.height))
        pygame.draw.rect(self.screen, GOLD, rect, width=0, border_radius=8)

    def draw_center_text(self, kicker, title, sub_lines, button_text, stats=None):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 20, 190))
        self.screen.blit(overlay, (0, 0))

        cy = HEIGHT / 2 - 120
        k = self.font_hud_label.render(kicker, True, TEAL)
        self.screen.blit(k, (WIDTH / 2 - k.get_width() / 2, cy))
        cy += 34

        t = self.font_title.render(title, True, INK)
        self.screen.blit(t, (WIDTH / 2 - t.get_width() / 2, cy))
        cy += 64

        for line in sub_lines:
            s = self.font_sub.render(line, True, INK_DIM)
            self.screen.blit(s, (WIDTH / 2 - s.get_width() / 2, cy))
            cy += 26

        if stats:
            cy += 14
            total_w = len(stats) * 140
            sx = WIDTH / 2 - total_w / 2
            for label, val in stats:
                nsurf = self.font_hud_value.render(str(val), True, INK)
                lsurf = self.font_hud_label.render(label, True, INK_DIM)
                self.screen.blit(nsurf, (sx + 70 - nsurf.get_width() / 2, cy))
                self.screen.blit(lsurf, (sx + 70 - lsurf.get_width() / 2, cy + 36))
                sx += 140
            cy += 70
        else:
            cy += 20

        btn_w, btn_h = 220, 48
        btn_rect = pygame.Rect(int(WIDTH / 2 - btn_w / 2), int(cy), btn_w, btn_h)
        pygame.draw.rect(self.screen, GOLD, btn_rect, border_radius=8)
        bt = self.font_btn.render(button_text, True, (10, 14, 20))
        self.screen.blit(bt, (btn_rect.centerx - bt.get_width() / 2, btn_rect.centery - bt.get_height() / 2))
        return btn_rect

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        for orb in self.orbs:
            orb.draw(self.screen)
        for p in self.particles:
            p.draw(self.screen)

        if self.state in ("playing", "levelup"):
            self.draw_paddle()
            self.draw_hud()

        if self.flash_timer > 0 and self.state in ("playing", "levelup"):
            alpha = min(255, int(255 * min(1.0, self.flash_timer / 0.3)))
            txt = self.font_flash.render(f"LEVEL {self.level}", True, GOLD)
            txt.set_alpha(alpha)
            self.screen.blit(txt, (WIDTH / 2 - txt.get_width() / 2, HEIGHT * 0.4))

        self.start_btn_rect = None
        self.retry_btn_rect = None

        if self.state == "idle":
            self.start_btn_rect = self.draw_center_text(
                "ARCADE · SKILL",
                "Freefall",
                ["Orbs drop from the dark. Catch what you can,",
                 "let nothing slip. Every level sends more at once."],
                "Start run",
            )
        elif self.state == "over":
            title = "New best." if self.score == self.best_score and self.score > 0 else "Grounded."
            self.retry_btn_rect = self.draw_center_text(
                "RUN ENDED",
                title,
                [],
                "Run it back",
                stats=[("SCORE", self.score), ("LEVEL", self.level), ("BEST", self.best_score)],
            )

        pygame.display.flip()

    # ---- main loop ----

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)  # clamp for stalls

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if self.state in ("idle", "over"):
                            self.start_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "idle" and self.start_btn_rect and self.start_btn_rect.collidepoint(event.pos):
                        self.start_game()
                    elif self.state == "over" and self.retry_btn_rect and self.retry_btn_rect.collidepoint(event.pos):
                        self.start_game()

            keys = pygame.key.get_pressed()
            self.update(dt, keys)
            self.draw()


if __name__ == "__main__":
    Game().run()