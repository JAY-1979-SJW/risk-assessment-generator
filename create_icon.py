# -*- coding: utf-8 -*-
"""
아이콘 생성 스크립트
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # 256x256 크기의 이미지 생성
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 배경 - 파란색 원
    margin = 10
    draw.ellipse([margin, margin, size-margin, size-margin],
                 fill='#2c5282', outline='#1a365d', width=3)

    # 방패 모양 (안전 상징)
    shield_points = [
        (size//2, 45),      # 상단 중앙
        (size-55, 70),      # 우측 상단
        (size-55, 150),     # 우측 중간
        (size//2, 210),     # 하단 중앙
        (55, 150),          # 좌측 중간
        (55, 70),           # 좌측 상단
    ]
    draw.polygon(shield_points, fill='#48bb78', outline='white', width=3)

    # 체크마크 (평가 완료 상징)
    check_points = [
        (85, 130),
        (115, 165),
        (175, 95),
    ]
    draw.line(check_points, fill='white', width=12)

    # ICO 파일로 저장 (여러 크기 포함)
    icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')

    # 여러 크기의 이미지 생성
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    for s in sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        images.append(resized)

    # ICO 파일 저장
    img.save(icon_path, format='ICO', sizes=[(s[0], s[1]) for s in sizes])
    print(f"아이콘 생성 완료: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()
