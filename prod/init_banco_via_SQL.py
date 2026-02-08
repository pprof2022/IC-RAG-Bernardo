# Inicializa o banco com os arquivos .sql em sql_original
# Nescessário rodar init_api_embeddings.py e init_embedding.py

import pyodbc

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

# Lista de arquivos na ordem correta
sql_files = [
    'Institutions.sql',
    'Tags.sql',
    'Parameters.sql',
    'Apis.sql',
    'ApiResponses.sql',
    'ApiEndpoints.sql',
    'EndpointParameters.sql',
    'EndpointTags.sql'
]

conexao = pyodbc.connect(CONNECTION_STRING, autocommit=True)
cursor = conexao.cursor()

for sql_file in sql_files:
    print(f'Executando {sql_file}...')
    with open(('sql_original/' + sql_file), 'r', encoding='utf-8') as file:
        sql_script = file.read()
        cursor.execute(sql_script)
    print(f'{sql_file} executado com sucesso!')

cursor.close()
conexao.close()
print('Todos os scripts foram executados!')
