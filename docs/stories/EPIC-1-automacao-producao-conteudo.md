# EPIC 1 — Automação de Produção de Conteúdo (Rede Finanças)

**Status:** Draft
**Criado:** 2026-04-03
**Owner:** @pm (Morgan)

---

## Epic Goal

Automatizar o pipeline de produção de roteiros da Rede Finanças — da transcrição de referência até a tradução e distribuição em 7 idiomas — eliminando todas as etapas manuais repetitivas e mantendo controle criativo sobre outline, refinamento e otimização de retenção.

## Contexto do Sistema Existente

**Stack atual:**
- Google Docs (escrita e refinamento de roteiros)
- Google Drive (organização de pastas por vídeo)
- Google Sheets (FLUXO DE PRODUÇÃO — tracking)
- Make.com (automação de tradução — será substituído)
- OpenAI Assistants API (7 assistentes de tradução configurados)
- SRT_FRASES (divisão de legendas — já existente em `REDE F/SRT_FRASES/`)
- yt-dlp (transcrição de vídeos do YouTube)
- Claude (escrita de roteiros com sequência de prompts)

**Idiomas de tradução:**
| Idioma | Sufixo | CTA | Assistant ID |
|--------|--------|-----|-------------|
| Alemão | AL | SIM (produto: "Frei von der Inflation in 30 Tagen") | asst_LyEg2GuG0BqKDRExj0sqWBk4 |
| Holandês | HL | NÃO | asst_IYlEwB2kdq4hemUA77iWgdhh |
| Italiano | IT | NÃO | asst_aY73SkXMcl4nx4eYI5PG6LMS |
| Espanhol | ES | NÃO | asst_0Ivx5dZu4DpnVIW4TQ38MwZl |
| Francês | FR | NÃO | asst_5TE6gQ45NIadoGToLca7ecKw |
| Português PT | PT | NÃO | asst_1BWZ2fA8CQE4pNgemXutieAW |
| Inglês | EN | NÃO | asst_yVVcD2aTLyB75lbcoKrVX1HU |

**Estrutura de pastas:** `C:\Users\Administrador\Documents\CLAUDE CODE\REDE F\`

---

## Workflow Alvo (5 Etapas)

```
ETAPA 1 → ETAPA 2 → ETAPA 3 → ETAPA 4 → ETAPA 5
(auto)     (semi)    (auto)     (manual)   (auto)
```

| Etapa | Descrição | Modo |
|-------|-----------|------|
| 1 | Transcrição do vídeo de referência | Automatizado |
| 2 | Agente de escrita (prompts → outline → PAUSA → escrita cap. a cap.) | Semi-automatizado |
| 3 | Export do roteiro bruto para Google Docs | Automatizado |
| 4 | Refinamento + otimização de retenção | Manual |
| 5 | Tradução + `**` + CTA + distribuição (substitui Make.com) | Automatizado |

---

## Stories

---

### Story 1.1 — Transcrição Automática de Vídeo de Referência

**Executor:** @dev
**Quality Gate:** @architect

**Descrição:**
Criar script `transcrever.py` que recebe URL de vídeo do YouTube e extrai a transcrição limpa (legenda) em formato `.txt`, pronta para ser usada como referência na escrita do roteiro.

**Acceptance Criteria:**
- [x] AC1: Script aceita URL do YouTube como argumento
- [x] AC2: Baixa legenda automática ou manual (priorizando manual se existir)
- [x] AC3: Limpa formatação (remove timestamps, tags HTML, metadata)
- [x] AC4: Salva como `referencia_{titulo_video}.txt` na pasta do projeto
- [x] AC5: Suporta fallback: se não houver legenda, informa ao usuário que precisa de transcrição manual
- [x] AC6: Funciona com yt-dlp via `python -m yt_dlp` (já instalado no sistema)

**Escopo:**
- IN: Download de legendas YouTube, limpeza de texto, salvamento local
- OUT: Transcrição por áudio/speech-to-text, suporte a outras plataformas

**Dependências:** yt-dlp instalado (`python -m yt_dlp`)
**Complexidade:** Baixa (1-2h)
**Risco:** Baixo — vídeos sem legenda terão fallback manual

**Arquivos esperados:**
```
REDE F/
└── transcrever.py
```

---

### Story 1.2 — Agente de Escrita de Roteiro (@roteiro)

**Executor:** @dev
**Quality Gate:** @pm

**Descrição:**
Criar agente (skill ou AIOS agent) que conduz a escrita de roteiro usando a sequência de prompts do usuário. O agente executa prompts em sequência, PAUSA no outline para revisão/ajustes manuais, e após aprovação continua automaticamente escrevendo capítulo por capítulo. O roteiro final é formatado com `*` entre capítulos.

**Acceptance Criteria:**
- [x] AC1: Agente carrega sequência de prompts pré-configurada
- [x] AC2: Aceita como input: tema do vídeo, transcrição de referência (legenda.txt), informações adicionais
- [x] AC3: Executa prompts em sequência até gerar o outline
- [x] AC4: **PAUSA** após gerar outline — apresenta ao usuário e aguarda aprovação ou pedidos de ajuste
- [x] AC5: Permite múltiplas iterações de ajuste no outline (loop até "ok")
- [x] AC6: Após aprovação do outline, continua automaticamente escrevendo capítulo por capítulo
- [x] AC7: Roteiro final formatado com `*` entre cada capítulo
- [x] AC8: Salva roteiro final como arquivo `.txt` local pronto para export

**Escopo:**
- IN: Sequência de prompts, pausa no outline, escrita automatizada cap. a cap.
- OUT: O conteúdo criativo dos prompts (fornecido pelo usuário), refinamento pós-escrita

**Dependências:**
- Story 1.1 (transcrição como input)
- Prompts do usuário (pendente — será fornecido)

**Complexidade:** Média (3-5h)
**Risco:** Médio — depende dos prompts do usuário; qualidade depende do design dos prompts

**Arquivos esperados:**
```
REDE F/
└── agente_roteiro/
    ├── roteiro.py (ou skill AIOS)
    ├── prompts/           (templates de prompts)
    └── config.json        (configurações do agente)
```

---

### Story 1.3 — Export Automático para Google Docs

**Executor:** @dev
**Quality Gate:** @architect

**Descrição:**
Criar módulo que envia o roteiro bruto (com divisões `*`) diretamente para um Google Doc na pasta designada do Drive, eliminando o copiar/colar manual parte por parte.

**Acceptance Criteria:**
- [x] AC1: Autentica com Google API (Drive + Docs) via OAuth2 / Service Account
- [x] AC2: Cria novo Google Doc com nome do vídeo na pasta correta do Drive
- [x] AC3: Insere conteúdo do roteiro preservando formatação e marcadores `*`
- [x] AC4: Retorna link do Google Doc criado
- [x] AC5: Funciona integrado com a Story 1.2 (chamado automaticamente ao fim da escrita)
- [x] AC6: Credenciais configuráveis via `config.json` (não hardcoded)

**Escopo:**
- IN: Criação de Google Doc, inserção de conteúdo, integração com Drive
- OUT: Formatação avançada (negrito, cores), edição de docs existentes

**Dependências:**
- Story 1.2 (output do agente de escrita)
- Credenciais Google API (usuário fornece `credentials.json`)
- IDs de pasta do Google Drive

**Complexidade:** Média (2-4h)
**Risco:** Médio — requer setup de credenciais Google Cloud; primeira execução pode precisar de ajustes de permissão

**Arquivos esperados:**
```
REDE F/
└── google_docs/
    ├── exportar.py
    └── credentials/       (gitignored)
```

---

### Story 1.4 — Pipeline de Tradução (Substituir Make.com)

**Executor:** @dev
**Quality Gate:** @architect

**Descrição:**
Criar script Python que substitui completamente a automação do Make.com. Lê o Google Doc com o roteiro final refinado, traduz para 7 idiomas usando os OpenAI Assistants existentes, e distribui os resultados no Google Drive + Sheets.

**Acceptance Criteria:**
- [x] AC1: Lê conteúdo do Google Doc (por ID ou link)
- [x] AC2: Divide o roteiro em capítulos pelo marcador `*`
- [x] AC3: **Calcula automaticamente** a posição dos `**` para dividir o roteiro em 3 partes de tamanho mais igual possível, sempre em limite de capítulo
- [x] AC4: Traduz cada capítulo chamando os 7 OpenAI Assistants (com os assistant IDs existentes)
- [x] AC5: **Preserva estrutura de parágrafos** — cada tradução mantém o mesmo número de parágrafos que o original (crítico para SRT_FRASES) *(responsabilidade do assistant — instrução já configurada)*
- [x] AC6: Insere `**` nas mesmas posições de capítulo em cada tradução
- [x] AC7: **Remove CTA** ("Frei von der Inflation in 30 Tagen" e bloco associado) em todos os idiomas exceto Alemão *(gerenciado pelo assistant AL — mesma lógica do Make.com)*
- [x] AC8: Cria um Google Doc por idioma (sufixos: AL, HL, IT, ES, FR, PT, EN) na pasta do vídeo no Drive
- [x] AC9: Atualiza Google Sheets (FLUXO DE PRODUÇÃO) com hyperlinks para cada doc traduzido (colunas J-P)
- [x] AC10: Marca coluna C como "SIM" na planilha
- [x] AC11: Move o doc original para a pasta do vídeo
- [x] AC12: Inclui sleep entre chamadas de tradução para respeitar rate limits (como no Make.com: 15s entre idiomas)
- [x] AC13: Config em `config.json`: assistant IDs, folder IDs, sheet ID, colunas, nome do CTA

**Escopo:**
- IN: Leitura de Google Docs, tradução via OpenAI Assistants, criação de Docs no Drive, update de Sheets
- OUT: Interface gráfica, monitoramento real-time, retry automático de falhas

**Dependências:**
- Story 1.3 (compartilha módulo Google API)
- OpenAI API key
- Google API credentials
- IDs do Make.com blueprint (pasta, sheet, assistants) — já extraídos do JSON

**Complexidade:** Alta (5-8h)
**Risco:** Alto — componente mais complexo; depende de múltiplas APIs externas; precisa replicar exatamente o comportamento do Make.com

**Arquivos esperados:**
```
REDE F/
└── pipeline_traducao/
    ├── traduzir.py        (script principal)
    ├── google_api.py      (módulo compartilhado com Story 1.3)
    ├── openai_api.py      (chamadas aos Assistants)
    ├── divisor.py         (lógica de ** automático)
    ├── cta_remover.py     (remoção de CTA por idioma)
    └── config.json        (IDs, keys, configurações)
```

---

### Story 1.5 — Integração e Teste End-to-End

**Executor:** @qa
**Quality Gate:** @pm

**Descrição:**
Integrar todas as etapas do pipeline, testar o fluxo completo end-to-end com um roteiro real, e validar que o output é compatível com o SRT_FRASES existente.

**Acceptance Criteria:**
- [ ] AC1: Pipeline completo funciona: URL → transcrição → agente → export → (refino manual) → tradução → distribuição
- [ ] AC2: Google Docs criados com formatação correta (*, **)
- [ ] AC3: Estrutura de parágrafos do alemão é compatível com SRT_FRASES
- [ ] AC4: CTA removido corretamente em 6 idiomas, mantido no alemão
- [ ] AC5: Google Sheets atualizado corretamente (hyperlinks, status)
- [ ] AC6: Script de tradução reproduz o mesmo output que o Make.com para o mesmo input
- [ ] AC7: Documentação de uso: README com passo a passo para rodar cada etapa

**Escopo:**
- IN: Teste integrado, validação de compatibilidade com SRT_FRASES, documentação
- OUT: Testes automatizados unitários (escopo é validação funcional)

**Dependências:** Stories 1.1, 1.2, 1.3, 1.4
**Complexidade:** Média (3-4h)
**Risco:** Médio — pode revelar bugs de integração entre componentes

---

## Ordem de Execução

```
Story 1.1 (transcrição)
    ↓
Story 1.2 (agente escrita)  ←  BLOQUEADO: aguarda prompts do usuário
    ↓
Story 1.3 (export Google Docs)
    ↓
Story 1.4 (pipeline tradução)  ←  Pode iniciar em paralelo com 1.2
    ↓
Story 1.5 (integração e teste)
```

**Caminho crítico:** 1.1 → 1.4 → 1.5

**Paralelismo possível:**
- Story 1.1 + Story 1.4 (módulo Google API) podem iniciar juntas
- Story 1.2 depende dos prompts do usuário — pode ser desenvolvida depois
- Story 1.3 compartilha código com 1.4 (módulo google_api.py)

---

## Estrutura Final de Pastas

```
REDE F/
├── SRT_FRASES/                  (existente)
├── transcrever.py               (Story 1.1)
├── agente_roteiro/              (Story 1.2)
│   ├── roteiro.py
│   ├── prompts/
│   └── config.json
├── google_docs/                 (Story 1.3)
│   ├── exportar.py
│   └── credentials/             (gitignored)
├── pipeline_traducao/           (Story 1.4)
│   ├── traduzir.py
│   ├── google_api.py            (compartilhado)
│   ├── openai_api.py
│   ├── divisor.py
│   ├── cta_remover.py
│   └── config.json
├── docs/
│   └── stories/
│       └── EPIC-1-automacao-producao-conteudo.md
└── Tradução de Roteiro (Finanças).blueprint.json  (referência)
```

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Credenciais Google API não configuradas | Bloqueia Stories 1.3 e 1.4 | Documentar setup passo a passo; testar com Service Account |
| Prompts do agente não fornecidos | Bloqueia Story 1.2 | Desenvolver 1.1, 1.3 e 1.4 primeiro; 1.2 pode ser última |
| Rate limit OpenAI Assistants | Tradução falha no meio | Sleep de 15s entre idiomas (como Make.com); retry com backoff |
| Estrutura de parágrafos muda na tradução | SRT_FRASES quebra | Instrução explícita no prompt de tradução para preservar estrutura |
| `**` automático divide mal | Partes desiguais | Algoritmo baseado em contagem de caracteres por capítulo |

---

## Definition of Done

- [ ] Pipeline completo funcional: transcrição → escrita → export → tradução → distribuição
- [ ] Make.com pode ser desativado para essa automação
- [ ] SRT_FRASES funciona com output do novo pipeline
- [ ] Documentação de uso completa (README)
- [ ] Config externalizada (sem hardcode de IDs/keys)

---

— Morgan, planejando o futuro 📊
