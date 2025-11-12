from agente_bd import agenteBD
from agente_chat import agenteChat
from bd import integracaoBD

from langchain_ollama import ChatOllama
import re

# config inicial ================================================================================

modeloBd = ChatOllama(model="llama3.2:latest", base_url="http://localhost:11434")   # LLM proprio para escrita de consultas SQL
modeloChat = ChatOllama(model="qwen2:7b", base_url="http://localhost:11434")        # LLM de conversa
modeloEmbedding = "embeddinggemma:latest"                                           # LLM para gerar embeddings

integracaoBd = integracaoBD()
agente_bd = agenteBD(modeloBd, integracaoBd)
agente_chat = agenteChat(modeloChat, agente_bd, modeloEmbedding, integracaoBd)

# sistema ============================================================================

entrada = "Onde eu posso encontrar dados sobre as agencias supervisionadas pelo Bacen"

while not entrada.strip().lower().startswith("sair"):
    
    entrada = re.sub(r"[^a-zA-Z0-9\s]", "", entrada)
    
    agente_chat.controleResposta(entrada)
    
    entrada = input("Escreva sua pergunta: ") # proxima pergunta
    
print("debug")

# finalizacao do sistema ==========================================================================================

agente_chat.apagaTabelas()
integracaoBd.fecharConexao()