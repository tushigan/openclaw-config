#!/usr/bin/env python3
from PIL import Image, ImageDraw
from pathlib import Path
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--image', required=True)
ap.add_argument('--output-mask', required=True)
ap.add_argument('--output-boxes', required=True)
ap.add_argument('--min-pixels', type=int, default=200)
args = ap.parse_args()

img = Image.open(args.image).convert('RGB')
w,h = img.size
pix = img.load()
visited = [[False]*h for _ in range(w)]

# red-box stroke detector
# detect vivid red pixels
reds = set()
for x in range(w):
    for y in range(h):
        r,g,b = pix[x,y]
        if r > 160 and g < 120 and b < 120 and r > g*1.3 and r > b*1.3:
            reds.add((x,y))

# BFS connected comps
from collections import deque
boxes=[]
seen=set()
for p in list(reds):
    if p in seen: continue
    q=deque([p]); seen.add(p)
    pts=[]
    while q:
        x,y=q.popleft(); pts.append((x,y))
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if (nx,ny) in reds and (nx,ny) not in seen:
                seen.add((nx,ny)); q.append((nx,ny))
    if len(pts) >= args.min_pixels:
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        boxes.append((min(xs), min(ys), max(xs), max(ys), len(pts)))

# merge nearby/overlapping boxes
merged=[]
for box in sorted(boxes, key=lambda b:b[4], reverse=True):
    x1,y1,x2,y2,n = box
    added=False
    for i,(a1,b1,a2,b2,nn) in enumerate(merged):
        if not (x2 < a1-10 or a2 < x1-10 or y2 < b1-10 or b2 < y1-10):
            merged[i]=(min(a1,x1), min(b1,y1), max(a2,x2), max(b2,y2), nn+n)
            added=True
            break
    if not added:
        merged.append(box)

# expand boxes slightly to cover full interior area
expanded=[]
for x1,y1,x2,y2,n in merged:
    pad=8
    expanded.append((max(0,x1-pad), max(0,y1-pad), min(w-1,x2+pad), min(h-1,y2+pad)))

# Create mask: white editable only inside boxes, black preserved elsewhere
mask = Image.new('RGBA', (w,h), (0,0,0,255))
draw = ImageDraw.Draw(mask)
for x1,y1,x2,y2 in expanded:
    draw.rectangle([x1,y1,x2,y2], fill=(255,255,255,255))

Path(args.output_mask).parent.mkdir(parents=True, exist_ok=True)
mask.save(args.output_mask)
Path(args.output_boxes).write_text('\n'.join([','.join(map(str,b)) for b in expanded]), encoding='utf-8')
print('boxes', expanded)
print('mask', args.output_mask)
