# Projeto CPGF - Processamento e Carga em MySQL

Este projeto realiza o download, tratamento, correção e importação automática dos dados do **Cartão de Pagamento do Governo Federal (CPGF)** obtidos através do Portal da Transparência do Governo Federal.


## Requisitos do Sistema

- **Python:** Versão **3.11** (Recomendada para total compatibilidade com os pacotes utilitários)
- **Base de Dados:** MySQL Server / MariaDB
- **Ambiente de Desenvolvimento:** VS Code ou qualquer IDE da sua preferência

---

## Alterações e Evolução do Projeto

- **Segurança de Dados (.env):** Credenciais da base de dados protegidas via `python-dotenv` para evitar exposição no repositório Git.
- **Estrutura de Base de Dados (`esquema.sql`):** Tabela padronizada para comportar colunas ajustadas em `snake_case` com tipos de dados otimizados (`DECIMAL`, `VARCHAR`, `TIMESTAMP`).
- **Automação Completa via Menu:** Criado `manutencao.py` como ponto centralizador do fluxo de trabalho.
- **Portabilidade:** Uso de caminhos relativos para execução em qualquer ambiente sem necessidade de alterar o código.
- **Performance de Inserção:** Substituição do loop linha a linha por inserções em lote (`executemany`) de 1.000 registos com barra de progresso (`tqdm`).
- **Prevenção de Duplicidade:** Verificação prévia por `ano_extrato` e `mes_extrato` antes de realizar a carga.

---

##  Esquema da Base de Dados (`esquema.sql`)

A estrutura da tabela é gerada a partir do arquivo `esquema.sql`:

```sql
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
```

---

##  Estrutura de Arquivos

CPGF/
├── .env                  # Credenciais locais reais (NÃO SUBIR PRO GIT)
├── .env.example          # Modelo seguro de variáveis de ambiente
├── .gitignore            # Regras para ignorar venv, logs, .env e temporários
├── esquema.sql           # Script DDL da tabela MySQL (db_GPGF)
├── manutencao.py         # Script principal / Menu de controle do projeto
├── correcao_csv.py       # Correção de cabeçalhos e snake_case
├── renomear_arquivos.py  # Padronização e exclusão de arquivos temporários
├── inserir_SQL.py        # Validação de colunas e importação em lote
└── Download/             # Diretório local para os arquivos baixados (Ano/Mês)

## Como executar o sistema

-- No windows:

1 -  Criar o ambiente virtual na pasta .venv
python -m venv .venv

2 - Ativar o ambiente virtual (PowerShell)
.\.venv\Scripts\Activate.ps1

3 -  Ativar o ambiente virtual (CMD)
.\.venv\Scripts\activate.bat

-- No Linux / macOS:
1 -  Criar o ambiente virtual
python3.11 -m venv .venv

2 - Ativar o ambiente virtual
source .venv/bin/activate

# Dependências
./venv/Scripts/python.exe -m pip install python-dotenv pandas pymysql tqdm requests 

ou se não tiver feito a criação do ambiente virtual (não orientado)

pip install pandas pymysql tqdm requests python-dotenv


# Configurar as Variáveis de Ambiente (.env)

Por razões de segurança, o arquivo .env contendo senhas e acessos não é enviado para o repositório. Deve configurá-lo manualmente a partir do modelo .env.example:

Faça uma cópia do arquivo .env.example e renomeie-a para .env:

Windows (PowerShell): copy .env.example .env

Linux/macOS ou Git Bash: cp .env.example .env

Abra o arquivo .env no seu editor de código e insira os dados de conexão da base de dados da nova máquina:

```
DB_HOST=ip_ou_host_do_servidor
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=seu_banco_de_dados
DB_TABLE=db_GPGF
```

## Executar o Projeto

python manutencao.py

## Manual 

Opções disponíveis no menu:

1 - Ver tabela: Exibe a contagem de linhas e uma amostra dos dados.

2 - Teste de conexão: Valida o acesso ao servidor MySQL configurado no .env.

3 - Exportar CSV: Baixa automaticamente os pacotes ZIP do Portal da Transparência do ano selecionado.

4 - Rodar processo de correção: Ajusta as colunas para o padrão do projeto e renomeia os ficheiros.

5 - Diagnóstico de um CSV: Analisa a codificação (encoding) e separador de um arquivo específico.

6 - Importar para o MySQL: Executa a carga dos ficheiros corrigidos para a tabela db_GPGF.

Mapeamento de Observações (Favorecidos)
Na coluna cnpj_cpf_favorecido:

CPF (11 dígitos) / CNPJ (14 dígitos): Favorecido identificado na transação.

-11: Informação protegida por Sigilo Bancário.

-1 / -2: Operações de saque em dinheiro ou sem favorecido aplicável.