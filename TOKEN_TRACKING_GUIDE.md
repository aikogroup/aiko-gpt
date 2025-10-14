# 📊 Guide d'utilisation du Token Tracker

## 🎯 Vue d'ensemble

Le `TokenTracker` est un outil pour surveiller la consommation de tokens et les coûts associés aux appels API OpenAI.

### Fonctionnalités

- ✅ **Comptage automatique des tokens** (input & output)
- ✅ **Calcul des coûts** par appel et par session
- ✅ **Statistiques par agent** (need_analysis, workshop, etc.)
- ✅ **Export JSON** des rapports détaillés
- ✅ **Affichage formaté** des résumés
- ✅ **Support multi-modèles** (gpt-4, gpt-5-nano, o1, etc.)

---

## 📦 Installation

Le module est déjà installé dans `utils/token_tracker.py`.

Aucune dépendance externe n'est requise.

---

## 🚀 Utilisation rapide

### Exemple 1 : Tracking basique

```python
from utils.token_tracker import TokenTracker

# Créer le tracker
tracker = TokenTracker()

# Après un appel API
response = client.responses.parse(...)

# Tracker la réponse
tracker.track_response(
    response,
    agent_name="need_analysis",
    operation="analyze_needs",
    model="gpt-5-nano"
)

# Afficher le résumé
tracker.print_summary()

# Sauvegarder le rapport
tracker.save_report()
```

### Exemple 2 : Intégration dans un agent

```python
from utils.token_tracker import TokenTracker

class NeedAnalysisAgent:
    def __init__(self, api_key: str, tracker: TokenTracker = None):
        self.client = OpenAI(api_key=api_key)
        self.tracker = tracker  # ⬅️ AJOUT
        
    def analyze_needs(self, ...):
        response = self.client.responses.parse(
            model=self.model,
            input=[...],
            text_format=NeedAnalysisResponse
        )
        
        # ⬅️ AJOUT: Tracking
        if self.tracker:
            self.tracker.track_response(
                response,
                agent_name="need_analysis",
                operation="analyze_needs",
                model=self.model
            )
        
        return response.output_parsed
```

### Exemple 3 : Workflow complet

```python
from utils.token_tracker import TokenTracker

# Créer le tracker au début du workflow
tracker = TokenTracker()

# Initialiser les agents avec le tracker
need_analysis_agent = NeedAnalysisAgent(api_key, tracker=tracker)
use_case_agent = UseCaseAnalysisAgent(api_key, tracker=tracker)
workshop_agent = WorkshopAgent(api_key, tracker=tracker)

# Exécuter le workflow
# ... (les agents trackeront automatiquement)

# À la fin du workflow
tracker.print_summary()
report_path = tracker.save_report()
print(f"Rapport sauvegardé: {report_path}")
```

---

## 📊 Exemple de sortie

```
======================================================================
📊 RÉSUMÉ DES TOKENS & COÛTS
======================================================================
🕐 Session démarrée: 2025-10-14T15:30:45
📞 Nombre d'appels API: 7
🔤 Tokens totaux: 32,000
   ├─ Input:  22,000
   └─ Output: 10,000
💰 Coût total: $0.1240

📊 Détails par agent:
   • workshop:
     ├─ Appels: 2
     ├─ Tokens: 5,500
     └─ Coût: $0.0110
   • transcript:
     ├─ Appels: 2
     ├─ Tokens: 10,500
     └─ Coût: $0.0420
   • need_analysis:
     ├─ Appels: 1
     ├─ Tokens: 8,000
     └─ Coût: $0.0320
   • use_case_analysis:
     ├─ Appels: 2
     ├─ Tokens: 8,000
     └─ Coût: $0.0390
======================================================================
```

---

## 💰 Tarifs supportés

| Modèle | Input ($/1M tokens) | Output ($/1M tokens) |
|--------|---------------------|----------------------|
| gpt-4 | $30.00 | $60.00 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-4o | $5.00 | $15.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| **gpt-5-nano** | **$0.10** | **$0.40** |
| o1 | $15.00 | $60.00 |
| o1-mini | $3.00 | $12.00 |

**Note**: Les tarifs pour `gpt-5-nano` sont estimés. Ajustez dans `token_tracker.py` si nécessaire.

---

## 📁 Rapports générés

Les rapports sont sauvegardés dans `outputs/token_tracking/` par défaut.

### Structure d'un rapport JSON

```json
{
  "session_start": "2025-10-14T15:30:45",
  "total_calls": 7,
  "total_input_tokens": 22000,
  "total_output_tokens": 10000,
  "total_tokens": 32000,
  "total_cost": 0.1240,
  "calls_by_agent": {
    "need_analysis": {
      "calls": 1,
      "total_tokens": 8000,
      "total_cost": 0.0320
    }
  },
  "calls_detail": [
    {
      "timestamp": "2025-10-14T15:30:46",
      "agent_name": "need_analysis",
      "operation": "analyze_needs",
      "model": "gpt-5-nano",
      "input_tokens": 5000,
      "output_tokens": 3000,
      "total_tokens": 8000,
      "cost_usd": 0.0320
    }
  ]
}
```

---

## 🔧 Configuration avancée

### Personnaliser le répertoire de sortie

```python
tracker = TokenTracker(output_dir="my_custom_dir")
```

### Mettre à jour les tarifs

Éditez `utils/token_tracker.py` :

```python
PRICING = {
    "gpt-5-nano": {
        "input": 0.10,   # Votre tarif
        "output": 0.40   # Votre tarif
    }
}
```

### Utiliser le tracker global (singleton)

```python
from utils.token_tracker import get_global_tracker

tracker = get_global_tracker()  # Toujours la même instance
```

---

## 🧪 Tester le tracker

Exécutez l'exemple de démonstration :

```bash
cd /home/addeche/aiko/aikoGPT
python examples/token_tracker_usage.py
```

---

## 📝 Checklist d'intégration

Pour intégrer le tracker dans vos agents :

- [ ] Ajouter `tracker: TokenTracker = None` au `__init__` de l'agent
- [ ] Après chaque `response = client.responses.parse(...)`, ajouter :
  ```python
  if self.tracker:
      self.tracker.track_response(response, "agent_name", "operation", self.model)
  ```
- [ ] Dans le workflow, créer le tracker et le passer aux agents
- [ ] À la fin du workflow, appeler `tracker.print_summary()` et `tracker.save_report()`

---

## 🎯 Cas d'usage recommandés

1. **Développement** : Identifier les appels coûteux
2. **Production** : Monitorer les coûts par utilisateur/session
3. **Optimisation** : Comparer différents prompts/modèles
4. **Budgeting** : Estimer les coûts mensuels
5. **Debugging** : Analyser les variations de tokens entre itérations

---

## ⚠️ Limitations

- Les tarifs doivent être mis à jour manuellement
- Ne compte pas les tokens des images/fichiers uploadés
- Nécessite que l'API retourne les informations d'usage (ce qui est le cas pour `responses.parse()`)

---

## 📚 Références

- [OpenAI Pricing](https://openai.com/api/pricing/)
- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- Code source : `utils/token_tracker.py`

---

**Créé le** : 14 octobre 2025  
**Version** : 1.0

