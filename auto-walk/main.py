import time
import threading
from pynput import keyboard, mouse

# Configurações iniciais
COMBINACAO_ATIVA = False
teclado = keyboard.Controller()

def pressionar_teclas():
    """Função que roda em loop para manter as teclas pressionadas"""
    global COMBINACAO_ATIVA
    while True:
        if COMBINACAO_ATIVA:
            # Pressiona as teclas
            teclado.press(keyboard.Key.ctrl)
            teclado.press('w')
        else:
            # Garante que as teclas sejam soltas ao desativar
            teclado.release('w')
            teclado.release(keyboard.Key.ctrl)
        
        time.sleep(0.1)  # Pequeno delay para evitar sobrecarga de CPU

def ao_clicar(x, y, button, pressed):
    """Monitora os botões do mouse"""
    global COMBINACAO_ATIVA
    
    # Button.x1 e x2 geralmente correspondem aos botões 4 e 5 (laterais)
    if pressed and (button == mouse.Button.x1 or button == mouse.Button.x2):
        COMBINACAO_ATIVA = not COMBINACAO_ATIVA
        estado = "ATIVADO" if COMBINACAO_ATIVA else "DESATIVADO"
        print(f"Status: {estado}")

# Iniciar a thread que mantém as teclas pressionadas
thread_teclado = threading.Thread(target=pressionar_teclas, daemon=True)
thread_teclado.start()

# Iniciar o monitor do mouse
print("Script rodando. Pressione o Botão Lateral do Mouse (4 ou 5) para ligar/desligar.")
with mouse.Listener(on_click=ao_clicar) as listener:
    listener.join()