"""
Módulo de divisão automática do roteiro em 3 partes com marcadores **.

O roteiro tem capítulos separados por *
O ** divide o roteiro em 3 blocos de tamanho mais igual possível (por caracteres),
sempre em limite de capítulo.

Exemplo:
  capítulos = [c1, c2, c3, c4, c5, c6]
  resultado  = [c1, c2, "**", c3, c4, "**", c5, c6]

Onde "**" representa uma entrada vazia (que ao juntar com * forma **: *\n*\n)
"""


def calculate_split_positions(chapters, num_parts=3):
    """
    Calcula os índices dos capítulos onde inserir o ** para dividir em num_parts partes iguais.

    Retorna lista de índices (0-based) APÓS os quais inserir o divisor.
    Ex: [1, 3] significa inserir ** após capítulo 1 e após capítulo 3.
    """
    if len(chapters) < num_parts:
        return []

    total_chars = sum(len(c) for c in chapters)
    target_per_part = total_chars / num_parts

    split_indices = []
    accumulated = 0
    splits_placed = 0

    for i, chapter in enumerate(chapters):
        accumulated += len(chapter)
        # Verifica se chegamos perto do alvo desta parte
        if splits_placed < num_parts - 1:
            target = target_per_part * (splits_placed + 1)
            if accumulated >= target:
                # Não inserir no último capítulo
                if i < len(chapters) - 1:
                    split_indices.append(i)
                    splits_placed += 1

    return split_indices


def apply_double_markers(chapters, split_positions):
    """
    Retorna uma lista de capítulos intercalados com strings vazias ('')
    nas posições de split. As strings vazias representam o **.

    Ao montar o texto final com join('*'), as strings vazias criarão **.
    """
    result = []
    for i, chapter in enumerate(chapters):
        result.append(chapter)
        if i in split_positions:
            result.append("")  # Representa o **

    return result


def build_text_from_chapters(chapters_with_markers):
    """
    Une os capítulos com * entre eles.
    Capítulos vazios ('') criarão ** quando adjacentes a outros *.
    """
    return "\n*\n".join(chapters_with_markers)


def split_text_to_chapters(text):
    """
    Divide o texto em capítulos pelo *.
    Preserva entradas vazias (que representam **).
    """
    return text.split("*")


def get_split_positions_from_chapters(chapters_with_markers):
    """
    Dado uma lista que pode conter strings vazias (marcadores **),
    retorna os índices reais das strings vazias.
    """
    return [i for i, c in enumerate(chapters_with_markers) if not c.strip()]


def apply_split_positions_to_translated(translated_chapters, split_positions):
    """
    Aplica as mesmas posições de ** à lista de capítulos traduzidos.
    translated_chapters: capítulos sem marcadores vazios (só conteúdo real).
    split_positions: índices de capítulos REAIS após os quais inserir **.

    Retorna lista com '' nos lugares corretos.
    """
    result = []
    for i, chapter in enumerate(translated_chapters):
        result.append(chapter)
        if i in split_positions:
            result.append("")
    return result
