# User Stories – K8s Dojo MVP

## Sprint 1 : Le Moteur d'exécution (CLI + Katas)

**Objectif** : L'utilisateur peut lancer un kata, suivre les indices, et valider sa solution avec un retour immédiat (kubectl + IA).

| ID | US | Critère d'acceptation (DoD) |
| :--- | :--- | :--- |
| US-01 | Setup projet Python | `pyproject.toml` avec `click`, `openai`, `jinja2`, `pytest`. Commande `dojo --version` affiche `0.1.0`. |
| US-02 | Initialisation du Dojo | `dojo init` crée `~/.k8s-dojo/` (ou `.` si `--local`), la DB SQLite, et génère un UUID pour le profil. |
| US-03 | Chargement d'un kata | `dojo start kata-001` copie les fichiers de `katas-library/001-pods/initial/` vers un workspace (ex: `./workspace/kata-001`). Si workspace existe, demande écrasement (`--force`). |
| US-04 | Système d'indices Socratiques | `dojo hint` appelle DeepSeek avec le prompt `system_tutor.txt` et le niveau actuel (1-4). Le niveau s'incrémente à chaque appel (max 4). Stocke le niveau dans la session en cours. |
| US-05 | Validation kubectl | `dojo submit` exécute la liste des `validation.checks` du kata.yaml (ex: `kubectl get pvc -o json`). Compare le résultat attendu (via `jq` ou regex simple). Affiche "✅ SUCCESS" ou "❌ FAIL" avec la diff. |
| US-06 | Validation IA (qualité) | Si US-05 est OK, `dojo submit` envoie les manifests YAML du workspace à DeepSeek (prompt `system_validator.txt`). L'IA renvoie un score (0-100) et un commentaire. La session est sauvegardée en DB. |
| US-07 | Gestion d'erreur réseau (IA) | Si l'API DeepSeek est injoignable, le CLI continue sans IA (seulement la validation kubectl) et enregistre "IA_OFFLINE" dans le log. |

## Sprint 2 : Le Journal & La Mémoire (Réflexion)

**Objectif** : L'utilisateur construit son historique d'apprentissage, garde le contrôle de ses données, et alimente ses métriques.

| ID | US | Critère d'acceptation (DoD) |
| :--- | :--- | :--- |
| US-08 | Génération du brouillon | `dojo journal generate` interroge DeepSeek avec le prompt `system_journalist.txt` (contexte : dernière session, logs bruts). Crée un fichier `private/drafts/YYYY-MM-DD.md` avec la structure : Objectif, Action, Cause, Erreur, Leçon. |
| US-09 | Révision manuelle | `dojo journal review` ouvre le brouillon dans l'éditeur défini par `$EDITOR` (fallback: `nano`). Après fermeture, demande "Valider ce journal ? (o/N)". |
| US-10 | Publication contrôlée | `dojo publish` copie le journal validé de `private/drafts/` vers `public/journal/YYYY-MM-DD.md`. Met à jour la DB avec la date de publication. |
| US-11 | Mise à jour des compétences | Après chaque session réussie, la DB met à jour la table `competence_snapshots` : les scores augmentent en fonction du `category` du kata (ex: +5% pour "storage"). La progression est cumulative mais plafonnée à 100. |

## Sprint 3 : Le Dashboard & L'Intégration GitHub

**Objectif** : Transformer le dojo en outil de valorisation professionnelle (vitrine + CI).

| ID | US | Critère d'acceptation (DoD) |
| :--- | :--- | :--- |
| US-12 | Génération du Dashboard | `dojo build-dashboard` utilise `jinja2` pour générer `public/index.html`. Intègre Chart.js (CDN) pour afficher : (1) Radar des compétences, (2) Courbe de progression (temps), (3) Badges (ex: "Boss Slayer", "Storage Master"), (4) Temps moyen de résolution. |
| US-13 | GitHub Action CI – Validation | Workflow `.github/workflows/ci-katas.yml` : À chaque PR sur `main`, exécute `dojo test --all` (mode dry-run sans cluster) pour valider que tous les katas chargent et que leurs checks sont syntaxiquement corrects. Échoue si un kata.yaml est invalide. |
| US-14 | GitHub Action – Scan IaC | Dans la même PR, lance `kubeconform -summary` sur tous les manifests YAML des katas modifiés, et `trivy config` sur les charts Helm. Les résultats sont affichés dans la PR (via `actions/github-script`). |
| US-15 | IA Lead Dev en PR (le Faux Manager) | Sur la PR, un workflow appelle DeepSeek avec le prompt `system_leaddev.txt` et les fichiers YAML modifiés. L'IA commente la PR avec : un point positif, 3 axes d'amélioration, une question piège, et un "Score de confiance : X/100". Le score est également écrit en tant que `check_run` (visible dans la PR). |
| US-16 | Déploiement automatique du Dashboard | Workflow `deploy-docs.yml` : À chaque push sur `main`, exécute `dojo build-dashboard` et pousse le contenu de `public/` vers la branche `gh-pages`. |
| US-17 | Documentation utilisateur | Le README.md doit contenir : (1) Installation (pip install -e .), (2) Configuration (DeepSeek API key), (3) Exemple de session complète (start -> hint -> submit -> journal -> publish). |
