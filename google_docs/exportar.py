"""
Story 1.3 — Export Automático para Google Docs

Uso:
    python exportar.py <arquivo_roteiro.txt> [--titulo "Título do Vídeo"]

Exemplo:
    python exportar.py ../roteiros/meu_roteiro.txt
    python exportar.py ../roteiros/meu_roteiro.txt --titulo "Como Investir em 2025"

O script:
1. Lê o arquivo .txt do roteiro (com * entre capítulos)
2. Cria um Google Doc na pasta raiz do Drive da Rede F
3. Insere o conteúdo preservando os marcadores *
4. Exibe o link do documento criado
"""

import os
import sys
import argparse

# Adiciona o diretório pai ao path para importar google_api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_api import create_doc, insert_text_into_doc

# ID da pasta raiz no Drive (Rede F)
DRIVE_ROOT_FOLDER_ID = "1sydZsMMxhmrSsck4Hmxmwn8zpY6v9rY2"


def exportar_roteiro(arquivo_txt, titulo=None):
    # Lê o roteiro
    with open(arquivo_txt, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Define o título
    if not titulo:
        basename = os.path.basename(arquivo_txt)
        titulo = os.path.splitext(basename)[0]
        # Remove prefixo "referencia_" se existir
        if titulo.startswith("referencia_"):
            titulo = titulo[len("referencia_"):]

    print(f"Exportando roteiro: '{titulo}'")
    print(f"Arquivo: {arquivo_txt}")
    print(f"Pasta Drive: {DRIVE_ROOT_FOLDER_ID}")
    print()

    # Cria o Google Doc
    print("Criando Google Doc...")
    doc = create_doc(titulo, DRIVE_ROOT_FOLDER_ID)
    doc_id = doc["id"]
    doc_link = doc["webViewLink"]
    print(f"Doc criado: {doc_link}")

    # Insere o conteúdo
    print("Inserindo conteúdo...")
    insert_text_into_doc(doc_id, conteudo)
    print("Conteúdo inserido com sucesso.")

    print()
    print("=" * 60)
    print(f"EXPORTADO COM SUCESSO")
    print(f"Título: {titulo}")
    print(f"Link: {doc_link}")
    print(f"ID:   {doc_id}")
    print("=" * 60)

    return {"id": doc_id, "link": doc_link, "titulo": titulo}


def main():
    parser = argparse.ArgumentParser(
        description="Exporta roteiro .txt para Google Docs"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo .txt do roteiro")
    parser.add_argument("--titulo", help="Título do Google Doc (padrão: nome do arquivo)")
    args = parser.parse_args()

    if not os.path.exists(args.arquivo):
        print(f"Erro: arquivo não encontrado: {args.arquivo}")
        sys.exit(1)

    exportar_roteiro(args.arquivo, args.titulo)


if __name__ == "__main__":
    main()
