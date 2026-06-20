#!/usr/bin/env python3
"""
orbital_video_generator_v2.py
QuoteMyAnything — Orbital Brand Video Generator (v2)

Renders a short, social-ready promo video in which the home-service verticals
orbit the central QMA brand mark, set to the QMA jingle. Built for Reels /
Shorts / TikTok (vertical 9:16) with square and landscape variants.

Brand-locked per BRAND_GUIDELINES.md:
  - Dark theme (#0f172a), emerald accent (#10b981), amber CTA (#f59e0b)
  - Slogan: "Free Quotes On Anything!"
  - One-liner: 3+ competing quotes from local pros in 60 seconds. Always free.

v2 improvements over v1:
  - Self-contained renderer (PIL frames piped straight to a bundled ffmpeg) so
    it runs with zero system packages — no system ffmpeg required.
  - Two counter-rotating orbit rings with eased intro/outro animation.
  - Jingle is auto-selected by duration, looped and muxed with -shortest.
  - Square / vertical / landscape presets, configurable duration + fps.
  - Graceful degradation: renders a silent video if no audio backend is found
    and a programmatic brand mark if logo assets are missing.

Usage:
    python orbital_video_generator_v2.py
    python orbital_video_generator_v2.py --format square --duration 6
    python orbital_video_generator_v2.py --out build/qma_orbital.mp4 --fps 30
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit(
        "Pillow is required. Install it with:\n"
        "    pip install Pillow imageio-ffmpeg\n"
    )

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

# --- Brand palette (locked, see BRAND_GUIDELINES.md §3) -----------------------
BG_DARK = (15, 23, 42)        # #0f172a  page background
SURFACE = (30, 41, 59)        # #1e293b  cards / chips
EMERALD = (16, 185, 129)      # #10b981  primary accent (trust / free)
EMERALD_DK = (5, 150, 105)    # #059669  accent dark
AMBER = (245, 158, 11)        # #f59e0b  CTA gold
TEXT = (241, 245, 249)        # #f1f5f9  primary text
MUTED = (148, 163, 184)       # #94a3b8  muted text
BORDER = (51, 65, 85)         # #334155  borders

SLOGAN = "Free Quotes On Anything!"
DOMAIN = "quotemyanything.com"
SUBLINE = "3 local pros compete  ·  60 seconds  ·  always free"

# Verticals that orbit the mark. (label, ring index) — ring 0 inner, 1 outer.
VERTICALS = [
    ("Roofing", 0), ("HVAC", 1), ("Plumbing", 0), ("Lawn Care", 1),
    ("Moving", 0), ("Solar", 1), ("Electrical", 0), ("Painting", 1),
    ("Cleaning", 0), ("Pest Control", 1),
]

FORMATS = {
    "vertical": (1080, 1920),
    "square": (1080, 1080),
    "landscape": (1920, 1080),
}


# --- Fonts --------------------------------------------------------------------
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/{}.ttf",
    "/usr/share/fonts/truetype/liberation/{}.ttf",
    "/Library/Fonts/{}.ttf",
    "/mnt/skills/examples/canvas-design/canvas-fonts/{}.ttf",
]
# (logical name -> filename stems to try, bold first where relevant)
_FONT_FILES = {
    "bold": ["DejaVuSans-Bold", "LiberationSans-Bold", "Geist-Bold", "Arial Bold"],
    "regular": ["DejaVuSans", "LiberationSans-Regular", "Geist-Regular", "Arial"],
}


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for stem in _FONT_FILES[kind]:
        for tmpl in FONT_CANDIDATES:
            path = Path(tmpl.format(stem))
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except OSError:
                    pass
        # also try bare filename via PIL's own search
        try:
            return ImageFont.truetype(f"{stem}.ttf", size)
        except OSError:
            continue
    return ImageFont.load_default()


# --- Easing -------------------------------------------------------------------
def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0 if x < edge0 else 1.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


# --- Config -------------------------------------------------------------------
@dataclass
class Config:
    fmt: str = "vertical"
    duration: float = 15.0
    fps: int = 30
    out: Path = ROOT / "build" / "qma_orbital_v2.mp4"
    no_audio: bool = False
    crf: int = 18
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self):
        self.width, self.height = FORMATS[self.fmt]

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.duration * self.fps)))


# --- Scene assets -------------------------------------------------------------
class Scene:
    """Pre-builds reusable layers and fonts for a given resolution."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        W, H = cfg.width, cfg.height
        self.W, self.H = W, H
        self.cx, self.cy = W // 2, int(H * 0.46)
        base = min(W, H)

        # Mark + orbit geometry scale with the short edge.
        self.mark_r = int(base * 0.13)
        self.ring_r = [int(base * 0.27), int(base * 0.40)]
        self.ring_speed = [0.16, -0.11]   # rad/sec, counter-rotating

        # Fonts
        self.f_slogan = load_font("bold", int(base * 0.072))
        self.f_chip = load_font("bold", int(base * 0.030))
        self.f_mark = load_font("bold", int(self.mark_r * 1.15))
        self.f_domain = load_font("bold", int(base * 0.050))
        self.f_sub = load_font("regular", int(base * 0.028))

        self.bg = self._build_background()
        self.logo = self._load_logo()

    # -- background: dark base + emerald glow + drifting star specks ----------
    def _build_background(self) -> Image.Image:
        W, H = self.W, self.H
        bg = Image.new("RGB", (W, H), BG_DARK)
        # vertical gradient toward near-black at the edges
        grad = Image.new("L", (1, H))
        for y in range(H):
            d = abs(y - self.cy) / H
            grad.putpixel((0, y), int(255 * (1 - min(0.55, d))))
        grad = grad.resize((W, H))
        dark = Image.new("RGB", (W, H), (7, 11, 22))
        bg = Image.composite(bg, dark, grad)

        # soft emerald glow behind where the mark sits
        glow = Image.new("L", (W, H), 0)
        gd = ImageDraw.Draw(glow)
        gr = int(min(W, H) * 0.34)
        gd.ellipse([self.cx - gr, self.cy - gr, self.cx + gr, self.cy + gr], fill=70)
        glow = glow.filter(ImageFilter.GaussianBlur(int(min(W, H) * 0.06)))
        emerald_layer = Image.new("RGB", (W, H), EMERALD_DK)
        bg = Image.composite(emerald_layer, bg, glow)
        return bg

    def _load_logo(self):
        for name in ("qma_logo_approved.png", "qma_logo_icon.jpg"):
            p = ASSETS / "logos" / name
            if p.exists():
                try:
                    return Image.open(p).convert("RGBA")
                except OSError:
                    pass
        return None  # fall back to drawn mark


# --- Drawing primitives -------------------------------------------------------
def rounded_pill(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_centered(draw, xy, text, font, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (r - l) / 2 - l, xy[1] - (b - t) / 2 - t), text, font=font, fill=fill)


def draw_brand_mark(img: Image.Image, scene: Scene, alpha: float, scale: float):
    """Central rounded-emerald-square 'Q' mark, pulsing/scaling in."""
    cx, cy = scene.cx, scene.cy
    r = int(scene.mark_r * scale)
    if r < 4:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = [cx - r, cy - r, cx + r, cy + r]
    a = int(255 * alpha)
    # outer soft ring
    ring = [cx - int(r * 1.18), cy - int(r * 1.18), cx + int(r * 1.18), cy + int(r * 1.18)]
    d.ellipse(ring, outline=EMERALD + (int(120 * alpha),), width=max(2, r // 18))
    # rounded square
    d.rounded_rectangle(box, radius=int(r * 0.34), fill=EMERALD + (a,))
    d.rounded_rectangle(box, radius=int(r * 0.34), outline=(255, 255, 255, int(60 * alpha)),
                        width=max(2, r // 26))
    # the "Q"
    f = load_font("bold", int(r * 1.15))
    draw_centered(d, (cx, cy - r * 0.04), "Q", f, (255, 255, 255, a))
    img.alpha_composite(layer)


def draw_chip(img: Image.Image, x: float, y: float, label: str, font, scale: float, alpha: float):
    if alpha <= 0.01 or scale <= 0.05:
        return
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((0, 0), label, font=font)
    tw, th = r - l, b - t
    pad_x = int(th * 0.95 * scale)
    pad_y = int(th * 0.55 * scale)
    w = tw * scale + 2 * pad_x
    h = th * scale + 2 * pad_y
    box = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
    a = int(255 * alpha)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.rounded_rectangle(box, radius=int(h / 2), fill=SURFACE + (int(235 * alpha),),
                         outline=EMERALD + (int(200 * alpha),), width=max(1, int(2 * scale)))
    # accent dot
    dot_r = max(2, int(th * 0.18 * scale))
    dl.ellipse([box[0] + pad_x * 0.7 - dot_r, y - dot_r, box[0] + pad_x * 0.7 + dot_r, y + dot_r],
               fill=EMERALD + (a,))
    if scale > 0.4:
        f = font
        dl.text((box[0] + pad_x + dot_r * 2.2, y - th * scale / 2 - t * scale),
                label, font=f, fill=TEXT + (a,))
    img.alpha_composite(layer)


def draw_text_block(img, scene: Scene, t_norm: float):
    """Slogan (top) + domain/subline (bottom) with timed reveals."""
    W, H = scene.W, scene.H
    base = min(W, H)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Slogan: fade + slide down in the first ~1.2s
    s_a = smoothstep(0.06, 0.28, t_norm)
    if s_a > 0:
        y = int(H * 0.13) - int((1 - ease_out_cubic(s_a)) * base * 0.05)
        # auto-fit the slogan to ~92% of the frame width
        full = SLOGAN
        max_w = W * 0.92
        font = scene.f_slogan
        l, t0, r, b = d.textbbox((0, 0), full, font=font)
        if (r - l) > max_w:
            shrunk = int(font.size * max_w / (r - l))
            font = load_font("bold", shrunk)
            l, t0, r, b = d.textbbox((0, 0), full, font=font)
        x = W / 2 - (r - l) / 2 - l
        # split colourize: "Free" emerald, rest white
        first = "Free "
        fl, ft, fr, fb = d.textbbox((0, 0), first, font=font)
        a = int(255 * s_a)
        d.text((x, y), first, font=font, fill=EMERALD + (a,))
        d.text((x + (fr - fl), y), full[len(first):], font=font, fill=TEXT + (a,))

    # Bottom block: domain + subline reveal after ~40%
    b_a = smoothstep(0.40, 0.62, t_norm)
    if b_a > 0:
        a = int(255 * b_a)
        yd = int(H * 0.80)
        # CTA pill behind the domain
        l, t0, r, b = d.textbbox((0, 0), DOMAIN, font=scene.f_domain)
        tw, th = r - l, b - t0
        pad = int(base * 0.03)
        box = [W / 2 - tw / 2 - pad, yd - th / 2 - pad * 0.7,
               W / 2 + tw / 2 + pad, yd + th / 2 + pad * 0.7]
        d.rounded_rectangle(box, radius=int((box[3] - box[1]) / 2),
                            fill=AMBER + (a,))
        draw_centered(d, (W / 2, yd), DOMAIN, scene.f_domain, BG_DARK + (a,))
        # subline
        draw_centered(d, (W / 2, yd + int(base * 0.085)), SUBLINE, scene.f_sub, MUTED + (a,))

    img.alpha_composite(layer)


# --- Frame renderer -----------------------------------------------------------
def render_frame(scene: Scene, cfg: Config, frame_idx: int) -> Image.Image:
    t = frame_idx / cfg.fps
    t_norm = frame_idx / max(1, cfg.total_frames - 1)
    img = scene.bg.copy().convert("RGBA")

    # Orbit rings (drawn faintly behind chips)
    intro = ease_out_cubic(smoothstep(0.0, 0.30, t_norm))
    outro = 1.0 - smoothstep(0.92, 1.0, t_norm)
    ring_alpha = intro * outro
    rl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rl)
    for rr in scene.ring_r:
        r = int(rr * (0.6 + 0.4 * intro))
        rd.ellipse([scene.cx - r, scene.cy - r, scene.cx + r, scene.cy + r],
                   outline=BORDER + (int(120 * ring_alpha),), width=2)
    img.alpha_composite(rl)

    # Orbiting service chips
    n_inner = sum(1 for _, ring in VERTICALS if ring == 0)
    n_outer = len(VERTICALS) - n_inner
    counts = [n_inner, n_outer]
    idx_in_ring = [0, 0]
    for label, ring in VERTICALS:
        count = counts[ring]
        slot = idx_in_ring[ring]
        idx_in_ring[ring] += 1
        # stagger appearance so chips fly in one-by-one
        appear = smoothstep(0.10 + slot * 0.04, 0.30 + slot * 0.04, t_norm)
        chip_scale = ease_out_cubic(appear) * (0.6 + 0.4 * intro)
        chip_alpha = appear * outro
        radius = scene.ring_r[ring] * (0.55 + 0.45 * ease_out_cubic(appear) * intro)
        base_ang = (2 * math.pi / count) * slot + (ring * math.pi / count)
        ang = base_ang + scene.ring_speed[ring] * t * 2 * math.pi * 0.16
        x = scene.cx + radius * math.cos(ang)
        y = scene.cy + radius * math.sin(ang) * 0.92  # slight vertical squash
        draw_chip(img, x, y, label, scene.f_chip, max(0.0, chip_scale), max(0.0, chip_alpha))

    # Central mark (pulse) — drawn over chips
    mark_in = ease_out_cubic(smoothstep(0.0, 0.18, t_norm))
    pulse = 1.0 + 0.03 * math.sin(t * 2 * math.pi * 0.6)
    draw_brand_mark(img, scene, alpha=mark_in * outro, scale=mark_in * pulse)

    # Text overlays
    draw_text_block(img, scene, t_norm)

    return img.convert("RGB")


# --- Audio selection ----------------------------------------------------------
def pick_jingle(duration: float) -> Path | None:
    short = ASSETS / "jingles" / "qma_jingle_6s.mp3"
    long = ASSETS / "jingles" / "qma_jingle_15s.mp3"
    if duration <= 8 and short.exists():
        return short
    if long.exists():
        return long
    return short if short.exists() else None


def find_ffmpeg() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# --- Encode -------------------------------------------------------------------
def encode(cfg: Config) -> Path:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit(
            "No ffmpeg backend found. Install the bundled static build with:\n"
            "    pip install imageio-ffmpeg\n"
        )

    cfg.out.parent.mkdir(parents=True, exist_ok=True)
    scene = Scene(cfg)
    jingle = None if cfg.no_audio else pick_jingle(cfg.duration)

    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{cfg.width}x{cfg.height}", "-r", str(cfg.fps),
        "-i", "-",
    ]
    if jingle:
        cmd += ["-stream_loop", "-1", "-i", str(jingle)]
    cmd += [
        "-map", "0:v",
    ]
    if jingle:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(cfg.crf), "-preset", "medium",
        "-movflags", "+faststart",
        "-shortest",
        str(cfg.out),
    ]

    total = cfg.total_frames
    print(f"[orbital v2] {cfg.fmt} {cfg.width}x{cfg.height} @ {cfg.fps}fps "
          f"· {cfg.duration:.0f}s · {total} frames")
    print(f"[orbital v2] audio: {jingle.name if jingle else 'none (silent)'}")

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for i in range(total):
            frame = render_frame(scene, cfg, i)
            proc.stdin.write(frame.tobytes())
            if i % cfg.fps == 0 or i == total - 1:
                pct = (i + 1) / total * 100
                print(f"\r[orbital v2] rendering {i + 1}/{total} ({pct:5.1f}%)",
                      end="", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode("utf-8", "ignore")
    code = proc.wait()
    print()
    if code != 0:
        sys.stderr.write(err[-2000:] + "\n")
        sys.exit(f"[orbital v2] ffmpeg failed (exit {code}).")
    return cfg.out


def parse_args(argv=None) -> Config:
    p = argparse.ArgumentParser(
        description="QuoteMyAnything orbital brand video generator (v2).")
    p.add_argument("--format", "-f", dest="fmt", default="vertical",
                   choices=list(FORMATS), help="aspect preset (default: vertical 9:16)")
    p.add_argument("--duration", "-d", type=float, default=15.0,
                   help="length in seconds (default: 15)")
    p.add_argument("--fps", type=int, default=30, help="frames per second (default: 30)")
    p.add_argument("--out", "-o", type=Path, default=Config.out,
                   help="output mp4 path")
    p.add_argument("--no-audio", action="store_true", help="render without the jingle")
    p.add_argument("--crf", type=int, default=18, help="x264 quality, lower=better (default 18)")
    a = p.parse_args(argv)
    return Config(fmt=a.fmt, duration=a.duration, fps=a.fps, out=a.out,
                  no_audio=a.no_audio, crf=a.crf)


def main(argv=None):
    cfg = parse_args(argv)
    out = encode(cfg)
    size_mb = out.stat().st_size / 1e6
    print(f"[orbital v2] done → {out}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
