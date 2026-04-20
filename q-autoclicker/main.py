import time
import threading
from pynput.mouse import Listener, Button
from pynput.keyboard import Controller

# Configurações globais
DELAY_MS = 100.0
running = False
keyboard = Controller()

def pressionar_tecla():
    """Função que roda em segundo plano para pressionar a tecla 'Q' repetidamente."""
    while True:
        if running:
            keyboard.press('q')
            keyboard.release('q')
        
        # O time.sleep usa segundos, então dividimos os milissegundos por 1000
        time.sleep(DELAY_MS / 1000.0)

def ao_clicar(x, y, button, pressed):
    """Função que escuta os cliques do mouse para ligar/desligar o script."""
    global running
    
    # Button.x1 representa o Mouse Button 4 (Geralmente o botão lateral 'Voltar')
    # Button.x2 representa o Mouse Button 5 (Geralmente o botão lateral 'Avançar')
    if pressed and button in (Button.x1, Button.x2):
        running = not running
        estado = "LIGADO" if running else "DESLIGADO"
        print(f"[STATUS] Auto-clicker {estado}")

if __name__ == "__main__":
    print("=== Auto-Clicker da Tecla 'Q' ===")
    
    # Configuração de Delay pelo usuário
    try:
        entrada = input("Defina o delay entre os cliques (em milissegundos, ex: 50): ")
        DELAY_MS = float(entrada)
        if DELAY_MS <= 0:
            raise ValueError
    except ValueError:
        print("Valor inválido inserido. Usando delay padrão de 100ms.")
        DELAY_MS = 100.0

    print(f"\nConfigurações:")
    print(f"- Tecla: 'Q'")
    print(f"- Delay: {DELAY_MS} ms")
    print("\nInstruções:")
    print("-> Pressione o botão lateral do mouse (Mouse Button 4 ou 5) para INICIAR ou PARAR.")
    print("-> Pressione Ctrl + C neste terminal para encerrar o programa totalmente.\n")

    # Inicia a thread do teclado (roda em paralelo para não travar o mouse)
    thread_teclado = threading.Thread(target=pressionar_tecla, daemon=True)
    thread_teclado.start()

    # Inicia o "escutador" do mouse
    try:
        with Listener(on_click=ao_clicar) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n[AVISO] Programa encerrado pelo usuário.")