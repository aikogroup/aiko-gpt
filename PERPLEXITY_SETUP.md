# 🔍 Configuration Perplexity API

> **Date** : 21 octobre 2025  
> **Status** : ⚠️ Configuration requise

---

## 🎯 Pourquoi Perplexity ?

Perplexity permet de récupérer des **informations contextuelles à jour** sur l'entreprise :
- Secteur d'activité
- Taille (nombre d'employés)
- Localisation
- Actualités récentes

---

## 🔧 Configuration

### 1. Obtenir une clé API

1. **Créer un compte** : https://www.perplexity.ai/api-platform/
2. **Aller dans API Settings**
3. **Générer une clé API**
4. **Configurer la facturation** (carte bancaire requise)

⚠️ **Important** : Perplexity nécessite un mode de paiement configuré même pour les tests.

### 2. Ajouter la clé dans `.env`

Ouvrez le fichier `.env` à la racine du projet et ajoutez :

```bash
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Modèles disponibles (octobre 2024)

Les modèles Perplexity supportés :
- `sonar-small-online` ✅ (recommandé, utilisé actuellement)
- `sonar-medium-online`
- `sonar-small-chat`
- `sonar-medium-chat`

---

## 🧪 Tester la configuration

```bash
cd /Users/julliardcyril/Projets/aikoGPT
USE_CHECKPOINTER=true uv run python test_graph.py
```

Vérifiez les logs :
- ✅ **Succès** : `✅ Recherche Perplexity terminée - XXX caractères`
- ❌ **Échec** : `❌ Erreur API Perplexity (400)`

---

## ⚠️ Erreur 400 - Causes possibles

| Cause | Solution |
|-------|----------|
| Clé API invalide | Régénérer une nouvelle clé |
| Facturation non configurée | Ajouter une carte bancaire |
| Modèle incorrect | Utiliser `sonar-small-online` |
| Quota dépassé | Vérifier usage sur le dashboard |

---

## 🔄 Fallback automatique

**Bonne nouvelle** : Si Perplexity échoue, le système utilise **OpenAI comme fallback** !

```
❌ Erreur API Perplexity (400)
🤖 Structuration des résultats avec OpenAI pour Cousin Biotech...
✅ Structuration terminée - Secteur: Biotechnologie
```

Le workflow continue sans interruption, mais avec des informations moins à jour.

---

## 📊 État actuel du projet

**WebSearchAgent fonctionne** avec le fallback OpenAI :
- ✅ Identifie le secteur d'activité
- ✅ Estime la taille de l'entreprise
- ⚠️ Utilise les connaissances d'OpenAI (pas de recherche web en temps réel)

**Pour activer Perplexity** :
1. Obtenir une clé API valide
2. L'ajouter à `.env`
3. Relancer le workflow

---

## 💡 Alternative : Désactiver Perplexity

Si vous ne voulez pas utiliser Perplexity, le système fonctionne **parfaitement avec OpenAI uniquement**.

Aucune action requise - le fallback est automatique !

---

## 📚 Ressources

- [Perplexity API Docs](https://docs.perplexity.ai/)
- [Guide de démarrage](https://docs.perplexity.ai/guides/search-quickstart)
- [Tarification](https://www.perplexity.ai/api-platform/pricing)

---

**Le backend fonctionne avec ou sans Perplexity grâce au fallback OpenAI ! ✅**

