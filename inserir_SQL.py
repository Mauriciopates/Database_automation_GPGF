import os
import pandas as pd
import pymysql
from tqdm import tqdm
from dotenv import load_dotenv



def trunc(v, tamanho):
    if v is None:
        return ""
    v = str(v)
    return v[:tamanho]


def to_valor(v):
    """Converte '40,60' -> 40.60 (trata vírgula decimal e separador de milhar)."""
    if v in (None, ""):
        return None
    return float(str(v).replace(".", "").replace(",", "."))


def garantir_estrutura_tabela(cursor, conn, tabela: str):
    """
    Verifica a estrutura real da tabela e ajusta automaticamente, sem
    precisar de correr SQL manual no Workbench nem depender do manutencao.py:
      - Remove identificador_registro (se existir)
      - Remove periodo_referencia (se existir)
      - Adiciona ano_extrato (se não existir)
      - Adiciona mes_extrato (se não existir)
    """
    cursor.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s;
        """,
        (tabela,),
    )
    colunas_atuais = [linha[0] for linha in cursor.fetchall()]

    def existe(col):
        return col in colunas_atuais

    if existe("identificador_registro"):
        print(
            "[ESTRUTURA] Removendo coluna obsoleta identificador_registro..."
        )
        cursor.execute(
            f"ALTER TABLE `{tabela}` DROP COLUMN identificador_registro;"
        )
        conn.commit()
        colunas_atuais.remove("identificador_registro")

    if existe("periodo_referencia"):
        print("[ESTRUTURA] Removendo coluna obsoleta periodo_referencia...")
        cursor.execute(
            f"ALTER TABLE `{tabela}` DROP COLUMN periodo_referencia;"
        )
        conn.commit()
        colunas_atuais.remove("periodo_referencia")

    if not existe("ano_extrato"):
        print("[ESTRUTURA] Adicionando coluna ano_extrato...")
        cursor.execute(
            f"ALTER TABLE `{tabela}` ADD COLUMN ano_extrato VARCHAR(10) NULL AFTER nome_unidade_gestora;"
        )
        conn.commit()
        colunas_atuais.append("ano_extrato")

    if not existe("mes_extrato"):
        print("[ESTRUTURA] Adicionando coluna mes_extrato...")
        cursor.execute(
            f"ALTER TABLE `{tabela}` ADD COLUMN mes_extrato VARCHAR(10) NULL AFTER ano_extrato;"
        )
        conn.commit()
        colunas_atuais.append("mes_extrato")


def importar_sql(
    ano: int,
    download_dir: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    tabela: str,
):
    """
    Lê os CSV já corrigidos do ano indicado e insere na tabela MySQL,
    mês a mês, sem duplicar (verifica por ano_extrato + mes_extrato antes de inserir).

    Antes de importar, garante sozinho que a tabela tem a estrutura certa
    (ano_extrato/mes_extrato em vez de identificador_registro/periodo_referencia),
    sem precisar de SQL manual nem do manutencao.py.
    """
    base_dir = os.path.join(download_dir, str(ano))
    print(f"Ano configurado: {ano}")
    print(f"Pasta base: {base_dir}\n")

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
    )
    cursor = conn.cursor()

    # ======================================
    # Garante que a tabela tem a estrutura certa antes de importar,
    # sem precisar de SQL manual nem do manutencao.py
    # ======================================
    garantir_estrutura_tabela(cursor, conn, tabela)

    sql = f"""
    INSERT INTO {tabela} (
        codigo_unidade_gestora, nome_unidade_gestora,
        ano_extrato,mes_extrato, tipo_transacao, data_transacao,
        codigo_orgao, nome_orgao,
        cnpj_cpf_favorecido, descricao_transacao,
        cpf_portador, nome_portador,
        valor_transacao
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    total_importado = 0

    for mes in range(1, 13):
        mes_str = f"{mes:02d}"
        periodo = f"{ano}{mes_str}"
        pasta = os.path.join(base_dir, mes_str)
        arquivo_csv = os.path.join(pasta, f"{periodo}_CPGF.csv")

        print("\n====================================")
        print(f"A importar: {arquivo_csv}")
        print("====================================")

        if not os.path.isfile(arquivo_csv):
            print("Ficheiro não encontrado. A ignorar.")
            continue

        # ======================================
        # TRAVA: verifica se este ano/mês já foi importado
        # ======================================
        cursor.execute(
            f"SELECT COUNT(*) FROM {tabela} WHERE ano_extrato = %s AND mes_extrato = %s;",
            (str(ano), mes_str),
        )
        ja_existe = cursor.fetchone()[0]  # type: ignore
        if ja_existe > 0:
            print(
                f"[PARADO] O período {ano}-{mes_str} já tem {ja_existe} registos na tabela. A ignorar."
            )
            continue

        try:
            df = pd.read_csv(
                arquivo_csv,
                sep=";",
                encoding="utf-8",
                dtype=str,
                low_memory=False,
            )
        except Exception as e:
            print(f"[ERRO] Não foi possível ler {arquivo_csv}: {e}")
            print(
                "       (provavelmente este mês ainda não passou pelo processo de correção)"
            )
            continue

        df = df.where(pd.notnull(df), None)

        # ======================================
        # REGRA DE ADAPTAÇÃO: garante que todas as colunas esperadas do CSV
        # existem, mesmo que venham faltando, fora de ordem, ou com nome
        # ligeiramente diferente. Colunas que não existirem são criadas
        # como vazias (None), em vez de travar linha a linha.
        # ======================================
        colunas_esperadas = [
            "codigo_orgao_superior",
            "nome_orgao_superior",
            "codigo_orgao_subordinado",
            "nome_orgao_subordinado",
            "codigo_unidade_gestora",
            "nome_unidade_gestora",
            "ano_extrato",
            "mes_extrato",
            "cpf_portador",
            "nome_portador",
            "cnpj_cpf_favorecido",
            "nome_favorecido",
            "tipo_transacao",
            "data_transacao",
            "valor_transacao",
        ]

        colunas_faltando = [
            c for c in colunas_esperadas if c not in df.columns
        ]
        if colunas_faltando:
            print(
                f"[ADAPTAÇÃO] Colunas não encontradas no CSV, serão tratadas como vazias: {colunas_faltando}"
            )
            for c in colunas_faltando:
                df[c] = None

        print(f"Total de registos: {len(df):,}")

        contador = 0
        lote = []
        erros = []

        for i, row in tqdm(
            df.iterrows(), total=len(df), desc=periodo, unit=" registos"
        ):
            try:
                descricao = (
                    f"{row['tipo_transacao']} - {row['nome_favorecido']}"
                )

                valores = (
                    trunc(
                        row["codigo_unidade_gestora"], 20
                    ),  # codigo_unidade_gestora
                    trunc(
                        row["nome_unidade_gestora"], 255
                    ),  # nome_unidade_gestora
                    trunc(row["ano_extrato"], 10),  # ano_extrato
                    trunc(row["mes_extrato"], 10),  # mes_extrato
                    trunc(row["tipo_transacao"], 100),  # tipo_transacao
                    trunc(row["data_transacao"], 50),  # data_transacao
                    trunc(row["codigo_orgao_subordinado"], 20),  # codigo_orgao
                    trunc(row["nome_orgao_subordinado"], 255),  # nome_orgao
                    trunc(
                        row["cnpj_cpf_favorecido"], 50
                    ),  # cnpj_cpf_favorecido
                    descricao,  # descricao_transacao
                    trunc(row["cpf_portador"], 30),  # cpf_portador
                    trunc(row["nome_portador"], 255),  # nome_portador
                    to_valor(row.get("valor_transacao")),  # valor_transacao
                )
                lote.append(valores)
            except Exception as e:
                erros.append((i, str(e)))
                continue

            if len(lote) >= 1000:
                cursor.executemany(sql, lote)
                conn.commit()
                contador += len(lote)
                total_importado += len(lote)
                lote = []

        if lote:
            cursor.executemany(sql, lote)
            conn.commit()
            contador += len(lote)
            total_importado += len(lote)

        print(f"Importados neste ficheiro: {contador:,}")
        if erros:
            print(f"Linhas com erro: {len(erros)}")
            with open(
                os.path.join(base_dir, "erros_import.log"),
                "a",
                encoding="utf-8",
            ) as f:
                for i, msg in erros:
                    f.write(f"{arquivo_csv} linha {i}: {msg}\n")

    cursor.close()
    conn.close()
    print(f"\nTOTAL IMPORTADO: {total_importado:,}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    # Carrega as variáveis de ambiente do ficheiro .env
    load_dotenv()

    ano_input = input("Digita o ano (ex: 2022): ").strip()
    download_dir_input = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "Download"
    )

    # Leitura dinâmica do .env protegida contra tipo None
    HOST = os.getenv("DB_HOST") or "3xr.ddns.net"
    PORT = int(os.getenv("DB_PORT") or 3306)
    USER = os.getenv("DB_USER") or "MauricioPates"
    PASSWORD = os.getenv("DB_PASSWORD") or ""
    DATABASE = os.getenv("DB_NAME") or "MauricioPates"
    TABELA = os.getenv("DB_TABLE") or "db_GPGF"

    importar_sql(
        int(ano_input),
        download_dir_input,
        HOST,
        PORT,
        USER,
        PASSWORD,
        DATABASE,
        TABELA,
    )