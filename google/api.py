"""
Módulo compartilhado de acesso à Google API.
Usado por exportar.py (Story 1.3) e traduzir.py (Story 1.4).
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# credentials/ permanece na raiz do projeto (um nível acima de google/)
_DEFAULT_CREDENTIALS = os.path.join(_BASE_DIR, "..", "credentials", "rede-f-credentials.json")


def get_credentials(credentials_path=None):
    path = credentials_path or _DEFAULT_CREDENTIALS
    return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)


def get_docs_service(credentials_path=None):
    return build("docs", "v1", credentials=get_credentials(credentials_path))


def get_drive_service(credentials_path=None):
    return build("drive", "v3", credentials=get_credentials(credentials_path))


def get_sheets_service(credentials_path=None):
    return build("sheets", "v4", credentials=get_credentials(credentials_path))


# ── Google Docs ──────────────────────────────────────────────────────────────

def create_doc(title, folder_id, credentials_path=None):
    """Cria um Google Doc vazio e o move para a pasta especificada."""
    drive = get_drive_service(credentials_path)
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    doc = drive.files().create(body=file_metadata, fields="id,webViewLink,name").execute()
    return doc


def get_doc_text(doc_id, credentials_path=None):
    """Retorna o texto completo de um Google Doc."""
    docs = get_docs_service(credentials_path)
    document = docs.documents().get(documentId=doc_id).execute()
    return _extract_text(document)


def _extract_text(document):
    text_parts = []
    body = document.get("body", {})
    for element in body.get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for pe in paragraph.get("elements", []):
                t = pe.get("textRun", {}).get("content", "")
                text_parts.append(t)
    return "".join(text_parts)


def insert_text_into_doc(doc_id, text, credentials_path=None):
    """Insere texto em um Google Doc (substitui conteúdo vazio inicial)."""
    docs = get_docs_service(credentials_path)
    requests = [{"insertText": {"location": {"index": 1}, "text": text}}]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def append_text_to_doc(doc_id, text, credentials_path=None):
    """Adiciona texto ao final de um Google Doc."""
    docs = get_docs_service(credentials_path)
    # Get current end index
    document = docs.documents().get(documentId=doc_id).execute()
    body = document.get("body", {})
    content = body.get("content", [])
    end_index = content[-1].get("endIndex", 1) - 1 if content else 1
    if end_index < 1:
        end_index = 1
    requests = [{"insertText": {"location": {"index": end_index}, "text": text}}]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


# ── Google Drive ─────────────────────────────────────────────────────────────

def create_folder(name, parent_folder_id, credentials_path=None):
    """Cria uma subpasta no Drive."""
    drive = get_drive_service(credentials_path)
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    folder = drive.files().create(body=file_metadata, fields="id,webViewLink,name").execute()
    return folder


def move_file_to_folder(file_id, new_folder_id, credentials_path=None):
    """Move um arquivo para outra pasta no Drive."""
    drive = get_drive_service(credentials_path)
    # Get current parents
    file = drive.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    drive.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()


def get_doc_id_from_link(link):
    """Extrai o ID do documento de um link do Google Docs."""
    import re
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", link)
    if match:
        return match.group(1)
    raise ValueError(f"Não foi possível extrair ID do link: {link}")


# ── Google Sheets ─────────────────────────────────────────────────────────────

def find_row_by_title(spreadsheet_id, sheet_name, title, col_letter="I", credentials_path=None):
    """Busca o número da linha onde col_letter = title. Retorna None se não encontrar."""
    sheets = get_sheets_service(credentials_path)
    col_range = f"'{sheet_name}'!{col_letter}:{col_letter}"
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=col_range
    ).execute()
    values = result.get("values", [])
    for i, row in enumerate(values):
        if row and row[0] == title:
            return i + 1  # 1-indexed
    return None


def update_cell(spreadsheet_id, sheet_name, cell, value, credentials_path=None):
    """Atualiza uma célula (valor USER_ENTERED, suporta fórmulas =HIPERLINK())."""
    sheets = get_sheets_service(credentials_path)
    range_notation = f"'{sheet_name}'!{cell}"
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_notation,
        valueInputOption="USER_ENTERED",
        body={"values": [[value]]},
    ).execute()


def hyperlink_formula(url, label):
    return f'=HIPERLINK("{url}";"{label}")'
