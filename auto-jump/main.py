import json
import sys
import time
import random
import threading
from pathlib import Path
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Listener, Key, KeyCode, Controller as KeyboardController

mouse = MouseController()
teclado = KeyboardController()

macro_ativado = False
rankup_em_andamento = False
tecla_toggle = KeyCode(char='f')

OCR_INTERVAL = 5.0
OCR_CONFIG_FILE = Path(__file__).parent / "ocr_config.json"


def nivel_limite(rank: int) -> int:
    """Nível necessário para dar rankup: rank 8 → 900, rank 9 → 1000, etc."""
    return (rank + 1) * 100


def executar_rankup():
    global rankup_em_andamento
    rankup_em_andamento = True
    print("[RankUp] Pausando farm...")
    time.sleep(0.5)  # aguarda espaço ser solto pela thread do macro

    # Abre o chat e digita /rankup
    teclado.press(KeyCode(char='t'))
    teclado.release(KeyCode(char='t'))
    time.sleep(0.4)

    teclado.type('/rankup')
    time.sleep(0.2)

    teclado.press(Key.enter)
    teclado.release(Key.enter)

    print("[RankUp] Comando /rankup enviado. Aguardando 5s para o servidor processar...")
    time.sleep(5)

    rankup_em_andamento = False
    print("[RankUp] Retomando farm.")


def loop_ocr():
    """Thread que verifica nível/rank periodicamente e dispara rankup automaticamente."""
    try:
        from ocr import ler_nivel, ler_rank
    except ImportError:
        print("[OCR] Bibliotecas não encontradas. Rankup automático desativado.")
        print("      Instale: pip install pytesseract mss pillow")
        return

    while True:
        time.sleep(OCR_INTERVAL)

        if not macro_ativado or rankup_em_andamento:
            continue

        if not OCR_CONFIG_FILE.exists():
            continue

        try:
            cfg = json.loads(OCR_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            continue

        nivel_region = cfg.get("nivel_region")
        rank_region = cfg.get("rank_region")

        if not nivel_region or not rank_region:
            continue

        nivel = ler_nivel(nivel_region)
        rank = ler_rank(rank_region)

        if nivel is None or rank is None:
            print(f"[OCR] Falha na leitura (nivel={nivel}, rank={rank}). Tentando novamente...")
            continue

        limite = nivel_limite(rank)
        print(f"[OCR] Nível: {nivel} | Rank: {rank} | Limite para rankup: {limite}")

        if nivel >= limite and not rankup_em_andamento:
            print(f"[RankUp] Nível {nivel} atingiu o limite {limite} do Rank {rank}!")
            threading.Thread(target=executar_rankup, daemon=True).start()


def executar_macro():
    global macro_ativado, rankup_em_andamento
    espaco_pressionado = False

    while True:
        if macro_ativado and not rankup_em_andamento:
            if not espaco_pressionado:
                teclado.press(Key.space)
                espaco_pressionado = True
            mouse.click(Button.left)
            time.sleep(random.uniform(0.145, 0.190))
        else:
            if espaco_pressionado:
                teclado.release(Key.space)
                espaco_pressionado = False
            time.sleep(0.01)


def ao_pressionar(tecla):
    global macro_ativado
    if hasattr(tecla, 'char') and tecla.char == 'f':
        macro_ativado = not macro_ativado
        estado = "ATIVADO" if macro_ativado else "DESATIVADO"
        print(f"[Sistema] Macro {estado}")


def cmd_test_ocr():
    """Testa a leitura OCR sem iniciar o farm."""
    try:
        from ocr import ler_nivel, ler_rank
    except ImportError:
        print("ERRO: Instale as dependências: pip install pytesseract mss pillow")
        return

    if not OCR_CONFIG_FILE.exists():
        print("ERRO: OCR não calibrado. Execute: python calibrate_ocr.py")
        return

    cfg = json.loads(OCR_CONFIG_FILE.read_text(encoding="utf-8"))
    nivel_region = cfg.get("nivel_region")
    rank_region = cfg.get("rank_region")

    print("Testando OCR em 3 segundos. Troque para o Minecraft com o HUD visível...")
    time.sleep(3)

    print(f"\nRegião Nível: {nivel_region}")
    nivel = ler_nivel(nivel_region)
    print(f"  → Nível lido: {nivel}")

    print(f"\nRegião Rank: {rank_region}")
    rank = ler_rank(rank_region)
    print(f"  → Rank lido: {rank}")

    if nivel is not None and rank is not None:
        limite = nivel_limite(rank)
        print(f"\nLimite para rankup: {limite} (rank {rank} → rank {rank + 1})")
        print("OCR funcionando corretamente!")
    else:
        print("\nOCR falhou. Recalibre com: python calibrate_ocr.py")


if __name__ == "__main__":
    if "--test-ocr" in sys.argv:
        cmd_test_ocr()
        sys.exit(0)

    thread_macro = threading.Thread(target=executar_macro, daemon=True)
    thread_macro.start()

    thread_ocr = threading.Thread(target=loop_ocr, daemon=True)
    thread_ocr.start()

    print("=" * 50)
    print("  Auto-Jump + RankUp Automático")
    print("=" * 50)
    print("  F        → Ligar/desligar farm")
    print("  Ctrl+C   → Fechar o programa")
    print()

    if not OCR_CONFIG_FILE.exists():
        print("[AVISO] OCR não calibrado — rankup automático inativo.")
        print("        Execute: python calibrate_ocr.py")
    else:
        cfg = json.loads(OCR_CONFIG_FILE.read_text(encoding="utf-8"))
        if cfg.get("nivel_region") and cfg.get("rank_region"):
            print("[OCR] Calibração encontrada — rankup automático ATIVO.")
            print(f"      Verificação a cada {OCR_INTERVAL:.0f}s.")
        else:
            print("[AVISO] Calibração incompleta. Execute: python calibrate_ocr.py")
    print()

    escutador = Listener(on_press=ao_pressionar)
    escutador.daemon = True
    escutador.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[Sistema] Encerrando...")
        teclado.release(Key.space)
