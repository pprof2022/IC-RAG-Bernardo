from bd import integracaoBD
from classe_faiss import Faiss

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
    
        respotaTipoAcao = self.modelo.invoke(prompotDefineAcao) # Define qual das acoes listadas pela string acima sera executada
        id = respotaTipoAcao.content.strip()
        
        return id
        
    def controleResposta (self, msg:str): # Centro de controle de execucao, gerencia todas as funcoes e dados nescessarios
        
        id = self.defTipoResposta(msg)

        if id == "0":
            self.respostaNatural(msg)
            return
        
        embedMsg = self.retEmbedMsg(msg) # gera o embedding da msg
        idApi = self.faiss.ret_api_mais_similar(embedMsg)
        idsEndpoints = self.faiss.ret_top_endpoints(embedMsg, idApi)
        
        if idsEndpoints:
            ids_formatados = tuple(idsEndpoints) if len(idsEndpoints) > 1 else f"({idsEndpoints[0]})"
            
        query = f"select id, nome, url, documentacao, tipo_resposta, texto from embeddings where id in {ids_formatados}"
        resultadosFaiss = self.integracaoBd.executaQuery(query)
        
        print(resultadosFaiss)
        print("===================================================")
        
        promptSelecaoEndpoints = f"""
            Sua tarefa e retornar uma lista de numeros, 
            que deverao ser apenas aqueles relevantes para o contexto da mensagem do usuario (formato numero -> explicacao do contexto), listados abaixo:
        """
        # Adiciona as descrições dos endpoints numeradas
        promptSelecaoEndpoints += "\n".join(
            f"{i} -> {resultado["texto"]}" for i, resultado in enumerate(resultadosFaiss)
        )
        # Adiciona a mensagem do usuário
        promptSelecaoEndpoints += f"\n\nMensagem do usuario: {msg}"
        # Instrução final para forçar formato
        promptSelecaoEndpoints += "\nIMPORTANTE: Retorne apenas uma lista com os numeros (exemplo: [0, 2, 4]), sem explicar"
        
        print(f"Mensagem tradada para filtragem de endpoints: {promptSelecaoEndpoints}")
        print("===================================")
        
        try:
            
            endpointsRelevantes = self.modelo.invoke(promptSelecaoEndpoints)
            
            lista = ast.literal_eval(endpointsRelevantes.content.strip())
            
        except Exception as e:
            lista = []
            
        endpointsFinais = []
        
        for i, resultado in enumerate(resultadosFaiss): # para cada id selecionado pela LLM, adiciona a descricao do respectivo endpoint
            if i in lista:
                endpointsFinais.append(resultado)
            
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