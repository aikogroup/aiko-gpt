# 🚀 aikoGPT - Démarrage Docker

> **Une seule commande pour tout lancer**

---

## ⚡ Lancement rapide

### 1. Configuration (une seule fois)

```bash
# Créer le fichier .env
cp .env.example .env

# Éditer .env et ajouter votre clé OpenAI
# OPENAI_API_KEY=sk-...
```

### 2. Démarrer l'application

```bash
docker compose up --build -d
```

**C'est tout !** 🎉

### 3. Accéder à l'application

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:2024
- **API Docs** : http://localhost:2024/docs

---

## 📊 Services lancés

| Service | Port | Status |
|---------|------|--------|
| **Backend** (LangGraph Server) | 2024 | ✅ Healthy |
| **Frontend** (Next.js) | 3000 | ✅ Running |

---

## 🛑 Arrêter l'application

```bash
# Arrêter et supprimer les conteneurs
docker compose down

# Nettoyer complètement (images, volumes, etc.)
docker compose down --rmi all --volumes
```

---

## 📝 Voir les logs

```bash
# Tous les logs
docker compose logs -f

# Backend uniquement
docker compose logs -f backend

# Frontend uniquement
docker compose logs -f frontend
```

---

## 🔧 Redémarrer après modifications de code

```bash
# Pour redémarrer complètement
docker compose down
docker compose up --build -d

# OU pour rebuilder un seul service
docker compose up --build backend -d
```

---

## ⚠️ En cas de problème

### Port déjà utilisé

```bash
# Nettoyer les ports
lsof -ti:2024 -ti:3000 | xargs kill -9

# Ou modifier les ports dans docker-compose.yml
```

### Conteneur unhealthy

```bash
# Voir les logs
docker logs aikogpt-backend

# Rebuilder complètement
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## ✅ Vérifier que tout fonctionne

### Backend

```bash
curl http://localhost:2024/ok
# Réponse : {"ok":true}
```

### Frontend

Ouvrir http://localhost:3000 dans votre navigateur

---

## 🐳 Avantages de Docker

- ✅ **Installation simplifiée** : Aucune installation de Python, Node, UV, etc.
- ✅ **Environnement isolé** : Pas de conflit avec votre système
- ✅ **Reproductible** : Fonctionne identiquement partout
- ✅ **Hot reload** : Les modifications de code sont prises en compte
- ✅ **Production-ready** : Architecture proche de la production

---

## 📚 Commandes utiles

```bash
# Statut des conteneurs
docker compose ps

# Redémarrer un service
docker compose restart backend

# Voir les ressources utilisées
docker stats

# Nettoyer les conteneurs orphelins
docker compose down --remove-orphans
```

---

## 🎯 Prochaines étapes

Maintenant que Docker fonctionne :

1. Ouvrir http://localhost:3000
2. Uploader vos fichiers Excel + PDF/JSON
3. Saisir le nom de l'entreprise
4. Cliquer sur "Analyser"
5. ⚠️ **Note** : L'upload n'est pas encore implémenté backend, utiliser les fichiers d'exemple en attendant

---

## 🚀 Commande magique

```bash
docker compose up --build -d && sleep 5 && echo "✅ Backend:" && curl -s http://localhost:2024/ok && echo "" && echo "✅ Frontend: http://localhost:3000"
```

---

**Projet lancé avec succès !** 🎉

Pour développement avancé, voir `DEMARRAGE.md`

