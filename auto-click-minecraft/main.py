"""
Minecraft Pumpkin Auto-Farmer
==============================
Segura o botão esquerdo do mouse por 3 segundos, 3 vezes,
em intervalos definidos pelo usuário.

Abóboras no Minecraft crescem em média a cada 20-30 minutos,
dependendo do random tick speed. Padrão: 1200 segundos (20 min).

Dependência: pip install pynput
"""

import time
import sys
from pynput.mouse import Button, Controller

mouse = Controller()

def segurar_clique(duracao=3, repeticoes=3, pausa_entre=0.5):
    """Segura o botão esquerdo por `duracao` segundos, `repeticoes` vezes."""
    for i in range(1, repeticoes + 1):
        print(f"  [{i}/{repeticoes}] Segurando botão esquerdo por {duracao}s...")
        mouse.press(Button.left)
        time.sleep(duracao)
        mouse.release(Button.left)
        print(f"  [{i}/{repeticoes}] Solto.")
        if i < repeticoes:
            time.sleep(pausa_entre)

def countdown(segundos):
    """Mostra contagem regressiva no terminal."""
    for restante in range(segundos, 0, -1):
        mins, secs = divmod(restante, 60)
        print(f"\r  Próxima colheita em: {mins:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
    print()  # nova linha após contagem

def main():
    print("=" * 50)
    print("  🎃 Minecraft Pumpkin Auto-Farmer")
    print("=" * 50)
    print()
    print("  Abóboras crescem em ~20-30 min (vanilla).")
    print("  Deixe o Minecraft em fullscreen e posicione")
    print("  o cursor sobre a abóbora antes de iniciar.")
    print()

    try:
        entrada = input("  Intervalo entre colheitas em segundos [padrão: 1200]: ").strip()
        intervalo = int(entrada) if entrada else 1200
    except ValueError:
        print("  Valor inválido. Usando padrão de 1200 segundos.")
        intervalo = 1200

    print()
    print(f"  ✅ Intervalo definido: {intervalo}s ({intervalo // 60}min {intervalo % 60}s)")
    print("  ⌨️  Pressione Ctrl+C a qualquer momento para parar.")
    print()

    ciclo = 1
    try:
        while True:
            print(f"--- Ciclo #{ciclo} ---")
            print(f"  ⏳ Aguardando {intervalo}s para a próxima colheita...")
            countdown(intervalo)
            print("  🌾 Iniciando colheita...")
            segurar_clique(duracao=3, repeticoes=3, pausa_entre=0.5)
            print(f"  ✅ Colheita #{ciclo} concluída!\n")
            ciclo += 1

    except KeyboardInterrupt:
        mouse.release(Button.left)  # garante que o botão seja solto
        print("\n\n  🛑 Script encerrado pelo usuário. Boa sorte na farm!")
        sys.exit(0)

if __name__ == "__main__":
    main()