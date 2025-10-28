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
# CRIAR A TABELA INSTITUICOES
# ============================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS instituicoes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    acronym VARCHAR(10) NOT NULL
);
""")

# ============================================================
# POPULAR TABELA INSTITUICOES
# ============================================================

cur.execute("""
INSERT INTO instituicoes (name, acronym) VALUES
('Sistema de Informações dos Regimes Públicos de Previdência Social', 'CADPREV'),
('Instituto Brasileiro de Geografia e Estatística', 'IBGE'),
('Agência Nacional de Saúde', 'ANS'),
('Instituto de Pesquisa Econômica Aplicada', 'IPEA'),
('Banco Central do Brasil', 'BACEN'),
('Ministério da Fazenda', 'MF'),
('Ministério da Saúde', 'MS'),
('Instituto Nacional de Pesquisas Espaciais', 'INPE'),
('Ministério da Economia', 'ME'),
('Ministério da Cultura', 'MinC'),
('Câmara dos Deputados', 'CD'),
('Controladoria-Geral da União', 'CGU'),
('Senado Federal', 'SF')
ON CONFLICT DO NOTHING;
""")

conexao.commit()

# ============================================================
# CRIAR A TABELA APIS
# ============================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS apis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(300) NOT NULL,
    baseurl VARCHAR(500) NOT NULL,
    documentation VARCHAR(500) NOT NULL,
    responsetype VARCHAR(50) NOT NULL,
    collectiondate DATE NOT NULL,
    authentication BOOLEAN NOT NULL, -- True = Sim, False = Não
    version VARCHAR(10),
    institutionid INT NOT NULL REFERENCES instituicoes(id),
    lastapiupdatedate DATE,
    classification VARCHAR(60)
);
""")

conexao.commit()

# ============================================================
# POPULAR TABELA APIS
# ============================================================

cur.execute("""
INSERT INTO apis 
(name, description, baseurl, documentation, responsetype, collectiondate, authentication, version, institutionid, lastapiupdatedate, classification)
VALUES
('API Cadprev',
 'Dados sobre o Sistema de Informações dos Regimes Públicos de Previdência Social.',
 'https://apicadprev.economia.gov.br/',
 'https://apicadprev.economia.gov.br/api-docs/#/',
 'JSON',
 '2023-09-26',
 FALSE,
 '1.0.0',
 1,
 NULL,
 'Previdência Social'),

('API de dados agregados do IBGE',
 'Dados agregados das pesquisas e censos realizados pelo IBGE.',
 'https://servicodados.ibge.gov.br/api/v3/agregados',
 'https://servicodados.ibge.gov.br/api/docs/agregados?versao=3',
 'JSON',
 '2023-07-30',
 FALSE,
 '3.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('Operadoras API',
 'Dados sobre operadoras com registro ativo na ANS.',
 'https://www.ans.gov.br/operadoras-entity/v1/',
 'https://www.ans.gov.br/operadoras-entity/v1/swagger-ui/index.html?configUrl=/operadoras-entity/v1/v3/api-docs/swagger-config',
 'JSON',
 '2023-06-18',
 FALSE,
 '2.0.6',
 3,
 NULL,
 'Assistência Hospitalar e Ambulatorial'),

('Ipea API',
 'Dados do Atlas do Estado Brasileiro.',
 'https://www.ipea.gov.br/atlasestado/',
 'https://www.ipea.gov.br/atlasestado/api',
 'JSON',
 '2023-09-20',
 FALSE,
 '1',
 4,
 NULL,
 'Pesquisa e Desenvolvimento'),

('Ipeadata - API de consulta',
 'Dados macroeconômicos, regionais e sociais.',
 'http://www.ipeadata.gov.br/api/odata4/',
 'http://www.ipeadata.gov.br/api/',
 'JSON',
 '2023-09-21',
 FALSE,
 '1',
 4,
 NULL,
 'Pesquisa e Desenvolvimento'),
 
('Indicadores de gestão do Banco Central do Brasil',
 'Conjunto de indicadores distribuídos pela cadeia de valor do Bacen e vinculados a seus processos chaves.',
 'https://olinda.bcb.gov.br/olinda/servico/',
 'https://dados.gov.br/dados/conjuntos-dados/indicadores-gestao-banco-central-do-brasil',
 'JSON',
 '2023-10-22',
 FALSE,
 '1',
 5,
 NULL,
 'Economia e Finanças'),

('Previsão de Tempo em XML - CPTEC/INPE',
 'Os dados da Previsão de Tempo, IUV e Ondas em XML possibilitam a recuperação de informações atualizadas do CPTEC/INPE para sua localidade.',
 'http://servicos.cptec.inpe.br/XML/',
 'http://servicos.cptec.inpe.br/XML/',
 'XML',
 '2023-11-19',
 FALSE,
 '1',
 8,
 NULL,
 'Clima'),

('Dados Abertos de Custos com Depreciação do Governo Federal',
 'APIs disponibilizadas pelo Tesouro Nacional.',
 'https://apidatalake.tesouro.gov.br/',
 'https://www.tesourotransparente.gov.br/ckan/dataset/custos-por-itens-de-custos-depreciacao',
 'JSON',
 '2023-07-01',
 FALSE,
 '1.0.0',
 6,
 NULL,
 'Economia e Finanças'),

('SADIPEM API',
 'Dados abertos da Secretaria do Tesouro Nacional.',
 'https://apidatalake.tesouro.gov.br/ords/sadipem/tt/',
 'https://apidatalake.tesouro.gov.br/docs/sadipem/',
 'JSON',
 '2023-06-30',
 FALSE,
 '1.1.0',
 6,
 NULL,
 'Fiscalização do Estado'),

('SICONFI API',
 'Ferramenta destinada ao recebimento de informações contábeis, financeiras e estatísticas fiscais oriundas de municípios, estados, DF e União.',
 'https://apidatalake.tesouro.gov.br/ords/siconfi/tt/',
 'https://www.gov.br/conecta/catalogo/apis/siconfi-extratos-das-declaracoes-contabeis',
 'JSON',
 '2023-06-26',
 FALSE,
 '1.1.0',
 6,
 NULL,
 'Fiscalização do Estado'),

('DEMAS - API de Dados Abertos',
 'Disponibilização de dados abertos para repartições pertencentes ao DEMAS.',
 'https://apidadosabertos.saude.gov.br/',
 'https://apidadosabertos.saude.gov.br/v1/#/',
 'JSON',
 '2023-08-31',
 TRUE,
 '1.7.0',
 7,
 NULL,
 'Saúde'),

('Open Data Sus',
 'Notificações de Síndrome Gripal - API ElasticSearch.',
 'https://elasticsearch-saps.saude.gov.br/desc-esus-notifica-estado-*/_search',
 'https://dados.gov.br/dados/conjuntos-dados/notificaes-de-sndrome-gripal---api-elasticsearch',
 'JSON',
 '2023-08-28',
 TRUE,
 NULL,
 7,
 NULL,
 'Saúde'),

('API de Compras Governamentais',
 'Dados sobre compras públicas.',
 'http://compras.dados.gov.br/',
 'https://compras.dados.gov.br/docs/home.html',
 'HTML, XML, JSON, CSV',
 '2023-11-15',
 FALSE,
 '1',
 9,
 NULL,
 'Compras governamentais'),

('PNPC',
 'Consultas aos dados de contratações, alienação de bens móveis e imóveis, atas de registro de preços e contratos realizados no âmbito da Lei n° 14.133/2021.',
 'https://pncp.gov.br/api/consulta',
 'https://www.gov.br/pncp/pt-br/acesso-a-informacao/manuais/ManualPNCPAPIConsultasVerso1.0.pdf',
 'JSON',
 '2023-10-27',
 FALSE,
 '1',
 10,
 NULL,
 'Administração'),

('SALIC API',
 'Reúne dados a respeito de propostas de projetos culturais a serem incentivados pelo Ministério da Cultura (MINC) por meio da Lei Rouanet.',
 'http://api.salic.cultura.gov.br/',
 'https://api.salic.cultura.gov.br/doc/',
 'JSON',
 '2023-09-19',
 FALSE,
 '0.2.1-beta',
 11,
 NULL,
 'Cultura'),

('Legislativo',
 'Dados sobre a Câmara dos Deputados.',
 'https://dadosabertos.camara.leg.br/swagger/api.html',
 'https://dadosabertos.camara.leg.br/swagger/api.html',
 'JSON',
 '2023-09-06',
 FALSE,
 '0.4.144',
 12,
 NULL,
 'Administração'),

('API REST do Portal da Transparência do Governo Federal',
 'API de dados do Portal da Transparência.',
 'https://api.portaldatransparencia.gov.br/api-de-dados/',
 'https://api.portaldatransparencia.gov.br/swagger-ui/index.html#/Viagens%20a%20servi%C3%A7o/viagensPorPeriodoEOrgao',
 'JSON',
 '2023-11-05',
 TRUE,
 '1',
 13,
 NULL,
 'Administração'),

('API REST do Portal de Dados Abertos',
 'API de dados do Portal de Dados Abertos.',
 'https://dados.gov.br/dados/api/',
 'https://dados.gov.br/swagger-ui/index.html#/',
 'JSON',
 '2024-05-03',
 TRUE,
 '1',
 13,
 NULL,
 'Administração'),

('Senado - Serviços de Dados Abertos',
 'API dos serviços de dados abertos do Senado Federal.',
 'https://legis.senado.leg.br/dadosabertos/',
 'https://legis.senado.leg.br/dadosabertos/docs/index.html',
 'JSON, XML, TXT',
 '2024-05-26',
 FALSE,
 '3.2.10',
 13,
 NULL,
 'Administração'),

('API do Banco de Dados Geodésicos (BDG)',
 'Reúne uma coleção de estações geodésicas, localizadas no país, cujos levantamentos foram realizados pelo IBGE.',
 'https://servicodados.ibge.gov.br/api/v1/bdg',
 'https://servicodados.ibge.gov.br/api/v1/bdg#api-_',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API Calendário',
 'Calendário de divulgação das pesquisas do IBGE.',
 'https://servicodados.ibge.gov.br/api/v3/calendario/',
 'https://servicodados.ibge.gov.br/api/docs/calendario?versao=3',
 'JSON',
 '2024-10-12',
 FALSE,
 '3.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API CNAE - Classificação Nacional de Atividades Econômicas',
 'Classificação oficialmente adotada pelo Sistema Estatístico Nacional na produção de estatísticas por tipo de atividade econômica.',
 'https://servicodados.ibge.gov.br/api/v2/cnae',
 'https://servicodados.ibge.gov.br/api/docs/CNAE?versao=2',
 'JSON',
 '2024-10-12',
 FALSE,
 '2.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API hgeoHNOR',
 'Modelo para conversão de altitudes geométricas (dadas pelos GNSS) em altitudes físicas (compatíveis com o Datum Vertical do SGB).',
 'https://servicodados.ibge.gov.br/api/v1/hgeohnor',
 'https://servicodados.ibge.gov.br/api/docs/hgeohnor?versao=1',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API de localidades',
 'Dados referentes aos países e divisões político-administrativas do Brasil, bem como meso e microrregiões.',
 'https://servicodados.ibge.gov.br/api/v1/localidades',
 'https://servicodados.ibge.gov.br/api/docs/localidades',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API de Malhas Geográficas',
 'Provê malhas simplificadas referentes às unidades político-administrativas do Brasil e regiões geográficas.',
 'https://servicodados.ibge.gov.br/api/v3/malhas',
 'https://servicodados.ibge.gov.br/api/docs/malhas?versao=3',
 'JSON, SVG, GEO JSON',
 '2024-10-12',
 FALSE,
 '3.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API de Metadados',
 'Dados estruturados sobre as informações estatísticas e geocientíficas produzidas pelo IBGE.',
 'http://servicodados.ibge.gov.br/api/v2/metadados',
 'https://servicodados.ibge.gov.br/api/docs/metadados?versao=2',
 'JSON',
 '2024-10-12',
 FALSE,
 '2.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API Nomes',
 'Coletados pela primeira vez no Censo 2010, informa a frequência dos nomes por década de nascimento.',
 'https://servicodados.ibge.gov.br/api/v2/censos/nomes',
 'https://servicodados.ibge.gov.br/api/docs/nomes?versao=2',
 'JSON',
 '2024-10-12',
 FALSE,
 '2.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API Notícias',
 'Nesta API estão disponíveis as notícias e releases sobre as pesquisas e produtos elaborados pelo IBGE.',
 'http://servicodados.ibge.gov.br/api/v3/noticias/',
 'https://servicodados.ibge.gov.br/api/docs/noticias?versao=3',
 'JSON',
 '2024-10-12',
 FALSE,
 '3.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('Países',
 'Informações sobre os 193 países-membros da ONU, com identificadores definidos pela norma ISO 3166-1 ALPHA-2.',
 'https://servicodados.ibge.gov.br/api/v1/paises',
 'https://servicodados.ibge.gov.br/api/docs/paises',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API de Pesquisas',
 'As pesquisas providas por este serviço são um subconjunto da API de Agregados e de outras fontes externas ao IBGE.',
 'https://servicodados.ibge.gov.br/api/v1/pesquisas',
 'https://servicodados.ibge.gov.br/api/docs/pesquisas',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API do Serviço de Posicionamento por Ponto Preciso (IBGE-PPP)',
 'Oferece pós-processamento de dados GNSS (Global Navigation Satellite System) para fornecer posicionamento de precisão.',
 'https://servicodados.ibge.gov.br/api/v1/ppp',
 'https://servicodados.ibge.gov.br/api/docs/ppp?versao=1',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API Produtos',
 'Produtos de estatísticas e geociências do IBGE. Útil para consultas nas APIs de calendário e notícias.',
 'https://servicodados.ibge.gov.br/api/v1/produtos',
 'https://servicodados.ibge.gov.br/api/docs/produtos?versao=1',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API ProGrid',
 'Transforma coordenadas em referenciais clássicos, Córrego Alegre e SAD 69, no atual referencial SIRGAS2000.',
 'https://servicodados.ibge.gov.br/api/v1/progrid',
 'https://servicodados.ibge.gov.br/api/docs/progrid?versao=1',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API Publicações',
 'Consulta às publicações produzidas pelo IBGE.',
 'http://servicodados.ibge.gov.br/api/v1/publicacoes',
 'https://servicodados.ibge.gov.br/api/docs/publicacoes',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API da Rede Brasileira de Monitoramento Contínuo dos Sistemas GNSS (RBMC)',
 'Permite obter dados das estações geodésicas pertencentes à Rede Brasileira de Monitoramento Contínuo dos Sistemas GNSS (RBMC).',
 'https://servicodados.ibge.gov.br/api/v1/rbmc/relatorio',
 'https://servicodados.ibge.gov.br/api/docs/rbmc?versao=1',
 'PDF',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento'),

('API da Rede Maregráfica Permanente para Geodésia (RMPG)',
 'Monitoramento das variações do nível do mar e relação entre o Datum Vertical Brasileiro e outros níveis de referência maregráficos.',
 'https://servicodados.ibge.gov.br/api/v1/rmpg',
 'https://servicodados.ibge.gov.br/api/docs/rmpg?versao=1',
 'JSON',
 '2024-10-12',
 FALSE,
 '1.0.0',
 2,
 NULL,
 'Pesquisa e Desenvolvimento');
""")

conexao.commit()

# ============================================================
# ENDPOINTS
# ============================================================

cur.execute(
    """
    CREATE TABLE endpoints_api (
        id SERIAL PRIMARY KEY,
        api_id INT NOT NULL,
        name VARCHAR(200) NOT NULL,
        url TEXT NOT NULL,
        description VARCHAR(999) NOT NULL,
        example VARCHAR(500) NOT NULL,
        active_example INT NOT NULL,
        short_name VARCHAR(400),

        CONSTRAINT fk_endpoints_api FOREIGN KEY (api_id)
            REFERENCES apis(id)
    );
""")

conexao.commit()

# ============================================================
# POPULAR
# ============================================================

cur.execute(
    """
    INSERT INTO endpoints_api (
        api_id,
        name,
        url,
        description,
        example,
        active_example,
        short_name
    ) VALUES (
        6,
        'Agências de instituições supervisionadas pelo Bacen',
        'https://olinda.bcb.gov.br/olinda/servico/Informes_Agencias/versao/v1/odata/Agencias',
        'Apresentam as informações mais atuais das agências de instituições supervisionadas pelo Bacen.',
        'https://olinda.bcb.gov.br/olinda/servico/Informes_Agencias/versao/v1/odata/Agencias',
        0,
        'Lista agências supervisionadas pelo Bacen'
    );
""")

# ============================================================
# FINALIZAR
# ============================================================

conexao.commit()
cur.close()
conexao.close()

print("✅ Tabelas criadas e dados inseridos com sucesso!")
