def gerar_navegadores_json(nome_arquivo_entrada, nome_arquivo_saida="navegadores_json.py"):
    """
    Lê o arquivo de entrada, extrai o ID de cada linha e gera o arquivo
    de saída com funções no formato 'def navegador_id{id}(jsonObj): pass'.

    Args:
        nome_arquivo_entrada (str): O nome do arquivo .txt de onde ler os IDs.
        nome_arquivo_saida (str): O nome do arquivo .py a ser criado.
    """
    print(f"Lendo IDs do arquivo: {nome_arquivo_entrada}")

    try:
        with open(nome_arquivo_entrada, 'r', encoding='utf-8') as arquivo_in:
            linhas = arquivo_in.readlines()
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo de entrada '{nome_arquivo_entrada}' não foi encontrado.")
        return

    conteudo_py = ""
    ids_processados = []

    for linha in linhas:
        # Tenta extrair o ID. O ID é o número no início da linha,
        # seguido por um espaço e um hífen.
        try:
            # Encontra o primeiro hífen seguido de espaço e pega o que está antes.
            # Ex: '1 - () - 249' -> pega '1'
            parte_id = linha.split(' - ', 1)[0].strip()
            
            # Verifica se é um número válido antes de adicionar
            if parte_id.isdigit():
                id_linha = int(parte_id)
                ids_processados.append(id_linha)
                
                # Cria a string da função no formato f-string
                # Note o uso de '\n' para garantir as quebras de linha corretas
                funcao_str = (
                    f"def navegador_id{id_linha} (jsonObj):\n"
                    f"    pass\n"
                    f"\n" # Linha extra para separar as definições
                )
                conteudo_py += funcao_str
            else:
                # Ignora linhas que não começam com um ID numérico válido
                continue

        except IndexError:
            # Ignora linhas que não seguem o formato esperado ('id - tupla - qtd')
            continue
        except Exception as e:
            print(f"Aviso: Não foi possível processar a linha: '{linha.strip()}'. Erro: {e}")
            continue

    # Remove o último '\n\n' extra para um arquivo limpo
    conteudo_py = conteudo_py.strip()

    print(f"IDs processados: {len(ids_processados)}")

    # Escreve o conteúdo no novo arquivo .py
    try:
        with open(nome_arquivo_saida, 'w', encoding='utf-8') as arquivo_out:
            arquivo_out.write(conteudo_py)
        
        print(f"✅ Arquivo '{nome_arquivo_saida}' criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao escrever no arquivo de saída: {e}")

# Nome do seu arquivo de entrada (se estiver diferente, altere aqui)
nome_do_arquivo_txt = "tuplas_ordenadas.txt" 

# Chamada da função para executar o processo
gerar_navegadores_json(nome_arquivo_entrada=nome_do_arquivo_txt)