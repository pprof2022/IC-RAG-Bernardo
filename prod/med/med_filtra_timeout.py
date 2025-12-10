def filtrar_timeout(arquivo_origem, arquivo_destino="endpoint_timeout.txt"):
    with open(arquivo_origem, "r", encoding="utf-8") as f_in, \
         open(arquivo_destino, "w", encoding="utf-8") as f_out:

        i = 0

        for linha in f_in:
            linha_limpa = linha.strip()

            try:
                # Divide em duas partes: "numero: emoji" e "relatório"
                partes = linha_limpa.split(" ", 2)
                relatorio = partes[2]

                if i == 0:
                    print(relatorio)

                i+=1

                # Verifica se começa com "ReadTimeout"
                if relatorio.startswith("ReadTimeout"):
                    f_out.write(linha)
            except ValueError:
                # Linha fora do formato esperado → ignorar
                continue

    print(f"Linhas filtradas salvas em: {arquivo_destino}")


# Exemplo de uso
filtrar_timeout("med.txt")
