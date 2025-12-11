import pyodbc
import json
import requests
import pandas as pd

import navegadores_json

DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
SERVER_NAME = '.'
DATABASE_NAME = 'ic'

CONNECTION_STRING = (
    f'DRIVER={{{DRIVER_NAME}}};'
    f'SERVER={SERVER_NAME};'
    f'DATABASE={DATABASE_NAME};'
    'Trusted_Connection=yes;'
)

conn = pyodbc.connect(CONNECTION_STRING)
cursor = conn.cursor()

# Agora também buscamos E.Id (o id do endpoint)
sql = """
    SELECT e.Example
    FROM [Endpoints da API] as e
    where e.Id = 3
"""

cursor.execute(sql)
rows = cursor.fetchall()

print(rows)

api = rows[0][0]

try:
    # A função requests.get envia a solicitação e recebe a resposta.
    # O timeout é uma boa prática para evitar que o programa fique travado.
    resposta = requests.get(api, params={}, timeout=240)
    
    # 4. Verifique o status da resposta
    # Um código 200 (OK) significa que a requisição foi bem-sucedida.
    if resposta.status_code == 200:
        print("✅ Requisição bem-sucedida (Status 200).")
        
        # Conversao via funcao
        #dados_json = navegadores_json.navegador_id16(resposta.json())
        
        # Conversao na mao
        dados_json = (resposta.json()["data"][0])
        
        print(dados_json)

    else:
        # Se o código de status for diferente de 200, algo deu errado
        print(f"❌ Erro na requisição: Status Code {resposta.status_code}")
        print(f"Detalhes do erro: {resposta.text}")
        
except requests.exceptions.RequestException as e:
    # Captura erros de conexão, timeout, etc.
    print(f"❌ Ocorreu um erro ao tentar se conectar à API: {e}")