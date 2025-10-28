from integracao_bd import integracaoBD
from agente_bd import agenteBD

import re
import ast
import ollama
from langchain_ollama import ChatOllama
import logging

# 1. Obter a instância do logger para este módulo
logger = logging.getLogger(__name__)

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
        
        logger.info(f"Mensagem: {msg}")
        
        # Geração do Embedding
        resposta = self.ollamaClient.embed(
            model=self.modeloEmbedding,
            input=msg
        )
        
        embedMsg = resposta["embeddings"][0]
        
        # Busca RAG (Retrieval Augmented Generation)
        resultados = self.integracaoBd.retTabelasEmbedding(5, embedMsg)

        # 2. Substituindo print(resultados) por log.info
        logger.info(f"Tabelas candidatas encontradas (RAG): {resultados}")

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

        respotaTipoAcao = self.modelo.invoke(msgDefinicaoAcao)

        # ==================================================================

        id = respotaTipoAcao.content.strip()

        # 2. Substituindo prints por log.info/debug
        logger.debug("======================================")
        logger.info(f"Resposta Tipo Acao (LLM): {id} (Content: {respotaTipoAcao.content})")

        if id == "0":
            logger.info("Ação definida como '0' (Resposta Natural). Chamando self.respostaNatural.")
            self.respostaNatural(msg)
            return

        # ==================================================================
        
        entradaTratada = f"""
            Sua tarefa e retornar uma lista de numeros, 
            que deverao ser apenas aqueles relevantes para o contexto da mensagem do usuario (formato numero -> explicacao do contexto), listados abaixo:
        """
        # Adiciona as descrições numeradas
        entradaTratada += "\n".join(
            f"{i} -> {resultado[1]}" for i, resultado in enumerate(resultados)
        )
        # Adiciona a mensagem do usuário
        entradaTratada += f"\n\nMensagem do usuario: {msg}"
        # Instrução final para forçar formato
        entradaTratada += "\nIMPORTANTE: Retorne apenas uma lista com os numeros (exemplo: [0, 2, 4]), sem explicar"

        # 2. Substituindo prints por log.debug
        logger.debug("===================================")
        logger.debug(f"Mensagem tradada para filtragem de tabelas: {entradaTratada}")

        # Chama o modelo para filtragem
        try:
            tabelasImportantes = self.modelo.invoke(entradaTratada)
            lista = ast.literal_eval(tabelasImportantes.content.strip())
            
            # 2. Substituindo prints por log.info
            logger.info("=======================================")
            logger.info(f"Lista das tabelas importantes (filtradas): {lista}")
            
        except Exception as e:
            logger.error(f"Erro ao processar a lista de tabelas importantes do LLM. Conteúdo: {tabelasImportantes.content}. Erro: {e}", exc_info=True)
            lista = [] # Garante que a lista não falhe a próxima etapa.

        # Filtragem dos resultados
        resultados_finais = []
        
        for i, resultado in enumerate(resultados):
            if i in lista:
                resultados_finais.append(resultado)
                
        # Atualiza a variável de resultados
        resultados = resultados_finais

        # 2. Substituindo prints por log.debug
        logger.debug("=======================================")
        logger.info(f"Resultados finais (após filtragem do LLM): {resultados}")
        
        # Execução da ação final
        if id == "1":
            logger.info("Ação definida como '1' (Explicação de Consulta). Chamando self.explicacaoConsulta.")
            self.explicacaoConsulta(msg, resultados)
        elif id == "2":
            # A lista idResultados parece não estar sendo construída corretamente
            # Se 'resultados' são (table_name, description, id), você precisa extrair o id
            idResultados = [res[2] for res in resultados] # Assume que o ID está no índice 2
            logger.info(f"Ação definida como '2' (Consulta SQL). Chamando self.consultaSql com IDs: {idResultados}")
            self.consultaSql(msg, idResultados)
        else:
             logger.warning(f"ID de ação desconhecido ou inválido recebido: {id}")


    def respostaNatural (self, msgUsuario):
        
        resposta = self.modelo.invoke(msgUsuario).content
        
        logger.info(f"Resposta Natural gerada: {resposta}")
        print(resposta) # Mantenha o print se a intenção é mostrar a resposta final ao usuário
        
    def consultaSql (self, msgUsuario, ids):
        
        logger.info(f"Iniciando consultaSql para mensagem: '{msgUsuario}'. IDs de API: {ids}")
        
        resposta = self.agenteBd.controleConsulta(msgUsuario, ids)
        
        if resposta == []:
            # 2. Substituindo print por log.warning
            logger.warning("SQL não retornou dados. Retornando mensagem ao usuário.")
            print("Desculpa, nao foi possivel recuperar os dados pedidos, ou eles nao existem no nosso banco de dados.")
            return
        
        if resposta == "Escrita nao permitida":
            # 2. Substituindo print por log.error
            logger.error("Tentativa de escrita/modificação de banco de dados detectada e bloqueada.")
            print("Foi detectada uma tentativa de modificar o banco de dados, o que nao e permitido")
            return
        
        msg = f"""
            O usuario fez essa requisicao: {msgUsuario}.
            O nosso banco de dados retornou esses dados: {resposta[0]}
            
            Responda o usuario em linguagem natural baseando-se nos dados recuperados pelo banco de dados
        """
        
        resposta_final = self.modelo.invoke(msg).content
        logger.info(f"Resposta final da consulta SQL (linguagem natural): {resposta_final}")
        print(resposta_final)
    
    def explicacaoConsulta(self, msg: str, resultados: list):
        
        logger.info(f"Iniciando explicacaoConsulta para mensagem: '{msg}'. {len(resultados)} APIs envolvidas.")
        
        dadosGerais = []
        entrada = f"""
            Responda essa mensagem: {msg}
            
            Com as seguintes instrucoes:
        """
        
        for i, resultado in enumerate(resultados):
            
            id_api = resultado[2]
            dados = self.integracaoBd.queryExplicacao(id_api)
            dadosGerais.append(dados)
            
            instrucao = (
                f"Explique como acessar a api com essa descricao: {dados[0]['short_name']}, "
                f"no texto adicione [API_{i}] no lugar do link da api, [DOC_{i}] no lugar do link da documentacao e [RET_{i}], no lugar do tipo de resposta"
            )
            
            entrada += instrucao + "\n"
                
        entrada += "\n Seja sucinto e use apenas os dados que foram informados acima, eles estao corretos"
        
        # 2. Substituindo prints por log.debug
        logger.debug("===================================================")
        logger.debug(f"Entrada para o modelo explicar consulta: {entrada}")
            
        respostaModelo = self.modelo.invoke(entrada).content
        logger.info("Resposta de explicação gerada pelo LLM. Iniciando substituições.")
        
        # gambiarra para substituir () por []
        padrao = r"\((API|DOC|RET)_(\d+)\)"
        substituicao = r"[\1_\2]"
        respostaModelo = re.sub(padrao, substituicao, respostaModelo)
        
        # Substituições finais
        for i, resultado in enumerate(resultados):
            
            nome_tabela = resultado[0] 
            dados_api = dadosGerais[i][0]
            
            respostaModelo = respostaModelo.replace(
                f"[API_{i}]", f"{nome_tabela}" 
                ).replace(
                    f"[DOC_{i}]", f"{dados_api.get('documentation', 'Link Indisponível')}"
                ).replace(
                    f"[RET_{i}]", f"{dados_api.get('responsetype', 'Tipo Indisponível')}"
                )
        
        print(respostaModelo)
    
    def apagaTabelas(self):
        logger.warning("Chamando método para apagar tabelas do BD (agenteBd.apagaBD()).")
        self.agenteBd.apagaBD()