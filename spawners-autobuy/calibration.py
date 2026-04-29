import json
import os
import keyboard
import pyautogui

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")


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
        "1/1  Open the spawners panel (/spawners), hover over the desired spawner and press F6."
    )

    data = {
        "spawner_slot": list(spawner_slot),
    }

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
    return data
