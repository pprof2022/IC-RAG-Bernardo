def gerar_stats():
    erros = 0
    divergencias = 0
    corretos = 0

    with open("med.txt", "r", encoding="utf-8") as f:
        for line in f:
            # Exemplo: "12: ❌ NomeDoErro"
            # Pegamos o conteúdo após o ":" e um espaço
            try:
                status = line.split(": ")[1].strip()
            except IndexError:
                continue  # Linha malformada, ignora

            if status.startswith("❌"):
                erros += 1
            elif status.startswith("🟠"):
                divergencias += 1
            elif status.startswith("✅"):
                corretos += 1

    # Salva o resultado
    with open("med_stats.txt", "w", encoding="utf-8") as f:
        f.write(f"Erros (❌): {erros}\n")
        f.write(f"Divergências (🟠): {divergencias}\n")
        f.write(f"Corretos (✅): {corretos}\n")

    print("Arquivo med_stats.txt gerado com sucesso!")


# Executa a função
gerar_stats()