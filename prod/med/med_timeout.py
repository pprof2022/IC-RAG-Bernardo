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

# ------------------------------------------------
# 1. Ler endpoint_timeout.txt
# ------------------------------------------------
with open("endpoint_timeout.txt", "r", encoding="utf-8") as f:
    timeout_lines = f.read().splitlines()

# Linhas que devem permanecer — somente ReadTimeout
keep_lines = []

# Carrega med.txt em memória
med_map = {}
with open("med.txt", "r", encoding="utf-8") as f:
    for line in f:
        if ":" in line:
            lid, msg = line.split(":", 1)
            med_map[lid.strip()] = msg.strip()

# ------------------------------------------------
# 2. Processar cada ID
# ------------------------------------------------
for line in timeout_lines:
    if ":" not in line:
        keep_lines.append(line)
        continue

    id_str, old_status = line.split(":", 1)
    endpoint_id = id_str.strip()

    print(f"\nReprocessando ID: {endpoint_id}")

    # Buscar URL e JSON esperado
    cursor.execute("""
        SELECT e.Example, ra.ResponseExample
        FROM [Endpoints da API] AS e
        INNER JOIN [Respostas da API] AS ra ON e.ApiResponseId = ra.Id
        WHERE e.Id = ?
    """, endpoint_id)

    result = cursor.fetchone()
    if not result:
        print(f"⚠️ ID {endpoint_id} não encontrado no banco.")
        med_map[endpoint_id] = "❌ Erro: ID não encontrado no banco"
        # remove do timeout.txt (não adiciona em keep_lines)
        continue

    example_url, response_example = result

    try:
        timeout = 30
        response = requests.get(example_url, timeout=timeout)
        response.raise_for_status()

        # Interpretar JSON retornado pela API
        try:
            json_returned = response.json()
        except Exception as e:
            error_name = type(e).__name__
            med_map[endpoint_id] = f"❌ Erro ao interpretar JSON retornado: {error_name} | timeout = {timeout}"
            continue  # remove da lista (não entra no keep_lines)

        # Interpretar JSON esperado
        try:
            json_expected = json.loads(response_example)
        except Exception as e:
            error_name = type(e).__name__
            med_map[endpoint_id] = f"❌ Erro ao interpretar ResponseExample do banco: {error_name} | timeout = {timeout}"
            continue  # remove da lista

        # Comparar as chaves
        keys_expected = set(json_expected.keys()) if isinstance(json_expected, dict) else set()
        keys_returned = set(json_returned.keys()) if isinstance(json_returned, dict) else set()

        if keys_expected != keys_returned:
            med_map[endpoint_id] = (
                f"🟠 Divergência de chaves: "
                f"esperado {list(keys_expected)}, recebeu {list(keys_returned)}. | | timeout = {timeout}"
            )
        else:
            med_map[endpoint_id] = f"✅ Resposta OK | timeout = {timeout}"

        # Em qualquer caso acima, REMOVE do arquivo (não põe em keep_lines)

    except Exception as e:
        # Identificar erro
        error_name = type(e).__name__

        if error_name == "ReadTimeout":
            print(f"⏳ ReadTimeout em {endpoint_id}. Mantendo no arquivo e não alterando med.txt.")
            keep_lines.append(line)  # mantém
            continue
        else:
            print(f"❌ Erro em {endpoint_id}: {error_name}")
            med_map[endpoint_id] = f"❌ Erro na requisição: {error_name} | timeout = {timeout}"
            # REMOVE do arquivo (não adiciona em keep_lines)
            continue

# ------------------------------------------------
# 3. Atualizar endpoint_timeout.txt
# ------------------------------------------------
with open("endpoint_timeout.txt", "w", encoding="utf-8") as f:
    for l in keep_lines:
        f.write(l + "\n")

print("\nendpoint_timeout.txt atualizado.")

# ------------------------------------------------
# 4. Atualizar med.txt
# ------------------------------------------------
with open("med.txt", "w", encoding="utf-8") as f:
    for id_key, msg in med_map.items():
        f.write(f"{id_key}: {msg}\n")

print("med.txt atualizado.")
