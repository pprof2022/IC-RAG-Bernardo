from bd import integracaoBD
from typing import List, Dict, Any
import ollama

# Configuração e Conexão ================================================

bd = integracaoBD()

ollama_client = ollama.Client()
modelo = "embeddinggemma:latest"

# 1. Queries SQL =======================================================

query = """
    SELECT 
        a.Id, 
        a.Name, 
        a.Description
    FROM APIs AS a
"""

queryNomeEndpoints = """
    SELECT
        e.ApiId,
        e.Name
    FROM [Endpoints da API] AS e
"""

# 2. Execução das Queries ===============================================

bd.criaTabelaEmbeddingsApis()
apis = bd.executaQuery(query)
endpoints = bd.executaQuery(queryNomeEndpoints)

# 3. CRIAÇÃO DO HASH MAP ================================================

# endpoints_por_api[ApiId] = [ "Endpoint 1", "Endpoint 2", ... ]
endpoints_por_api: Dict[int, List[str]] = {}

for ep in endpoints:
    api_id = ep["ApiId"]
    nome_ep = ep["Name"]

    if api_id not in endpoints_por_api:
        endpoints_por_api[api_id] = []

    endpoints_por_api[api_id].append(nome_ep)

# 4. FORMATAÇÃO DO TEXTO DE EMBEDDING ==================================

dados_finais_embeddings = []

for api in apis:
    api_id = api["Id"]

    lista_endpoints = endpoints_por_api.get(api_id, [])
    
    endpoints_str = ", ".join(lista_endpoints) if lista_endpoints else "Nenhum endpoint registrado"

    descricao_final = (
        f"{api['Name']}. "
        f"{api['Description']}. "
        f"Endpoints disponíveis: {endpoints_str}."
    )

    dicionario_final = {
        "Id": api["Id"],
        "Name": api["Name"],
        "Description": api["Description"],
        "Embedding_Text": descricao_final,
        "embedding": ""
    }

    dados_finais_embeddings.append(dicionario_final)

print("\n--- Prévia do Processamento ---")
if dados_finais_embeddings:
    print(dados_finais_embeddings[0])
else:
    print("Nenhuma API encontrada.")

# 5. GERAR EMBEDDINGS E SALVAR NO BANCO =================================

for dado in dados_finais_embeddings:
    
    resposta = ollama_client.embed(
        model=modelo,
        input=dado["Embedding_Text"]
    )

    dado["embedding"] = resposta["embeddings"][0]

    bd.addTabelaEmbeddingApi(dado)

# Fechamento da Conexão =====================================
bd.fecharConexao()