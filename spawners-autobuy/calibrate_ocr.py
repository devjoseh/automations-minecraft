"""
Calibração visual da região XYZ do F3.

Uso: python main.py --calibrate-ocr

Abre uma janela com o screenshot da tela. Clique e arraste sobre o texto
XYZ do F3 para selecionar a região. As coordenadas são salvas em config.py.
"""

import re
import time
import tkinter as tk
from pathlib import Path

import mss
from PIL import Image, ImageTk


CONFIG_PATH = Path(__file__).parent / "config.py"


def _save_region_to_config(region: tuple[int, int, int, int]):
    """Substitui o valor de SAFETY_XYZ_REGION em config.py."""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    new_line = f"SAFETY_XYZ_REGION = {region}"
    text = re.sub(r"SAFETY_XYZ_REGION\s*=\s*\(.*?\)", new_line, text)
    CONFIG_PATH.write_text(text, encoding="utf-8")


def run_calibrate_ocr():
    print("Capturando tela em 3 segundos. Troque para o Minecraft com F3 aberto...")
    time.sleep(3)

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # monitor primário
        raw = sct.grab(monitor)
        screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    screen_w, screen_h = screenshot.size

    root = tk.Tk()
    root.title("Selecione a região do XYZ — clique e arraste, depois solte")
    root.resizable(False, False)

    # Escala para caber na tela sem ultrapassar 90% da resolução lógica
    display_w = root.winfo_screenwidth()
    display_h = root.winfo_screenheight()
    scale = min(display_w * 0.9 / screen_w, display_h * 0.9 / screen_h, 1.0)
    canvas_w = int(screen_w * scale)
    canvas_h = int(screen_h * scale)

    img_display = screenshot.resize((canvas_w, canvas_h), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(img_display)

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, cursor="cross")
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    label = tk.Label(root, text="Clique e arraste sobre o texto XYZ do F3. Solte para confirmar.",
                     bg="#222", fg="white", font=("Arial", 11))
    label.pack(fill="x")

    state = {"start": None, "rect": None}
    result: list[tuple[int, int, int, int]] = []

    def on_press(event):
        state["start"] = (event.x, event.y)
        if state["rect"]:
            canvas.delete(state["rect"])

    def on_drag(event):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        if state["rect"]:
            canvas.delete(state["rect"])
        state["rect"] = canvas.create_rectangle(
            x0, y0, event.x, event.y,
            outline="#00ff00", width=2
        )

    def on_release(event):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        x1, y1 = event.x, event.y

        # Garante ordem correta (drag em qualquer direção)
        lx, rx = sorted([x0, x1])
        ty, by = sorted([y0, y1])

        # Converte coordenadas de display de volta para pixels reais
        real_left   = int(lx / scale)
        real_top    = int(ty / scale)
        real_width  = max(int((rx - lx) / scale), 1)
        real_height = max(int((by - ty) / scale), 1)

        region = (real_left, real_top, real_width, real_height)

        # Mostra preview da região selecionada
        preview = screenshot.crop((real_left, real_top, real_left + real_width, real_top + real_height))
        preview_big = preview.resize(
            (max(preview.width * 3, 300), max(preview.height * 3, 60)),
            Image.NEAREST
        )

        preview_win = tk.Toplevel(root)
        preview_win.title("Preview da região selecionada")
        tk_preview = ImageTk.PhotoImage(preview_big)
        tk.Label(preview_win, image=tk_preview).pack()
        tk.Label(preview_win, text=f"Região: {region}", font=("Courier", 10)).pack()

        def confirm():
            result.append(region)
            preview_win.destroy()
            root.destroy()

        def redo():
            preview_win.destroy()

        btn_frame = tk.Frame(preview_win)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Confirmar e salvar", bg="#2a2", fg="white",
                  font=("Arial", 11), command=confirm).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Selecionar novamente", font=("Arial", 11),
                  command=redo).pack(side="left", padx=8)

        preview_win.mainloop()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()

    if result:
        region = result[0]
        _save_region_to_config(region)
        print(f"Região salva em config.py: SAFETY_XYZ_REGION = {region}")
        print("Rode 'python main.py --test-ocr' para confirmar que o OCR está funcionando.")
    else:
        print("Calibração cancelada.")
