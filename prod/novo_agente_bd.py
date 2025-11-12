import pyodbc
from pyodbc import Connection, Cursor
from typing import ClassVar

class agenteBD:
    
    def __init__(self):
        pass
    
    def criaTabelasEmbeddings(self):
        pass
        
    def addTabelaEmbedding(self, tabela, embedding):
        pass
        
    def retTabelasEmbedding(self, max_tabelas: int, embed):
        pass
        
    def criaTabelaTemp(self, query: str):
        pass
    
    def retPK(self, nomeTabela:str):
        pass
    
    def populaTabelaTemp(self, nome_tabela: str, dados: dict):
        pass
    
    def executaQuery(self, query:str):
        pass
    
    def queryExplicacao(self, id):
        pass
        
    def apagaTabelas(self, nomeTabela):
        pass