import pyodbc
import requests
import json

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

query = """
    SELECT 
        e.Id, 
        e.Example, 
        ra.ResponseExample
    FROM [Endpoints da API] AS e
    INNER JOIN [Respostas da API] AS ra
        ON e.ApiResponseId = ra.Id;
"""

cursor.execute(query)

report_lines = []

for row in cursor.fetchall():
    endpoint_id = row.Id
    example_url = row.Example
    response_example = row.ResponseExample

    # Acompanhar execução
    print(f"Processando endpoint ID: {endpoint_id}")

    status_msg = ""

    # Tenta fazer requisição
    try:
        response = requests.get(example_url, timeout=60) # modifique momentaneamente o timeout
        response.raise_for_status()  # dispara exceção em caso de 4xx/5xx

        # Tenta interpretar JSON
        try:
            json_returned = response.json()
        except Exception as e:
            status_msg = f"❌ Erro ao interpretar JSON retornado: {str(e)}"
            report_lines.append(f"{endpoint_id}: {status_msg}")
            continue

        # Converte ResponseExample em JSON
        try:
            json_expected = json.loads(response_example)
        except Exception as e:
            status_msg = f"❌ Erro ao interpretar ResponseExample (banco): {str(e)}"
            report_lines.append(f"{endpoint_id}: {status_msg}")
            continue

        # Obtém as chaves
        keys_expected = set(json_expected.keys()) if isinstance(json_expected, dict) else set()
        keys_returned = set(json_returned.keys()) if isinstance(json_returned, dict) else set()

        # Verifica divergência
        if keys_expected != keys_returned:
            status_msg = (
                f"🟠 Divergencia de chaves. "
                f"Esperava-se {list(keys_expected)}, recebeu {list(keys_returned)}."
            )
        else:
            status_msg = "✅ Documentação atualizada."

    except requests.exceptions.RequestException as e:
        status_msg = f"❌ {type(e).__name__}: {str(e)}"

    report_lines.append(f"{endpoint_id}: {status_msg}")


# Salva o relatório
with open("med_novo.txt", "w", encoding="utf-8") as f: # modifiquei momentaneamente o caminho do arquivo
    for line in report_lines:
        f.write(line + "\n")

print("\nRelatório salvo em med_novo.txt")