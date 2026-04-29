"""
Spawner Bot — Minecraft Rankup Automation
Usage:
  python main.py             # Run the bot (F4 to start, F8 to stop)
  python main.py --calibrate # Calibration mode
"""

import sys
import threading
import time

import pyautogui

from calibration import load_calibration, run_calibration
from calibrate_ocr import run_calibrate_ocr
from config import SAFETY_MONITOR_ENABLED
from safety import get_current_xyz, start_safety_monitor
from actions import (
    buy_spawners,
    close_menu,
    open_spawner_menu,
    place_all_hotbar,
)

# Abort immediately if the mouse reaches corner (0, 0)
pyautogui.FAILSAFE = True

running = threading.Event()
safety_paused = threading.Event()  # Set quando pausado por detecção de teleporte
_safety_enabled = SAFETY_MONITOR_ENABLED  # Pode ser alterado pelo hotkey F7 em runtime


# ---------------------------------------------------------------------------
# Main automation cycle
# ---------------------------------------------------------------------------

def run_cycle(calibration: dict):
    """Execute one full buy-and-place cycle."""
    # PHASE 1 — Buy 9 packs (one per hotbar slot)
    print("[cycle] Phase 1: buying spawners...")
    open_spawner_menu()
    buy_spawners(calibration["spawner_slot"], running)
    close_menu()

    if not running.is_set():
        return

    # PHASE 2 — Merge all hotbar stacks into one and place on ground
    print("[cycle] Phase 2: merging and placing spawner...")
    place_all_hotbar()

    print("[cycle] Cycle complete.")


def automation_loop(calibration: dict):
    """Keep running cycles until F8 or safety monitor clears the 'running' event."""
    if _safety_enabled:
        if not start_safety_monitor(running, safety_paused):
            print("[bot] AVISO: Safety monitor inativo (F3 aberto no Minecraft?). Continuando sem proteção.")
    else:
        print("[bot] Safety monitor OCR desativado (F7 para ativar).")

    cycle = 0
    while running.is_set():
        cycle += 1
        print(f"\n=== Starting cycle #{cycle} ===")
        run_cycle(calibration)

    if safety_paused.is_set():
        print("\n[bot] Bot PAUSADO por segurança. Pressione F4 para retomar.")
    else:
        print("\n[bot] Automation stopped.")


# ---------------------------------------------------------------------------
# Hotkeys
# ---------------------------------------------------------------------------

def setup_hotkeys(calibration: dict):
    import keyboard

    def on_f4():
        if running.is_set():
            print("[hotkey] Bot is already running.")
            return

        if safety_paused.is_set():
            print("[hotkey] Retomando após pausa de segurança...")
            safety_paused.clear()
        else:
            print("[hotkey] F4 pressed — starting in 3 seconds. Switch to Minecraft!")
            time.sleep(3)

        running.set()
        t = threading.Thread(
            target=automation_loop,
            args=(calibration,),
            daemon=True,
        )
        t.start()

    def on_f8():
        if not running.is_set():
            print("[hotkey] Bot is not running.")
            return
        print("[hotkey] F8 pressed — stopping after current step...")
        running.clear()

    def on_f7():
        global _safety_enabled
        _safety_enabled = not _safety_enabled
        label = "ATIVADO" if _safety_enabled else "DESATIVADO"
        print(f"[hotkey] Safety Monitor OCR {label} (surte efeito na próxima vez que o bot iniciar)")

    keyboard.add_hotkey("f4", on_f4)
    keyboard.add_hotkey("f7", on_f7)
    keyboard.add_hotkey("f8", on_f8)

    print("Hotkeys registered:")
    print("  F4 — Start automation")
    print(f"  F7 — Ativar/desativar Safety Monitor OCR (atual: {'ATIVADO' if _safety_enabled else 'DESATIVADO'})")
    print("  F8 — Stop automation")
    print("  Move mouse to top-left corner (0,0) — Emergency abort\n")
    print("Make sure Minecraft is in focus before pressing F4.\n")

    keyboard.wait()  # Block main thread; hotkeys keep running in background


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if "--calibrate" in sys.argv:
        run_calibration()
        return

    if "--calibrate-ocr" in sys.argv:
        run_calibrate_ocr()
        return

    if "--test-ocr" in sys.argv:
        import pytesseract
        from config import SAFETY_XYZ_REGION
        from safety import grab_region, _run_tesseract
        print("Testando OCR da região XYZ.")
        print(f"Região configurada: {SAFETY_XYZ_REGION}")
        print("Troque para o Minecraft com F3 aberto. Capturando em 5 segundos...")
        time.sleep(5)
        # Captura e salva para inspeção visual
        screenshot = grab_region(SAFETY_XYZ_REGION)
        screenshot.save("test_ocr_region.png")
        # Mostra texto bruto usando o mesmo helper de produção (sem timeout interno do pytesseract)
        raw_text = _run_tesseract(screenshot)
        print(f"Texto OCR bruto:\n  {repr(raw_text.strip())}")
        # Usa exatamente o mesmo caminho de código que a produção
        result = get_current_xyz()
        if result:
            print(f"\nXYZ lido com sucesso: {result}")
        else:
            print("\nFalha ao parsear XYZ. Verifique test_ocr_region.png para ver o que foi capturado.")
            print("Ajuste SAFETY_XYZ_REGION em config.py conforme necessário.")
        return

    calibration = load_calibration()
    if calibration is None:
        print("Calibration not found. Run: python main.py --calibrate")
        sys.exit(1)

    print("=== SPAWNER BOT ===")
    print(f"Spawner slot: {calibration['spawner_slot']}")

    setup_hotkeys(calibration)


if __name__ == "__main__":
    main()
