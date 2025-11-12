import pyodbc
from pyodbc import Cursor, Connection, Error
from typing import List, Dict, Any, ClassVar
import json

class integracaoBD:
    
    DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
    SERVER_NAME = '.'
    DATABASE_NAME = 'master'

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
            texto VARCHAR(MAX) NULL,
            
            -- Coluna de Embedding (JSON string para uso com OPENJSON)
            embedding NVARCHAR(MAX) NOT NULL 
        );
        """
        
        try:
            
            self.cur.execute(sql_drop)
            self.cur.execute(sql_create)
            
            self.conexao.commit()
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
            texto_embedding = linha.get("Embedding_Text", "")
            
            # 2. Query SQL Server (Usando placeholders '?' e nomes de colunas atualizados)
            sql_insert = """
            INSERT INTO embeddings 
                (id, nome, url, documentacao, tipo_resposta, texto, embedding)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?);
            """
            
            # 3. Execução
            self.cur.execute(
                sql_insert, 
                (id, nome, url, documentacao, tipo_resposta, texto_embedding, embedding_json_string)
            )
            
            self.conexao.commit()
            print(f"✅ Embedding da tabela '{nome}' inserido e commitado.")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao adicionar embedding para '{nome}': {e.args[1]}")
            self.conexao.rollback()
            raise
        
    def retTabelasEmbedding(self, max_tabelas: int, embed_list: List[float], l2: float):
        
        """
        Adapta a busca vetorial para SQL Server usando a Distância Euclidiana (L2) 
        com OPENJSON, assumindo que os vetores na tabela estão em formato JSON string.
        
        Args:
            max_tabelas: Limite de resultados a retornar (TOP).
            embed_list: O vetor de embedding como uma lista Python (embedMsg).
        """
        
        print(f"Buscando as {max_tabelas} tabelas mais próximas (vetorização).")
        
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
                SUM(POWER(CAST(s_vec.value AS FLOAT) - t.val, 2)) AS L2_Distance
            FROM embeddings AS s
            CROSS APPLY OPENJSON(s.embedding) AS s_vec
            INNER JOIN InputVector AS t ON t.idx = s_vec.[key]
            GROUP BY s.id, s.nome, s.url, s.documentacao, s.tipo_resposta, s.texto
            HAVING SUM(POWER(CAST(s_vec.value AS FLOAT) - t.val, 2)) < {l2}
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
        
    def criaTabelaTemp(self, query: str):
        print("Executando query de criação de tabela temporária.")
        print(f"Query: {query.strip()}")
        try:
            self.cur.execute(query)
            self.conexao.commit()
            print("Tabela temporária criada e commitada.")
        except Error as e:
            print(f"Erro ao criar tabela temporária: {e}", exc_info=True)
            self.conexao.rollback()
            raise
    
    def retPK(self, nomeTabela:str):
        print(f"Buscando chave primária para a tabela: {nomeTabela}")
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
                print(f"Tabela '{nomeTabela}' não possui chave primária.")
                raise ValueError(f"Tabela {nomeTabela} não possui chave primária.")
            
            pks = [row[0] for row in result]
            print(f"Chave(s) primária(s) encontrada(s): {pks}")
            return pks
        except Error as e:
            print(f"Erro ao buscar chave primária para '{nomeTabela}': {e}", exc_info=True)
            raise
        except ValueError:
            # Re-lança o erro de PK não encontrada
            raise
    
    def populaTabelaTemp(self, nome_tabela: str, dados: dict):
        if not dados:
            print(f"Tentativa de popular a tabela '{nome_tabela}' com dados vazios.")
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
            print(f"Dados inseridos/atualizados na tabela '{nome_tabela}'. PK: {pk_clause}")
        except Error as e:
            print(f"Erro ao popular a tabela '{nome_tabela}': {e}", exc_info=True)
            self.conexao.rollback()
            raise
        except ValueError as e:
            print(f"Erro na lógica de população da tabela '{nome_tabela}': {e}")
            self.conexao.rollback()
            raise
    
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
    
    def queryExplicacao(self, id):
        print(f"Buscando dados de explicação para a API ID: {id}")
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
        
    def apagaTabelas(self, nomeTabela):
        print(f"Executando DROP TABLE para: {nomeTabela}")
        try:
            # Uso de f-string é inevitável para DROP TABLE, mas logamos
            self.cur.execute(f"DROP TABLE {nomeTabela}")
            self.conexao.commit()
            print(f"Tabela '{nomeTabela}' apagada com sucesso.")
        except Error as e:
            print(f"Erro ao apagar a tabela '{nomeTabela}': {e}", exc_info=True)
            self.conexao.rollback()