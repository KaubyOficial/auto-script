"""
Story 1.4 — Pipeline de Tradução (substitui Make.com)

Uso:
    python traduzir.py <doc_id_ou_link> [--linha N] [--idiomas AL,HL,IT,ES,FR,PT,EN]

Exemplos:
    python traduzir.py 1BxYz_abcDEFGHIJKLMNO
    python traduzir.py "https://docs.google.com/document/d/1BxYz.../edit"
    python traduzir.py 1BxYz... --idiomas AL,EN
    python traduzir.py 1BxYz... --linha 5

O script replica exatamente o Make.com:
1. Lê o Google Doc com o roteiro final (já refinado manualmente)
2. Divide em capítulos pelo marcador *
3. Cria subpasta no Drive com o nome do vídeo
4. Para cada idioma:
   - Cria Google Doc vazio (NomeTítuloAL, NomeTítuloHL, etc.)
   - Traduz capítulo por capítulo via OpenAI Assistant
   - Appenda cada capítulo traduzido + * ao doc
   - Aguarda 15s entre capítulos
5. Atualiza Google Sheets:
   - Colunas J-P: links dos docs traduzidos
   - Coluna C: SIM
   - Coluna I: link do doc original
6. Move doc original para a subpasta
"""

import os
import sys
import json
import time
import argparse

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_api import (
    create_doc,
    get_doc_text,
    append_text_to_doc,
    create_folder,
    move_file_to_folder,
    get_doc_id_from_link,
    find_row_by_title,
    update_cell,
    hyperlink_formula,
)
from openai_assistants import translate_all_chapters
from divisor import (
    calculate_split_positions,
    apply_double_markers,
    build_text_from_chapters,
    apply_split_positions_to_translated,
)

# ── Config ────────────────────────────────────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CREDENTIALS_PATH = os.path.join(_BASE_DIR, CONFIG["drive"]["credentials_path"])
ROOT_FOLDER_ID = CONFIG["drive"]["root_folder_id"]
SPREADSHEET_ID = CONFIG["sheets"]["spreadsheet_id"]
SHEET_NAME = CONFIG["sheets"]["sheet_name"]
COL_TITLE = CONFIG["sheets"]["col_title"]
COL_STATUS = CONFIG["sheets"]["col_status"]
COL_ORIGINAL = CONFIG["sheets"]["col_original_doc"]
LANGUAGES = CONFIG["languages"]
SLEEP_CHAPTERS = CONFIG["sleep_between_chapters_sec"]
SLEEP_LANGS = CONFIG["sleep_between_languages_sec"]


# ── Core ──────────────────────────────────────────────────────────────────────

def split_chapters(text):
    """Divide o roteiro em capítulos pelo marcador *. Retorna apenas capítulos com conteúdo."""
    chapters = text.split("*")
    return [c for c in chapters if c.strip()]


def run_pipeline(doc_id, row_number=None, idiomas_filter=None):
    print("=" * 60)
    print("PIPELINE DE TRADUÇÃO — REDE FINANÇAS")
    print("=" * 60)

    # ── 1. Lê o doc original ──────────────────────────────────────────────
    print(f"\n[1/6] Lendo Google Doc: {doc_id}")
    text = get_doc_text(doc_id, CREDENTIALS_PATH)

    # Pega o título via API Drive
    from google_api import get_drive_service
    drive = get_drive_service(CREDENTIALS_PATH)
    file_meta = drive.files().get(fileId=doc_id, fields="id,name,webViewLink,parents").execute()
    doc_title = file_meta["name"]
    doc_link = file_meta["webViewLink"]
    print(f"Título: {doc_title}")

    # ── 2. Divide em capítulos e calcula posições de ** ──────────────────
    chapters = split_chapters(text)
    print(f"\n[2/6] Capítulos encontrados: {len(chapters)}")
    if not chapters:
        print("ERRO: nenhum capítulo encontrado. O roteiro deve ter * entre capítulos.")
        sys.exit(1)

    # Calcula onde inserir ** para dividir em 3 partes iguais
    split_positions = calculate_split_positions(chapters, num_parts=3)
    if split_positions:
        print(f"Divisões automáticas (**) após capítulos: {[p+1 for p in split_positions]}")
    else:
        print("Aviso: poucos capítulos para dividir em 3 partes.")

    # ── 3. Cria subpasta no Drive ─────────────────────────────────────────
    print(f"\n[3/6] Criando subpasta '{doc_title}' no Drive...")
    subfolder = create_folder(doc_title, ROOT_FOLDER_ID, CREDENTIALS_PATH)
    subfolder_id = subfolder["id"]
    print(f"Subpasta criada: {subfolder['webViewLink']}")

    # ── 4. Encontra linha na planilha ─────────────────────────────────────
    if row_number is None:
        print(f"\n[4/6] Buscando linha na planilha para '{doc_title}'...")
        row_number = find_row_by_title(SPREADSHEET_ID, SHEET_NAME, doc_title, COL_TITLE, CREDENTIALS_PATH)
        if row_number is None:
            print(f"AVISO: linha não encontrada na coluna {COL_TITLE}. Planilha não será atualizada.")
        else:
            print(f"Linha encontrada: {row_number}")
    else:
        print(f"\n[4/6] Usando linha fornecida: {row_number}")

    # ── 5. Traduz para cada idioma ────────────────────────────────────────
    print(f"\n[5/6] Iniciando traduções...")
    langs_to_process = LANGUAGES
    if idiomas_filter:
        suffixes = [s.strip().upper() for s in idiomas_filter.split(",")]
        langs_to_process = [l for l in LANGUAGES if l["suffix"] in suffixes]
        print(f"Idiomas selecionados: {[l['suffix'] for l in langs_to_process]}")

    created_docs = {}

    for i, lang in enumerate(langs_to_process, 1):
        suffix = lang["suffix"]
        assistant_id = lang["assistant_id"]
        sheet_col = lang["sheet_col"]

        print(f"\n  [{i}/{len(langs_to_process)}] Traduzindo para {suffix}...")

        # Cria Google Doc vazio para este idioma
        doc_name = f"{doc_title}{suffix}"
        translated_doc = create_doc(doc_name, subfolder_id, CREDENTIALS_PATH)
        t_doc_id = translated_doc["id"]
        t_doc_link = translated_doc["webViewLink"]
        print(f"  Doc criado: {doc_name}")

        # Traduz capítulos (apenas capítulos com conteúdo)
        translated_chapters = translate_all_chapters(
            chapters, assistant_id, SLEEP_CHAPTERS, suffix
        )

        # Aplica as mesmas posições de ** à tradução
        translated_with_markers = apply_split_positions_to_translated(
            translated_chapters, split_positions
        )

        # Monta o texto final com * entre capítulos (vazios criam **)
        full_translation = build_text_from_chapters(translated_with_markers)

        # Appenda ao Google Doc
        print(f"  Gravando no Google Doc...")
        append_text_to_doc(t_doc_id, full_translation, CREDENTIALS_PATH)

        created_docs[suffix] = {"id": t_doc_id, "link": t_doc_link, "name": doc_name}

        # Atualiza planilha
        if row_number:
            formula = hyperlink_formula(t_doc_link, doc_name)
            update_cell(SPREADSHEET_ID, SHEET_NAME, f"{sheet_col}{row_number}", formula, CREDENTIALS_PATH)
            print(f"  Planilha atualizada: coluna {sheet_col}")

        # Sleep entre idiomas (exceto após o último)
        if i < len(langs_to_process):
            print(f"  Aguardando {SLEEP_LANGS}s antes do próximo idioma...")
            time.sleep(SLEEP_LANGS)

    # ── 6. Finaliza planilha e move doc original ──────────────────────────
    print(f"\n[6/6] Finalizando...")

    if row_number:
        # Coluna C = SIM
        update_cell(SPREADSHEET_ID, SHEET_NAME, f"{COL_STATUS}{row_number}", "SIM", CREDENTIALS_PATH)
        print(f"  Planilha: coluna C{row_number} = SIM")

        # Coluna I = link do doc original
        formula_original = hyperlink_formula(doc_link, doc_title)
        update_cell(SPREADSHEET_ID, SHEET_NAME, f"{COL_ORIGINAL}{row_number}", formula_original, CREDENTIALS_PATH)
        print(f"  Planilha: coluna I{row_number} = link original")

    # Move doc original para subpasta
    print(f"  Movendo doc original para subpasta...")
    move_file_to_folder(doc_id, subfolder_id, CREDENTIALS_PATH)
    print(f"  Doc original movido.")

    # ── Resumo ────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("PIPELINE CONCLUÍDO")
    print(f"Vídeo: {doc_title}")
    print(f"Subpasta: {subfolder['webViewLink']}")
    print()
    print("Docs traduzidos:")
    for suffix, info in created_docs.items():
        print(f"  {suffix}: {info['link']}")
    print("=" * 60)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de tradução Rede Finanças (substitui Make.com)"
    )
    parser.add_argument(
        "doc",
        help="ID do Google Doc ou link completo do doc com o roteiro final"
    )
    parser.add_argument(
        "--linha",
        type=int,
        default=None,
        help="Número da linha na planilha (se não informado, busca automaticamente)"
    )
    parser.add_argument(
        "--idiomas",
        default=None,
        help="Idiomas a traduzir separados por vírgula (ex: AL,EN). Padrão: todos"
    )
    args = parser.parse_args()

    # Aceita link completo ou ID direto
    doc_input = args.doc.strip()
    if doc_input.startswith("http"):
        doc_id = get_doc_id_from_link(doc_input)
    else:
        doc_id = doc_input

    run_pipeline(doc_id, row_number=args.linha, idiomas_filter=args.idiomas)


if __name__ == "__main__":
    main()
