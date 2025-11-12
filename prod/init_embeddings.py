from bd import integracaoBD
from typing import List, Dict, Any
import ollama

# Configuração e Conexão ================================================

bd = integracaoBD()

ollama_client = ollama.Client()
modelo = "embeddinggemma:latest"

# 1. Queries SQL =======================================================

# Query 1: Busca informações principais dos Endpoints e da API (E, A)
query_endpoints = """
    SELECT 
        E.Id, 
        E.Name, 
        E.Url, 
        E.ShortName,
        A.Documentation,
        A.ResponseType
    FROM [Endpoints da API] AS E
    INNER JOIN APIs AS A
        ON E.ApiId = A.Id;
    """
    
# Query 2: Busca os Parâmetros ligados aos Endpoints (PE, P)
query_parametros = """
SELECT 
    E.Id AS EndpointId, -- Chave de ligação
    P.Name AS ParameterName, 
    P.Description AS ParameterDescription,
    PE.Required AS ParameterRequired
FROM [Endpoints da API] AS E
INNER JOIN [Parametros dos endpoints] AS PE
    ON E.Id = PE.ApiEndpointId 
INNER JOIN Parameters AS P
    ON PE.ParameterId = P.Id;
"""

# 2. Execução das Queries ===============================================

endpoints = bd.executaQuery(query_endpoints)
parametros = bd.executaQuery(query_parametros)

# 3. CRIAÇÃO DO HASH MAP (DICIONÁRIO DE LOOKUP) =========================

# Agrupa os parâmetros por Id do Endpoint para O(1) lookup
parametros_por_endpoint: Dict[int, List[Dict[str, Any]]] = {}

for p in parametros:
    endpoint_id = p["EndpointId"]
    
    param_info = {
        "name": p["ParameterName"],
        "description": p["ParameterDescription"],
        "required": p["ParameterRequired"]
    }
    
    if endpoint_id not in parametros_por_endpoint:
        parametros_por_endpoint[endpoint_id] = []
        
    parametros_por_endpoint[endpoint_id].append(param_info)

# 4. JUNÇÃO E FORMATAÇÃO FINAL =========================================

dados_finais_embeddings = []

for endpoint in endpoints:
    endpoint_id = endpoint["Id"]
    
    # Busca a lista de parâmetros para este endpoint
    lista_de_parametros = parametros_por_endpoint.get(endpoint_id, [])
    
    # 5. CONSTRUÇÃO DA STRING FINAL (Embedding_Text)
    parametros_formatados = []
    
    for param in lista_de_parametros:
        # Formato: "ParameterName": ParameterDescription
        param_str = f'"{param["name"]}": {param["description"]}'
        parametros_formatados.append(param_str)
        
    # Junta as strings de parâmetro
    string_parametros_final = ", ".join(parametros_formatados)
    
    # Define ShortName (usa Name se ShortName for NULL)
    short_name = endpoint["ShortName"] if endpoint["ShortName"] is not None else endpoint["Name"]
    
    descricao_final = (
        f"{short_name}. "
        f"Contém esses parâmetros: "
        f"{string_parametros_final}"
    )
    
    # 6. Cria o Dicionário Final
    dicionario_final = {
        "Id": endpoint["Id"],
        "Name": endpoint["Name"],
        "Url": endpoint["Url"],
        "Documentation": endpoint["Documentation"],
        "ResponseType": endpoint["ResponseType"],
        "Embedding_Text": descricao_final,
        "embedding": ""
    }
    
    dados_finais_embeddings.append(dicionario_final)

# Exibindo o resultado final do processamento
print("\n--- Resultado do Processamento ---")
if dados_finais_embeddings:
    print(dados_finais_embeddings[0])
else:
    print("Nenhum dado processado.")

bd.criaTabelasEmbeddings()

for dado in dados_finais_embeddings:
    
    resposta = ollama_client.embed(
        model=modelo,
        input=dado["Embedding_Text"]
    )

    dado["embedding"] = resposta["embeddings"][0]

    bd.addTabelaEmbedding(dado)

# Fechamento da Conexão =====================================
bd.fecharConexao()

print("=====================================================")
print("✅ TUDO DEU CERTO MÃE, PODE DESLIGAR O COMPUTADOR ✅")
print("=====================================================")