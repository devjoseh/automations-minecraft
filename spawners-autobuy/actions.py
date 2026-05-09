import random
import time
import pyautogui
from pynput.keyboard import Controller as KeyboardController, Key

# Cached screen center — usado para todo posicionamento de camera/mouse
_SCREEN_W, _SCREEN_H = pyautogui.size()
_CENTER_X = _SCREEN_W // 2
_CENTER_Y = _SCREEN_H // 2

from config import (
    ACTION_DELAY_MS,
    CAMERA_STABILIZE_MS,
    INVENTORY_CLICK_DELAY_MS,
    INVENTORY_MOVE_DELAY_MS,
    KEY_CLOSE_MENU,
    KEY_INVENTORY,
    KEY_OPEN_CHAT,
    KEY_SPAWNERS_CMD,
    MOUSE_MOVE_DELAY_MS,
    PLACE_SLOT_DELAY_MS,
    POSITION_RECHECK_INTERVAL,
    Q_PRESS_INTERVAL_MS,
    SHOP_OPEN_DELAY_MS,
    TOTAL_Q_PRESSES,
)

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


def _center_mouse():
    """Move mouse to exact screen center and let it stabilize.

    ONLY called inside buy_spawners() while the shop GUI is still open.
    In a GUI, the cursor is free — moveTo just repositions it without
    affecting the camera. When close_menu() then presses E, Minecraft
    recaptures the cursor at center → zero delta → zero camera rotation.

    NEVER call this when no GUI is open — in the game world, moveTo
    generates mouse events that Minecraft interprets as camera rotation.
    """
    pyautogui.moveTo(_CENTER_X, _CENTER_Y)
    time.sleep(CAMERA_STABILIZE_MS / 1000)


# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------

def open_spawner_menu():
    """Type /spawners in chat to open the spawner purchase panel.

    When the shop opens, Minecraft centers the cursor automatically.
    We never move the mouse here — the only mouse movement in the entire
    cycle happens inside buy_spawners() while the GUI is open.
    """
    _pynput_kb.press(KEY_OPEN_CHAT)
    _pynput_kb.release(KEY_OPEN_CHAT)
    _jitter_ms(ACTION_DELAY_MS)

    for char in KEY_SPAWNERS_CMD:
        _pynput_kb.press(char)
        _pynput_kb.release(char)
    _jitter_ms(50)

    _pynput_kb.press(Key.enter)
    _pynput_kb.release(Key.enter)

    # Wait for shop GUI to fully open — server may be laggy
    _jitter_ms(SHOP_OPEN_DELAY_MS)


def close_menu():
    """Close any open GUI (inventory, shop, etc.).

    Mouse is already centered by buy_spawners() while the GUI was open.
    Just press E — when Minecraft recaptures the cursor at center,
    delta is zero → zero camera rotation.
    """
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

def _guard_position(spawner_pos: tuple, max_retries: int = 5) -> bool:
    """Ensure cursor is at spawner_pos before starting Q presses.

    Returns True if cursor is confirmed at position, False after exhausting
    retries (should not happen in practice — logs a warning).
    """
    for attempt in range(max_retries):
        cur_x, cur_y = pyautogui.position()
        if abs(cur_x - spawner_pos[0]) <= 20 and abs(cur_y - spawner_pos[1]) <= 20:
            return True
        print(f"[buy] Cursor em ({cur_x},{cur_y}), esperado ({spawner_pos[0]},{spawner_pos[1]}) — "
              f"tentativa {attempt+1}/{max_retries}. Reposicionando...")
        _jitter_ms(300)
        pyautogui.moveTo(*_jitter_pos(*spawner_pos))
        _jitter_ms(MOUSE_MOVE_DELAY_MS)
    print("[buy] AVISO: não foi possível confirmar posição do cursor após retries.")
    return False


def buy_spawners(spawner_pos: tuple, running=None):
    """Move mouse to spawner_pos and press Q TOTAL_Q_PRESSES times.

    Uses perf_counter to compensate timing drift.
    'running' is an optional threading.Event; if cleared, stop early.

    Robustness:
    - Retry loop (up to 5 attempts) to ensure cursor is on the spawner slot
      before any Q press. This catches late shop openings where Minecraft
      resets the cursor to center AFTER our initial moveTo.
    - Periodic re-verification every POSITION_RECHECK_INTERVAL Q presses.
      If the shop GUI refreshes and recenters the cursor mid-loop, we catch
      it before Q presses hit the wrong item.
    - After buying, moves mouse to exact screen center while the shop is still
      open. This guarantees that when close_menu() presses E, Minecraft
      recaptures the cursor at center → zero delta → zero camera rotation.
    """
    # The shop GUI is already open (open_spawner_menu waited and centered).
    # Move to the spawner slot inside the GUI.
    pyautogui.moveTo(*_jitter_pos(*spawner_pos))
    _jitter_ms(MOUSE_MOVE_DELAY_MS)

    # Retry guard: shop may have opened late and reset cursor to center.
    # Keep retrying until we're confident the cursor is on the spawner.
    _guard_position(spawner_pos)

    base_interval = Q_PRESS_INTERVAL_MS / 1000
    jitter_range = base_interval * 0.20
    for i in range(TOTAL_Q_PRESSES):
        if running is not None and not running.is_set():
            break

        # Periodic position recheck — every N presses, verify cursor hasn't
        # been recentered by a GUI refresh or late shop open.
        if i > 0 and i % POSITION_RECHECK_INTERVAL == 0:
            cur_x, cur_y = pyautogui.position()
            if abs(cur_x - spawner_pos[0]) > 20 or abs(cur_y - spawner_pos[1]) > 20:
                print(f"[buy] Cursor desviou no Q press #{i} — reposicionando.")
                pyautogui.moveTo(*_jitter_pos(*spawner_pos))
                _jitter_ms(30)

        interval = base_interval + random.uniform(-jitter_range, jitter_range)
        t_start = time.perf_counter()
        _pynput_kb.press('q')
        _pynput_kb.release('q')
        elapsed = time.perf_counter() - t_start
        remaining = interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    # Center mouse while shop is STILL OPEN (cursor is free inside GUI).
    # This is the critical moment: when close_menu() closes the shop,
    # Minecraft recaptures the cursor exactly at center → no camera rotation.
    _center_mouse()


# ---------------------------------------------------------------------------
# Placing spawners from hotbar
# ---------------------------------------------------------------------------

_HOTBAR_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']


def place_all_hotbar():
    """Select slot 1, shift+right-click to merge all spawners, right-click to place.

    NEVER moves the mouse. When this function runs, NO GUI is open — the player
    is looking at the world. Any pyautogui.moveTo() call here would generate
    mouse-move events that Minecraft interprets as camera rotation, causing
    drift that accumulates over cycles.

    The cursor is already at center from buy_spawners()'s final centering
    (which happened while the shop GUI was still open, so it was safe).
    Right-clicks at the current position hit the exact same crosshair spot.
    """
    # Select slot 1
    _pynput_kb.press(_HOTBAR_KEYS[0])
    _pynput_kb.release(_HOTBAR_KEYS[0])
    _jitter_ms(PLACE_SLOT_DELAY_MS)

    # Shift + right-click: compacta todos os spawners do inventario no slot 1
    pyautogui.keyDown('shift')
    try:
        pyautogui.rightClick()
    finally:
        pyautogui.keyUp('shift')
    _jitter_ms(ACTION_DELAY_MS)

    # Right-click: coloca o spawner resultante no chao
    pyautogui.rightClick()
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
