"""
Safety monitor — detecta teleporte via OCR das coordenadas XYZ do F3.

Requer:
  pip install pytesseract
  Tesseract OCR instalado: https://github.com/UB-Mannheim/tesseract/wiki
"""

import concurrent.futures
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
    SAFETY_CONSECUTIVE_READS,
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


def _run_tesseract(screenshot: Image.Image) -> str:
    """Executa pytesseract em uma thread separada (sem timeout interno).

    O parâmetro timeout= do pytesseract usa subprocess.communicate(timeout=)
    que no Windows pode encerrar o processo silenciosamente ou retornar vazio.
    Usamos concurrent.futures com timeout externo, que é cross-platform.
    """
    return pytesseract.image_to_string(screenshot)


def _capture_xyz(sct: mss.mss = None) -> tuple[float, float, float] | None:
    """Faz OCR na região do F3 e retorna (x, y, z) ou None se falhar."""
    screenshot = grab_region(SAFETY_XYZ_REGION, sct)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_tesseract, screenshot)
            try:
                text = future.result(timeout=5)  # timeout externo, cross-platform
            except concurrent.futures.TimeoutError:
                return None
    finally:
        del screenshot  # libera memória da imagem imediatamente
    # O Tesseract frequentemente lê "XYZ" como "4W2", "4Y2" etc.
    # Estratégia: aceitar qualquer prefixo de palavra antes do ':' e capturar
    # apenas a parte INTEIRA de cada coordenada.
    # A parte decimal pode ter lixo (ex: "138.008e88") — descartamos tudo após
    # a vírgula/ponto. Isso é suficiente para detectar teleportes (dezenas de blocos).
    match = re.search(
        r'\w+:\s*'                      # prefixo tolerante (XYZ, 4W2, 4Y2…)
        r'([-]?\d+)[,.]?[\d\w]*'       # coord X — só o inteiro
        r'\s*/\s*'
        r'([-]?\d+)[,.]?[\d\w]*'       # coord Y — só o inteiro
        r'\s*/\s*'
        r'([-]?\d+)[,.]?[\d\w]*',      # coord Z — só o inteiro
        text,
    )
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

    Requer SAFETY_CONSECUTIVE_READS leituras consecutivas acima do threshold para
    acionar o alarme, evitando paradas por erros pontuais de OCR.

    Mantém um único contexto mss aberto durante toda a vida da thread para evitar
    vazamento de handles GDI em sessões longas (48h+).
    """
    print(f"[safety] Monitorando posição. XYZ inicial: {initial_xyz}")
    print(f"[safety] Threshold: {SAFETY_TELEPORT_THRESHOLD_BLOCKS} blocos | "
          f"Confirmações para acionar: {SAFETY_CONSECUTIVE_READS}x")

    suspicious_count = 0  # contador de leituras consecutivas suspeitas

    with mss.mss() as sct:
        while running.is_set():
            time.sleep(SAFETY_MONITOR_INTERVAL_S)
            if not running.is_set():
                break

            current = get_current_xyz(sct)
            if current is None:
                print("[safety] AVISO: OCR falhou nessa verificação, pulando.")
                suspicious_count = 0  # falha de OCR não é evidência de movimento
                continue

            dx = abs(current[0] - initial_xyz[0])
            dy = abs(current[1] - initial_xyz[1])
            dz = abs(current[2] - initial_xyz[2])
            dist = max(dx, dy, dz)

            if dist > SAFETY_TELEPORT_THRESHOLD_BLOCKS:
                suspicious_count += 1
                print(
                    f"[safety] Suspeito ({suspicious_count}/{SAFETY_CONSECUTIVE_READS}): "
                    f"Δ X={dx:.0f}  Y={dy:.0f}  Z={dz:.0f} blocos "
                    f"| pos atual: {current}"
                )
                if suspicious_count >= SAFETY_CONSECUTIVE_READS:
                    print(
                        f"\n[SAFETY] *** TELEPORTE CONFIRMADO! ***\n"
                        f"  Posição inicial: {initial_xyz}\n"
                        f"  Posição atual:   {current}\n"
                        f"  Δ X={dx:.0f}  Y={dy:.0f}  Z={dz:.0f} blocos\n"
                        f"  {suspicious_count} leituras consecutivas confirmaram o movimento.\n"
                        f"  BOT PAUSADO. Pressione F4 para retomar quando estiver seguro.\n"
                    )
                    running.clear()
                    safety_paused.set()
                    return
            else:
                if suspicious_count > 0:
                    print(f"[safety] Leitura voltou ao normal — resetando contador (era {suspicious_count}).")
                suspicious_count = 0  # leitura normal zera o contador

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
