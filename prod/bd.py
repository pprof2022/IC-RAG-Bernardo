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
        
        print("Inicaindo criação da tabela embeddings_api")
        print("=======================================")
        
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
            self.cur.execute(sqlCreate),
            print("Tabela 'embeddings_api' criada/verificada com sucesso.")
            print("=======================================")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao criar tabelas de embeddings: {e.args[1]}")
            print("=======================================")
            self.conexao.rollback()
            raise
         
    def addTabelaEmbeddingApi(self, linha: Dict): # adiciona o embedding da respectiva API
        
        print(f"Adicionando embedding para api: {linha['Name']}")
        print("=======================================")
        
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
            
            print(f"✅ Embedding da api '{nome}' inserido e commitado.")
            print("=======================================")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao adicionar embedding para '{nome}': {e.args[1]}")
            print("=======================================")
            self.conexao.rollback()
            raise
        
    def criaTabelasEmbeddings(self): # Cria a Tabela que armazena o embedding da descricao de cada endpoint
        
        print("Iniciando criação da tabela 'embeddings'.")
        print("=======================================")
        
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
            
            print("Tabela 'embeddings' criada/verificada com sucesso.")
            print("=======================================")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao criar tabelas de embeddings: {e.args[1]}")
            print("=======================================")
            self.conexao.rollback()
            raise
        
    def addTabelaEmbedding(self, linha: Dict): # adiciona o embedding da respectiva API
        
        print(f"Adicionando embedding para endpoint: {linha['Name']}")
        print("=======================================")
        
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
            
            print(f"✅ Embedding da tabela '{nome}' inserido e commitado.")
            print("=======================================")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao adicionar embedding para '{nome}': {e.args[1]}")
            print("=======================================")
            self.conexao.rollback()
            raise
        
    def retEndpoints(self, ids):
        
        query = f"select id, nome, url, documentacao, tipo_resposta, texto from embeddings where id in {ids}"
        return self.executaQuery(query)
    
    def executaQuery(self, query: str) -> List[Dict[str, Any]]: # Executa uma query qlqr
        
        print("Executando consulta SQL passada por parametro")
        print(f"Query: {query.strip()}")
        print("=======================================")
        
        try:
            
            self.cur.execute(query)
            
            if self.cur.description is None:
                
                self.conexao.commit()
                linhas_afetadas = self.cur.rowcount
                print(f"Query DML/DDL executada com sucesso. Linhas afetadas: {linhas_afetadas}.")
                print("=======================================")
                
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
            
            print(f"Query SELECT executada com sucesso. Retornou {len(resultados)} linha(s).")
            print("=======================================")
            return resultados
        
        except pyodbc.Error as e:
            
            print(f"\n❌ ERRO ao executar a query SQL: {e.args[1]}")
            print("=======================================")
            self.conexao.rollback()
            
            return []
    
    def retParametros(self, id):  # retornar os parametros de um determinado endpoint

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

            resultados = []

            for linha in linhas:
                registro = {}

                for coluna, valor in zip(colunas, linha):
                    if isinstance(valor, str):
                        try:
                            valor = valor.encode("latin1").decode("utf-8")
                        except UnicodeError:
                            pass

                    registro[coluna] = valor
                resultados.append(registro)
            return resultados

        except Error as e:
            print(f"Erro ao buscar parametros do endpoint {id}: {e}", exc_info=True)
            print("=======================================")
            return []
    
    def fecharConexao(self): # fecha a conexao
        self.cur.close()
        self.conexao.close()