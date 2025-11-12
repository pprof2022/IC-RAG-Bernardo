from bd import integracaoBD
from agente_bd import agenteBD

import time
import ast
import ollama
from langchain_ollama import ChatOllama

class agenteChat:
    
    def __init__(self, modelo: ChatOllama, agenteBd: agenteBD, modeloEmbedding: str, integracaoBd: integracaoBD):
        self.modelo: ChatOllama = modelo
        self.modeloEmbedding = modeloEmbedding
        self.integracaoBd = integracaoBd
        self.agenteBd = agenteBd
        self.ollamaClient = ollama.Client()
        self.mapRespostas = {
            "0": self.respostaNatural,
            "1": self.consultaSql
        }
        
    def controleResposta (self, msg): # Verifica que tipo de resposta deve ser feita
        
        flag = 0
        
        print(f"Mensagem: {msg}")
        
        # Geração do Embedding
        resposta = self.ollamaClient.embed(
            model=self.modeloEmbedding,
            input=msg
        )
        
        embedMsg = resposta["embeddings"][0]
        
        t1 = time.time()
        # Busca RAG (Retrieval Augmented Generation)
        resultados = self.integracaoBd.retTabelasEmbedding(5, embedMsg, 1.1)
        print(f"Tempo para RAG: {time.time() - t1}")

        # 2. Substituindo print(resultados) por log.info
        print(f"Tabelas candidatas encontradas (RAG): {resultados}")

        # Definição do tipo de ação (0, 1, 2)
        msgDefinicaoAcao = f"""
            Voce devera definir o contexto da mensagem abaixo, dentro dos 3 listados
            
            Mensagem: {msg}

            Contextos possiveis:
            0 -> Conversa normal
            1 -> Explicacao sobre como acessar os dados
            2 -> Consulta de dados, ou seja, qual e o dado    
            
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
            
        if flag:
            # Execução da ação final
            if id == "1":
                print("Ação definida como '1' (Explicação de Consulta). Chamando self.explicacaoConsulta.")
                self.explicacaoConsulta(msg, resultados)
            elif id == "2":
                # A lista idResultados parece não estar sendo construída corretamente
                # Se 'resultados' são (table_name, description, id), você precisa extrair o id
                idResultados = [res[2] for res in resultados] # Assume que o ID está no índice 2
                print(f"Ação definida como '2' (Consulta SQL). Chamando self.consultaSql com IDs: {idResultados}")
                self.consultaSql(msg, idResultados)
            else:
                print(f"ID de ação desconhecido ou inválido recebido: {id}")


    def respostaNatural (self, msgUsuario):
        
        resposta = self.modelo.invoke(msgUsuario).content
        
        print(f"Resposta Natural gerada: {resposta}")
        print(resposta) # Mantenha o print se a intenção é mostrar a resposta final ao usuário
        
    def consultaSql (self, msgUsuario, ids):
        
        print(f"Iniciando consultaSql para mensagem: '{msgUsuario}'. IDs de API: {ids}")
        
        resposta = self.agenteBd.controleConsulta(msgUsuario, ids)
        
        if resposta == []:
            # 2. Substituindo print por log.warning
            print("SQL não retornou dados. Retornando mensagem ao usuário.")
            print("Desculpa, nao foi possivel recuperar os dados pedidos, ou eles nao existem no nosso banco de dados.")
            return
        
        if resposta == "Escrita nao permitida":
            # 2. Substituindo print por log.error
            print("Tentativa de escrita/modificação de banco de dados detectada e bloqueada.")
            print("Foi detectada uma tentativa de modificar o banco de dados, o que nao e permitido")
            return
        
        msg = f"""
            O usuario fez essa requisicao: {msgUsuario}.
            O nosso banco de dados retornou esses dados: {resposta[0]}
            
            Responda o usuario em linguagem natural baseando-se nos dados recuperados pelo banco de dados
        """
        
        resposta_final = self.modelo.invoke(msg).content
        print(f"Resposta final da consulta SQL (linguagem natural): {resposta_final}")
        print(resposta_final)
    
    def explicacaoConsulta(self, msg: str, resultados: list):
        
        print(f"Iniciando explicacaoConsulta para mensagem: '{msg}'. {len(resultados)} APIs envolvidas.")
        
        saida = f"""
        Voce pode encontrar os dados desejados nessas fontes:
            
        """
        
        for i, resultado in enumerate(resultados):
            id_api = resultado[2]
            dados = self.integracaoBd.queryExplicacao(id_api)
            print("===================================================")
            print(dados)
            print("===================================================")
            saida += f"\n{dados[0]['short_name']}\nAPI: {resultados[0][0]}\nDocumentacao: {dados[0]["documentation"]}\nFormato da resposta: {dados[0]["responsetype"]}\n"
        
        print(saida)
    
    def apagaTabelas(self):
        print("Chamando método para apagar tabelas do BD (agenteBd.apagaBD()).")
        self.agenteBd.apagaBD()