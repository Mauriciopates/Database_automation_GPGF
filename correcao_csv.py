import os
import pandas as pd

RENOMEAR = {
    "CÓDIGO ÓRGÃO SUPERIOR": "codigo_orgao_superior",
    "NOME ÓRGÃO SUPERIOR": "nome_orgao_superior",
    "CÓDIGO ÓRGÃO": "codigo_orgao_subordinado",
    "NOME ÓRGÃO": "nome_orgao_subordinado",
    "CÓDIGO UNIDADE GESTORA": "codigo_unidade_gestora",
    "NOME UNIDADE GESTORA": "nome_unidade_gestora",
    "ANO EXTRATO": "ano_extrato",
    "MÊS EXTRATO": "mes_extrato",
    "CPF PORTADOR": "cpf_portador",
    "NOME PORTADOR": "nome_portador",
    "TRANSAÇÃO": "tipo_transacao",
    "DATA TRANSAÇÃO": "data_transacao",
    "CNPJ OU CPF FAVORECIDO": "cnpj_cpf_favorecido",
    "NOME FAVORECIDO": "nome_favorecido",    
    "VALOR TRANSAÇÃO": "valor_transacao",
}


def corrigir_csv(ano: int, download_dir: str):
    """
    Lê o CSV bruto de cada mês do ano indicado e grava uma versão
    com colunas em snake_case (sufixo _corrigido.csv).

    ano: ano a processar (ex: 2022)
    download_dir: caminho da pasta "Download" do projeto
    """
    base_dir = os.path.join(download_dir, str(ano))
    print(f"Ano configurado: {ano}")
    print(f"Pasta base: {base_dir}\n")

    for mes in range(1, 13): #inseri do mês 1 ao 12
        mes_str = f"{mes:02d}"
        periodo = f"{ano}{mes_str}"
        pasta = os.path.join(base_dir, mes_str)

        entrada = os.path.join(pasta, f"{periodo}_CPGF.csv")
        saida = os.path.join(pasta, f"{periodo}_CPGF_corrigido.csv")

        if not os.path.isfile(entrada):
            print(f"[IGNORADO] Não encontrado: {entrada}")
            continue

        print(f"Lendo {entrada}")

        try:
            df = pd.read_csv(entrada, sep=";", encoding="latin1", dtype=str, low_memory=False)
        except Exception as e:
            print(f"  [ERRO] Não foi possível ler o ficheiro: {e}")
            continue

        faltando = [c for c in RENOMEAR if c not in df.columns]
        if faltando:
            print(f"  [ATENÇÃO] Colunas não encontradas: {faltando}")
            continue

        df.rename(columns=RENOMEAR, inplace=True)

        df.to_csv(saida, sep=";", index=False, encoding="utf-8")
        print(f"  ✔ Criado: {saida}")

    print("\nCorreção de CSV concluída!")


if __name__ == "__main__":
    ano_input = input("Digita o ano a corrigir (ex: 2022): ").strip()
    download_dir_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Download")
    corrigir_csv(int(ano_input), download_dir_input)