def filtrar_timeout(arquivo_origem, arquivo_destino="divergencias_chaves.txt"):
    with open(arquivo_origem, "r", encoding="utf-8") as f_in, \
         open(arquivo_destino, "w", encoding="utf-8") as f_out:

        for linha in f_in:
            linha_limpa = linha.strip()

            try:
                # Divide em duas partes: "numero: emoji" e "relatório"
                _, texto = linha_limpa.split(" ", 1)

                # Verifica se começa com "ReadTimeout"
                if texto.startswith("🟠"):
                    f_out.write(linha)
            except ValueError:
                # Linha fora do formato esperado → ignorar
                continue

    print(f"Linhas filtradas salvas em: {arquivo_destino}")


# Exemplo de uso
filtrar_timeout("med.txt")
