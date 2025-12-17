from bd import integracaoBD
from agente_bd import agenteBD

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
        
    def controleResposta (self, msg): # Verifica que tipo de resposta deve ser feita
        
        print(f"Mensagem: {msg}")

        # Definição do tipo de ação (0, 1, 2)
        msgDefinicaoAcao = f"""
            Voce devera definir o contexto da mensagem abaixo, dentro dos 3 listados
            
            Mensagem: {msg}

            Contextos possiveis:
            0 -> Conversa normal
            1 -> Explicacao sobre como e onde acessar os dados 
            
            Retorne apenas o numero, fuck the explanation           
        """
        t1 = time.time()
        respotaTipoAcao = self.modelo.invoke(msgDefinicaoAcao)
        print(f"Tempo para definir acao: {time.time() - t1}")

        # ==================================================================

        id = respotaTipoAcao.content.strip()

        # 2. Substituindo prints por log.info/debug
        print("======================================")
        print(f"Resposta Tipo Acao (LLM): {id} (Content: {respotaTipoAcao.content})")

        if id == "0":
            print("Ação definida como '0' (Resposta Natural). Chamando self.respostaNatural.")
            self.respostaNatural(msg)
            return

        # ==================================================================
        
        # Geração do Embedding
        resposta = self.ollamaClient.embed(
            model=self.modeloEmbedding,
            input=msg
        )
        
        embedMsg = resposta["embeddings"][0]
        
        t1 = time.time()
        api = self.integracaoBd.retApiEmbedding(embedMsg)
        print(f"Tempo para RAG: {time.time() - t1}")
        
        apiId = api[0][0] # id da api relevante
        
        t1 = time.time()
        # Busca RAG (Retrieval Augmented Generation)
        resultados = self.integracaoBd.retTabelasEmbedding(5, embedMsg, apiId)
        print(f"Tempo para RAG: {time.time() - t1}")

        # 2. Substituindo print(resultados) por log.info
        print(f"Tabelas candidatas encontradas (RAG): {resultados}")
        
        entradaTratada = f"""
            Sua tarefa e retornar uma lista de numeros, 
            que deverao ser apenas aqueles relevantes para o contexto da mensagem do usuario (formato numero -> explicacao do contexto), listados abaixo:
        """
        # Adiciona as descrições numeradas
        entradaTratada += "\n".join(
            f"{i} -> {resultado[5]}" for i, resultado in enumerate(resultados)
        )
        # Adiciona a mensagem do usuário
        entradaTratada += f"\n\nMensagem do usuario: {msg}"
        # Instrução final para forçar formato
        entradaTratada += "\nIMPORTANTE: Retorne apenas uma lista com os numeros (exemplo: [0, 2, 4]), sem explicar"

        print("===================================")
        print(f"Mensagem tradada para filtragem de tabelas: {entradaTratada}")

        # Chama o modelo para filtragem
        try:
            t1 = time.time()
            tabelasImportantes = self.modelo.invoke(entradaTratada)
            print(f"Tempo para definir tabelas relevantes: {time.time() - t1}")
            lista = ast.literal_eval(tabelasImportantes.content.strip())
            
            print("=======================================")
            print(f"Lista das tabelas importantes (filtradas): {lista}")
            
        except Exception as e:
            print(f"Erro ao processar a lista de tabelas importantes do LLM. Conteúdo: {tabelasImportantes.content}. Erro: {e}", exc_info=True)
            lista = [] # Garante que a lista não falhe a próxima etapa.

        # Filtragem dos resultados
        resultados_finais = []
        
        for i, resultado in enumerate(resultados):
            if i in lista:
                resultados_finais.append(resultado)
                
        # Atualiza a variável de resultados
        resultados = resultados_finais

        # 2. Substituindo prints por log.debug
        print("=======================================")
        print(f"Resultados finais (após filtragem do LLM): {resultados}")
            
        print("Ação definida como '1' (Explicação de Consulta). Chamando self.explicacaoConsulta.")
        self.explicacaoConsulta(msg, resultados)


    def respostaNatural (self, msgUsuario):
        
        resposta = self.modelo.invoke(msgUsuario).content
        
        print(f"Resposta Natural gerada: {resposta}")
        print(resposta) # Mantenha o print se a intenção é mostrar a resposta final ao usuário
    
    def explicacaoConsulta(self, msg: str, resultados: list):
        
        print(f"Iniciando explicacaoConsulta para mensagem: '{msg}'. {len(resultados)} APIs envolvidas.")
        
        saida = f"""
        Voce pode encontrar os dados desejados nessas fontes:
            
        """
        
        for resultado in resultados:
            parametros = self.integracaoBd.retParametros(resultado[0])
            print("===================================================")
            print(parametros)
            print("===================================================")
            saida += f"\n{resultado[1]}\nAPI: {resultado[2]}\nDocumentacao: {resultado[3]}\nFormato da resposta: {resultado[4]}\n"
            if parametros:
                saida += "Parametros: \n"
                for parametro in parametros:
                    saida += f" - {parametro["Name"]}: {parametro["Description"]}\n"
                saida += "\n"
        
        print(saida)