import pyodbc

# ------------------------------------------------------------------
# CONFIGURAÇÕES E STRING DE CONEXÃO (Mantidas)
# ------------------------------------------------------------------

DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
SERVER_NAME = '.'
DATABASE_NAME = 'ic' 

CONNECTION_STRING = (
    f'DRIVER={{{DRIVER_NAME}}};'
    f'SERVER={SERVER_NAME};'
    f'DATABASE={DATABASE_NAME};'
    'Trusted_Connection=yes;' 
)

# --- FUNÇÕES DE UTILIDADE ---

def listar_tabelas(cursor: pyodbc.Cursor) -> list[str]:
    """Consulta o catálogo do sistema para listar as tabelas de usuário."""
    sql_query = "SELECT name FROM sys.tables WHERE type_desc = 'USER_TABLE' ORDER BY name;"
    tabelas = []
    cursor.execute(sql_query)
    for row in cursor.fetchall():
        tabelas.append(row[0]) 
    return tabelas

def deletar_tabela(cursor: pyodbc.Cursor, conn: pyodbc.Connection, nome_tabela: str):
    """
    Executa o comando DROP TABLE para remover uma tabela.
    
    Args:
        cursor: O objeto cursor ativo.
        conn: O objeto de conexão ativo para confirmação.
        nome_tabela: O nome exato da tabela a ser deletada.
    """
    
    # ⚠️ IMPORTANTE: Uso de f-string para o nome da tabela (DROP TABLE)
    # É aceitável aqui, mas tenha MUITO cuidado ao usar entrada de usuário.
    # Colchetes são usados para garantir que funcione com nomes que têm espaços (ex: [Tags dos endpoints])
    sql_drop = f"DROP TABLE [{nome_tabela}]" 
    
    print(f"\nTentando executar: {sql_drop}")
    
    try:
        cursor.execute(sql_drop)
        conn.commit()
        print(f"✅ Tabela '{nome_tabela}' deletada (DROP) com sucesso!")
    except pyodbc.ProgrammingError as pe:
        if 'does not exist' in str(pe):
            print(f"Aviso: A tabela '{nome_tabela}' não existe. Ignorando.")
        elif 'foreign key constraint' in str(pe):
            print(f"❌ ERRO: Não é possível deletar a tabela '{nome_tabela}' porque outras tabelas dependem dela (Chave Estrangeira).")
        else:
            raise pe
    except pyodbc.Error as ex:
        print(f"❌ Erro ao deletar a tabela: {ex.args[0]}")
        conn.rollback()


# ------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------------

print(f"Tentando conectar ao Servidor: {SERVER_NAME}...")

try:
    with pyodbc.connect(CONNECTION_STRING, timeout=5) as conn:
        print("\n✅ Conexão bem-sucedida usando Autenticação do Windows!")

        with conn.cursor() as cursor:
            
            # 1. LISTA AS TABELAS ATUAIS
            lista_tabelas_antes = listar_tabelas(cursor)
            print("\n--- Tabelas ANTES da Operação ---")
            if lista_tabelas_antes:
                for nome in lista_tabelas_antes:
                    print(f"- {nome}")
            else:
                print("Nenhuma tabela de usuário encontrada.")

            # 2. ESPECIFICA A TABELA A SER DELETADA
            # 💡 Substitua 'Nome da Tabela para Deletar' pelo nome real que você quer remover.
            TABELA_ALVO = '' 
            
            if TABELA_ALVO in lista_tabelas_antes:
                deletar_tabela(cursor, conn, TABELA_ALVO)
            else:
                print(f"\n🚫 Tabela '[{TABELA_ALVO}]' não encontrada. Nada deletado.")


            # 3. LISTA AS TABELAS NOVAMENTE PARA VERIFICAR
            lista_tabelas_depois = listar_tabelas(cursor)
            print("\n--- Tabelas DEPOIS da Operação ---")
            if lista_tabelas_depois:
                for nome in lista_tabelas_depois:
                    print(f"- {nome}")
            else:
                print("Nenhuma tabela de usuário encontrada após a operação.")
                
            TABELA_ALVO = 'embeddings'
            
            cursor.execute(f"SELECT TOP 1 * FROM [{TABELA_ALVO}]")
            
            # 3. Recupera os resultados
            resultados = cursor.fetchall()
            
            # 4. Opcional: Recupera os nomes das colunas
            # Isso é útil para exibir os resultados de forma organizada
            colunas = [column[0] for column in cursor.description]
            
            print(colunas)
            print(f"✅ Consulta executada com sucesso. Total de registros: {len(resultados)}")
            print(resultados)
            
            print(cursor.fetchall())

except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"\n❌ ERRO DE CONEXÃO: {sqlstate}")
    
    

print("\nConexão fechada automaticamente.")