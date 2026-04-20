import json
import os
import keyboard
import pyautogui

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")


def calculate_inventory_slots(top_left: tuple, bottom_right: tuple) -> list:
    """
    Returns a [row][col] matrix with (x, y) coordinates for each inventory slot.
    top_left     = (x, y) of slot [0][0] — row 1, column 1
    bottom_right = (x, y) of slot [2][8] — row 3, column 9
    """
    rows = 3
    cols = 9
    x0, y0 = top_left
    x1, y1 = bottom_right

    slots = []
    for row in range(rows):
        row_slots = []
        for col in range(cols):
            x = x0 + (x1 - x0) * col / (cols - 1)
            y = y0 + (y1 - y0) * row / (rows - 1)
            row_slots.append((int(x), int(y)))
        slots.append(row_slots)
    return slots


def _wait_for_f6(prompt: str) -> tuple:
    """Display prompt, wait for F6, return current mouse position."""
    print(prompt)
    print("  → Press F6 to capture the position...")
    event = keyboard.read_event(suppress=False)
    while not (event.event_type == "down" and event.name == "f6"):
        event = keyboard.read_event(suppress=False)
    pos = pyautogui.position()
    print(f"  ✓ Captured: ({pos.x}, {pos.y})")
    return (pos.x, pos.y)


def run_calibration():
    """Interactive calibration flow. Saves calibration.json when done."""
    print("\n=== SPAWNER BOT — CALIBRATION ===\n")

    spawner_slot = _wait_for_f6(
        "1/3  Open the spawners panel (/spawners), hover over the desired spawner and press F6."
    )

    inv_slot_0_0 = _wait_for_f6(
        "2/3  Open your inventory (E), hover over the FIRST slot (row 1, column 1) and press F6."
    )

    inv_slot_8_2 = _wait_for_f6(
        "3/3  Hover over the LAST slot (row 3, column 9) and press F6."
    )

    data = {
        "spawner_slot": list(spawner_slot),
        "inv_slot_0_0": list(inv_slot_0_0),
        "inv_slot_8_2": list(inv_slot_8_2),
    }

    # Preview calculated slots
    slots = calculate_inventory_slots(inv_slot_0_0, inv_slot_8_2)
    print("\n--- Calculated inventory slots ---")
    for r, row in enumerate(slots):
        coords = "  ".join(f"({x},{y})" for x, y in row)
        print(f"  Row {r + 1}: {coords}")

    with open(CALIBRATION_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Calibration saved to {CALIBRATION_FILE}\n")


def load_calibration() -> dict | None:
    """Load calibration.json. Returns None if file does not exist."""
    if not os.path.exists(CALIBRATION_FILE):
        return None
    with open(CALIBRATION_FILE) as f:
        data = json.load(f)
    data["spawner_slot"] = tuple(data["spawner_slot"])
    data["inv_slot_0_0"] = tuple(data["inv_slot_0_0"])
    data["inv_slot_8_2"] = tuple(data["inv_slot_8_2"])
    return data


def get_inventory_slots(calibration: dict) -> list:
    """Return the 3×9 slot matrix from loaded calibration data."""
    return calculate_inventory_slots(
        calibration["inv_slot_0_0"],
        calibration["inv_slot_8_2"],
    )
