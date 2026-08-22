# K8s Dojo

Moteur d'apprentissage adaptatif Kubernetes/DevOps en CLI.

## Installation

```bash
# Cloner le repo
cd k8s-dojo

# Créer un environnement virtuel (recommandé)
python3 -m venv .venv
source .venv/bin/activate

# Installer le CLI en mode éditable
pip install -e .
```

Vérifie l'installation :

```bash
dojo --version
```

## Configuration

Crée un fichier `.env` à la racine du projet avec au minimum ta clé DeepSeek :

```dotenv
DEEPSEEK_API_KEY=sk-...
KUBECONFIG=/chemin/vers/kubeconfig   # optionnel
```

Le CLI lit automatiquement `.env` via `python-dotenv`.

## Session type

```bash
# 1. Initialiser le Dojo (local au repo)
dojo init --local

# 2. Démarrer un kata (copie les manifests dans workspace/)
dojo start kata-001

# 3. Demander un indice socratique (4 niveaux)
dojo hint

# 4. Soumettre la solution (kubectl + IA Validator)
dojo submit

# 5. Générer le journal réflexif
dojo journal generate

# 6. Relire et valider le brouillon
dojo journal review

# 7. Publier le journal (public/journal/)
dojo publish

# 8. Générer le dashboard statique
dojo build-dashboard --output ./public
```

## Commandes CI

```bash
# Valider tous les katas en dry-run (utilisé par la CI GitHub)
dojo test --all --dry-run
```

## Structure

```text
k8s-dojo/
├── cli/                 # Code source Python
├── katas-library/       # Exercices (kata-001, kata-002, kata-003)
├── private/             # Données locales (DB, brouillons) – .gitignored
├── public/              # Vitrine publique (dashboard + journaux)
└── scripts/             # IA PR review (Lead Dev)
```

## Notes

- Si DeepSeek est injoignable, le CLI continue en mode dégradé : validation kubectl pour `submit`, indices locaux pour `hint`, brouillon basique pour `journal`.
- Les workflows GitHub Actions sont dans `.github/workflows/`.
