-- Comando para criar a tabela

CREATE TABLE [Instituições] (
    Id INT NOT NULL PRIMARY KEY, 
    Name VARCHAR(100) NOT NULL,          
    Acronym VARCHAR(10) NOT NULL            
);

-- Comandos para inserir os registros.

INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (1, 
        N'Sistema de Informações dos Regimes Públicos de Previdência Social', 
        N'CADPREV');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (2, 
        N'Instituto Brasilieiro de Geografia e Estatística', 
        N'IBGE');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (3, 
        N'Agência Nacional de Saúde', 
        N'ANS');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (4, 
        N'Instituto de Pesquisa Econômica Aplicada', 
        N'IPEA');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (5, 
        N'Banco Central do Brasil', 
        N'BACEN');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (6, 
        N'Ministério da Fazenda', 
        N'MF');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (7, 
        N'Ministério da Saúde', 
        N'MS');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (8, 
        N'Instituto Nacional de Pesquisas Espaciais', 
        N'INPE');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (9, 
        N'Ministério da Economia', 
        N'ME');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (10, 
        N'Ministério da Cultura', 
        N'MinC');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (11, 
        N'Câmara dos Deputados', 
        N'CD');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (12, 
        N'Controladoria-Geral da União', 
        N'CGU');
INSERT INTO [Instituições] (Id, Name, Acronym)
VALUES (13, 
        N'Senado Federal', 
        N'SF');