
# arquivo so para adicionar embeddings

from dotenv import load_dotenv
import os
import psycopg2
from integracao_bd import integracaoBD
import psycopg2
import ollama

# Config ini ================================================

load_dotenv()
senha = os.getenv("SENHA_DB")

conexao = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password=senha,
    port=5433
)

ollama_client = ollama.Client()
modelo = "embeddinggemma:latest"

conBd = integracaoBD(conexao)

# ============================================================
#
# ============================================================

dados = [
    {
        "nome": "cédulas_nacionais",
        "desc": "Informacoes sobre todos os lotes de cedulas monetarias feitas pelo Banco Central. Inclui nome da moeda, descricao de valores, Ministro da Fazenda, presidente do Banco Central, codigo de serie inicial, codigo de serie final e serie de reposicao",
        "api":  "https://olinda.bcb.gov.br/olinda/servico/mecir_chancelas/versao/v1/swagger-ui3#/",
        "embedding": ""
    },
    {
        "nome": "territorios",
        "desc": "Area de todos os territorios do Brasil(pais, regioes, estados e municipios). Inclui codigo, nome, capital e area",
        "api":  "http://www.ipeadata.gov.br/api/odata4/Territorios",
        "embedding": ""
    },
    {
        "nome": "dados_cnpj",
        "desc": "Categorizacao de dados cadastrais sobre a situacao de pessoa juridica. Inclui codigo e descricao da categoria",
        "api":  "https://olinda.bcb.gov.br/olinda/servico/BcBase/versao/v2/odata/TipoSituacaoPessoaJuridica",
        "embedding": ""
    },
]

for tabela in dados:
    
    resposta = ollama_client.embed(
        model=modelo,
        input=tabela["desc"]
    )
    
    tabela["embedding"] = resposta["embeddings"][0]
    
    conBd.addTabelaEmbedding(tabela, tabela["embedding"])

# ============================================================
# FINALIZAR
# ============================================================
conBd.fecharCursor()
conexao.close()

print("✅ Embeddings criados e dados inseridos com sucesso!")