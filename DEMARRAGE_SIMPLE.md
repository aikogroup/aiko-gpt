# 🚀 Démarrage aikoGPT - Ultra Simple

> **Une seule commande pour tout lancer avec Docker**

---

## ⚡ Démarrage en 3 étapes

### 1. Configurer les clés API

Créez le fichier `.env` :

```bash
cp .env.example .env
```

Éditez `.env` et ajoutez vos clés :

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini-2024-07-18
PERPLEXITY_API_KEY=pplx-...  # Optionnel
```

### 2. Lancer Docker

```bash
docker compose up --build
```

**C'est tout !** 🎉

### 3. Ouvrir l'application

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:2024
- **API Docs** : http://localhost:2024/docs

---

## 🛑 Arrêter

```bash
# Dans le terminal où docker tourne, appuyez sur :
Ctrl+C

# Ou dans un autre terminal :
docker compose down
```

---

## 🔧 Que fait Docker ?

Docker lance **automatiquement** :

| Service | Port | Description |
|---------|------|-------------|
| **Backend** | 2024 | LangGraph Server (Python) |
| **Frontend** | 3000 | Next.js (React) |

✅ **Hot reload activé** : Les changements de code sont détectés automatiquement !

---

## 📝 Logs

### Voir tous les logs
```bash
docker compose logs -f
```

### Logs backend uniquement
```bash
docker compose logs -f backend
```

### Logs frontend uniquement
```bash
docker compose logs -f frontend
```

---

## 🧹 Nettoyer et redémarrer

Si vous avez des problèmes :

```bash
# Arrêter et supprimer les conteneurs
docker compose down

# Nettoyer complètement (images, volumes, etc.)
docker compose down --rmi all --volumes

# Reconstruire et relancer
docker compose up --build
```

---

## ⚠️ Prérequis

- ✅ Docker Desktop installé et lancé
- ✅ Fichier `.env` configuré avec `OPENAI_API_KEY`
- ✅ Ports 2024 et 3000 disponibles

**Vérifier que Docker tourne** :
```bash
docker --version
docker compose version
```

---

## 🐛 Problèmes courants

### "Port already in use"

**Solution** :
```bash
# Tuer les processus sur les ports
lsof -ti:2024 -ti:3000 | xargs kill -9

# Ou changer les ports dans docker-compose.yml
ports:
  - "2025:2024"  # Backend sur 2025 au lieu de 2024
  - "3001:3000"  # Frontend sur 3001 au lieu de 3000
```

### "Cannot connect to Docker daemon"

**Solution** : Lancez Docker Desktop

### Build très long la première fois

**Normal** ! Docker télécharge les images et installe toutes les dépendances.

Les prochains démarrages seront **beaucoup plus rapides**.

---

## 🎯 Tester que ça marche

Une fois `docker compose up` lancé :

### 1. Vérifier le backend
```bash
curl http://localhost:2024/ok
# Réponse attendue : {"ok":true}
```

### 2. Ouvrir le frontend
```
http://localhost:3000
```

### 3. Tester avec fichiers d'exemple

Les fichiers de test sont déjà dans le conteneur :
- `documents/atelier_exemple.xlsx`
- `documents/*.pdf`

---

## 📚 Avantages de Docker

| Avantage | Description |
|----------|-------------|
| ✅ **Simple** | Une seule commande |
| ✅ **Isolé** | Pas de conflit avec votre système |
| ✅ **Reproductible** | Même environnement partout |
| ✅ **Complet** | Python, Node, toutes les dépendances incluses |
| ✅ **Hot Reload** | Les changements de code sont pris en compte |

---

## 🚀 Commande magique

```bash
docker compose up --build
```

**Puis ouvrez** : http://localhost:3000

**C'est parti !** 🎉

