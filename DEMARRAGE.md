# 🚀 Guide de Démarrage - aikoGPT

> **2 méthodes** : Script rapide ou Docker

---

## ⚡ Méthode 1 : Script de développement (Recommandé)

### Avantages
- ✅ Démarrage rapide
- ✅ Hot reload actif
- ✅ Logs visibles
- ✅ Facile à débugger

### Commande

```bash
cd /Users/julliardcyril/Projets/aikoGPT
./start-dev.sh
```

### Que fait le script ?

1. Nettoie les ports 2024 et 3000
2. Lance LangGraph Server (backend)
3. Attend 10 secondes
4. Lance Next.js (frontend)
5. Affiche les URLs

### Arrêter

`Ctrl+C` pour arrêter tous les services

---

## 🐳 Méthode 2 : Docker Compose

### Avantages
- ✅ Environnement isolé
- ✅ Reproductible
- ✅ Production-like
- ✅ Pas de conflits de dépendances

### Commande

```bash
cd /Users/julliardcyril/Projets/aikoGPT
docker compose up --build
```

### Arrêter

```bash
docker compose down
```

---

## 📌 URLs de l'application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interface utilisateur |
| **Backend API** | http://localhost:2024 | LangGraph Server |
| **API Docs** | http://localhost:2024/docs | Documentation Swagger |
| **Health Check** | http://localhost:2024/ok | Vérification serveur |

---

## ⚠️ Problèmes courants

### Erreur : "Address already in use"

**Solution** : Tuer les processus

```bash
lsof -ti:2024 -ti:3000 | xargs kill -9
```

### Erreur 422 : "Unprocessable Content"

**Cause** : L'upload de fichiers n'est pas encore implémenté côté serveur.

**Solution temporaire** : Utiliser les fichiers d'exemple

Modifiez `frontend/src/app/page.tsx` ligne 103 pour utiliser les fichiers existants :

```typescript
// FR: TEMPORAIRE - Utiliser les fichiers d'exemple
const { needs, threadId } = await generateNeeds({
  excel_file_path: "./documents/atelier_exemple.xlsx",
  pdf_json_file_paths: [
    "./documents/040425-Cousin-Biotech-x-aiko-Echange-IA-Booster-RH-DAF-4e7c7d16-b8f6.pdf"
  ],
  company_name: companyName,
  action: 'generate_needs',
});
```

**Solution permanente** : À implémenter

- Créer un endpoint `/upload` qui sauvegarde les fichiers
- Retourner les chemins des fichiers sauvegardés
- Utiliser ces chemins dans le workflow

---

## 🧪 Tester avec les fichiers d'exemple

### Fichiers disponibles

- ✅ `documents/atelier_exemple.xlsx` - 107 lignes d'ateliers
- ✅ `documents/040425-Cousin-Biotech-x-aiko-Echange-IA-Booster-RH-DAF-4e7c7d16-b8f6.pdf` - Transcription
- ✅ `documents/*.json` - Autres transcriptions

### Test backend seul

```bash
cd /Users/julliardcyril/Projets/aikoGPT
USE_CHECKPOINTER=true uv run python tests/backend/test_graph.py
```

**Résultat attendu** :
```
✅ WorkshopAgent - 107 lignes → 34 cas d'usage
✅ TranscriptAgent - 1 PDF → 6 citations
✅ WebSearchAgent - Perplexity → 1725 caractères
✅ NeedAnalysisAgent - 10 besoins générés
```

---

## 🔧 Configuration requise

### Variables d'environnement (`.env`)

```bash
# Obligatoire
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini-2024-07-18

# Optionnel
PERPLEXITY_API_KEY=pplx-...
LANGSMITH_API_KEY=lsv2_pt_...
```

### Dépendances

**Backend** :
```bash
cd backend
uv sync
```

**Frontend** :
```bash
cd frontend
npm install
```

---

## 📝 Logs et Debugging

### Voir les logs backend

```bash
# Si lancé avec start-dev.sh
# Les logs s'affichent directement

# Si lancé avec Docker
docker logs aikogpt-backend -f
```

### Voir les logs frontend

```bash
# Si lancé avec start-dev.sh
# Les logs s'affichent directement

# Si lancé avec Docker
docker logs aikogpt-frontend -f
```

---

## 🎯 Workflow de test recommandé

### 1. Vérifier que le backend fonctionne

```bash
curl http://localhost:2024/ok
# Réponse attendue: {"ok":true}
```

### 2. Tester un workflow complet

```bash
USE_CHECKPOINTER=true uv run python tests/backend/test_graph.py
```

### 3. Ouvrir le frontend

```
http://localhost:3000
```

### 4. Tester l'interface

⚠️ **Attention** : L'upload n'est pas encore implémenté.

**Pour tester** : Modifier le code comme indiqué ci-dessus pour utiliser les fichiers d'exemple.

---

## 🚧 Limitations actuelles

| Fonctionnalité | Status | Note |
|----------------|--------|------|
| Backend LangGraph | ✅ Opérationnel | Tous les tests passent |
| Frontend UI | ✅ Opérationnel | 4 pages complètes |
| Upload fichiers | ❌ À implémenter | Utilisez fichiers d'exemple |
| Téléchargement Word | ❌ À implémenter | Retourne blob vide |

---

## 📚 Documentation complémentaire

- `README.md` - Documentation générale
- `PROJET_FINAL.md` - Synthèse complète
- `BACKEND_VALIDATION.md` - Validation backend
- `tests/backend/` - Scripts de tests

---

## ✅ Checklist avant de démarrer

- [ ] Fichier `.env` créé avec `OPENAI_API_KEY`
- [ ] Backend installé (`cd backend && uv sync`)
- [ ] Frontend installé (`cd frontend && npm install`)
- [ ] Ports 2024 et 3000 libres
- [ ] Script `start-dev.sh` exécutable (`chmod +x`)

---

**Prêt à démarrer !** 🚀

```bash
./start-dev.sh
```

Puis ouvrir : http://localhost:3000


