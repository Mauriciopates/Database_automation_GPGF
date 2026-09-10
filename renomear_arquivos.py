import os


def renomear_arquivos(ano: int, download_dir: str):
    """
    Apaga o CSV original e renomeia o CSV corrigido para o nome original,
    para todos os meses do ano indicado.

    ano: ano a processar (ex: 2022)
    download_dir: caminho da pasta "Download" do projeto
    """
    base_dir = os.path.join(download_dir, str(ano))
    print(f"Ano configurado: {ano}\n")

    for mes in range(1, 13):
        mes_str = f"{mes:02d}"
        periodo = f"{ano}{mes_str}"
        pasta = os.path.join(base_dir, mes_str)

        original = os.path.join(pasta, f"{periodo}_CPGF.csv")
        corrigido = os.path.join(pasta, f"{periodo}_CPGF_corrigido.csv")

        if not os.path.exists(corrigido):
            print(f"[IGNORADO] Não existe o ficheiro corrigido: {corrigido}")
            continue

        try:
            if os.path.exists(original):
                os.remove(original)
                print(f"Apagado: {original}")

            os.rename(corrigido, original)
            print(f"Renomeado: {corrigido} -> {original}")

        except Exception as e:
            print(f"Erro no mês {mes_str}: {e}")

    print("\nRenomeação concluída!")


if __name__ == "__main__":
    ano_input = input("Digita o ano (ex: 2022): ").strip()
    download_dir_input = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "Download"
    )
    renomear_arquivos(int(ano_input), download_dir_input)
