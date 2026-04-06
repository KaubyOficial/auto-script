"""
transcrever.py — Transcrição automática de vídeo de referência
Story 1.1 | Epic 1 — Automação de Produção de Conteúdo (Rede Finanças)

Uso:
    python transcrever.py <URL_YOUTUBE>
    python transcrever.py <URL_YOUTUBE> --idioma en
    python transcrever.py <URL_YOUTUBE> --output meu_arquivo.txt
"""

import subprocess
import sys
import re
import json
import os
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "referencias"


def get_video_info(url: str) -> dict:
    """Busca metadados do vídeo (título, idioma das legendas disponíveis)."""
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp",
         "--skip-download", "--dump-json", "--no-warnings", url],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"Erro ao buscar info do vídeo: {result.stderr.strip()}")
        sys.exit(1)
    return json.loads(result.stdout)


def find_best_subtitle(info: dict, preferred_lang: str = None) -> tuple:
    """
    Determina a melhor legenda disponível.
    Prioridade: manual > automática, idioma preferido > idioma original.
    Retorna (lang_code, tipo) onde tipo é 'manual' ou 'auto'.
    """
    manual_subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}

    # Se idioma preferido foi especificado
    if preferred_lang:
        if preferred_lang in manual_subs:
            return preferred_lang, "manual"
        if preferred_lang in auto_subs:
            return preferred_lang, "auto"
        # Tenta variações (ex: "en" pode estar como "en-US")
        for key in manual_subs:
            if key.startswith(preferred_lang):
                return key, "manual"
        for key in auto_subs:
            if key.startswith(preferred_lang) and "-" not in key.split(preferred_lang, 1)[-1][:1]:
                return key, "auto"

    # Detecta idioma original do vídeo
    original_lang = info.get("language") or "en"

    # Prioridade 1: legenda manual no idioma original
    if original_lang in manual_subs:
        return original_lang, "manual"

    # Prioridade 2: qualquer legenda manual
    if manual_subs:
        lang = list(manual_subs.keys())[0]
        return lang, "manual"

    # Prioridade 3: legenda automática no idioma original
    if original_lang in auto_subs:
        return original_lang, "auto"

    # Prioridade 4: legenda automática em inglês
    if "en" in auto_subs:
        return "en", "auto"

    # Sem legendas
    return None, None


def download_subtitle(url: str, lang: str, sub_type: str) -> str:
    """Baixa legenda e retorna o texto bruto."""
    args = [
        sys.executable, "-m", "yt_dlp",
        "--skip-download",
        "--write-sub" if sub_type == "manual" else "--write-auto-sub",
        "--sub-lang", lang,
        "--sub-format", "srt",
        "--output", "%(id)s",
        "--no-warnings",
        url
    ]

    # Trabalha em diretório temporário
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(args, capture_output=True, text=True,
                                encoding="utf-8", cwd=tmpdir)

        if result.returncode != 0:
            print(f"Erro ao baixar legenda: {result.stderr.strip()}")
            sys.exit(1)

        # Encontra o arquivo .srt gerado
        srt_files = list(Path(tmpdir).glob("*.srt"))
        if not srt_files:
            # Tenta .vtt
            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if not vtt_files:
                print("Erro: arquivo de legenda não foi gerado.")
                sys.exit(1)
            srt_file = vtt_files[0]
        else:
            srt_file = srt_files[0]

        return srt_file.read_text(encoding="utf-8")


def clean_subtitle_text(raw_text: str) -> str:
    """Remove timestamps, tags, numeração e limpa o texto da legenda."""
    lines = raw_text.split("\n")
    cleaned = []
    seen = set()

    for line in lines:
        line = line.strip()

        # Pula linhas vazias
        if not line:
            continue

        # Pula cabeçalho WEBVTT
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue

        # Pula numeração de blocos SRT (linhas apenas com números)
        if re.match(r"^\d+$", line):
            continue

        # Pula timestamps (SRT e VTT)
        if re.match(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->", line):
            continue

        # Remove tags HTML/XML
        line = re.sub(r"<[^>]+>", "", line)

        # Remove marcadores de posição VTT
        line = re.sub(r"align:start position:\d+%", "", line).strip()

        # Remove BOM
        line = line.replace("\ufeff", "")

        if not line:
            continue

        # Remove duplicatas consecutivas (comum em legendas automáticas)
        if line not in seen:
            cleaned.append(line)
            seen.add(line)
        else:
            seen.clear()
            seen.add(line)

    # Junta em texto contínuo com quebras naturais
    text = " ".join(cleaned)

    # Limpa espaços múltiplos
    text = re.sub(r"\s{2,}", " ", text)

    # Adiciona quebras de parágrafo após pontos finais seguidos de maiúscula
    text = re.sub(r"([.!?])\s+([A-ZÁÉÍÓÚÀÂÃÊÔÇ])", r"\1\n\n\2", text)

    return text.strip()


def sanitize_filename(title: str) -> str:
    """Converte título do vídeo em nome de arquivo seguro."""
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = title.strip()
    if len(title) > 80:
        title = title[:80].rsplit(" ", 1)[0]
    return title


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Transcrição automática de vídeo de referência (YouTube)"
    )
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument("--idioma", "-i", default=None,
                        help="Idioma preferido da legenda (ex: en, pt, de)")
    parser.add_argument("--output", "-o", default=None,
                        help="Nome do arquivo de saída (default: auto)")
    parser.add_argument("--listar", "-l", action="store_true",
                        help="Apenas listar legendas disponíveis")

    args = parser.parse_args()

    print(f"Buscando informações do vídeo...")
    info = get_video_info(args.url)
    title = info.get("title", "video")
    video_id = info.get("id", "unknown")

    print(f"Título: {title}")
    print(f"ID: {video_id}")

    # Modo listar
    if args.listar:
        manual = info.get("subtitles") or {}
        auto = info.get("automatic_captions") or {}
        print(f"\nLegendas manuais ({len(manual)}):")
        for lang in sorted(manual.keys()):
            print(f"  {lang}")
        print(f"\nLegendas automáticas ({len(auto)}):")
        for lang in sorted(auto.keys())[:20]:
            print(f"  {lang}")
        if len(auto) > 20:
            print(f"  ... e mais {len(auto) - 20}")
        return

    # Encontra melhor legenda
    lang, sub_type = find_best_subtitle(info, args.idioma)

    if lang is None:
        print("\nNenhuma legenda disponível para este vídeo.")
        print("Opções:")
        print("  1. Transcreva manualmente e salve como .txt na pasta referencias/")
        print("  2. Use um serviço de speech-to-text externo")
        sys.exit(1)

    print(f"Legenda encontrada: {lang} ({sub_type})")
    print(f"Baixando...")

    raw_text = download_subtitle(args.url, lang, sub_type)
    clean_text = clean_subtitle_text(raw_text)

    # Prepara output
    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.output:
        output_path = OUTPUT_DIR / args.output
    else:
        safe_title = sanitize_filename(title)
        output_path = OUTPUT_DIR / f"referencia_{safe_title}.txt"

    # Cabeçalho com metadata
    header = f"# Referência: {title}\n"
    header += f"# URL: {args.url}\n"
    header += f"# Legenda: {lang} ({sub_type})\n"
    header += f"# Video ID: {video_id}\n"
    header += "# ---\n\n"

    output_path.write_text(header + clean_text, encoding="utf-8")

    print(f"\nSalvo em: {output_path}")
    print(f"Tamanho: {len(clean_text)} caracteres, ~{len(clean_text.split())} palavras")


if __name__ == "__main__":
    main()
