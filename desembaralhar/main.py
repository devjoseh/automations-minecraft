import os
import sys

def carregar_dicionario(caminho_dicionario="lexico.txt"):
    """
    Carrega o dicionário para a memória apenas uma vez.
    Isso deixa as buscas no loop instantâneas.
    """
    if not os.path.exists(caminho_dicionario):
        print(f"Erro: O arquivo '{caminho_dicionario}' não foi encontrado no diretório atual.")
        sys.exit(1) # Encerra o programa com erro

    print("Carregando dicionário... aguarde um instante.")
    dicionario_memoria = []
    
    with open(caminho_dicionario, 'r', encoding='utf-8') as arquivo:
        for linha in arquivo:
            palavra = linha.strip().lower()
            if palavra:
                # Já guardamos a palavra e a assinatura dela juntas na memória
                dicionario_memoria.append({
                    'palavra': palavra,
                    'assinatura': sorted(palavra),
                    'tamanho': len(palavra)
                })
    
    print(f"Dicionário carregado com sucesso! ({len(dicionario_memoria)} palavras prontas para busca)\n")
    return dicionario_memoria

def buscar_palavras(letras_embaralhadas, dicionario_memoria):
    """
    Busca na memória as palavras que correspondem à sequência.
    """
    letras_embaralhadas = letras_embaralhadas.lower()
    assinatura_entrada = sorted(letras_embaralhadas)
    tamanho_entrada = len(letras_embaralhadas)
    
    palavras_encontradas = []

    for item in dicionario_memoria:
        # Filtra pelo tamanho e depois compara a assinatura
        if item['tamanho'] == tamanho_entrada:
            if item['assinatura'] == assinatura_entrada:
                palavras_encontradas.append(item['palavra'])

    return palavras_encontradas

# ==========================================
# ÁREA DE INTERAÇÃO COM O USUÁRIO (LOOP)
# ==========================================
if __name__ == "__main__":
    # 1. Carrega os dados primeiro
    meu_dicionario = carregar_dicionario("lexico.txt")
    
    print("=====================================================")
    print(" DESEMBARALHADOR DE PALAVRAS INICIADO")
    print(" Pressione Ctrl + C a qualquer momento para sair.")
    print("=====================================================")

    # 2. Inicia o loop infinito
    try:
        while True:
            # Pede a entrada do usuário
            entrada = input("\nDigite a sequência de letras: ").strip()
            
            # Se o usuário apertar Enter sem digitar nada, o programa pede de novo
            if not entrada:
                continue
                
            resultados = buscar_palavras(entrada, meu_dicionario)
            
            # Exibe os resultados
            if resultados:
                print(f"✅ Encontrei {len(resultados)} palavra(s):")
                for palavra in resultados:
                    print(f"   -> {palavra}")
            else:
                print("❌ Nenhuma palavra encontrada com exatamente essas letras.")

    # 3. Intercepta o Ctrl + C para fechar de forma elegante
    except KeyboardInterrupt:
        print("\n\nSaindo do programa... Até a próxima!")
        sys.exit(0)