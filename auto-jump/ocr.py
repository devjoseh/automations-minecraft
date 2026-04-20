"""
Leitura OCR do HUD do Minecraft — Nível e Rank.

Requer:
  pip install pytesseract mss pillow
  Tesseract OCR instalado: https://github.com/UB-Mannheim/tesseract/wiki
"""

import re
import time

import mss
import pytesseract
from PIL import Image, ImageEnhance

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

_sct = None


def _get_sct() -> mss.mss:
    global _sct
    if _sct is None:
        _sct = mss.mss()
    return _sct


def _grab(region: list | tuple) -> Image.Image:
    left, top, w, h = region
    raw = _get_sct().grab({"left": left, "top": top, "width": w, "height": h})
    return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def _preprocess(img: Image.Image) -> Image.Image:
    """Escala 3x, grayscale e aumenta contraste para melhorar OCR em texto de jogo."""
    img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(3.0)
    return img


def _ocr_numero(region: list | tuple) -> int | None:
    """Captura região, faz OCR e retorna o primeiro número inteiro encontrado."""
    try:
        img = _preprocess(_grab(region))
        text = pytesseract.image_to_string(img, config="--psm 7", timeout=2)
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else None
    except Exception:
        return None


def ler_nivel(region: list | tuple) -> int | None:
    """Tenta ler o nível até 3 vezes (OCR pode falhar ocasionalmente)."""
    for _ in range(3):
        result = _ocr_numero(region)
        if result is not None:
            return result
        time.sleep(0.2)
    return None


def ler_rank(region: list | tuple) -> int | None:
    """Tenta ler o rank até 3 vezes."""
    for _ in range(3):
        result = _ocr_numero(region)
        if result is not None:
            return result
        time.sleep(0.2)
    return None
