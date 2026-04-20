# Timing (milliseconds)
Q_PRESS_INTERVAL_MS = 60      # Interval between each Q press (50–60ms)
MOUSE_MOVE_DELAY_MS = 80      # Delay after moving mouse before acting
ACTION_DELAY_MS = 100         # Delay between major actions (open menu, etc.)

# Inventory
TOTAL_Q_PRESSES = 2260        # 35 slots × 64 + 1 slot with 1 unit
HOTBAR_SLOTS = 9              # Slots 1–9
INVENTORY_ROWS = 3            # Inventory rows above hotbar
SLOTS_PER_ROW = 9             # Columns per row

# Keys
KEY_OPEN_CHAT = "t"
KEY_SPAWNERS_CMD = "/spawners"
KEY_BUY = "q"
KEY_CLOSE_MENU = "e"
KEY_INVENTORY = "e"

# Safety / Anti-Staff Detection
# Região da tela onde aparecem as coordenadas XYZ no F3 (left, top, width, height).
# O XYZ fica na 2ª linha do painel F3 (lado esquerdo). Ajuste para sua resolução/UI scale.
SAFETY_XYZ_REGION = (0, 215, 516, 34)        # Pixels (left, top, width, height) — 1920x1080 125% DPI
PLACE_PASS1_ENABLED = True      # Se True, faz right-click simples (sem shift) nos slots 1–9 antes do shift+right-click
PLACE_SLOT_DELAY_MS = 60        # Delay entre troca de slot e right-click ao colocar no chão
INVENTORY_MOVE_DELAY_MS = 60    # Delay após mover mouse para slot do inventário
INVENTORY_CLICK_DELAY_MS = 40   # Delay entre shift-clicks no inventário

SAFETY_MONITOR_INTERVAL_S = 3.0             # Intervalo entre verificações de posição
SAFETY_TELEPORT_THRESHOLD_BLOCKS = 2.0    # Distância máxima antes de pausar (blocos)
