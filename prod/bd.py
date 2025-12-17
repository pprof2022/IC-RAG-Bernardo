import pyodbc
from pyodbc import Cursor, Connection, Error
from typing import List, Dict, Any, ClassVar
import json

class integracaoBD:
    
    DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
    SERVER_NAME = '.'
    DATABASE_NAME = 'ic'

    CONNECTION_STRING = (
        f'DRIVER={{{DRIVER_NAME}}};'
        f'SERVER={SERVER_NAME};'
        f'DATABASE={DATABASE_NAME};'
        'Trusted_Connection=yes;' 
        'CharSet=utf8;'
    )
    
    CONNECTION_STRING: ClassVar[str] = CONNECTION_STRING
    
    def __init__(self):
        self.conexao: Connection = pyodbc.connect(self.CONNECTION_STRING, autocommit=True)
        self.cur: Cursor = self.conexao.cursor()
        
    def criaTabelaEmbeddingsApis(self): # Cria a Tabela que armazena o embedding da descricao de cada API
        
        sqlDrop = "IF OBJECT_ID('embeddings_api', 'U') IS NOT NULL DROP TABLE embeddings_api;"
        
        sqlCreate = """
            CREATE TABLE embeddings_api (
            id INT NOT NULL PRIMARY KEY, 
            nome VARCHAR(100) NOT NULL,
            descricao VARCHAR(300) NOT NULL,
            
            -- Coluna de Embedding (JSON string para uso com OPENJSON)
            embedding NVARCHAR(MAX) NOT NULL 
        );
        """
        
        try:
            
            self.cur.execute(sqlDrop)
            self.cur.execute(sqlCreate)
            
        except pyodbc.Error as e:
            self.conexao.rollback()
            raise
         
    def addTabelaEmbeddingApi(self, linha: Dict): # adiciona o embedding da respectiva API
        
        try:
           
            embedding_json_string = json.dumps(linha.get("embedding", ""))
            
            
            id = linha.get("Id", "")
            nome = linha.get("Name", "N/A")
            descricao = linha.get("Description", "")
            
            sql_insert = """
            INSERT INTO embeddings_api
                (id, nome, descricao, embedding)
            VALUES 
                (?, ?, ?, ?);
            """

            self.cur.execute(
                sql_insert, 
                (id, nome, descricao, embedding_json_string)
            )
                        
        except pyodbc.Error as e:
            self.conexao.rollback()
            raise
        
    def criaTabelasEmbeddings(self): # Cria a Tabela que armazena o embedding da descricao de cada endpoint
                
        sql_drop = "IF OBJECT_ID('embeddings', 'U') IS NOT NULL DROP TABLE embeddings;"
        
        sql_create = """
        CREATE TABLE embeddings (
            id INT NOT NULL PRIMARY KEY, 
            
            -- Colunas solicitadas (ajustadas para SQL Server)
            nome VARCHAR(200) NOT NULL,
            url VARCHAR(MAX) NULL,
            documentacao VARCHAR(MAX) NULL,
            tipo_resposta VARCHAR(20) NULL,
            idApi INT,
            texto VARCHAR(MAX) NULL,
            
            -- Coluna de Embedding (JSON string para uso com OPENJSON)
            embedding NVARCHAR(MAX) NOT NULL 
        );
        """
        
        try:
            
            self.cur.execute(sql_drop)
            self.cur.execute(sql_create)
                        
        except pyodbc.Error as e:
            self.conexao.rollback()
            raise
        
    def addTabelaEmbedding(self, linha: Dict): # adiciona o embedding da respectiva API
                
        try:
            
            embedding_json_string = json.dumps(linha.get("embedding", ""))
            
            id = linha.get("Id", "")
            nome = linha.get("Name", "N/A")
            url = linha.get("Url", "")
            documentacao = linha.get("Documentation", "")
            tipo_resposta = linha.get("ResponseType", "")
            idApi = linha.get("idApi", "")
            texto_embedding = linha.get("Embedding_Text", "")
            
            sql_insert = """
            INSERT INTO embeddings 
                (id, nome, url, documentacao, tipo_resposta, idApi, texto, embedding)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            self.cur.execute(
                sql_insert, 
                (id, nome, url, documentacao, tipo_resposta, idApi, texto_embedding, embedding_json_string)
            )
                        
        except pyodbc.Error as e:
            self.conexao.rollback()
            raise
        
    def retApiEmbedding(self, embed_list:List[float]): # Busca a api com o embedding mais similar da msg do usuario 
                
        try:
            embed_json_string = json.dumps(embed_list)
        except Exception as e:
            return []

        sql_query = f"""
            ;WITH InputVector AS (
                SELECT CAST([key] AS INT) AS idx, CAST(value AS FLOAT) AS val
                FROM OPENJSON(N'{embed_json_string}')
            )
            SELECT TOP 1
                ea.id as idApi,
                SUM(POWER(CAST(s_vec.value AS FLOAT) - t.val, 2)) AS L2_Distance
            FROM embeddings_api AS ea
            CROSS APPLY OPENJSON(ea.embedding) AS s_vec
            INNER JOIN InputVector AS t ON t.idx = s_vec.[key]
            GROUP BY ea.id
            ORDER BY L2_Distance ASC;
            """
        
        try:
            self.cur.execute(sql_query)
            
            resultados = self.cur.fetchall()
            return resultados
            
        except pyodbc.Error as e:
            self.conexao.rollback()
            raise
    
    def retTabelasEmbedding(self, max_tabelas: int, embed_list: List[float], idApi: int): # Busca os top X endpoints com o embedding mais similar da msg do usuario
                
        try:
            embed_json_string = json.dumps(embed_list)
        except Exception as e:
            return []

        sql_query = f"""
            ;WITH InputVector AS (
                SELECT CAST([key] AS INT) AS idx, CAST(value AS FLOAT) AS val
                FROM OPENJSON(N'{embed_json_string}')
            )
            SELECT TOP ({max_tabelas})
                s.id,
                s.nome,
                s.url,
                s.documentacao,
                s.tipo_resposta,
                s.texto,
                SUM(CAST(s_vec.value AS FLOAT) * t.val) AS DotProduct
            FROM embeddings AS s
            CROSS APPLY OPENJSON(s.embedding) AS s_vec
            INNER JOIN InputVector AS t ON t.idx = s_vec.[key]
            WHERE s.idApi = {idApi}
            GROUP BY s.id, s.nome, s.url, s.documentacao, s.tipo_resposta, s.texto
            ORDER BY DotProduct DESC;
        """
        
        try:
            self.cur.execute(sql_query)
            
            resultados = self.cur.fetchall()
            return resultados
            
        except pyodbc.Error as e:
            self.conexao.rollback()
    
    def executaQuery(self, query: str) -> List[Dict[str, Any]]: # Executa uma query qlqr
        
        try:
            
            self.cur.execute(query)
            
            if self.cur.description is None:
                
                self.conexao.commit()
                
                return []
                
            colunas = [desc[0] for desc in self.cur.description]
            linhas = self.cur.fetchall()
            resultados = []
            
            for linha in linhas:
                resultado_linha = {}
                for i, valor in enumerate(linha):
                    coluna_nome = colunas[i]
                    
                    if isinstance(valor, str):
                        if 'Ã' in valor or '§' in valor or '£' in valor:
                            
                            try:
                                valor_corrigido = valor.encode('latin-1').decode('utf-8')
                                valor = valor_corrigido
                                
                            except UnicodeEncodeError:
                                pass
                            except UnicodeDecodeError:
                                pass
                            
                    resultado_linha[coluna_nome] = valor
                
                resultados.append(resultado_linha)
            
            return resultados
        
        except pyodbc.Error as e:
            self.conexao.rollback()
            
            return []
    
    def retParametros(self, id): # retonar os parametros de um determinado endpoint
        
        query = """
            SELECT 
                p.Name,
                p.Description
            FROM [Parametros dos endpoints] AS pe
            INNER JOIN Parameters AS p
                ON pe.ParameterId = p.Id
            INNER JOIN [Endpoints da API] AS e
                ON pe.ApiEndpointId = e.Id
            WHERE e.Id = ?
        """
        
        try:
            self.cur.execute(query, (id,))
            colunas = [desc[0] for desc in self.cur.description]
            linhas = self.cur.fetchall()
            return [dict(zip(colunas, linha)) for linha in linhas]
        
        except Error as e:
            return []
    
    def fecharConexao(self): # fecha a conexao
        self.cur.close()
        self.conexao.close()