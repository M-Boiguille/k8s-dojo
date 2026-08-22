# K8s Dojo - Adaptive DevOps/SRE Learning Engine

## 🎯 Vision
Construis un moteur d'apprentissage adaptatif, orienté métier, qui transforme l'utilisateur en ingénieur système résilient. Ce n'est PAS un énième playground Kubernetes. C'est un **Dojo** où l'on apprend en construisant, en cassant et en réparant, guidé par une IA au profil de Lead SRE.

## 🧠 Philosophie pédagogique (Le "Pourquoi")
- **Pratique délibérée** : L'utilisateur enchaîne des Katas (exercices) classés par domaine (Pods, Services, Storage, Networking, RBAC, Git, Architecture).
- **Zone proximale de développement** : L'IA analyse les performances (temps, erreurs, indices demandés) pour proposer le prochain défi adapté.
- **Méthode socratique** : L'IA ne donne JAMAIS la solution. Elle pose des questions (4 niveaux d'indices) pour guider la réflexion.
- **Métacognition** : Chaque session est suivie d'un journal de bord structuré, que l'IA aide à reformuler, mais dont l'utilisateur garde le contrôle de la publication.

## 🎨 Architecture fonctionnelle (Le "Quoi")
- **CLI (Python)** : Le cœur du dojo. Commandes : `start`, `hint`, `submit`, `journal`, `publish`, `dashboard`.
- **Dashboard Statique (HTML/JS)** : Vitrine publique pour recruteurs. Affiche les stats, la courbe de progression, les badges.
- **IA (DeepSeek)** : Moteur de validation, tuteur socratique, et faux Lead Dev pour les revues de PR.
- **Infrastructure (K3s hybride)** : Cluster Kubernetes exécuté sur OCI Always Free + Laptop perso, interconnecté via Tailscale.
- **GitHub Actions** : CI pour valider les Katas, scanner la sécurité (Trivy, Kubeconform) et reviewer automatiquement les PRs via l'IA.

## 🎓 Alignement métier (Le "Pour qui")
- **Cible finale** : Un ingénieur DevOps/SRE junior visant un poste en France/Europe.
- **Alignement** : Les katas couvrent le curriculum **CKA (Certified Kubernetes Administrator)**.
- **Argument de vente** : Le portfolio généré (dashboard + journaux) prouve une progression mesurable et une maîtrise des bonnes pratiques (Git, IaC, CI/CD, sécurité).

## ⚙️ Stack Technique Résumée
- **Langage** : Python 3.11+
- **CLI** : `click`
- **BDD Locale** : SQLite (via `sqlite3`)
- **Génération HTML** : `jinja2` + Chart.js (CDN)
- **IA** : DeepSeek API (via SDK `openai` avec `base_url` overridé)
- **Kubernetes** : K3s (local/cloud) avec `kubectl` via `subprocess`
- **CI/CD** : GitHub Actions
