from datetime import datetime
import re
import requests

from bd import integracaoBD

class agenteBD:
    
    def __init__(self, modelo, integracaoBd: integracaoBD):
        
        self.integracaoBd = integracaoBd
        
        # dados para exeucao da classe
        self.modelo = modelo
        self.mapFuncoesApis = {
            1: self.agencias_bacen
        }
        self.queriesCriacao = {
            1: """
                CREATE TABLE IF NOT EXISTS agencias_bancarias (
                    nomeIf TEXT,
                    segmento TEXT,
                    codigoCompe TEXT,
                    nomeAgencia TEXT,
                    endereco TEXT,
                    bairro TEXT,
                    cep TEXT,
                    municipioIbge TEXT,
                    municipio TEXT,
                    estado TEXT,
                    dataInicio DATE,
                    telefone TEXT,
                    posicao DATE,
                    cnpj TEXT PRIMARY KEY
                );
            """,
        }
        self.tabelasCriadas = []
    
    def controleConsulta(self, msgUsuario, ids):
        print(f"Iniciando controleConsulta. IDs de APIs a processar: {ids}")
        
        for id in ids:
            try:
                self.criaTabela(id)
                
                # Assume que mapFuncoesApis.get(id) retorna uma função
                funcao_api = self.mapFuncoesApis.get(id)
                if funcao_api:
                    funcao_api()
                else:
                    print(f"ID {id} não tem função de API mapeada em mapFuncoesApis.")
            except Exception as e:
                print(f"Falha ao criar tabela ou executar API para ID {id}: {e}", exc_info=True)
                
        return self.resposta(msgUsuario, ids)
        
    def criaTabela(self, id):
        query = self.queriesCriacao.get(id)
        if query:
            self.integracaoBd.criaTabelaTemp(query)
            print(f"Tabela temporária criada para API ID: {id}")
        else:
            print(f"ID {id} não tem query de criação de tabela associada.")
    
    def resposta(self, msgUsuario: str, ids: list):
        print(f"Gerando query SQL para o LLM. Mensagem: '{msgUsuario}'")
        
        msg = f"""
            Gere um comando em SQL que visa resolver essa questao: {msgUsuario}
            O comando ira rodar em uma base de dados representada abaixo:
        """
        
        for id in ids:
            msg += f"\n {self.queriesCriacao.get(id)}"
        
        msg += """
            \n 
            Retorne apenas o comando em SQL, sem aspas ou identificação, ou seja apenas o que estiver entre "select" e ";"
            Sempre use operadores ILIKE '%valor%' em vez de igualdade.
        """
        
        retorno = self.modelo.invoke(msg)
        resposta = retorno.content
        
        # Lógica de extração e sanitização da query
        resposta_limpa = re.sub(r"```.*?```", "", resposta, flags=re.DOTALL).strip()
        match = re.search(r"(select.*?)(;|$)", resposta_limpa, flags=re.IGNORECASE | re.DOTALL)

        query = None
        if match:
            query = match.group(1) + ";" 
            query = re.sub(r"=\s*'([^']+)'", r"ILIKE '%\1%'", query)
            query = re.sub(r"\bLIKE\b", "ILIKE", query, flags=re.IGNORECASE)

        print("===========================")
        print(f"Retorno do modelo: {retorno}")
        print(f"Resposta content: {resposta}")
        print(f"Query final (se extraída): {query}")
        print("===========================")

        if query and query.strip().lower().startswith("select"): 
            print("Executando query no banco de dados através de integracaoBd.")
            return self.integracaoBd.executaQuery(query)
            
        print(f"Query inválida ou tentativa de escrita detectada: {query}")
        return "Escrita nao permitida"
    
    def agencias_bacen(self):
        print("Iniciando requisição e populando tabela 'agencias_bancarias'.")
        
        self.tabelasCriadas.append("agencias_bancarias")
        
        link = "https://olinda.bcb.gov.br/olinda/servico/Informes_Agencias/versao/v1/odata/Agencias/"
        params = {
            "$format": "json",
        }
        
        try:
            response = requests.get(link, params=params)
            response.raise_for_status() 
            data = response.json()
            agencias = data.get('value', [])
            print(f"API BACEN retornou {len(agencias)} agências.")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar API do BACEN: {e}", exc_info=True)
            return
        except Exception as e:
            print(f"Erro ao processar JSON da API do BACEN: {e}", exc_info=True)
            return
        
        agenciasLTDA = agencias[:10] 
        colunasRemover = ['DDD', 'Numero', 'Complemento', 'CnpjBase', 'CnpjSequencial', 'CnpjDv', 'UF']

        for agencia in agenciasLTDA:
            try:
                # Trata os dados
                agencia['Telefone'] = (agencia.get('DDD', '') or '').strip() + ' ' + (agencia.get('Telefone', '') or '').strip()
                agencia['CNPJ'] = str(agencia.get('CnpjBase', '')) + str(agencia.get('CnpjSequencial', '')) + str(agencia.get('CnpjDv', ''))
                agencia["DataInicio"] = self.format_data_escrita(agencia.get("DataInicio"))
                agencia["Posicao"] = self.format_data_escrita(agencia.get("Posicao"))
                agencia['Endereco'] = self.padroniza_endereco(agencia.get('Endereco', '')) + ' ' + (agencia.get('Numero', '') or '') + ' ' + (agencia.get('Complemento', '') or '')
                agencia['estado'] = self.padronizaUF(agencia.get('UF', ''))
                agencia['Cep'] = self.padronizaCEP(agencia.get('Cep', ''))

                # Remove colunas indesejadas
                for coluna in colunasRemover:
                    agencia.pop(coluna, None)

                self.integracaoBd.populaTabelaTemp("agencias_bancarias", agencia)
            except Exception as e:
                print(f"Erro ao processar e popular agência: {agencia.get('CNPJ')}. Erro: {e}", exc_info=True)

        print(f"{len(agenciasLTDA)} agências enviadas para o banco de dados.")

    
    def format_data_escrita(self, data_str):
        if not data_str:
            return None
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            print(f"Formato de data inválido: {data_str}. Retornando None.")
            return None


    def padroniza_endereco(self, endereco: str) -> str:
        if not endereco:
            return endereco

        endereco = endereco.strip()

        # Caminho 1: abreviação sem espaço
        endereco = re.sub(
            r'^av\.(?=\w)', 
            'AVENIDA ',
            endereco,
            flags=re.IGNORECASE
        )
        endereco = re.sub(
            r'^r\.(?=\w)', 
            'RUA ',
            endereco,
            flags=re.IGNORECASE
        )

        # Caminho 2: abreviação ou palavra normal seguida de espaço
        endereco = re.sub(
            r'^(av\.?|avenida)\s+', 
            'AVENIDA ',
            endereco,
            flags=re.IGNORECASE
        )
        endereco = re.sub(
            r'^(r\.?|rua)\s+', 
            'RUA ',
            endereco,
            flags=re.IGNORECASE
        )

        return endereco.upper()

    def padronizaUF(self, uf):
        nomeEstados = {
            "AC": "Acre AC", "AL": "Alagoas AL", "AP": "Amapa AP", "AM": "Amazonas AM", "BA": "Bahia BA", "CE": "Ceara CE",
            "DF": "Distrito Federal DF", "ES": "Espirito Santo ES", "GO": "Goias GO", "MA": "Maranhao MA", "MT": "Mato Grosso MT",
            "MS": "Mato Grosso do Sul", "MG": "Minas Gerais MG", "PA": "Para PA", "PB": "Paraiba PB", "PR": "Parana PR", 
            "PE": "Pernambuco PE", "PI": "Piaui PI", "RJ": "Rio de Janeiro RJ", "RN": "Rio Grande do Norte RN", 
            "RS": "Rio Grande do Sul RS", "RO": "Rondonia RO", "RR": "Roraima RR", "SC": "Santa Catarina SC", 
            "SP": "Sao Paulo SP", "SE": "Sergipe SE", "TO": "Tocantins TO"
        }
        
        return nomeEstados.get(uf, "").upper()

    def padronizaCEP(self, cep: str):
        return cep.replace("-", "")
    
    def apagaBD(self):
        for tabela in self.tabelasCriadas:
            try:
                self.integracaoBd.apagaTabelas(tabela)
            except Exception as e:
                print(f"erro excluir tabela : {tabela}, erro: {e}")