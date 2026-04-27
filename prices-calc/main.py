def formatar_numero(valor):
    """Formata números grandes para facilitar a leitura no Minecraft (K, M, B)"""
    if valor >= 1_000_000_000:
        return f"{valor / 1_000_000_000:.1f}B".replace(".0B", "B")
    elif valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M".replace(".0M", "M")
    elif valor >= 1_000:
        return f"{valor / 1_000:.1f}K".replace(".0K", "K")
    else:
        return str(int(valor))

def gerar_tabela_limites(taxa_base):
    # Configuração dos limites e seus respectivos bônus
    # Bônus: 0.05 = 5%, 0.10 = 10%, etc.
    limites = [
        {"nome": "10K", "valor": 10_000, "bonus": 0.00},
        {"nome": "50K", "valor": 50_000, "bonus": 0.00},
        {"nome": "100K", "valor": 100_000, "bonus": 0.05},
        {"nome": "500K", "valor": 500_000, "bonus": 0.07},
        {"nome": "1M", "valor": 1_000_000, "bonus": 0.09},
        {"nome": "5M", "valor": 5_000_000, "bonus": 0.11},
    ]

    print("\n" + "=" * 60)
    print(f" TABELA DE PREÇOS (BASE: 1 Limite = {taxa_base} Grãos)")
    print("=" * 60)
    print(f"{'Item a Comprar':<16} | {'Preço a Pagar':<15} | {'Taxa Aplicada'}")
    print("-" * 60)

    for limite in limites:
        # Calcula a taxa com o bônus de incentivo
        taxa_com_bonus = taxa_base * (1 + limite["bonus"])
        
        # Calcula o preço final
        preco_total = limite["valor"] * taxa_com_bonus

        # Formata para exibição
        preco_formatado = formatar_numero(preco_total)
        taxa_str = f"1 = {int(taxa_com_bonus)}"

        print(f"Limite {limite['nome']:<9} | {preco_formatado:<15} | {taxa_str}")
    
    print("=" * 60 + "\n")

# --- Execução do Script ---
if __name__ == "__main__":
    try:
        entrada = input("Digite o valor base que deseja pagar por 1 Limite (ex: 100, 60, 150): ")
        taxa = float(entrada) # Usa float caso você queira testar valores quebrados
        gerar_tabela_limites(taxa)
    except ValueError:
        print("Por favor, digite um número válido!")