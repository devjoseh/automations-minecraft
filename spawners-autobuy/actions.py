import random
import time
import pyautogui
from pynput.keyboard import Controller as KeyboardController, Key

# Cached screen center — usado para mover o mouse para o mundo antes de right-click
_SCREEN_W, _SCREEN_H = pyautogui.size()
_CENTER_X = _SCREEN_W // 2
_CENTER_Y = _SCREEN_H // 2

from config import (
    ACTION_DELAY_MS,
    HOTBAR_SLOTS,
    INVENTORY_CLICK_DELAY_MS,
    INVENTORY_MOVE_DELAY_MS,
    KEY_CLOSE_MENU,
    KEY_INVENTORY,
    KEY_OPEN_CHAT,
    KEY_SPAWNERS_CMD,
    MOUSE_MOVE_DELAY_MS,
    PLACE_PASS1_ENABLED,
    PLACE_SLOT_DELAY_MS,
    Q_PRESS_INTERVAL_MS,
    TOTAL_Q_PRESSES,
)

_pass1_enabled: bool = PLACE_PASS1_ENABLED


def toggle_pass1() -> bool:
    """Liga/desliga o Pass 1 (right-click sem shift). Retorna o novo estado."""
    global _pass1_enabled
    _pass1_enabled = not _pass1_enabled
    return _pass1_enabled

_pynput_kb = KeyboardController()


def _sleep_ms(ms: float):
    time.sleep(ms / 1000)


def _jitter_ms(base_ms: float, pct: float = 0.30) -> None:
    """Sleep for base_ms ± pct variation to simulate human timing."""
    delta = base_ms * pct
    time.sleep(random.uniform(base_ms - delta, base_ms + delta) / 1000)


def _jitter_pos(x: int, y: int, radius: int = 2) -> tuple[int, int]:
    """Return (x, y) with a small random pixel offset to avoid pixel-perfect clicks."""
    return (
        x + random.randint(-radius, radius),
        y + random.randint(-radius, radius),
    )


# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------

def open_spawner_menu():
    """Type /spawners in chat to open the spawner purchase panel."""
    _pynput_kb.press(KEY_OPEN_CHAT)
    _pynput_kb.release(KEY_OPEN_CHAT)
    _jitter_ms(ACTION_DELAY_MS)

    for char in KEY_SPAWNERS_CMD:
        _pynput_kb.press(char)
        _pynput_kb.release(char)
    _jitter_ms(50)

    _pynput_kb.press(Key.enter)
    _pynput_kb.release(Key.enter)
    _jitter_ms(ACTION_DELAY_MS)


def close_menu():
    """Close any open GUI (inventory, shop, etc.)."""
    _pynput_kb.press(KEY_CLOSE_MENU)
    _pynput_kb.release(KEY_CLOSE_MENU)
    _jitter_ms(ACTION_DELAY_MS)


def open_inventory():
    """Open the player inventory."""
    _pynput_kb.press(KEY_INVENTORY)
    _pynput_kb.release(KEY_INVENTORY)
    _jitter_ms(ACTION_DELAY_MS)


# ---------------------------------------------------------------------------
# Buying
# ---------------------------------------------------------------------------

def buy_spawners(spawner_pos: tuple, running=None):
    """
    Move mouse to spawner_pos and press Q TOTAL_Q_PRESSES times.
    Uses perf_counter to compensate timing drift.
    'running' is an optional threading.Event; if cleared, stop early.

    Ao terminar, move o mouse para o centro da tela ENQUANTO o shop ainda está
    aberto (cursor livre), evitando que o Minecraft interprete o delta como
    rotação de câmera ao recapturar o cursor no close_menu() seguinte.
    """
    pyautogui.moveTo(*_jitter_pos(*spawner_pos))
    _jitter_ms(MOUSE_MOVE_DELAY_MS)

    base_interval = Q_PRESS_INTERVAL_MS / 1000
    jitter_range = base_interval * 0.20
    for i in range(TOTAL_Q_PRESSES):
        if running is not None and not running.is_set():
            break
        interval = base_interval + random.uniform(-jitter_range, jitter_range)
        t_start = time.perf_counter()
        _pynput_kb.press('q')
        _pynput_kb.release('q')
        elapsed = time.perf_counter() - t_start
        remaining = interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    # Move para o centro enquanto o shop ainda está aberto (cursor liberado pelo GUI).
    # Quando close_menu() fechar o shop, o Minecraft vai recapturar o cursor já
    # centrado → nenhum delta → nenhuma rotação de câmera.
    pyautogui.moveTo(_CENTER_X, _CENTER_Y)
    _jitter_ms(MOUSE_MOVE_DELAY_MS)


# ---------------------------------------------------------------------------
# Placing spawners from hotbar
# ---------------------------------------------------------------------------

_HOTBAR_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']


def place_all_hotbar():
    """
    Place spawners from every hotbar slot (1–9) onto the ground.

    Pass 1 — right-click only (sem shift): descarta itens como corante azul que
    não respondem ao shift+direito (chaves e poções também são consumidas aqui).

    Pass 2 — shift segurado: passa slot 1→9 com shift+direito para descartar
    os spawners restantes em pilha.

    IMPORTANTE: NÃO faz pyautogui.moveTo aqui. O mouse já é centrado dentro
    dos GUIs anteriores (buy_spawners / refill_hotbar_from_row) antes de fechar,
    para que o Minecraft não interprete nenhum delta como rotação de câmera.
    """
    # Pass 1: right-click simples em cada slot (descartar itens que não respondem ao shift+direito)
    if _pass1_enabled:
        for slot in range(1, HOTBAR_SLOTS + 1):
            _pynput_kb.press(_HOTBAR_KEYS[slot - 1])
            _pynput_kb.release(_HOTBAR_KEYS[slot - 1])
            _jitter_ms(PLACE_SLOT_DELAY_MS)
            pyautogui.rightClick()
            _jitter_ms(PLACE_SLOT_DELAY_MS)

        # Volta para slot 1
        _pynput_kb.press(_HOTBAR_KEYS[0])
        _pynput_kb.release(_HOTBAR_KEYS[0])
        _jitter_ms(PLACE_SLOT_DELAY_MS)

    # Pass 2: shift segurado, right-click em cada slot
    pyautogui.keyDown('shift')
    try:
        for slot in range(1, HOTBAR_SLOTS + 1):
            _pynput_kb.press(_HOTBAR_KEYS[slot - 1])
            _pynput_kb.release(_HOTBAR_KEYS[slot - 1])
            _jitter_ms(PLACE_SLOT_DELAY_MS)
            pyautogui.rightClick()
            _jitter_ms(PLACE_SLOT_DELAY_MS)
    finally:
        pyautogui.keyUp('shift')
    _jitter_ms(ACTION_DELAY_MS)


# ---------------------------------------------------------------------------
# Refilling hotbar from inventory
# ---------------------------------------------------------------------------

def refill_hotbar_from_row(row_index: int, inventory_slots: list):
    """
    Shift+click every slot in 'row_index' of the inventory to move items
    to the hotbar. Holds shift once for all 9 slots.
    row_index: 0 = top row, 1 = middle, 2 = bottom

    Ao terminar, move o mouse para o centro da tela ENQUANTO o inventário ainda
    está aberto (cursor livre). Quando close_menu() fechar o inventário, o
    Minecraft recaptura o cursor já centrado → nenhum delta → câmera estável.
    """
    pyautogui.keyDown('shift')
    try:
        for col in range(9):
            x, y = _jitter_pos(*inventory_slots[row_index][col])
            pyautogui.moveTo(x, y)
            _jitter_ms(INVENTORY_MOVE_DELAY_MS)
            pyautogui.click(x, y)
            _jitter_ms(INVENTORY_CLICK_DELAY_MS)
    finally:
        pyautogui.keyUp('shift')

    # Centraliza o mouse ANTES de fechar o inventário (cursor ainda livre).
    # Evita que o Minecraft gire a câmera ao recapturar o cursor.
    pyautogui.moveTo(_CENTER_X, _CENTER_Y)
    _jitter_ms(MOUSE_MOVE_DELAY_MS)
