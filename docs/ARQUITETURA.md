# Arquitetura do Jogos Vivos

> Por que o grafo é desenhado assim. A pesquisa completa (100+ fontes, 27/08/2026)
> está no diretório `NEGOCIO/` do workspace do autor; este doc é a versão operacional.

## Premissas vindas de evidência

| Premissa | Evidência |
|---|---|
| Prompt único não gera jogo publicável | Melhor agente: 41,46% no GameCraft-Bench (Godot 4); 54,5% no GameDevBench, 31,6% em 2D |
| Verificação estrutural > juiz aberto | GameGen-Verifier: 92,2% de acurácia vs 58,8% do Agent-as-a-Verifier, 16,6× mais rápido |
| Feedback visual melhora agentes de código | GameDevBench: Sonnet 4.5 sobe de 33,3% → 47,7% com imagem+vídeo |
| Recompensa programática > LLM-as-judge p/ mecânica | CreativeGame (ICLR-style 2026) |
| LLM-as-judge funciona com rubrica + screenshots | WebVoyager (ACL 2024): 85,3% de concordância humana |
| O público perdoa IA no código, não no soul | consenso documentado em r/gamedev + WaPo jan/2026 (protestos anti-slop) |
| O gap do mercado é o loop fechado | nenhum sistema público gera→testa→publica→evolui (awesome-game-gen, 80 papers) |

## Decisões de design

1. **Contrato JV no template** — o LLM escreve apenas o miolo do jogo contra uma
   engine de ~150 linhas (estados, input, áudio, partículas, shake, recorde).
   Superfície de API mínima = menos alucinação. Menu/game over consistentes de graça
   (critério de qualidade explícito do CrazyGames).

2. **Gates em camada, barato primeiro** — `node --check` (grátis) → regras regex
   anti-slop (grátis) → checagem de contrato e paleta (grátis). Só depois viria o
   JUDGE multimodal (F2, <$0,02/avaliação). Nada de gastar token com jogo que nem abre.

3. **Loop de reparo com teto** — o gate devolve os erros ao nó CODE por até 3
   iterações. Passou, publica; falhou, arquiva em `report.json` com o motivo. O
   custo real por jogo é 3–5× a passada única; o teto impede espiral de tokens.

4. **Seeds em rotação determinística** — 36 combinações gênero×mecânica×tema em
   `fabrica/data/seeds.yaml`, índice = nº de runs % len(seeds). A variedade vem do
   estado, não do RNG: o mesmo dia nunca repete tema, e o `state.json` no git é auditável.

5. **Git como banco de dados** — cada jogo é um diretório `games/<slug>/` com
   `index.html` (single-file) e `report.json` (proveniência: seed, iterações, gate).
   Evolução = commit novo no mesmo slug. Changelog de graça.

## O que ainda não está implementado (roadmap)

- **F2 — PLAYTEST + JUDGE**: Playwright headless com harness heurístico (fps > 30,
  sem `pageerror`, sem deadlock, smoke menu→jogo→game over) e juiz multimodal com
  rubrica `{fun, clarity, difficulty_curve, ai_ness, publish}`.
- **F3 — PUBLISH**: deploy gh-pages por jogo + índice dos jogos + devlog gerado.
- **F4 — EVOLVE**: cron separado reabre jogos publicados (sinal: judge score, idade,
  plays) e propõe v2 — balanceamento à la RuleSmith, novo nível, juice extra.
- **F5 — skill library cross-game**: biblioteca versionada de mecânicas/padrões
  testados que os nós CODE reutilizam (padrão Voyager aplicado ao gerador).

## Custos (verificados 27/08/2026)

30 jogos/mês com DeepSeek V4-Flash off-peak: **US$ 2–6/mês total**, incluindo juiz.
GitHub Actions + Pages em repo público: $0. O gargalo do sistema é o desenho do
loop de correção, nunca o token.
