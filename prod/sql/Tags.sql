-- Criar tabela

CREATE TABLE Tags (
    Id INT NOT NULL PRIMARY KEY,  
    Name VARCHAR(100) NOT NULL                 
);

-- Inserir registros. Obs.: os registros com ids 20 e 28 estão em duplicidade.

INSERT INTO Tags (Id, Name)
VALUES (1, N'financeiro');
INSERT INTO Tags (Id, Name)
VALUES (2, N'investimento');
INSERT INTO Tags (Id, Name)
VALUES (3, N'contrato');
INSERT INTO Tags (Id, Name)
VALUES (4, N'gestão');
INSERT INTO Tags (Id, Name)
VALUES (5, N'administrativo');
INSERT INTO Tags (Id, Name)
VALUES (6, N'estatística');
INSERT INTO Tags (Id, Name)
VALUES (7, N'planejamento');
INSERT INTO Tags (Id, Name)
VALUES (8, N'pesquisa');
INSERT INTO Tags (Id, Name)
VALUES (9, N'cadastro');
INSERT INTO Tags (Id, Name)
VALUES (10, N'cotação');
INSERT INTO Tags (Id, Name)
VALUES (11, N'orçamento');
INSERT INTO Tags (Id, Name)
VALUES (12, N'ranking');
INSERT INTO Tags (Id, Name)
VALUES (13, N'relatório');
INSERT INTO Tags (Id, Name)
VALUES (14, N'boletim');
INSERT INTO Tags (Id, Name)
VALUES (15, N'taxa');
INSERT INTO Tags (Id, Name)
VALUES (16, N'previsão');
INSERT INTO Tags (Id, Name)
VALUES (17, N'saúde');
INSERT INTO Tags (Id, Name)
VALUES (18, N'política');
INSERT INTO Tags (Id, Name)
VALUES (19, N'projeto');
INSERT INTO Tags (Id, Name)
VALUES (20, N'consulta');
INSERT INTO Tags (Id, Name)
VALUES (21, N'fornecedor');
INSERT INTO Tags (Id, Name)
VALUES (22, N'localidade');
INSERT INTO Tags (Id, Name)
VALUES (23, N'prazo');
INSERT INTO Tags (Id, Name)
VALUES (24, N'ramo');
INSERT INTO Tags (Id, Name)
VALUES (25, N'ocorrência');
INSERT INTO Tags (Id, Name)
VALUES (26, N'licitação');
INSERT INTO Tags (Id, Name)
VALUES (27, N'serviços');
INSERT INTO Tags (Id, Name)
VALUES (28, N'consulta');
INSERT INTO Tags (Id, Name)
VALUES (29, N'votação');
INSERT INTO Tags (Id, Name)
VALUES (30, N'viagem');
INSERT INTO Tags (Id, Name)
VALUES (31, N'clima');
INSERT INTO Tags (Id, Name)
VALUES (32, N'tarifa');
INSERT INTO Tags (Id, Name)
VALUES (33, N'processo');
INSERT INTO Tags (Id, Name)
VALUES (34, N'Previdência Social');
INSERT INTO Tags (Id, Name)
VALUES (35, N'geografia');
INSERT INTO Tags (Id, Name)
VALUES (36, N'processamento');