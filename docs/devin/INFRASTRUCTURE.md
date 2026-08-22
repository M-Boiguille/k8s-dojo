# Infrastructure Cible : Le "Hybrid Cloud Dojo"

## Architecture physique
- **Node 1 (Control Plane + Worker)** : OCI Always Free (2 OCPU / 16 Go RAM) - Ubuntu 22.04.
- **Node 2 (Worker)** : Honor D16 (Ryzen 5, 16 Go) - Ubuntu 22.04 (ou WSL2) - Reste allumé 24/7.
- **Réseau** : Tailscale (overlay VPN) pour interconnecter les deux nœuds de manière sécurisée.

## Installation du Cluster (Script fourni à Devin pour qu'il le documente)
Le script d'installation (que Devin doit écrire dans `scripts/setup-cluster.sh`) doit :
1. Installer K3s sur le Node 1 (Control Plane) avec `--bind-address` sur l'IP Tailscale.
2. Récupérer le token (`/var/lib/rancher/k3s/server/node-token`).
3. Installer K3s sur le Node 2 (Worker) avec `K3S_URL=https://<TAILSCALE_IP_NODE1>:6443` et `K3S_TOKEN=...`.
4. Installer **Helm** sur le Node 1.
5. Installer **Chaos Mesh** via Helm :
   ```bash
   helm repo add chaos-mesh https://charts.chaos-mesh.org
   helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --create-namespace
   ```

## Connexion du CLI
Le CLI Python (`k8s_client.py`) utilisera le `kubeconfig` généré par K3s (par défaut `/etc/rancher/k3s/k3s.yaml` sur le node 1). Si Devin exécute le CLI depuis son laptop, il doit copier ce fichier et définir `KUBECONFIG`.

## Stratégie de coût
- **OCI** : Profiter du "Always Free". Le forfait inclut 10 Go de stockage block, suffisant.
- **Power Management** : Le script doit `kubectl drain` le worker laptop avant de l'éteindre, et `uncordon` au redémarrage (ou utiliser des `taints` pour éviter de scheduler des pods critiques dessus).
- **Persistance** : Tous les katas de stockage utiliseront le `local-path-provisioner` de K3s ou un PVC basique.

## Sécurité (Minimum Viable)
- Désactiver l'API anonyme de K3s (`--anonymous-auth=false`).
- Créer un ServiceAccount `dojo-user` avec des permissions restreintes (RBAC) pour que le CLI ne tourne pas en `cluster-admin` (bonne pratique).
