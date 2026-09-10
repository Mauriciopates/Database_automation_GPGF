-- Arquivo: esquema.sql
-- Criação da tabela para armazenamento dos dados de Cartão de Pagamento do Governo Federal (CPGF)

CREATE TABLE IF NOT EXISTS db_GPGF (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_unidade_gestora VARCHAR(20) NULL,
    nome_unidade_gestora VARCHAR(255) NULL,
    ano_extrato VARCHAR(10) NULL,
    mes_extrato VARCHAR(10) NULL,
    tipo_transacao VARCHAR(100) NULL,
    data_transacao VARCHAR(50) NULL,
    codigo_orgao VARCHAR(20) NULL,
    nome_orgao VARCHAR(255) NULL,
    cnpj_cpf_favorecido VARCHAR(50) NULL,
    descricao_transacao TEXT NULL,
    cpf_portador VARCHAR(30) NULL,
    nome_portador VARCHAR(255) NULL,
    valor_transacao DECIMAL(15, 2) NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;