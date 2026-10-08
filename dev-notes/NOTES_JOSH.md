# telemetry-archive-reconcile — notes de travail (pas pour le repo)

## Contenu de tasks/telemetry-archive-reconcile/
- instruction.md : BROUILLON, à réécrire toi-même (GPTZero).
- task.toml : schéma supposé ; aligne les champs sur tasks/snowmelt-runoff-prediction/task.toml.
- environment/ : Dockerfile (python:3.12-slim, user `recon`), app/ (code de départ, _durable.py,
  tools/harness.py, SEMANTICS.md), visible_scenarios.tgz (3 scénarios, extraits dans /app/scenarios).
- solution/ : référence (engine.py + __main__.py), solve.sh.
- tests/ : test.sh, verify.py, harness.py, _durable.py, gen/ (générateur + familles + seeds),
  reference/engine.py. Les scénarios cachés sont régénérés au moment de la vérification.
- Canary : copie les lignes canary de ta tâche snowmelt dans les fichiers que les checks exigent.

## Vérifications locales (hors Docker, sandbox 1 CPU)
Voir RESULTS en bas, rempli après les runs.

## Commandes
```
# oracle / nop
harbor run -p tasks/telemetry-archive-reconcile --agent oracle
harbor run -p tasks/telemetry-archive-reconcile --agent nop
# Codex
caffeinate -i harbor run -p tasks/telemetry-archive-reconcile -k 1 -n 1 --job-name tar-codex-1 \
  --agent codex --model openai/gpt-6-astra --env docker --yes \
  --ae CODEX_FORCE_AUTH_JSON=1 --ak reasoning_effort=xhigh
```
Hors Docker, pour rejouer le verifier sur une copie de /app :
`RECON_APP=<app> RECON_WORKERS=4 python3 tests/verify.py` (en root, user `recon` requis).
`RECON_SKIP_CRASH=1` saute la phase crash.
