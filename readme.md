# SMS Reply Webhook

Ce projet déploie un service Python qui reçoit des webhooks de **httpSMS** à l'adresse `http://.....`. 
L'application valide les requêtes entrantes en utilisant un token JWT signé, extrait les informations du message SMS reçu et les affiche.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
  - [1. Cloner le dépôt](#1-cloner-le-dépôt)
  - [2. Configurer l'application Python](#2-configurer-lapplication-python)
- [Construction de l'image Docker](#construction-de-limage-docker)
- [Déploiement sur Kubernetes](#déploiement-sur-kubernetes)
  - [1. Créer le namespace 'dev'](#1-créer-le-namespace-dev)
  - [2. Créer le Secret Kubernetes](#2-créer-le-secret-kubernetes)
  - [3. Déployer l'application](#3-déployer-lapplication)
- [Test de l'application](#test-de-lapplication)
- [Notes supplémentaires](#notes-supplémentaires)
- [Nettoyage](#nettoyage)

## Fonctionnalités

- **Réception de webhooks** : L'application écoute les requêtes POST à la racine `/`.
- **Validation JWT** : Les requêtes sont validées en utilisant un token JWT signé avec une clé secrète.
- **Traitement des messages** : Les données du message SMS sont extraites et affichées dans les logs.
- **Déploiement Kubernetes** : L'application est conteneurisée avec Docker et déployée sur un cluster Kubernetes local (k3s).

## Prérequis

- **Docker** installé sur votre machine locale.
- **kubectl** installé et configuré pour votre cluster Kubernetes (k3s).
- Accès à un cluster Kubernetes (k3s) fonctionnel.
- Compte Docker Hub (ou un registre d'images Docker accessible).
- **Python 3.9** (pour les tests locaux, optionnel).

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/sms-reply-webhook.git
cd sms-reply-webhook
```

### 2. Configurer l'application Python 

Assurez-vous que les fichiers suivants sont présents :
 
- `main.py` : Code source de l'application Flask.
 
- `requirements.txt` : Liste des dépendances Python.

## Construction de l'image Docker 
 
1. **Construire l'image Docker :** 

```bash
docker build -t docker-user/sms-reply-webhook:latest .
```
 
2. **Pousser l'image vers Docker Hub :** 
Si vous utilisez Docker Hub pour héberger votre image :


```bash
docker login
docker push docker-user/sms-reply-webhook:latest
```
**Remarque :**  Si vous travaillez en local et que votre cluster k3s peut accéder aux images locales, vous pouvez sauter cette étape.

## Déploiement sur Kubernetes 

### 1. Créer le namespace 'dev' 


```bash
kubectl create namespace dev
```

### 2. Créer le Secret Kubernetes 
Remplacez `'votre_clé_de_signature'` par la clé de signature que vous avez configurée dans httpSMS.

```bash
kubectl create secret generic sms-reply-webhook-secret \
  --from-literal=SIGNING_KEY='votre_clé_de_signature' \
  -n dev
```

### 3. Déployer l'application 
 
1. **Déployer le Deployment :** Créez un fichier `deployment.yaml` avec le contenu adapté à votre application, en vous assurant que : 
  - Le nom du déploiement est `sms-reply-webhook-deployment`.
 
  - Le namespace est `dev`.
 
  - L'image utilisée est `docker-user/sms-reply-webhook:latest`.
 
  - Le container expose le port `8181`.
 
  - La variable d'environnement `SIGNING_KEY` est définie à partir du Secret Kubernetes.

Appliquez le déploiement :


```bash
kubectl apply -f deployment.yaml
```
 
2. **Déployer le Service :** Créez un fichier `service.yaml` avec le contenu adapté, en vous assurant que : 
  - Le nom du service est `sms-reply-webhook-service`.
 
  - Le namespace est `dev`.
 
  - Le service expose le port `8181` et cible le port `8181` du container.

Appliquez le service :


```bash
kubectl apply -f service.yaml
```
 
3. **Déployer l'Ingress :** Créez un fichier `ingress.yaml` avec le contenu adapté, en vous assurant que : 
  - Le nom de l'ingress est `sms-reply-webhook-ingress`.
 
  - Le namespace est `dev`.

  - L'annotation pour le contrôleur d'Ingress (par exemple, Traefik) est correcte.
 
  - La règle d'hôte pointe `notif.xxx` vers le service `sms-reply-webhook-service` sur le port `8181`.

Appliquez l'ingress :


```bash
kubectl apply -f ingress.yaml
```

## Test de l'application 

### 1. Vérifier que les pods sont en cours d'exécution 


```bash
kubectl get pods -n dev
```

### 2. Consulter les logs du pod 


```bash
kubectl logs -n dev <nom-du-pod>
```

### 3. Ajouter une entrée dans le fichier hosts (si nécessaire) 
Si vous travaillez en local, ajoutez l'entrée suivante à votre fichier `hosts` :

```
127.0.0.1   notif.xxx
```
4. Tester le webhook avec `curl` 
1. **Générer un token JWT valide pour le test :** Créez un script `generate_token.py` pour générer un token JWT signé avec votre clé de signature.

```python
import jwt

SIGNING_KEY = 'votre_clé_de_signature'

payload = {
    "some": "payload"
}

token = jwt.encode(payload, SIGNING_KEY, algorithm='HS256')
print(token)
```

Exécutez le script :


```bash
python generate_token.py
```
 
2. **Envoyer une requête de test :** Remplacez `<token_jwt_valide>` par le token généré précédemment.

```bash
curl -X POST http://notif.xxx/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_jwt_valide>" \
  -H "X-Event-Type: message.phone.received" \
  -d '{
        "data": {
            "contact": "+18005550100",
            "content": "Ceci est un message de test",
            "message_id": "0b0123bb-ef2e-468f-908a-c026d51636aa",
            "owner": "+18005550199",
            "sim": "SIM1",
            "timestamp": "2023-06-29T03:21:19.814Z",
            "user_id": "XtABz6zdeFMoBLoltz6SREDvRSh2"
        },
        "datacontenttype": "application/json",
        "id": "f4aed1d3-ab4f-42b9-b9dd-9fc7182f7197",
        "source": "/v1/messages/receive",
        "specversion": "1.0",
        "time": "2023-06-29T03:21:19.524331882Z",
        "type": "message.phone.received"
    }'
```
 
3. **Vérifier les logs :** 

```bash
kubectl logs -n dev <nom-du-pod>
```

Vous devriez voir une sortie similaire :


```bash
Nouveau message reçu de +18005550100 à 2023-06-29T03:21:19.814Z: Ceci est un message de test
```

## Notes supplémentaires 
 
- **Contrôleur d'Ingress**  : Par défaut, k3s utilise Traefik comme contrôleur d'Ingress. Si vous utilisez un autre contrôleur, ajustez l'annotation dans `ingress.yaml` en conséquence.
 
- **Sécurité**  : 
  - **Clé de signature**  : Ne partagez jamais votre clé de signature. Elle doit être gardée secrète.
 
  - **HTTPS**  : Pour une utilisation en production, configurez TLS pour sécuriser les communications.
 
- **Scalabilité**  : Vous pouvez augmenter le nombre de réplicas dans `deployment.yaml` si nécessaire.
 
- **Monitoring**  : Envisagez d'ajouter des outils de monitoring pour surveiller l'état de l'application.

## Nettoyage 

Pour supprimer les ressources déployées :


```bash
kubectl delete -f ingress.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete secret sms-reply-webhook-secret -n dev
kubectl delete namespace dev
```


---

**Auteur**  : Clément V.**Licence**  : Ce projet est sous licence MIT.
**Contact**  : Pour toute question, veuillez me contacter via Github
