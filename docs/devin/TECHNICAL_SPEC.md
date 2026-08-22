# Spécifications Techniques Détaillées - K8s Dojo

## 1. Structure du Projet (Filesystem)
```text
k8s-dojo/
├── .github/workflows/          # CI/CD (Lot 3)
├── cli/                        # CODE SOURCE PRINCIPAL
│   ├── __init__.py
│   ├── dojo.py                 # Entrypoint click
│   ├── commands/
│   │   ├── start.py
│   │   ├── hint.py
│   │   ├── submit.py
│   │   ├── journal.py
│   │   ├── publish.py
│   │   └── dashboard.py
│   ├── core/
│   │   ├── db.py               # SQLite CRUD
│   │   ├── llm_client.py       # Wrapper DeepSeek
│   │   ├── k8s_client.py       # Wrapper kubectl
│   │   ├── kata_loader.py      # Charge les YAMLs
│   │   └── validator.py        # Vérifie les checks
│   └── prompts/                # Fichiers .txt pour les System Prompts (Lot 3)
├── katas-library/              # LES KATAS (YAML + manifests)
│   ├── 001-pods/
│   ├── 002-services/
│   └── ...
├── public/                     # BRANCHE GH-PAGES (Dashboard + Journaux publiés)
│   ├── index.html
│   └── journal/
├── private/                    # .gitignored (DB + logs bruts)
│   └── dojo.db
├── pyproject.toml
└── README.md
```

## 2. Modèle de Données (SQLite)

### Table `profile`
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (PK) | UUID généré à la création |
| `created_at` | DATETIME | Date d'init |
| `total_katas` | INTEGER | 0 par défaut |
| `boss_defeated` | INTEGER | 0 par défaut |
| `total_hints_used` | INTEGER | 0 par défaut |

### Table `sessions`
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Auto-incrément |
| `kata_id` | TEXT | Référence au dossier du kata (ex: "001-pods") |
| `started_at` | DATETIME | Début du `dojo start` |
| `ended_at` | DATETIME | Fin du `dojo submit` |
| `duration_seconds` | INTEGER | Calculé |
| `hint_level_reached` | INTEGER | 0 à 4 |
| `ia_score` | INTEGER | Score donné par DeepSeek (0-100) |
| `success` | BOOLEAN | Validation kubectl OK |
| `raw_log` | TEXT | Sortie de la dernière commande submit |

### Table `competence_snapshots` (pour la courbe de progression)
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Auto-incrément |
| `date` | DATETIME | Fin de session |
| `pods` | INTEGER | 0-100 |
| `services` | INTEGER | 0-100 |
| `storage` | INTEGER | 0-100 |
| `networking` | INTEGER | 0-100 |
| `rbac` | INTEGER | 0-100 |
| `git` | INTEGER | 0-100 |
| `architecture` | INTEGER | 0-100 |

## 3. Contrat de l'API DeepSeek

- **Endpoint** : `https://api.deepseek.com/v1/chat/completions`
- **Headers** : `Authorization: Bearer $DEEPSEEK_API_KEY`
- **Modèle** : `deepseek-chat` (équivaut à V3)
- **Structure de l'appel** :
```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.3,  # Factuel pour la validation
    max_tokens=800   # Limité pour le coût
)
```

## 4. Commandes CLI (Interface obligatoire)

| Commande | Arguments | Action |
| :--- | :--- | :--- |
| `dojo init` | (none) | Crée le profil, la DB, les dossiers. |
| `dojo start <kata_id>` | [--workspace PATH] | Copie les manifests `initial/` dans le workspace. |
| `dojo hint` | (none) | Incrémente le niveau d'indice et appelle l'IA (prompt socratique). |
| `dojo submit` | (none) | Exécute les `checks` du kata. Si OK, appelle l'IA Validator. Sauvegarde la session. |
| `dojo journal generate` | (none) | Crée un brouillon markdown dans `private/draft/` en interrogeant l'IA. |
| `dojo journal review` | (none) | Ouvre le draft dans l'éditeur par défaut ($EDITOR) pour révision. |
| `dojo publish` | (none) | Copie le draft validé vers `public/journal/YYYY-MM-DD.md`. |
| `dojo build-dashboard` | (none) | Génère `public/index.html` avec les stats. |

## 5. Variables d'Environnement
- `DEEPSEEK_API_KEY` : Obligatoire pour l'IA.
- `KUBECONFIG` : Optionnel. Le CLI doit fonctionner avec le context actuel de kubectl.
- `EDITOR` : Pour la revue de journal (fallback: `nano`).
