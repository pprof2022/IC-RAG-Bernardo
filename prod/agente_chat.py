from bd import integracaoBD
from classe_faiss import Faiss

import time
import ast
import ollama
from langchain_ollama import ChatOllama
import re

class agenteChat:
    
    def __init__(self, modelo: ChatOllama, modeloClass: str, modeloFiltro: str, modeloEmbedding: str, integracaoBd: integracaoBD):
        self.modeloClass: str = modeloClass
        self.modeloFiltro: str = modeloFiltro
        self.modelo: ChatOllama = modelo
        self.modeloEmbedding = modeloEmbedding
        self.integracaoBd = integracaoBd
        self.ollamaClient = ollama.Client()
        self.mapRespostas = {
            "0": self.respostaNatural,
            "1": self.explicacaoConsulta
        }
        self.faiss = Faiss()
    
    def defTipoResposta(self, msg:str): # Verifica que tipo de resposta deve ser feita
        
        #t1 = time.time()
        
        promptClass = f"0=conversa 1=consulta APIs\n\n{msg}\n\nResposta:"
        
        classificacao = ollama.generate(
            model=self.modeloClass,
            prompt=promptClass,
            options={
                'num_predict': 5, 
                'temperature': 0,
                'num_ctx': 512
            }
        )['response'].strip()
        
        id = "0" if "0" in classificacao else "1"

        print(f"Resposta Tipo Acao (LLM): {id}")
        print("===================================================")
        
        #print(f"Tempo funcao defTipoResposta: {time.time() - t1}")
        
        return id
        
    def filtraEndpoints(self, msg, embedMsg):
        
        #t1 = time.time()
        
        idsEndpoints = self.faiss.ret_top_endpoints(embedMsg)
        
        if idsEndpoints:
            ids_formatados = tuple(idsEndpoints) if len(idsEndpoints) > 1 else f"({idsEndpoints[0]})"
            
        resultadosFaiss = self.integracaoBd.retEndpoints(ids_formatados)
        
        print(resultadosFaiss)
        print("===================================================")
        
        promptSelecaoEndpoints = f"Pergunta: {msg}\n\nOpções:\n"
        for i, resultado in enumerate(resultadosFaiss):
            promptSelecaoEndpoints += f"{i}. {resultado['texto']}\n"
        promptSelecaoEndpoints += "\nRetorne APENAS os números relevantes (formato: [0,1,2]):"
        
        print(f"Mensagem tradada para filtragem de endpoints: {promptSelecaoEndpoints}")
        print("===================================")
        
        validacao = ollama.generate(
            model="qwen2:7b",
            prompt=promptSelecaoEndpoints,
            options={'temperature': 0, 'num_ctx': 1024}
        )["response"]
        
        nums = re.findall(r'\d+', validacao)
        indices_selecionados = [
            resultadosFaiss[int(n)] 
            for n in nums 
            if int(n) < len(resultadosFaiss)
        ]

        print("Endpoints apos a filtragem da LLM:")
        print(indices_selecionados)
        print("===================================================")

        #print(f"Tempo funcao filtraEndpoints: {time.time() - t1}")

        return indices_selecionados
        
    def controleResposta (self, msg:str): # Centro de controle de execucao, gerencia todas as funcoes e dados nescessarios
        
        id = self.defTipoResposta(msg)

        if id == "0":
            print("Ação definida como '0' (Resposta Natural). Chamando self.respostaNatural.")
            print("===================================================")
            self.respostaNatural(msg)
            return
        
        print("Ação definida como '1' (Explicacao Consulta)")
        print("===================================================")
        
        embedMsg = self.retEmbedMsg(msg) # gera o embedding da msg
        endpointsFinais = self.filtraEndpoints(msg, embedMsg)
            
        self.explicacaoConsulta(msg, endpointsFinais)
        
    def retEmbedMsg(self, msg:str): # Gera o embedding da msg do usuario
        
        #t1 = time.time()
        
        msgUsuario = self.ollamaClient.embed(
            model=self.modeloEmbedding,
            input=msg
        )
        
        embedMsg = msgUsuario["embeddings"][0]
        
        #print(f"Tempo funcao retEmbedMsg: {time.time() - t1}")
        
        return embedMsg
    
    def respostaNatural(self, msg:str): # resposta de um chatbot normal, sem RAG
        
        resposta = self.modelo.invoke(msg).content
        print(f"Resposta Natural gerada: {resposta}")
    
    def explicacaoConsulta(self, msg:str, resultados:list): #resposta que consulta os endpoints relevantes para a mensagem do usuario
        
        print(f"Iniciando explicacaoConsulta para mensagem: '{msg}'.")
        print("===================================================")
        
        resposta = f"""Voce pode encontrar os dados desejados nessas fontes:"""
        
        for resultado in resultados:
            
            parametros = self.integracaoBd.retParametros(resultado["id"]) # passa o id do endpoint
            
            # Adiciona nome, link da api, link da documentacao e formato da resposta, respectivamente
            resposta += f"\n{resultado["nome"]}\nAPI: {resultado["url"]}\nDocumentacao: {resultado["documentacao"]}\nFormato da resposta: {resultado["tipo_resposta"]}\n"
            
            if parametros: # adiciona os parametros
                resposta += "Parametros: \n"
                
                for parametro in parametros:
                    resposta += f" - {parametro["Name"]}: {parametro["Description"]}\n"
                    
                resposta += "\n"
                
        print(resposta)