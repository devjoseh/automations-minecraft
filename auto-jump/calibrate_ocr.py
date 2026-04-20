"""
Calibração visual das regiões OCR de Nível e Rank.

Uso: python calibrate_ocr.py

Captura a tela e abre uma janela para você selecionar onde estão
os campos 'Nível: X' e 'Rank: X' no HUD. As coordenadas são salvas
em ocr_config.json e funcionam em qualquer resolução/zoom.
"""

import json
import time
import tkinter as tk
from pathlib import Path

import mss
from PIL import Image, ImageTk

CONFIG_FILE = Path(__file__).parent / "ocr_config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def selecionar_regiao(screenshot: Image.Image, titulo: str, instrucao: str) -> tuple | None:
    """
    Abre janela Tkinter com o screenshot. Usuário clica e arrasta para
    selecionar uma região. Retorna (left, top, width, height) em pixels reais,
    ou None se cancelado.
    """
    screen_w, screen_h = screenshot.size

    root = tk.Tk()
    root.title(titulo)
    root.resizable(False, False)

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

    label = tk.Label(root, text=instrucao, bg="#222", fg="white", font=("Arial", 11))
    label.pack(fill="x")

    state = {"start": None, "rect": None}
    result: list = []

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
            x0, y0, event.x, event.y, outline="#00ff00", width=2
        )

    def on_release(event):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        x1, y1 = event.x, event.y

        lx, rx = sorted([x0, x1])
        ty, by = sorted([y0, y1])

        real_left = int(lx / scale)
        real_top = int(ty / scale)
        real_width = max(int((rx - lx) / scale), 1)
        real_height = max(int((by - ty) / scale), 1)

        region = (real_left, real_top, real_width, real_height)

        preview = screenshot.crop(
            (real_left, real_top, real_left + real_width, real_top + real_height)
        )
        preview_big = preview.resize(
            (max(preview.width * 3, 300), max(preview.height * 3, 60)),
            Image.NEAREST,
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
        tk.Button(
            btn_frame, text="Confirmar e salvar", bg="#2a2", fg="white",
            font=("Arial", 11), command=confirm,
        ).pack(side="left", padx=8)
        tk.Button(
            btn_frame, text="Selecionar novamente", font=("Arial", 11),
            command=redo,
        ).pack(side="left", padx=8)

        preview_win.mainloop()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()

    return result[0] if result else None


def run():
    print("Calibração OCR — Nível e Rank")
    print("=" * 40)
    print("Capturando tela em 3 segundos.")
    print("Troque para o Minecraft com o HUD visível antes!")
    time.sleep(3)

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    cfg = _load_config()

    print("\n[Passo 1/2] Selecione a região da linha 'Nível: X' no HUD.")
    nivel_region = selecionar_regiao(
        screenshot,
        "Calibração OCR — Passo 1/2: Nível",
        "Clique e arraste sobre a linha 'Nível: X'. Solte para confirmar.",
    )

    if nivel_region is None:
        print("Calibração cancelada no Passo 1.")
        return

    cfg["nivel_region"] = list(nivel_region)
    print(f"  nivel_region = {nivel_region}")

    print("\n[Passo 2/2] Selecione a região da linha 'Rank: X' no HUD.")
    rank_region = selecionar_regiao(
        screenshot,
        "Calibração OCR — Passo 2/2: Rank",
        "Clique e arraste sobre a linha 'Rank: X'. Solte para confirmar.",
    )

    if rank_region is None:
        print("Calibração cancelada no Passo 2.")
        return

    cfg["rank_region"] = list(rank_region)
    print(f"  rank_region  = {rank_region}")

    _save_config(cfg)
    print("\nCalibração salva em ocr_config.json!")
    print("Rode 'python main.py --test-ocr' para verificar a leitura.")


if __name__ == "__main__":
    run()
