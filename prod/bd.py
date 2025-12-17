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
        
    def criaTabelaEmbeddingsApis(self):
        print("Inicaindo criação da tabela embeddings_api")
        
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
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao criar tabelas de embeddings: {e.args[1]}")
            self.conexao.rollback()
            raise
        
    def addTabelaEmbeddingApi(self, linha: Dict):
        print(f"Adicionando embedding para api: {linha['Name']}")
        
        try:
            # 1. Preparação dos Dados
            
            # Converte o vetor Python (Lista de floats) para uma string JSON (para NVARCHAR(MAX))
            embedding_json_string = json.dumps(linha.get("embedding", ""))
            
            # Mapeamento dos dados do dicionário 'linha' (que é o dicionário final do processamento)
            id = linha.get("Id", "")
            nome = linha.get("Name", "N/A")
            descricao = linha.get("Description", "")
            
            # 2. Query SQL Server (Usando placeholders '?' e nomes de colunas atualizados)
            sql_insert = """
            INSERT INTO embeddings_api
                (id, nome, descricao, embedding)
            VALUES 
                (?, ?, ?, ?);
            """
            
            # 3. Execução
            self.cur.execute(
                sql_insert, 
                (id, nome, descricao, embedding_json_string)
            )
            
            print(f"✅ Embedding da api '{nome}' inserido e commitado.")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao adicionar embedding para '{nome}': {e.args[1]}")
            self.conexao.rollback()
            raise
        
    def criaTabelasEmbeddings(self):
        print("Iniciando criação da tabela 'embeddings'.")
        
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
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao criar tabelas de embeddings: {e.args[1]}")
            self.conexao.rollback()
            raise
        
    def addTabelaEmbedding(self, linha: Dict):
        
        print(f"Adicionando embedding para endpoint: {linha['Name']}")
        
        try:
            # 1. Preparação dos Dados
            
            # Converte o vetor Python (Lista de floats) para uma string JSON (para NVARCHAR(MAX))
            embedding_json_string = json.dumps(linha.get("embedding", ""))
            
            # Mapeamento dos dados do dicionário 'linha' (que é o dicionário final do processamento)
            id = linha.get("Id", "")
            nome = linha.get("Name", "N/A")
            url = linha.get("Url", "")
            documentacao = linha.get("Documentation", "")
            tipo_resposta = linha.get("ResponseType", "")
            idApi = linha.get("idApi", "")
            texto_embedding = linha.get("Embedding_Text", "")
            
            # 2. Query SQL Server (Usando placeholders '?' e nomes de colunas atualizados)
            sql_insert = """
            INSERT INTO embeddings 
                (id, nome, url, documentacao, tipo_resposta, idApi, texto, embedding)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            # 3. Execução
            self.cur.execute(
                sql_insert, 
                (id, nome, url, documentacao, tipo_resposta, idApi, texto_embedding, embedding_json_string)
            )
            
            print(f"✅ Embedding da tabela '{nome}' inserido e commitado.")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao adicionar embedding para '{nome}': {e.args[1]}")
            self.conexao.rollback()
            raise
        
    def retApiEmbedding(self, embed_list:List[float]):    
        
        print(f"Buscando a API mais conexa com o pedido")
        
        # 1. CONVERSÃO CRÍTICA: Lista Python para String JSON (para o SQL Server)
        try:
            embed_json_string = json.dumps(embed_list)
        except Exception as e:
            print(f"❌ Erro ao converter vetor Python para JSON: {e}")
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
            print(f"Retornadas {len(resultados)} tabelas relevantes do RAG.")
            return resultados
            
        except pyodbc.Error as e:
            # Captura a exceção específica do pyodbc
            print(f"Erro ao executar busca de embeddings no SQL Server: {e.args[1]}")
            self.conexao.rollback()
            raise # Re-lança a exceção para o código chamador
    
    def retTabelasEmbedding(self, max_tabelas: int, embed_list: List[float], idApi: int):
        
        print(f"Buscando {max_tabelas} endpoints mais próximos dentro da API id={idApi}.")
        
        # 1. CONVERSÃO CRÍTICA: Lista Python para String JSON (para o SQL Server)
        try:
            embed_json_string = json.dumps(embed_list)
        except Exception as e:
            print(f"❌ Erro ao converter vetor Python para JSON: {e}")
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
            print(f"Retornados {len(resultados)} endpoints relevantes da API id={idApi}.")
            return resultados
            
        except pyodbc.Error as e:
            # Captura a exceção específica do pyodbc
            print(f"Erro ao executar busca de embeddings no SQL Server: {e.args[1]}")
            self.conexao.rollback()
            raise # Re-lança a exceção para o código chamador
    
    def executaQuery(self, query: str) -> List[Dict[str, Any]]:
        
        print("Executando consulta SQL passada por parametro")
        print(f"Query: {query.strip()}")
        
        try:
            
            self.cur.execute(query)
            
            if self.cur.description is None:
                
                self.conexao.commit()
                linhas_afetadas = self.cur.rowcount
                print(f"Query DML/DDL executada com sucesso. Linhas afetadas: {linhas_afetadas}.")
                
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
            return resultados
        
        except pyodbc.Error as e:
            
            print(f"\n❌ ERRO ao executar a query SQL: {e.args[1]}")
            self.conexao.rollback()
            
            return []
    
    def retParametros(self, id):
        
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
            print(f"Erro ao buscar parametros do endpoint {id}: {e}", exc_info=True)
            return []
            
    
    def queryExplicacao(self, id):
        print(f"Buscando dados de explicação para o endpoint: {id}")
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
        except Error as e:
            print(f"Erro ao buscar dados de explicação para API ID {id}: {e}", exc_info=True)
            return []
    
    def fecharConexao(self):
        self.cur.close()
        self.conexao.close()