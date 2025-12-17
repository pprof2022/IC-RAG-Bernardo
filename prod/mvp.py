from agente_chat import agenteChat
from bd import integracaoBD

from langchain_ollama import ChatOllama
import re

# config inicial ================================================================================

modeloChat = ChatOllama(model="qwen2:7b", base_url="http://localhost:11434")        # LLM de conversa
modeloEmbedding = "embeddinggemma:latest"                                           # LLM para gerar embeddings

integracaoBd = integracaoBD()
agente_chat = agenteChat(modeloChat, modeloEmbedding, integracaoBd)

# sistema ============================================================================

entrada = "Onde eu posso encontrar os dados dos deputados da Camara dos Deputados"

while not entrada.strip().lower().startswith("sair"):
    
    entrada = re.sub(r"[^a-zA-Z0-9\s]", "", entrada)
    
    agente_chat.controleResposta(entrada)
    
    entrada = input("Escreva sua pergunta: ") # proxima pergunta
    
print("debug")
# finalizacao do sistema ==========================================================================================

integracaoBd.fecharConexao()