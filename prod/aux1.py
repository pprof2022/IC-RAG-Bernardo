import pyodbc
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


def extract_top_level_keys(json_text):
    """Extrai as chaves do primeiro nível do JSON."""
    try:
        obj = json.loads(json_text)
        return tuple(obj.keys()) if isinstance(obj, dict) else tuple()
    except:
        return tuple()


def carregar_apis_maps():
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    # Agora também buscamos E.Id (o id do endpoint)
    sql = """
        SELECT 
            A.Id AS ApiId,
            A.Name AS ApiName,
            E.Id AS EndpointId,
            R.ResponseExample
        FROM [Respostas da API] R
        INNER JOIN [Endpoints da API] E
            ON R.Id = E.ApiResponseId
        INNER JOIN APIs A
            ON A.Id = E.ApiId
        ORDER BY A.Id;
    """

    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return []

    max_api_id = max(r[0] for r in rows)

    # Cada API terá:
    # nome: string
    # tuplas: { tuple: count }
    # endpoints: [ {id, tupla} ]
    api_list = [
        {"nome": None, "tuplas": {}, "endpoints": []}
        for _ in range(max_api_id)
    ]

    for api_id, api_name, endpoint_id, response_json in rows:

        idx = api_id - 1

        if api_list[idx]["nome"] is None:
            api_list[idx]["nome"] = api_name

        tuple_keys = extract_top_level_keys(response_json)

        # Incrementar contagem da tupla
        if tuple_keys not in api_list[idx]["tuplas"]:
            api_list[idx]["tuplas"][tuple_keys] = 0

        api_list[idx]["tuplas"][tuple_keys] += 1

        # Registrar o endpoint individual
        api_list[idx]["endpoints"].append({
            "id": endpoint_id,
            "tupla": tuple_keys
        })

    conn.close()
    return api_list


# =======================================================
# 🔥 SALVAR NO TXT
# =======================================================

def salvar_endpoints_txt(api_list, filename="endpoints_tuplas.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for api in api_list:
            f.write("============================================\n")
            f.write(f"API: {api['nome']}\n")
            f.write("============================================\n")

            for ep in api["endpoints"]:
                ep_id = ep["id"]
                tupla = ep["tupla"]
                f.write(f"{ep_id} - {tupla}\n")

            f.write("\n")

    print(f"Arquivo salvo com sucesso em: {filename}")


# =======================================================
# EXECUÇÃO
# =======================================================

result = carregar_apis_maps()

for idx, api_info in enumerate(result, start=1):
    print(f"API {idx} - {api_info['nome']}:")
    print(api_info['tuplas'])
    print("============================================")

salvar_endpoints_txt(result)