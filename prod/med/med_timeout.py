import pyodbc
import requests
import json

DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
SERVER_NAME = '.'
DATABASE_NAME = 'master'

CONNECTION_STRING = (
    f'DRIVER={{{DRIVER_NAME}}};'
    f'SERVER={SERVER_NAME};'
    f'DATABASE={DATABASE_NAME};'
    'Trusted_Connection=yes;'
)

conn = pyodbc.connect(CONNECTION_STRING)
cursor = conn.cursor()

# ----------------------------
# 1. Ler arquivo endpoint_timeout.txt
# ----------------------------

with open("endpoint_timeout.txt", "r", encoding="utf-8") as f:
    timeout_lines = f.read().splitlines()

# Vamos armazenar aqui as linhas que NÃO serão removidas (que falharam novamente)
keep_lines = []

# Carregar med.txt em memória para permitir atualização
med_map = {}
with open("med.txt", "r", encoding="utf-8") as f:
    for line in f:
        if ":" in line:
            lid, msg = line.split(":", 1)
            med_map[lid.strip()] = msg.strip()

# ----------------------------
# 2. Processar cada linha de timeout
# ----------------------------

for line in timeout_lines:
    if ":" not in line:
        keep_lines.append(line)
        continue

    id_str, old_status = line.split(":", 1)
    endpoint_id = id_str.strip()

    print(f"\nReprocessando ID: {endpoint_id}")

    # ----------------------------
    # Buscar Example e ResponseExample no banco
    # ----------------------------
    cursor.execute("""
        SELECT e.Example, ra.ResponseExample
        FROM [Endpoints da API] AS e
        INNER JOIN [Respostas da API] AS ra
            ON e.ApiResponseId = ra.Id
        WHERE e.Id = ?
    """, endpoint_id)

    result = cursor.fetchone()
    if not result:
        print(f"⚠️ ID {endpoint_id} não encontrado no banco. Mantendo no arquivo.")
        keep_lines.append(line)
        continue

    example_url = result[0]
    response_example = result[1]

    # ----------------------------
    # Tentar requisição
    # ----------------------------
    try:
        timeout = 30
        response = requests.get(example_url, timeout=timeout)
        response.raise_for_status()

        # Tenta interpretar JSON retornado pela API
        try:
            json_returned = response.json()
        except Exception as e:
            print(f"❌ Erro ao interpretar JSON retornado: {str(e)}")
            keep_lines.append(line)
            continue

        # Tenta interpretar JSON do banco
        try:
            json_expected = json.loads(response_example)
        except Exception as e:
            print(f"❌ Erro ao interpretar ResponseExample do banco: {str(e)}")
            keep_lines.append(line)
            continue

        # Obtém chaves
        keys_expected = set(json_expected.keys()) if isinstance(json_expected, dict) else set()
        keys_returned = set(json_returned.keys()) if isinstance(json_returned, dict) else set()

        # ----------------------------
        # Comparar chaves
        # ----------------------------
        if keys_expected != keys_returned:
            new_status = (
                f"🟠 Divergencia de chaves. "
                f"Esperava-se {list(keys_expected)}, recebeu {list(keys_returned)}."
            )
        else:
            new_status = f"✅ Resposta OK (timeout resolvido) | timeout = {timeout}"

        # Atualizar med.txt
        med_map[endpoint_id] = new_status

    except Exception as e:
        # Ainda falhou → mantém linha original
        print(f"❌ Ainda falhou para {endpoint_id}: {type(e).__name__}")
        keep_lines.append(line)
        continue


# ----------------------------
# 3. Reescrever endpoint_timeout.txt APENAS com os que falharam
# ----------------------------

with open("endpoint_timeout.txt", "w", encoding="utf-8") as f:
    for l in keep_lines:
        f.write(l + "\n")

print("\nendpoint_timeout.txt atualizado.")

# ----------------------------
# 4. Reescrever med.txt atualizado
# ----------------------------

with open("med.txt", "w", encoding="utf-8") as f:
    for id_key, msg in med_map.items():
        f.write(f"{id_key}: {msg}\n")

print("med.txt atualizado.")