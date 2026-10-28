"""assets/icon.ico 생성 스크립트 (python assets/make_icon.py)"""
from pathlib import Path
from PIL import Image, ImageDraw

S = 1024
OUT = Path(__file__).parent

# 배경: 어두운 남색 -> 보라 세로 그라데이션, 둥근 사각형
bg = Image.new('RGBA', (S, S))
px = bg.load()
top, bot = (30, 34, 70), (64, 40, 110)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
    for x in range(S):
        px[x, y] = c
mask = Image.new('L', (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=210, fill=255)
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
img.paste(bg, (0, 0), mask)

# 4개 스템(보컬/드럼/베이스/기타)을 상징하는 컬러 막대 파형
d = ImageDraw.Draw(img)
colors = [(255, 99, 132), (255, 190, 70), (70, 210, 160), (80, 170, 255)]
heights = [0.38, 0.62, 0.84, 0.56, 0.72, 0.46, 0.30]
n = len(heights)
bw, gap = 78, 40
total = n * bw + (n - 1) * gap
x0 = (S - total) // 2
cy = S // 2
for i, h in enumerate(heights):
    hh = int(S * 0.62 * h)
    x = x0 + i * (bw + gap)
    d.rounded_rectangle((x, cy - hh // 2, x + bw, cy + hh // 2),
                        radius=bw // 2, fill=colors[i % 4])

img.resize((256, 256), Image.LANCZOS).save(
    OUT / 'icon.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
img.resize((512, 512), Image.LANCZOS).save(OUT / 'icon.png')
