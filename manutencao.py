"""
manutencao.py
Painel de controlo do projeto CPGF -> MySQL.

Este ficheiro contém TODA a configuração do projeto (caminhos, ano ativo,
credenciais da base de dados) e o menu que roda cada etapa do processo.
Os outros ficheiros (correcao_csv.py, renomear_arquivos.py, inserir_SQL.py)
só têm a lógica de cada etapa; recebem o ano/pasta/credenciais daqui.

Estrutura esperada do projeto:
    CPGF/
      manutencao.py       <- este ficheiro (configuração + menu)
      correcao_csv.py
      renomear_arquivos.py
      inserir_SQL.py
      Download/
        2022/
          01/202201_CPGF.csv
          02/...
        2023/
          01/...

Opções do menu:
1 - Ver tabela
2 - Teste de conexão
3 - Exportar CSV (baixar do Portal da Transparência)
4 - Rodar processo de correção (corrigir colunas + renomear ficheiros)
5 - Diagnóstico de um CSV
6 - Importar para o MySQL

Opções de modificação
7 - Limpar tabela no SQL
8 - Mudar ano ativo

0 - Sair
"""

import os
import zipfile
import requests
import pymysql
import pandas as pd
from dotenv import load_dotenv

from correcao_csv import corrigir_csv
from renomear_arquivos import renomear_arquivos
from inserir_SQL import importar_sql

# ======================================
# RAIZ DO PROJETO (funciona em qualquer PC)
# ======================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "Download")

# ======================================
# ANO ATIVO (pode ser mudado em runtime pela opção 8 do menu)
# ======================================
_ANO_ATUAL = 2022


def get_ano() -> int:
    """Devolve o ano atualmente ativo."""
    return _ANO_ATUAL


def set_ano(novo_ano: int) -> None:
    """Muda o ano ativo em tempo real (sem editar ficheiro)."""
    global _ANO_ATUAL
    _ANO_ATUAL = int(novo_ano)


def get_base_dir(ano: int = None) -> str:  # type: ignore
    """Devolve a pasta Download/{ano} do ano ativo (ou de um ano específico)."""
    ano_usado = ano if ano is not None else _ANO_ATUAL
    return os.path.join(DOWNLOAD_DIR, str(ano_usado))


def caminho_csv(mes: int, corrigido: bool = False, ano: int = None) -> str:  # type: ignore
    """Devolve o caminho completo do CSV de um mês (original ou corrigido)."""
    ano_usado = ano if ano is not None else _ANO_ATUAL
    periodo = f"{ano_usado}{mes:02d}"
    pasta = os.path.join(DOWNLOAD_DIR, str(ano_usado), f"{mes:02d}")
    sufixo = "_CPGF_corrigido.csv" if corrigido else "_CPGF.csv"
    return os.path.join(pasta, f"{periodo}{sufixo}")

# Carrega as variáveis do ficheiro .env
load_dotenv()

# ======================================
# BASE DE DADOS (Carregada via .env)
# ======================================
HOST = os.getenv("DB_HOST") or "3xr.ddns.net"
PORT = int(os.getenv("DB_PORT") or 3306)
USER = os.getenv("DB_USER") or "MauricioPates"
PASSWORD = os.getenv("DB_PASSWORD") or ""
DATABASE = os.getenv("DB_NAME") or "MauricioPates"
TABELA = os.getenv("DB_TABLE") or "db_GPGF"

def conectar():
    return pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset="utf8mb4",
    )

# ======================================
# 1 - Ver tabela
# ======================================
def ver_tabela():
    try:
        conn = conectar()
        cursor = conn.cursor()

        print(f"\n--- Estrutura da tabela `{TABELA}` ---")
        cursor.execute(f"DESCRIBE `{TABELA}`;")
        for linha in cursor.fetchall():
            print(linha)

        cursor.execute(f"SELECT COUNT(*) FROM `{TABELA}`;")
        total = cursor.fetchone()[0]  # type: ignore
        print(f"\nTotal de registos: {total:,}")

        if total > 0:
            print("\n--- Amostra (5 primeiras linhas) ---")
            cursor.execute(f"SELECT * FROM `{TABELA}` LIMIT 5;")
            for linha in cursor.fetchall():
                print(linha)

            cursor.execute(f"""
                SELECT ano_extrato, mes_extrato, cpf_portador, data_transacao, valor_transacao, COUNT(*) as qtd
                FROM `{TABELA}`
                GROUP BY ano_extrato, mes_extrato, cpf_portador, data_transacao, valor_transacao
                HAVING qtd > 1
                LIMIT 5;
            """)
            duplicados = cursor.fetchall()
            if duplicados:
                print(
                    f"\n[ATENÇÃO] Encontrados registos possivelmente duplicados, exemplos: {duplicados}"
                )
            else:
                print("\nSem duplicados detetados (por ano/mês/portador/data/valor).")

        conn.close()

    except Exception as e:
        print(f"[ERRO] Não foi possível consultar a tabela: {e}")


# ======================================
# 2 - Teste de conexão
# ======================================
def teste_conexao():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tabelas = cursor.fetchall()
        conn.close()
        print("Ligação OK!")
        print("Tabelas encontradas:", tabelas)
    except Exception as e:
        print(f"[ERRO] Falha na ligação: {e}")


# ======================================
# 3 - Exportar CSV
# ======================================
def exportar_csv():
    """
    Pergunta o ano e descarrega os ZIP de CPGF de Janeiro a Dezembro,
    extraindo para CPGF/Download/{ano}/{mes}/ e apagando o ZIP depois.
    """
    ano = input("Digita o ano que queres exportar (ex: 2022): ").strip()

    if not ano.isdigit() or len(ano) != 4:
        print("[ERRO] Ano inválido. Usa o formato 2022, 2023, etc.")
        return

    pasta_raiz = os.path.join(DOWNLOAD_DIR, ano)
    os.makedirs(pasta_raiz, exist_ok=True)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"\nExportando ano {ano} para: {pasta_raiz}\n")

    for mes in range(1, 13):
        mes_str = f"{mes:02d}"
        pasta_mes = os.path.join(pasta_raiz, mes_str)
        os.makedirs(pasta_mes, exist_ok=True)

        url = f"https://portaldatransparencia.gov.br/download-de-dados/cpgf/{ano}{mes_str}"
        caminho_zip = os.path.join(pasta_mes, f"CPGF_{ano}{mes_str}.zip")

        print(f"--- Processando mês {mes_str}/{ano} ---")

        try:
            print("Baixando arquivo...")
            response = requests.get(url, headers=headers, stream=True)

            if response.status_code == 200:
                with open(caminho_zip, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                print("OK - Download concluído.")

                print(f"Extraindo arquivos em: {pasta_mes}")
                with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
                    zip_ref.extractall(pasta_mes)
                print("OK - Extração concluída.")

                os.remove(caminho_zip)
                print("OK - Arquivo ZIP removido.\n")

            else:
                print(
                    f"[ERRO] Código {response.status_code} ao baixar o mês {mes_str}\n"
                )

        except Exception as e:
            print(f"[ERRO] Falha no processamento do mês {mes_str}: {e}\n")

    print("Exportação concluída! Estrutura de pastas pronta em:", pasta_raiz)

    tornar_ativo = (
        input(f"\nQueres tornar {ano} o ano ativo agora? (s/n): ").strip().lower()
    )
    if tornar_ativo == "s":
        set_ano(int(ano))
        print(f"Ano ativo agora é {ano}.")


# ======================================
# 4 - Rodar processo de correção
# ======================================
def processo_correcao():
    ano = get_ano()
    print(f"\n=== RODANDO PROCESSO DE CORREÇÃO PARA O ANO {ano} ===\n")

    print("--- ETAPA 1/2: Corrigir CSV (renomear colunas) ---")
    corrigir_csv(ano, DOWNLOAD_DIR)

    print("\n--- ETAPA 2/2: Aplicar correção (renomear ficheiros) ---")
    renomear_arquivos(ano, DOWNLOAD_DIR)

    print("\n=== PROCESSO DE CORREÇÃO FINALIZADO ===")
    print("Os CSV já estão prontos. Usa a opção 6 para importar para o MySQL.")


# ======================================
# 5 - Diagnóstico de um CSV
# ======================================
def diagnostico_csv():
    caminho = input(
        f"Cola o caminho completo do CSV (ENTER para usar janeiro de {get_ano()}): "
    ).strip()

    if not caminho:
        caminho = caminho_csv(1)

    if not os.path.isfile(caminho):
        print(f"[ERRO] Ficheiro não encontrado: {caminho}")
        return

    df = None
    for encoding in ("utf-8", "latin1", "cp1252"):
        for sep in (";", ","):
            try:
                teste = pd.read_csv(
                    caminho, sep=sep, encoding=encoding, dtype=str, nrows=5
                )
                if len(teste.columns) > 1:
                    df = teste
                    print(f"OK -> encoding={encoding} | separador='{sep}'")
                    break
            except Exception:
                pass
        if df is not None:
            break

    if df is None:
        print("Não foi possível ler o ficheiro com nenhuma combinação testada.")
        return

    print("\nColunas encontradas:")
    for c in df.columns:
        print(f"  - {c}")

    print("\nPrimeiras linhas:")
    print(df.head(3).to_string())


# ======================================
# 6 - Importar para o MySQL
# ======================================
def rodar_importar_sql():
    importar_sql(get_ano(), DOWNLOAD_DIR, HOST, PORT, USER, PASSWORD, DATABASE, TABELA)


# ======================================
# 7 - Limpar tabela
# ======================================
def limpar_tabela():
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM `{TABELA}`;")
        total = cursor.fetchone()[0]  # type: ignore

        if total == 0:
            print("A tabela já está vazia. Nada a fazer.")
            conn.close()
            return

        print(f"\n[ATENÇÃO] A tabela `{TABELA}` tem {total:,} registos.")
        confirmacao = input(
            "Digita CONFIRMAR para apagar tudo (irreversível): "
        ).strip()

        if confirmacao != "CONFIRMAR":
            print("Operação cancelada.")
            conn.close()
            return

        cursor.execute(f"TRUNCATE TABLE `{TABELA}`;")
        conn.commit()

        cursor.execute(f"SELECT COUNT(*) FROM `{TABELA}`;")
        print(f"Total depois de limpar: {cursor.fetchone()}")

        conn.close()

    except Exception as e:
        print(f"[ERRO] Não foi possível limpar a tabela: {e}")


# ======================================
# 8 - Mudar ano ativo
# ======================================
def mudar_ano():
    print(f"\nAno ativo atualmente: {get_ano()}")
    novo = input("Digita o novo ano (ex: 2023): ").strip()

    if not novo.isdigit() or len(novo) != 4:
        print("[ERRO] Ano inválido. Usa o formato 2022, 2023, etc.")
        return

    pasta = get_base_dir(int(novo))
    if not os.path.isdir(pasta):
        print(f"[ATENÇÃO] A pasta {pasta} ainda não existe.")
        confirmar = (
            input(
                "Queres mudar o ano ativo mesmo assim (para depois usar a opção 3 - Exportar)? (s/n): "
            )
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Operação cancelada.")
            return

    set_ano(int(novo))
    print(f"Ano ativo agora é: {get_ano()}")


# ======================================
# MENU
# ======================================
def menu():
    while True:
        print("\n========== MANUTENÇÃO CPGF ==========")
        print(f"Ano ativo: {get_ano()}")
        print(f"Pasta base: {get_base_dir()}")
        print("--------------------------------------")
        print("1 - Ver tabela")
        print("2 - Teste de conexão")
        print("3 - Exportar CSV (baixar do Portal da Transparência)")
        print("4 - Rodar processo de correção (corrigir + renomear)")
        print("5 - Diagnóstico de um CSV")
        print("6 - Importar para o MySQL")
        print("--------------------------------------")
        print("Opções de modificação")
        print("7 - Limpar tabela no SQL")
        print("8 - Mudar ano ativo")
        print("--------------------------------------")
        print("0 - Sair")
        print("======================================")

        opcao = input("Escolhe uma opção: ").strip()

        if opcao == "1":
            ver_tabela()
        elif opcao == "2":
            teste_conexao()
        elif opcao == "3":
            exportar_csv()
        elif opcao == "4":
            processo_correcao()
        elif opcao == "5":
            diagnostico_csv()
        elif opcao == "6":
            rodar_importar_sql()
        elif opcao == "7":
            limpar_tabela()
        elif opcao == "8":
            mudar_ano()
        elif opcao == "0":
            print("Até já!")
            break
        else:
            print("Opção inválida, tenta de novo.")


if __name__ == "__main__":
    menu()