# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
import os
import glob

# Find the screenshot
pattern = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots", "Capture d'*104741*.png")
files = glob.glob(pattern)
if not files:
    # Try listing the directory
    screenshot_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
    print(f"Searching in: {screenshot_dir}")
    for f in os.listdir(screenshot_dir):
        if "104741" in f:
            files = [os.path.join(screenshot_dir, f)]
            break

if not files:
    print("File not found! Listing screenshots dir:")
    for f in os.listdir(screenshot_dir):
        print(f"  {f}")
    exit(1)

filepath = files[0]
print(f"Analyzing: {filepath}")

img = Image.open(filepath)
print(f"Size: {img.size}, Mode: {img.mode}")

arr = np.array(img)
h, w = arr.shape[0], arr.shape[1]
print(f"Dimensions: {w}x{h}")
print(f"Mean RGB: R={arr[:,:,0].mean():.0f}, G={arr[:,:,1].mean():.0f}, B={arr[:,:,2].mean():.0f}")

# White pixel ratio
white = np.all(arr[:,:,:3] > 240, axis=2)
print(f"White pixels: {white.sum()/white.size*100:.1f}%")

# Color analysis
r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
green_px = ((g > 80) & (g > r) & (g > b) & (r < 150)).sum()
blue_px = ((b > 80) & (b > r) & (b > g) & (r < 150)).sum()
orange_px = ((r > 180) & (g > 100) & (g < 200) & (b < 100)).sum()
red_px = ((r > 150) & (g < 100) & (b < 100)).sum()
purple_px = ((r > 100) & (b > 100) & (g < 80)).sum()
cyan_px = ((b > 100) & (g > 100) & (r < 100)).sum()
pink_px = ((r > 180) & (g < 120) & (b > 120)).sum()

total = white.size
print(f"Green pixels: {green_px} ({green_px/total*100:.1f}%)")
print(f"Blue pixels: {blue_px} ({blue_px/total*100:.1f}%)")
print(f"Orange pixels: {orange_px} ({orange_px/total*100:.1f}%)")
print(f"Red pixels: {red_px} ({red_px/total*100:.1f}%)")
print(f"Purple pixels: {purple_px} ({purple_px/total*100:.1f}%)")
print(f"Cyan pixels: {cyan_px} ({cyan_px/total*100:.1f}%)")
print(f"Pink pixels: {pink_px} ({pink_px/total*100:.1f}%)")

# Beige/tile-like colors (CartoDB voyager tiles)
beige = ((r > 200) & (r < 250) & (g > 195) & (g < 245) & (b > 180) & (b < 235)).sum()
print(f"Beige/tile-like pixels: {beige} ({beige/total*100:.1f}%)")

# Split into regions
top = arr[:h//3, :, :3]
mid = arr[h//3:2*h//3, :, :3]
bot = arr[2*h//3:, :, :3]
print(f"\nTop region mean RGB: [{top[:,:,0].mean():.1f}, {top[:,:,1].mean():.1f}, {top[:,:,2].mean():.1f}]")
print(f"Mid region mean RGB: [{mid[:,:,0].mean():.1f}, {mid[:,:,1].mean():.1f}, {mid[:,:,2].mean():.1f}]")
print(f"Bot region mean RGB: [{bot[:,:,0].mean():.1f}, {bot[:,:,1].mean():.1f}, {bot[:,:,2].mean():.1f}]")

# Check for map content in middle area
mid_non_white = ~np.all(mid > 240, axis=2)
print(f"Mid non-white pixels: {mid_non_white.sum()/mid_non_white.size*100:.1f}%")

# Detect polygon outlines (colored borders)
# Green borders (Y4)
green_border = ((g > 60) & (g < 130) & (r < 50) & (b < 80)).sum()
# Blue borders (4e Pont)
blue_border = ((b > 100) & (b < 180) & (r < 50) & (g < 80)).sum()
print(f"\nGreen border pixels (Y4): {green_border}")
print(f"Blue border pixels (4e Pont): {blue_border}")

unique_colors = len(np.unique(arr[:,:,:3].reshape(-1, 3), axis=0))
print(f"\nUnique colors: {unique_colors}")

# Check if map tiles are loading (look for varied non-UI colors in center)
center = arr[h//4:3*h//4, w//4:3*w//4, :3]
center_non_white = ~np.all(center > 240, axis=2)
center_variety = len(np.unique(center.reshape(-1, 3), axis=0))
print(f"\nCenter region: {center_non_white.sum()/center_non_white.size*100:.1f}% non-white, {center_variety} unique colors")
