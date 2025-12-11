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

# ----------------------------
# 1. Ler divergencias_chaves.txt
# ----------------------------

with open("divergencias_chaves.txt", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

# ----------------------------
# 2. Processar cada ID
# ----------------------------

for line in lines:
    if ":" not in line:
        continue

    id_str, _ = line.split(":", 1)
    endpoint_id = id_str.strip()

    print(f"\n🔄 Processando divergência para ID: {endpoint_id}")

    # ----------------------------
    # Obter o Example
    # ----------------------------
    cursor.execute("""
        SELECT Example
        FROM [Endpoints da API]
        WHERE Id = ?
    """, endpoint_id)

    result = cursor.fetchone()
    if not result:
        print(f"⚠️ Nenhum Example encontrado para ID {endpoint_id}. Pulando.")
        continue

    example_url = result[0]

    # ----------------------------
    # Requisição para obter o novo JSON
    # ----------------------------
    try:
        response = requests.get(example_url, timeout=15)
        response.raise_for_status()
        new_json = response.json()

        # 🔥 NOVO: caso venha lista, pegar só o primeiro item
        if isinstance(new_json, list):
            if len(new_json) > 0:
                new_json = new_json[0]
            else:
                print(f"⚠️ ID {endpoint_id}: JSON retornou lista vazia. Ignorando.")
                continue

    except Exception as e:
        print(f"❌ Falha ao obter JSON para ID {endpoint_id}: {type(e).__name__} ({str(e)})")
        continue

    # Converter para string JSON
    new_json_str = json.dumps(new_json, ensure_ascii=False)

    # ----------------------------
    # Atualizar ResponseExample
    # ----------------------------
    try:
        cursor.execute("""
            UPDATE [Respostas da API]
            SET ResponseExample = ?
            WHERE Id = ?
        """, new_json_str, endpoint_id)

        conn.commit()
        print(f"✅ ResponseExample atualizado com sucesso para ID {endpoint_id}")

    except Exception as e:
        print(f"❌ Erro ao atualizar banco para ID {endpoint_id}: {str(e)}")
        continue


print("\n🎉 Processo concluído com sucesso.")