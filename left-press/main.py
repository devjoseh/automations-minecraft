import threading
import tkinter as tk
from pynput.mouse import Controller, Button, Listener

mouse = Controller()
is_holding = False
pending_timer = None
root = None
status_label = None
toggle_btn = None


def update_gui():
    """Refresh status label and button text to match current state."""
    if pending_timer is not None:
        status_label.config(text="Status: Starting in 10s...", fg="orange")
        toggle_btn.config(text="Cancel")
    elif is_holding:
        status_label.config(text="Status: Active", fg="green")
        toggle_btn.config(text="Deactivate")
    else:
        status_label.config(text="Status: Inactive", fg="red")
        toggle_btn.config(text="Activate")


def _do_activate():
    """Press and hold the left mouse button."""
    global is_holding
    is_holding = True
    mouse.press(Button.left)
    root.after(0, update_gui)


def _do_deactivate():
    """Release the left mouse button and cancel any pending activation."""
    global is_holding, pending_timer
    if pending_timer is not None:
        pending_timer.cancel()
        pending_timer = None
    is_holding = False
    mouse.release(Button.left)
    root.after(0, update_gui)


def _delayed_activate():
    """Called by the timer after the 10-second countdown finishes."""
    global pending_timer
    pending_timer = None
    _do_activate()


def on_ui_toggle():
    """Called when the GUI button is clicked."""
    global pending_timer

    if is_holding:
        # Deactivate instantly
        _do_deactivate()
    elif pending_timer is not None:
        # Cancel the pending countdown
        pending_timer.cancel()
        pending_timer = None
        root.after(0, update_gui)
    else:
        # Schedule activation after 10 seconds so the user can switch windows
        pending_timer = threading.Timer(10.0, _delayed_activate)
        pending_timer.start()
        root.after(0, update_gui)


def on_mouse_click(x, y, button, pressed):
    """Called by the pynput listener — Mouse Button 4 toggles instantly."""
    global pending_timer, is_holding

    if button == Button.x1 and pressed:
        if is_holding:
            _do_deactivate()
        else:
            # Cancel any pending countdown and activate right away
            if pending_timer is not None:
                pending_timer.cancel()
                pending_timer = None
            _do_activate()


def start_listener():
    with Listener(on_click=on_mouse_click) as listener:
        listener.join()


def main():
    global root, status_label, toggle_btn

    root = tk.Tk()
    root.title("Left Press Macro")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.geometry("220x90")

    status_label = tk.Label(
        root, text="Status: Inactive", fg="red", font=("Arial", 12, "bold")
    )
    status_label.pack(pady=(12, 4))

    toggle_btn = tk.Button(root, text="Activate", command=on_ui_toggle, width=16)
    toggle_btn.pack(pady=(0, 12))

    # Run pynput listener in a background daemon thread
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    print("==================================================")
    print("⛏️  Minecraft Mining Macro Started! ⛏️")
    print("==================================================")
    print("> GUI: Use the window button to activate/deactivate.")
    print(">      Activating via button has a 10-second delay.")
    print("> Hotkey: Mouse Button 4 — instant toggle, no delay.")
    print("> Close the window to exit.\n")

    root.mainloop()


if __name__ == "__main__":
    main()
