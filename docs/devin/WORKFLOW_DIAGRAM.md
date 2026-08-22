# Workflow de développement : La boucle PR / Review / Merge

Ce document décrit le cycle de vie d'une modification dans le Dojo (qu'il s'agisse d'un nouveau kata ou d'une correction du code source). Il est conçu pour simuler un environnement professionnel où chaque ligne est scrutée.

## 1. Le Cycle de Développement

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       DEVELOPPER (Toi / Devin)                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 1. Créer une branche │
                        │ feature/ma-fonction  │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │  2. Commit + Push   │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │  3. Ouvrir une PR   │
                        │  (Draft PR)         │
                        └─────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐   ┌───────────────────────┐   ┌───────────────────┐
│ US-13 : CI        │   │ US-14 : Scan de Secu  │   │ US-15 : IA Lead   │
│ (Validation       │   │ (Kubeconform + Trivy) │   │ Dev (Review)      │
│  Katas)           │   │                       │   │                   │
└───────────────────┘   └───────────────────────┘   └───────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 4. Résultats dans   │
                        │    la PR (Checks)   │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 5. Corrections      │
                        │    (push --force)   │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 6. IA Lead Dev val  │
                        │    Score > 80/100   │
                        │    et Checks OK     │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 7. Merge sur main   │
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ 8. US-16 : Déploie  │
                        │    Dashboard        │
                        └─────────────────────┘
```

## 2. Détail des Jobs GitHub Actions

### Job A : `validate-katas`
- **Déclencheur** : `pull_request` (sur les chemins `katas-library/**`).
- **Runner** : `ubuntu-latest`.
- **Étapes** :
  1. Checkout du code.
  2. Setup Python + installation du CLI en mode editable (`pip install -e .`).
  3. Exécution de `dojo test --kata ${{ github.event.pull_request.changed_files }}` (vérifie le schema YAML + dry-run des checks kubectl sans cluster).
  4. Si échec, la PR est marquée en rouge.

### Job B : `security-scan`
- **Déclencheur** : `pull_request`.
- **Étapes** :
  1. Installer `kubeconform` et `trivy`.
  2. Lancer `kubeconform -summary katas-library/**/*.yaml`.
  3. Lancer `trivy config --severity HIGH,CRITICAL katas-library/**/`.
  4. Générer un rapport formaté en Markdown et le coller dans un commentaire de PR via `actions/github-script`.

### Job C : `ai-lead-review`
- **Déclencheur** : `pull_request` (optionnel: uniquement si label "review-ia" est posé).
- **Étapes** :
  1. Récupérer la liste des fichiers YAML modifiés.
  2. Construire un prompt système (`system_leaddev.txt`) + le contenu des fichiers.
  3. Appeler DeepSeek.
  4. Poster la réponse en tant que commentaire de PR.
  5. Ajouter le "Score de confiance" comme `check_run` (API GitHub).

## 3. Les Règles d'OR pour le Code
- **Branche principale** : `main` (protégée : pas de push direct, uniquement via PR).
- **Conventions de commits** : `feat:`, `fix:`, `docs:`, `chore:` (pour le parsing automatique).
- **Draft PR** : Les PRs ouvertes en "Draft" ne déclenchent **pas** le Job C (IA Lead Review) pour économiser les tokens DeepSeek. Elles déclenchent seulement le Job A et B.
- **Passage en "Ready for review"** : Le Job C est alors déclenché.

## 4. Stratégie de fallback
- Si l'API DeepSeek est en échec sur le Job C, le workflow **continue** (pas d'échec bloquant), mais laisse un commentaire : "⚠️ IA Review indisponible pour le moment."
