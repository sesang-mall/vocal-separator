"""launcher/launcher_icon.ico 생성 스크립트 (python launcher/make_launcher_icon.py)"""
from pathlib import Path
from PIL import Image, ImageDraw

S = 1024
OUT = Path(__file__).parent

bg = Image.new('RGBA', (S, S))
px = bg.load()
top, bot = (24, 52, 84), (20, 96, 120)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
    for x in range(S):
        px[x, y] = c
mask = Image.new('L', (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=210, fill=255)
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
img.paste(bg, (0, 0), mask)

# 3x3 앱 타일 그리드 (런처)
d = ImageDraw.Draw(img)
colors = [(255, 99, 132), (255, 190, 70), (70, 210, 160),
          (80, 170, 255), (180, 130, 255), (255, 140, 90),
          (70, 210, 160), (255, 99, 132), (255, 255, 255)]
tile, gap = 190, 52
total = 3 * tile + 2 * gap
x0 = (S - total) // 2
for i, col in enumerate(colors):
    r, c = divmod(i, 3)
    x, y = x0 + c * (tile + gap), x0 + r * (tile + gap)
    d.rounded_rectangle((x, y, x + tile, y + tile), radius=52, fill=col)

img.resize((256, 256), Image.LANCZOS).save(
    OUT / 'launcher_icon.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
img.resize((512, 512), Image.LANCZOS).save(OUT / 'launcher_icon.png')
