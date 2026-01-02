from bd import integracaoBD
from classe_faiss import Faiss

import time
import ast
import ollama
from langchain_ollama import ChatOllama

class agenteChat:
    
    def __init__(self, modelo: ChatOllama, modeloEmbedding: str, integracaoBd: integracaoBD):
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
        
        prompotDefineAcao = f"""
            Voce devera definir o contexto da mensagem abaixo, dentro dos 3 listados
            
            Mensagem: {msg}

            Contextos possiveis:
            0 -> Conversa normal
            1 -> Explicacao sobre como e onde acessar os dados 
            
            Retorne apenas o numero, fuck the explanation 
        """
        
        t1 = time.time()
        respotaTipoAcao = self.modelo.invoke(prompotDefineAcao) # Define qual das acoes listadas pela string acima sera executada
        print(f"Tempo para definir acao: {time.time() - t1}")
        print("===================================================")
        
        id = respotaTipoAcao.content.strip()

        print(f"Resposta Tipo Acao (LLM): {id} (Content: {respotaTipoAcao.content})")
        print("===================================================")
        
        return id
        
    def controleResposta (self, msg:str): # Centro de controle de execucao, gerencia todas as funcoes e dados nescessarios
        
        print("===================================================")
        print(f"Mensagem do usuario: {msg}")
        print("===================================================")
        
        id = self.defTipoResposta(msg)

        if id == "0":
            print("Ação definida como '0' (Resposta Natural). Chamando self.respostaNatural.")
            print("===================================================")
            self.respostaNatural(msg)
            return
        
        print("Ação definida como '1' (Explicacao Consulta)")
        print("===================================================")
        
        embedMsg = self.retEmbedMsg(msg) # gera o embedding da msg
        
        t1 = time.time()
        api = self.integracaoBd.retApiEmbedding(embedMsg) # retorna a API mais relevante para a msg do usuario
        print(f"Tempo para RAG API: {time.time() - t1}")
        print("===================================================")
        
        apiId = api[0][0] # extrai o id da api do retorno da consulta
        
        t1 = time.time()
        resultados = self.integracaoBd.retTabelasEmbedding(5, embedMsg, apiId) # retorna os 5 endpoints mais relevante para a msg do usuario
        print(f"Tempo para RAG Endpoint: {time.time() - t1}")
        print("===================================================")

        print(f"Tabelas candidatas encontradas (RAG): {resultados}")
        print("===================================================")
        
        print("Teste FAISS")
        print("===================================================")
        
        t1 = time.time()
        idApi = self.faiss.ret_api_mais_similar(embedMsg)
        print(f"Tempo para RAG API: {time.time() - t1}")
        print("===================================================")
        
        t1 = time.time()
        idsEndpoints = self.faiss.ret_top_endpoints(embedMsg, idApi)
        if idsEndpoints:
            ids_formatados = tuple(idsEndpoints) if len(idsEndpoints) > 1 else f"({idsEndpoints[0]})"
        query = f"select id, nome, url, documentacao, tipo_resposta, texto from embeddings where id in {ids_formatados}"
        resultadosFaiss = self.integracaoBd.executaQuery(query)
        print(f"Tempo para RAG Endpoint: {time.time() - t1}")
        print("===================================================")
        print(resultadosFaiss)
        print("===================================================")
        
        promptSelecaoEndpoints = f"""
            Sua tarefa e retornar uma lista de numeros, 
            que deverao ser apenas aqueles relevantes para o contexto da mensagem do usuario (formato numero -> explicacao do contexto), listados abaixo:
        """
        # Adiciona as descrições dos endpoints numeradas
        promptSelecaoEndpoints += "\n".join(
            f"{i} -> {resultado[5]}" for i, resultado in enumerate(resultados)
        )
        # Adiciona a mensagem do usuário
        promptSelecaoEndpoints += f"\n\nMensagem do usuario: {msg}"
        # Instrução final para forçar formato
        promptSelecaoEndpoints += "\nIMPORTANTE: Retorne apenas uma lista com os numeros (exemplo: [0, 2, 4]), sem explicar"
        print("===================================")
        
        print(f"Mensagem tradada para filtragem de endpoints: {promptSelecaoEndpoints}")
        print("===================================")
        
        try:
            
            t1 = time.time()
            endpointsRelevantes = self.modelo.invoke(promptSelecaoEndpoints)
            print(f"Tempo para definir tabelas relevantes: {time.time() - t1}")
            print("===================================")
            
            lista = ast.literal_eval(endpointsRelevantes.content.strip())
            
            print(f"Lista das tabelas importantes (filtradas): {lista}")
            print("=======================================")
            
        except Exception as e:
            print(f"Erro ao processar a lista de tabelas importantes do LLM. Conteúdo: {endpointsRelevantes.content}. Erro: {e}", exc_info=True)
            print("=======================================")
            lista = []
            
        endpointsFinais = []
        
        for i, resultado in enumerate(resultados): # para cada id selecionado pela LLM, adiciona a descricao do respectivo endpoint
            if i in lista:
                endpointsFinais.append(resultado)

        print(f"Resultados finais (após filtragem do LLM): {endpointsFinais}")
        print("=======================================")
            
        self.explicacaoConsulta(msg, endpointsFinais)
        
    def retEmbedMsg(self, msg:str): # Gera o embedding da msg do usuario
        
        msgUsuario = self.ollamaClient.embed(
            model=self.modeloEmbedding,
            input=msg
        )
        
        embedMsg = msgUsuario["embeddings"][0]
        
        return embedMsg
    
    def respostaNatural(self, msg:str): # resposta de um chatbot normal, sem RAG
        
        resposta = self.modelo.invoke(msg).content
        print(f"Resposta Natural gerada: {resposta}")
    
    def explicacaoConsulta(self, msg:str, resultados:list): #resposta que consulta os endpoints relevantes para a mensagem do usuario
        
        print(f"Iniciando explicacaoConsulta para mensagem: '{msg}'.")
        print("===================================================")
        
        resposta = f"""Voce pode encontrar os dados desejados nessas fontes:"""
        
        for resultado in resultados:
            
            parametros = self.integracaoBd.retParametros(resultado[0]) # passa o id do endpoint
            
            print(parametros)
            print("===================================================")
            
            # Adiciona nome, link da api, link da documentacao e formato da resposta, respectivamente
            resposta += f"\n{resultado[1]}\nAPI: {resultado[2]}\nDocumentacao: {resultado[3]}\nFormato da resposta: {resultado[4]}\n"
            
            if parametros: # adiciona os parametros
                resposta =+ "Parametros: \n"
                
                for parametro in parametros:
                    resposta += f" - {parametro["Name"]}: {parametro["Description"]}\n"
                    
                resposta += "\n"
                
        print(resposta)