"""
Safety monitor — detecta teleporte via OCR das coordenadas XYZ do F3.

Requer:
  pip install pytesseract
  Tesseract OCR instalado: https://github.com/UB-Mannheim/tesseract/wiki
"""

import math
import re
import threading
import time

import mss
import mss.tools
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from config import (
    SAFETY_MONITOR_INTERVAL_S,
    SAFETY_TELEPORT_THRESHOLD_BLOCKS,
    SAFETY_XYZ_REGION,
)

def grab_region(region: tuple[int, int, int, int], sct: mss.mss = None) -> Image.Image:
    """Captura uma região da tela usando mss (funciona com fullscreen/jogos).

    Aceita um contexto mss já aberto para evitar criação/destruição repetida de
    handles GDI a cada captura (importante para sessões longas).
    """
    left, top, width, height = region
    monitor = {"left": left, "top": top, "width": width, "height": height}
    if sct is not None:
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    with mss.mss() as _sct:
        raw = _sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def _capture_xyz(sct: mss.mss = None) -> tuple[float, float, float] | None:
    """Faz OCR na região do F3 e retorna (x, y, z) ou None se falhar."""
    screenshot = grab_region(SAFETY_XYZ_REGION, sct)
    try:
        # Timeout evita que tesseract.exe fique pendurado e acumule processos zumbis
        text = pytesseract.image_to_string(
            screenshot,
            timeout=2,
        )
    except RuntimeError:
        # pytesseract lança RuntimeError quando o timeout é atingido
        return None
    finally:
        del screenshot  # libera memória da imagem imediatamente
    match = re.search(r'[A-Z]YZ:\s*([-\d.]+)\s*/\s*([-\d.]+)\s*/\s*([-\d.]+)', text)
    if match:
        return float(match.group(1)), float(match.group(2)), float(match.group(3))
    return None


def get_current_xyz(sct: mss.mss = None) -> tuple[float, float, float] | None:
    """Tenta capturar XYZ até 3 vezes (OCR pode falhar ocasionalmente)."""
    for _ in range(3):
        result = _capture_xyz(sct)
        if result is not None:
            return result
        time.sleep(0.3)
    return None


def _monitor_loop(
    running: threading.Event,
    safety_paused: threading.Event,
    initial_xyz: tuple[float, float, float],
):
    """Thread de monitoramento. Para quando running é limpo ou teleporte é detectado.

    Mantém um único contexto mss aberto durante toda a vida da thread para evitar
    vazamento de handles GDI em sessões longas (48h+).
    """
    print(f"[safety] Monitorando posição. XYZ inicial: {initial_xyz}")

    with mss.mss() as sct:
        while running.is_set():
            time.sleep(SAFETY_MONITOR_INTERVAL_S)
            if not running.is_set():
                break

            current = get_current_xyz(sct)
            if current is None:
                print("[safety] AVISO: OCR falhou nessa verificação, pulando.")
                continue

            dx = abs(current[0] - initial_xyz[0])
            dy = abs(current[1] - initial_xyz[1])
            dz = abs(current[2] - initial_xyz[2])

            if max(dx, dy, dz) > SAFETY_TELEPORT_THRESHOLD_BLOCKS:
                print(
                    f"\n[SAFETY] *** MOVIMENTO DETECTADO! ***\n"
                    f"  Posição inicial: {initial_xyz}\n"
                    f"  Posição atual:   {current}\n"
                    f"  Δ X={dx:.1f}  Y={dy:.1f}  Z={dz:.1f} blocos\n"
                    f"  BOT PAUSADO. Pressione F4 para retomar quando estiver seguro.\n"
                )
                running.clear()
                safety_paused.set()
                return

    print("[safety] Monitor encerrado.")


def start_safety_monitor(
    running: threading.Event,
    safety_paused: threading.Event,
) -> bool:
    """
    Captura XYZ inicial e inicia thread de monitoramento em background.
    Retorna False se não conseguir ler as coordenadas (F3 não aberto ou região errada).
    """
    print("[safety] Capturando posição inicial...")
    initial_xyz = get_current_xyz()
    if initial_xyz is None:
        print(
            "[safety] ERRO: Não foi possível ler as coordenadas XYZ.\n"
            "  Certifique-se que o F3 está aberto e ajuste SAFETY_XYZ_REGION em config.py.\n"
            "  Use: python main.py --test-ocr  para debugar a região."
        )
        return False

    t = threading.Thread(
        target=_monitor_loop,
        args=(running, safety_paused, initial_xyz),
        daemon=True,
    )
    t.start()
    return True
