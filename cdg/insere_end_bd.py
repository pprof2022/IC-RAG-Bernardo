
# arquivo so para adicionar end_points

from dotenv import load_dotenv
import os
import psycopg2

# Config ini ================================================

load_dotenv()
senha = os.getenv("SENHA_DB")

conexao = psycopg2.connect(
    host="localhost",
    dbname="postgres",
    user="postgres",
    password=senha,
    port=5433
)
cur = conexao.cursor()

# ============================================================
#
# ============================================================

dados = [
    (
        6,
        'Chancelas de cédulas nacionais produzidas',
        'https://olinda.bcb.gov.br/olinda/servico/mecir_chancelas/versao/v1/swagger-ui3#/',
        'Traz informações sobre cédulas nacionais produzidas',
        'https://olinda.bcb.gov.br/olinda/servico/mecir_chancelas/versao/v1/odata/TodosDadosChancelas',
        0,
        'Chancela de  cédulas. '
    ),
    (
        5,
        'Territórios',
        'http://www.ipeadata.gov.br/api/odata4/Territorios',
        'Retorna os territórios',
        'http://www.ipeadata.gov.br/api/odata4/Territorios',
        0,
        'Busca Territórios'
    ),
    (
        6,
        'Dados cadastrais de entidades supervisionadas - Situação por pessoa jurídica',
        'https://olinda.bcb.gov.br/olinda/servico/BcBase/versao/v2/odata/TipoSituacaoPessoaJuridica',
        'Dados cadastrais de entidades supervisionadas pelo bacen por pessoa jurídica',
        'https://olinda.bcb.gov.br/olinda/servico/BcBase/versao/v2/odata/TipoSituacaoPessoaJuridica',
        0,
        'Dados de entidades supervisionadas por Situação Pessoa Jurídica'
    )
]

sql_insert = """
    INSERT INTO endpoints_api (
        api_id,
        name,
        url,
        description,
        example,
        active_example,
        short_name
    ) VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

cur.executemany(sql_insert, dados)

# ============================================================
# FINALIZAR
# ============================================================

conexao.commit()
cur.close()
conexao.close()

print("✅ Tabelas criadas e dados inseridos com sucesso!")