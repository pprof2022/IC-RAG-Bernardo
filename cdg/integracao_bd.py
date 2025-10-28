from psycopg2.extensions import cursor, connection
import os
import json
from datetime import datetime
import re
import logging
from psycopg2 import Error as Psycopg2Error

# Obter a instância do logger para este módulo
logger = logging.getLogger(__name__)

class integracaoBD:
    
    def __init__(self, conexao: connection):
        self.conexao: connection = conexao
        try:
            self.cur: cursor = conexao.cursor()
            logger.info("Instância de integracaoBD criada e cursor obtido.")
        except Exception as e:
            logger.critical(f"Falha ao obter cursor da conexão: {e}", exc_info=True)
            raise # Interrompe a inicialização se o cursor falhar
        
    def criaTabelasEmbeddings(self):
        logger.info("Iniciando criação da tabela 'schema_embeddings'.")
        try:
            # Ativa a extensão pgvector e cria a tabela
            self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_embeddings (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    api TEXT,
                    embedding VECTOR(768)  -- embeddinggemma
                );
            """)
            self.conexao.commit()
            logger.info("Tabela 'schema_embeddings' criada/verificada com sucesso.")
        except Psycopg2Error as e:
            logger.error(f"Erro ao criar tabelas de embeddings: {e}", exc_info=True)
            self.conexao.rollback()
            raise
        
    def addTabelaEmbedding(self, tabela, embedding):
        logger.info(f"Adicionando embedding para tabela: {tabela['nome']}")
        try:
            self.cur.execute("""
                INSERT INTO schema_embeddings (table_name, description, api, embedding)
                VALUES (%s, %s, %s, %s)
                """, (tabela["nome"], tabela["desc"], tabela["api"], embedding)
            )
            self.conexao.commit()
            logger.debug(f"Embedding da tabela '{tabela['nome']}' inserido e commitado.")
        except Psycopg2Error as e:
            logger.error(f"Erro ao adicionar embedding para '{tabela['nome']}': {e}", exc_info=True)
            self.conexao.rollback()
            raise
        
    def retTabelasEmbedding(self, max_tabelas: int, embed):
        logger.debug(f"Buscando as {max_tabelas} tabelas mais próximas (vetorização).")
        try:
            self.cur.execute("""
                SELECT api, description, id
                FROM schema_embeddings
                ORDER BY embedding <-> %s::vector
                LIMIT %s;
            """, (embed, max_tabelas))
            
            resultados = self.cur.fetchall()
            logger.info(f"Retornadas {len(resultados)} tabelas relevantes do RAG.")
            return resultados
        except Psycopg2Error as e:
            logger.error(f"Erro ao executar busca de embeddings: {e}", exc_info=True)
            raise
        
    def criaTabelaTemp(self, query: str):
        logger.info("Executando query de criação de tabela temporária.")
        logger.debug(f"Query: {query.strip()}")
        try:
            self.cur.execute(query)
            self.conexao.commit()
            logger.debug("Tabela temporária criada e commitada.")
        except Psycopg2Error as e:
            logger.error(f"Erro ao criar tabela temporária: {e}", exc_info=True)
            self.conexao.rollback()
            raise
    
    def retPK(self, nomeTabela:str):
        logger.debug(f"Buscando chave primária para a tabela: {nomeTabela}")
        query = """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid
                                AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                AND i.indisprimary;
            """
        try:
            self.cur.execute(query, (nomeTabela,))
            result = self.cur.fetchall()
            
            if not result:
                logger.warning(f"Tabela '{nomeTabela}' não possui chave primária.")
                raise ValueError(f"Tabela {nomeTabela} não possui chave primária.")
            
            pks = [row[0] for row in result]
            logger.debug(f"Chave(s) primária(s) encontrada(s): {pks}")
            return pks
        except Psycopg2Error as e:
            logger.error(f"Erro ao buscar chave primária para '{nomeTabela}': {e}", exc_info=True)
            raise
        except ValueError:
            # Re-lança o erro de PK não encontrada
            raise
    
    def populaTabelaTemp(self, nome_tabela: str, dados: dict):
        if not dados:
            logger.warning(f"Tentativa de popular a tabela '{nome_tabela}' com dados vazios.")
            return # Sai da função silenciosamente
            # Alternativa: raise ValueError("O dicionário de dados está vazio.")

        try:
            colunas = ", ".join(dados.keys())
            placeholders = ", ".join(["%s"] * len(dados))
            valores = tuple(dados.values())

            pks = self.retPK(nome_tabela)
            pk_clause = ", ".join(pks)
            updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in dados.keys() if col not in pks])

            query = f"INSERT INTO {nome_tabela} ({colunas}) VALUES ({placeholders}) ON CONFLICT ({pk_clause}) DO UPDATE SET {updates}"

            self.cur.execute(query, valores)
            self.conexao.commit()
            logger.debug(f"Dados inseridos/atualizados na tabela '{nome_tabela}'. PK: {pk_clause}")
        except Psycopg2Error as e:
            logger.error(f"Erro ao popular a tabela '{nome_tabela}': {e}", exc_info=True)
            self.conexao.rollback()
            raise
        except ValueError as e:
            logger.error(f"Erro na lógica de população da tabela '{nome_tabela}': {e}")
            self.conexao.rollback()
            raise
    
    def executaQuery(self, query:str):
        logger.info("Executando consulta SQL gerada pelo LLM.")
        logger.debug(f"Query: {query.strip()}")
        try:
            self.cur.execute(query)
            
            # Garante que a query era uma SELECT (se não, .description pode falhar)
            if self.cur.description is None:
                logger.warning("Query executada, mas não retornou resultados (provavelmente não era SELECT).")
                return [] 
                
            colunas = [desc[0] for desc in self.cur.description]
            linhas = self.cur.fetchall()
            
            # transforma tuplas em dicts
            resultados = [dict(zip(colunas, linha)) for linha in linhas]
            logger.info(f"Query executada com sucesso. Retornou {len(resultados)} linha(s).")
            return resultados
        except Psycopg2Error as e:
            logger.error(f"Erro ao executar a query SQL: {e}", exc_info=True)
            self.conexao.rollback()
            return [] # Retorna vazio em caso de erro
    
    def queryExplicacao(self, id):
        logger.info(f"Buscando dados de explicação para a API ID: {id}")
        query = f"""
            select a.responsetype, a.documentation, end_a.short_name
            from endpoints_api as end_a
            inner join apis as a on end_a.api_id = a.id
            where end_a.id = %s
            """
        try:
            # Usando %s de forma segura, embora a variável 'id' venha do seu próprio sistema
            self.cur.execute(query, (id,))
            colunas = [desc[0] for desc in self.cur.description]
            linhas = self.cur.fetchall()
            
            return [dict(zip(colunas, linha)) for linha in linhas]
        except Psycopg2Error as e:
            logger.error(f"Erro ao buscar dados de explicação para API ID {id}: {e}", exc_info=True)
            return []
    
    def fecharCursor(self):
        try:
            self.cur.close()
            logger.info("Cursor do BD fechado.")
        except Exception as e:
            logger.error(f"Erro ao fechar cursor: {e}")
        
    def apagaTabelas(self, nomeTabela):
        logger.warning(f"Executando DROP TABLE para: {nomeTabela}")
        try:
            # Uso de f-string é inevitável para DROP TABLE, mas logamos
            self.cur.execute(f"DROP TABLE {nomeTabela}")
            self.conexao.commit()
            logger.info(f"Tabela '{nomeTabela}' apagada com sucesso.")
        except Psycopg2Error as e:
            logger.error(f"Erro ao apagar a tabela '{nomeTabela}': {e}", exc_info=True)
            self.conexao.rollback()

# ===================================================
#
#   Desculpe o transtorno, estamos em obras
#
# ====================================================