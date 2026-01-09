from PIL import Image, ImageDraw, ImageFont
import os

# Создаем изображение 1200x630 (стандарт для превью)
img = Image.new('RGB', (1200, 630), color='#1a1a1a')
draw = ImageDraw.Draw(img)

# Градиент золотой (имитация)
for i in range(630):
    r = int(212 + (244-212) * i / 630)
    g = int(175 + (208-175) * i / 630)
    b = int(55 + (63-55) * i / 630)
    draw.rectangle([(0, i), (1200, i+1)], fill=(r, g, b))

# Темный оверлей
overlay = Image.new('RGBA', (1200, 630), (26, 26, 26, 200))
img.paste(overlay, (0, 0), overlay)

# Текст
try:
    # Пытаемся использовать системный шрифт
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    font_desc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
except:
    font_title = ImageFont.load_default()
    font_desc = ImageFont.load_default()

# Заголовок
title = "🎙️ Свободный Чат"
title_bbox = draw.textbbox((0, 0), title, font=font_title)
title_width = title_bbox[2] - title_bbox[0]
draw.text(((1200-title_width)/2, 150), title, fill='#d4af37', font=font_title)

# Описание
desc = "AI Собеседник с голосом"
desc_bbox = draw.textbbox((0, 0), desc, font=font_desc)
desc_width = desc_bbox[2] - desc_bbox[0]
draw.text(((1200-desc_width)/2, 280), desc, fill='#f0f0f0', font=font_desc)

# Теги
tags = "Python • Flask • AI • Голос"
tags_bbox = draw.textbbox((0, 0), tags, font=font_desc)
tags_width = tags_bbox[2] - tags_bbox[0]
draw.text(((1200-tags_width)/2, 380), tags, fill='#f4d03f', font=font_desc)

# Эмодзи внизу
emojis = "🤖 🎤 🔊 🎬"
emojis_bbox = draw.textbbox((0, 0), emojis, font=font_title)
emojis_width = emojis_bbox[2] - emojis_bbox[0]
draw.text(((1200-emojis_width)/2, 480), emojis, fill='white', font=font_title)

# Сохраняем
img.save('preview.jpg', 'JPEG', quality=95)
print("✓ preview.jpg создан!")
