"""
Módulo de chamada aos OpenAI Assistants para tradução.
Replica o comportamento do Make.com: envia capítulo por capítulo ao assistant.
"""

import os
import time
from openai import OpenAI

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Tenta carregar do .env no diretório pai
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada. Configure no .env ou variável de ambiente.")
        _client = OpenAI(api_key=api_key)
    return _client


def translate_chapter(chapter_text, assistant_id, max_wait_sec=1200):
    """
    Envia um capítulo ao assistant e aguarda a resposta.
    Replica o comportamento do Make.com: messageAssistantAdvanced (role=user).
    """
    client = get_client()

    # Cria uma thread nova para cada capítulo (stateless, como Make.com)
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=chapter_text,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    # Aguarda conclusão
    elapsed = 0
    interval = 2
    while elapsed < max_wait_sec:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            break
        if run.status in ("failed", "cancelled", "expired"):
            raise RuntimeError(f"Run falhou com status: {run.status}")
        time.sleep(interval)
        elapsed += interval

    if run.status != "completed":
        raise TimeoutError(f"Assistant não respondeu em {max_wait_sec}s (run_id={run.id})")

    # Recupera a última mensagem do assistant
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    for msg in messages.data:
        if msg.role == "assistant":
            return msg.content[0].text.value

    raise RuntimeError("Nenhuma resposta do assistant encontrada.")


def translate_all_chapters(chapters, assistant_id, sleep_between_sec=15, lang_suffix=""):
    """
    Traduz todos os capítulos sequencialmente com sleep entre eles.
    Retorna lista de capítulos traduzidos.
    """
    translated = []
    total = len(chapters)
    for i, chapter in enumerate(chapters, 1):
        if not chapter.strip():
            translated.append(chapter)
            continue
        print(f"  Capítulo {i}/{total}...", end=" ", flush=True)
        result = translate_chapter(chapter, assistant_id)
        translated.append(result)
        print("ok")
        if i < total:
            time.sleep(sleep_between_sec)
    return translated
