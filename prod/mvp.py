from agente_chat import agenteChat
from bd import integracaoBD

from langchain_ollama import ChatOllama
import re
import time

# config inicial ================================================================================

modeloChat = ChatOllama(model="qwen2:7b", base_url="http://localhost:11434")        # LLM de conversa
modeloClass = "gemma3:270m"                                                         # LLM para classificacao da conversa
modeloFiltro = "qwen3:1.7b"                                                         # LLM para filtrar endpoints
modeloEmbedding = "embeddinggemma:latest"                                           # LLM para gerar embeddings

integracaoBd = integracaoBD()
agente_chat = agenteChat(modeloChat, modeloClass, modeloFiltro, modeloEmbedding, integracaoBd)

# sistema ============================================================================

entrada = "Queria um jeito de consultar a taxa selic"

while not entrada.strip().lower().startswith("sair"):
    
    entrada = re.sub(r"[^a-zA-Z0-9\s]", "", entrada)
    
    t1 = time.time()
    agente_chat.controleResposta(entrada)
    print(f"Tempo total: {time.time()  - t1}")
    
    entrada = input("Escreva sua pergunta: ") # proxima pergunta
    
print("Fim")
# finalizacao do sistema ==========================================================================================

integracaoBd.fecharConexao()