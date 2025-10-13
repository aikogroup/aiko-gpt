# 🔄 Système de Régénération avec Feedback

## 📋 Vue d'ensemble

Ce document explique comment fonctionne le système de régénération avec prise en compte des commentaires utilisateur et des éléments rejetés, tant pour l'analyse des besoins que pour l'analyse des use cases.

## ✅ Corrections implémentées

### 1. **Analyse des Besoins (Need Analysis)**

#### Avant :
- ❌ Pas de prise en compte des besoins rejetés
- ❌ Pas de prise en compte des commentaires utilisateur
- ❌ Pas de prompt de régénération

#### Après :
- ✅ **Nouveau prompt de régénération** (`NEED_REGENERATION_PROMPT`)
- ✅ **Prise en compte des besoins rejetés** pour ne pas les reproposer
- ✅ **Prise en compte des commentaires utilisateur**
- ✅ **Contexte complet** : besoins précédents + besoins rejetés + commentaires + données sources

#### Fonctionnement :

Lors de la **première itération** :
```python
# Génération initiale sans contexte
result = need_analysis_agent.analyze_needs(
    workshop_data=workshop_data,
    transcript_data=transcript_data,
    web_search_data=web_search_data,
    iteration=1
)
```

Lors des **itérations suivantes** (régénération) :
```python
# Régénération avec contexte complet
result = need_analysis_agent.analyze_needs(
    workshop_data=workshop_data,
    transcript_data=transcript_data,
    web_search_data=web_search_data,
    iteration=2,  # ou 3
    previous_needs=previous_needs,          # ✅ Besoins proposés avant
    rejected_needs=rejected_needs,          # ✅ Besoins rejetés par l'utilisateur
    user_feedback=user_feedback,            # ✅ Commentaires de l'utilisateur
    validated_needs_count=validated_count   # ✅ Nombre de besoins déjà validés
)
```

**Instructions données à l'IA lors de la régénération :**
1. NE PAS reproposer les besoins qui ont été rejetés
2. Analyser les besoins rejetés pour comprendre ce qui n'allait pas
3. Prendre en compte les commentaires de l'utilisateur pour affiner les nouveaux besoins
4. Explorer d'autres thématiques ou angles d'approche non couverts
5. Proposer des besoins plus concrets, actionnables et mieux sourcés
6. Générer le nombre exact de nouveaux besoins pour atteindre l'objectif

---

### 2. **Analyse des Use Cases (Use Case Analysis)**

#### Avant :
- ✅ Prise en compte des use cases précédents
- ❌ **Pas de prise en compte des commentaires utilisateur**
- ❌ **Pas de prise en compte des use cases rejetés explicitement**

#### Après :
- ✅ **Prompt de régénération amélioré** avec commentaires et use cases rejetés
- ✅ **Prise en compte des Quick Wins rejetés**
- ✅ **Prise en compte des Structuration IA rejetés**
- ✅ **Prise en compte des commentaires utilisateur**
- ✅ **Contexte complet** : use cases précédents + rejetés + commentaires + besoins validés

#### Fonctionnement :

Lors de la **première itération** :
```python
# Génération initiale sans contexte
result = use_case_analysis_agent.analyze_use_cases(
    validated_needs=validated_needs,
    iteration=1,
    validated_quick_wins_count=0,
    validated_structuration_ia_count=0
)
```

Lors des **itérations suivantes** (régénération) :
```python
# Régénération avec contexte complet
result = use_case_analysis_agent.analyze_use_cases(
    validated_needs=validated_needs,
    iteration=2,  # ou 3
    previous_use_cases=previous_use_cases,              # ✅ Use cases proposés avant
    rejected_quick_wins=rejected_quick_wins,            # ✅ Quick Wins rejetés
    rejected_structuration_ia=rejected_structuration_ia, # ✅ Structuration IA rejetés
    user_feedback=user_feedback,                        # ✅ Commentaires de l'utilisateur
    validated_quick_wins_count=validated_qw_count,
    validated_structuration_ia_count=validated_sia_count
)
```

**Instructions données à l'IA lors de la régénération :**
1. NE PAS reproposer les cas d'usage qui ont été rejetés
2. Analyser les cas d'usage rejetés pour comprendre ce qui n'a pas plu
3. Prendre en compte les commentaires de l'utilisateur pour affiner les nouvelles propositions
4. Proposer des cas d'usage différents, plus pertinents, plus concrets
5. Améliorer la pertinence en te basant sur les besoins non encore couverts
6. Varier les thématiques et les approches techniques
7. Rester aligné avec le contexte et les contraintes de l'entreprise

---

## 🎯 Processus complet

### Scénario : Validation partielle de use cases

#### Étape 1 : Première proposition
```
L'agent propose :
- 8 Quick Wins
- 10 Structuration IA
```

#### Étape 2 : Vous sélectionnez partiellement
```
Vous validez :
- 2 Quick Wins (sur 8)
- 3 Structuration IA (sur 10)

Vous rejetez :
- 6 Quick Wins
- 7 Structuration IA

Vous écrivez un commentaire :
"Les Quick Wins sont trop génériques, je veux des solutions 
plus spécifiques à notre contexte médical. Les Structuration 
IA sont trop complexes, simplifiez."
```

#### Étape 3 : L'agent régénère intelligemment
```
L'agent reçoit :
✅ Les 18 use cases proposés précédemment
✅ Les 6 Quick Wins rejetés (avec leurs détails)
✅ Les 7 Structuration IA rejetés (avec leurs détails)
✅ Votre commentaire complet
✅ Le contexte : 2/5 Quick Wins validés, 3/5 Structuration IA validés

L'agent comprend :
- Il manque encore 3 Quick Wins et 2 Structuration IA
- Il doit éviter de reproposer les 6 Quick Wins et 7 Structuration IA rejetés
- Il doit faire des propositions plus spécifiques au contexte médical
- Il doit simplifier les solutions pour Structuration IA

L'agent génère :
- 6 nouveaux Quick Wins (pour remplacer les 6 rejetés)
  → Plus spécifiques au contexte Cousin Surgery / MedTech
- 7 nouvelles Structuration IA (pour remplacer les 7 rejetés)
  → Plus simples et actionnables
```

#### Étape 4 : Vous validez la nouvelle proposition
```
Vous pouvez maintenant :
- Valider les 3 Quick Wins manquants parmi les 6 nouveaux
- Valider les 2 Structuration IA manquants parmi les 7 nouveaux

Si besoin, vous pouvez :
- Ajouter de nouveaux commentaires
- Relancer une 3ème itération (maximum 3 itérations)
```

---

## 🔍 Points techniques importants

### 1. **Éviter les doublons**
Le workflow vérifie que les éléments nouvellement validés ne sont pas déjà dans la liste des validés :
```python
existing_ids = [need.get("theme", "") for need in existing_validated]
unique_newly_validated = [
    need for need in newly_validated 
    if need.get("theme", "") not in existing_ids
]
```

### 2. **Accumulation correcte**
Les éléments validés et rejetés s'accumulent au fil des itérations :
```python
state["validated_quick_wins"] = existing_qw + unique_qw
state["rejected_quick_wins"] = existing_rejected_qw + newly_rejected_qw
```

### 3. **Logs détaillés**
Le système affiche des logs pour tracer le processus :
```
💬 [DEBUG] Commentaires utilisateur : Les Quick Wins sont trop génériques...
🚫 [DEBUG] Quick Wins rejetés à éviter : 6
🚫 [DEBUG] Structuration IA rejetés à éviter : 7
```

---

## 📊 Résumé des fichiers modifiés

| Fichier | Modifications |
|---------|--------------|
| `prompts/need_analysis_agent_prompts.py` | ✅ Ajout de `NEED_REGENERATION_PROMPT` |
| `need_analysis/need_analysis_agent.py` | ✅ Ajout de paramètres pour la régénération |
| `prompts/use_case_analysis_prompts.py` | ✅ Amélioration de `USE_CASE_REGENERATION_PROMPT` |
| `use_case_analysis/use_case_analysis_agent.py` | ✅ Ajout de paramètres pour commentaires et rejetés |
| `workflow/need_analysis_workflow.py` | ✅ Passage des bons paramètres aux agents |

---

## ✨ Avantages

1. **Intelligence contextuelle** : L'IA comprend ce qui a été rejeté et pourquoi
2. **Économie de tokens** : Pas besoin de retraiter tous les besoins validés
3. **Meilleure UX** : L'utilisateur voit que ses commentaires sont pris en compte
4. **Convergence rapide** : Le système converge plus vite vers les 5+5 éléments validés
5. **Pas de répétition** : Les éléments rejetés ne sont pas reproposés

---

## 🚀 Prochaines étapes possibles

- [ ] Ajouter un système de scoring pour mesurer la qualité de la régénération
- [ ] Permettre de "sauvegarder" des éléments favoris même non validés
- [ ] Ajouter une vue comparative entre itérations
- [ ] Exporter un rapport de décision avec historique des itérations

