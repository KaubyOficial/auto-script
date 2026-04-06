"""
Lê a planilha FLUXO DE PRODUÇÃO e retorna título e link de referência
para um dado número de roteiro (ex: F.001, F.012).

Uso:
    python ler_planilha.py F.001

Saída (JSON):
    {"numero": "F.001", "titulo": "Título do vídeo", "link_ref": "https://..."}

Colunas da planilha:
    A = link de referência
    B = título do vídeo
    I = número F.XXX
"""

import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api import get_sheets_service

SPREADSHEET_ID = "1Va8y2pNZeF0Zj_2pachpjIK0sh6esp46Cuped16kgkg"
SHEET_NAME = "FLUXO DE PRODUÇÃO"


def buscar_roteiro(numero):
    """Busca título e link pelo número F.XXX na coluna I."""
    sheets = get_sheets_service()

    # Lê colunas A, B e I de uma vez
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A:I"
    ).execute()

    rows = result.get("values", [])
    for i, row in enumerate(rows):
        # Coluna I = índice 8
        if len(row) > 8 and row[8].strip() == numero.strip():
            link_ref = row[0].strip() if len(row) > 0 else ""
            titulo = row[1].strip() if len(row) > 1 else ""
            return {
                "numero": numero,
                "titulo": titulo,
                "link_ref": link_ref,
                "linha": i + 1
            }

    return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python ler_planilha.py F.001", file=sys.stderr)
        sys.exit(1)

    numero = sys.argv[1]
    dados = buscar_roteiro(numero)

    if not dados:
        print(json.dumps({"erro": f"Número '{numero}' não encontrado na planilha"}))
        sys.exit(1)

    print(json.dumps(dados, ensure_ascii=False))


if __name__ == "__main__":
    main()
