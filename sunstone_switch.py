#!/usr/bin/env python3
"""Sunstone Switch — neon three-rail junction racer for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "SUNSTONE SWITCH"
HANDLE = "x.com/ElbowOS"
VOID = (6, 12, 32)
NAVY = (10, 22, 54)
GOLD = (255, 196, 48)
AMBER = (255, 140, 28)
CYAN = (56, 228, 255)
MAG = (255, 64, 176)
LIME = (160, 255, 88)
SLAG = (255, 52, 72)
INK = (240, 248, 255)
RAIL = (38, 72, 140)
LANES = (270, 540, 810)
TOP = 280
BOT = 1680


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Seg:
    """A rail segment: kind in {orb, spike, gate, empty}."""
    __slots__ = ("y", "lane", "kind", "taken", "ang")

    def __init__(self, y, lane, kind):
        self.y, self.lane, self.kind = y, lane, kind
        self.taken = False
        self.ang = random.random() * 6.28


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 62)
        self.font_md = pygame.font.Font(None, 42)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()

    def reset(self) -> None:
        self.lane = 1
        self.tx = float(LANES[1])
        self.score = 0
        self.lives = 3
        self.pulse = 0.0
        self.cool = 0.0
        self.over = False
        self.shake = 0.0
        self.speed = 420.0
        self.dist = 0.0
        self.sparks: list[Spark] = []
        self.segs: list[Seg] = []
        self.switch_cd = 0.0
        self.stars = [(random.randrange(W), random.randrange(H), random.uniform(0.3, 1.4))
                      for _ in range(70)]
        y = 200
        for i in range(18):
            self._spawn_row(y - i * 210)

    def _spawn_row(self, y: float) -> None:
        kinds = ["empty", "empty", "orb", "orb", "spike", "gate"]
        used = set()
        for _ in range(random.randint(1, 3)):
            ln = random.randint(0, 2)
            if ln in used:
                continue
            used.add(ln)
            k = random.choice(kinds)
            if k == "empty":
                continue
            self.segs.append(Seg(y, ln, k))

    def burst(self, x, y, col, n=12) -> None:
        for _ in range(n):
            a = random.random() * 6.283
            s = random.uniform(70, 340)
            self.sparks.append(Spark(x, y, s * math.cos(a), s * math.sin(a),
                                     random.uniform(0.16, 0.46), col, random.randint(3, 7)))

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        if self.switch_cd > 0:
            return
        horizon = 640
        best, aim = -1e9, self.lane
        py = BOT - 80
        for cand in range(3):
            val = 0.0
            for sg in self.segs:
                dy = py - sg.y
                if dy < 30 or dy > horizon:
                    continue
                if sg.lane != cand or sg.taken:
                    continue
                if sg.kind == "orb":
                    val += 90 - dy * 0.05
                elif sg.kind == "spike":
                    val -= 260 - dy * 0.1
                elif sg.kind == "gate":
                    val += 24
            val -= abs(cand - self.lane) * 18
            if val > best:
                best, aim = val, cand
        if aim != self.lane:
            self.lane = aim
            self.switch_cd = 0.22

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        self.shake = max(0.0, self.shake - dt)
        self.switch_cd = max(0.0, self.switch_cd - dt)
        if self.record:
            self.autoplay()
        if self.over:
            self._fx(dt)
            return
        self.speed = min(760.0, 420.0 + self.dist * 0.012)
        scroll = self.speed * dt
        self.dist += scroll
        target = LANES[self.lane]
        self.tx += (target - self.tx) * min(1.0, 14 * dt)
        py = BOT - 80
        keep = []
        for sg in self.segs:
            sg.y += scroll
            sg.ang += 3.2 * dt
            if sg.y > H + 40:
                continue
            if (not sg.taken) and abs(sg.y - py) < 36 and sg.lane == self.lane and abs(self.tx - LANES[sg.lane]) < 48:
                sg.taken = True
                if sg.kind == "orb":
                    self.score += 25
                    self.burst(self.tx, py, GOLD, 14)
                elif sg.kind == "gate":
                    self.score += 40
                    self.burst(self.tx, py, CYAN, 16)
                    self.lane = random.choice([i for i in range(3) if i != self.lane] + [self.lane])
                elif sg.kind == "spike":
                    self._hit()
            keep.append(sg)
        self.segs = keep
        if not self.segs or min(sg.y for sg in self.segs) > 240:
            self._spawn_row(min((sg.y for sg in self.segs), default=240) - 210)
        while len(self.segs) < 16:
            top = min((sg.y for sg in self.segs), default=200)
            self._spawn_row(top - 210)
        self.score += int(scroll * 0.06)
        self._fx(dt)

    def _hit(self) -> None:
        if self.cool > 0:
            return
        self.lives -= 1
        self.shake = 0.32
        self.cool = 0.55
        self.burst(self.tx, BOT - 80, SLAG, 20)
        if self.lives <= 0:
            self.over = True
            self.cool = 1.4

    def _fx(self, dt: float) -> None:
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 140 * dt
            alive.append(sp)
        self.sparks = alive

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_r:
            self.reset()
        if self.over:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a):
            self.lane = max(0, self.lane - 1)
        if ev.key in (pygame.K_RIGHT, pygame.K_d):
            self.lane = min(2, self.lane + 1)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        ox = int(math.sin(self.pulse * 40) * 12 * self.shake)
        for sx, sy, sc in self.stars:
            yy = int((sy + self.dist * 0.18 * sc) % H)
            pygame.draw.circle(s, (40, 70, 130), (sx + ox, yy), 1 if sc < 0.8 else 2)
        pygame.draw.rect(s, NAVY, (70, TOP, W - 140, BOT - TOP), border_radius=28)
        pygame.draw.rect(s, CYAN, (70, TOP, W - 140, BOT - TOP), 3, border_radius=28)
        off = (self.dist * 0.55) % 64
        for i, lx in enumerate(LANES):
            pygame.draw.line(s, RAIL, (lx + ox, TOP + 8), (lx + ox, BOT - 8), 10)
            pygame.draw.line(s, CYAN if i == self.lane else (70, 110, 190),
                             (lx + ox, TOP + 8), (lx + ox, BOT - 8), 3)
            for k in range(28):
                y = int(TOP + 16 + k * 64 - off)
                if TOP < y < BOT:
                    pygame.draw.circle(s, GOLD if i == self.lane else (90, 130, 200),
                                       (lx + ox, y), 4)
        for sg in self.segs:
            if sg.y < TOP - 20 or sg.y > BOT + 20 or sg.taken:
                continue
            x = LANES[sg.lane] + ox
            y = int(sg.y)
            if sg.kind == "orb":
                r = 16 + int(4 * math.sin(self.pulse * 7 + sg.ang))
                pygame.draw.circle(s, (80, 50, 10), (x, y + 4), r + 6)
                pygame.draw.circle(s, GOLD, (x, y), r)
                pygame.draw.circle(s, INK, (x - 4, y - 4), 5)
            elif sg.kind == "spike":
                pts = [(x, y - 26), (x + 20, y + 16), (x - 20, y + 16)]
                pygame.draw.polygon(s, SLAG, pts)
                pygame.draw.polygon(s, AMBER, pts, 2)
            else:
                pts = []
                for k in range(4):
                    a = sg.ang + k * 1.5708
                    pts.append((x + int(math.cos(a) * 26), y + int(math.sin(a) * 26)))
                pygame.draw.polygon(s, MAG, pts)
                pygame.draw.polygon(s, CYAN, pts, 3)
        px, py = int(self.tx) + ox, BOT - 80
        glow = 20 + int(5 * math.sin(self.pulse * 9))
        pygame.draw.circle(s, (90, 40, 8), (px, py + 8), glow + 16)
        body = [(px, py - 34), (px + 28, py + 18), (px, py + 8), (px - 28, py + 18)]
        pygame.draw.polygon(s, GOLD, body)
        pygame.draw.polygon(s, AMBER, body, 3)
        pygame.draw.circle(s, CYAN, (px, py - 8), 8)
        trail = 10 + int(4 * math.sin(self.pulse * 12))
        pygame.draw.circle(s, MAG, (px, py + 26), trail)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x) + ox, int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, GOLD)
        s.blit(title, title.get_rect(center=(W // 2, 78)))
        handle = self.font_sm.render(HANDLE, True, MAG)
        s.blit(handle, handle.get_rect(center=(W // 2, 128)))
        meta = self.font_md.render(
            f"SCORE  {self.score}    LIVES  {max(0, self.lives)}    {int(self.dist)}m", True, CYAN
        )
        s.blit(meta, meta.get_rect(center=(W // 2, 186)))
        hint = self.font_sm.render("A / D  switch rails    R reset", True, LIME)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.over:
            over = self.font_md.render("RAIL SHATTERED", True, SLAG)
            s.blit(over, over.get_rect(center=(W // 2, 240)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/SUNSTONE_SWITCH_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
