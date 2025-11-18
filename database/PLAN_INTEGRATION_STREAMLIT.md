# 📋 Plan d'intégration de la base de données dans `app/app_api.py`

## 🎯 Objectifs

1. **Sélection de projet** : Permettre à l'utilisateur de choisir un projet existant ou d'en créer un nouveau
2. **Chargement automatique** : Charger toutes les données du projet depuis la DB (documents, transcripts, résultats, etc.)
3. **Reprise de workflow** : Si un workflow a déjà été exécuté, afficher directement les résultats finaux
4. **Modification** : Permettre de modifier les données existantes et de relancer des workflows

---

## 📐 Architecture proposée

### 1. **Sélection de projet (Sidebar - en haut)**

**Emplacement** : En haut de la sidebar, avant la navigation

**Fonctionnalités** :
- **Selectbox** pour choisir un projet existant
- **Bouton "➕ Nouveau projet"** pour créer un nouveau projet
- **Afficher le nom de l'entreprise** du projet sélectionné

**Comportement** :
- **Obligatoire** : L'utilisateur DOIT sélectionner un projet existant ou en créer un nouveau
- Si un projet est sélectionné → Charger toutes ses données dans `st.session_state` (avec cache Streamlit)
- Si l'utilisateur change de projet → Recharger toutes les données
- Si aucun projet n'est sélectionné → Afficher un écran de sélection/création obligatoire

---

### 2. **Chargement des données du projet**

**Fonction** : `load_project_data(project_id: int)`

**Données à charger** :
- **Projet** : `company_name`, `company_info`, `created_at`
- **Documents** : Tous les documents du projet (workshops, transcripts, word_report)
  - **IMPORTANT** : Charger le texte extrait (`extracted_text`) pour chaque document
  - Stocker dans `st.session_state.uploaded_workshops` (avec texte)
  - Stocker dans `st.session_state.uploaded_transcripts` (avec texte)
  - Stocker dans `st.session_state.word_path` (avec texte extrait si disponible)
- **Agent Results** : Résultats finaux validés uniquement (pas d'états intermédiaires)
  - `needs` (workflow_type="word_validation" ou "need_analysis") → `st.session_state.validated_needs`
  - `use_cases` (workflow_type="word_validation" ou "need_analysis") → `st.session_state.validated_use_cases`
  - `challenges` (workflow_type="executive_summary") → `st.session_state.validated_challenges`
  - `recommendations` (workflow_type="executive_summary") → `st.session_state.validated_recommendations`
  - `atouts` (workflow_type="atouts") → `st.session_state.validated_atouts`
  - `maturity` (workflow_type="executive_summary") → `st.session_state.validated_maturity`
  - `rappel_mission` (workflow_type="rappel_mission") → `st.session_state.rappel_mission`
  - `web_search_results` (workflow_type="rappel_mission" ou "atouts") → `st.session_state.web_search_results`

**Quand charger** :
- Au démarrage si un projet est sélectionné
- Quand l'utilisateur change de projet
- Après chaque sauvegarde de workflow/result

---

### 3. **Sauvegarde automatique**

**Points de sauvegarde** :

#### 3.1. **Agent Results (Résultats finaux uniquement)**
- **IMPORTANT** : Ne sauvegarder QUE les résultats finaux validés, pas les états intermédiaires
- Sauvegarder dans la table `agent_results` avec `status="validated"` :
  - `workflow_type` = `"word_validation"`, `"need_analysis"`, `"executive_summary"`, `"atouts"`, `"rappel_mission"`
  - `result_type` = `"needs"`, `"use_cases"`, `"challenges"`, `"recommendations"`, `"atouts"`, `"maturity"`, `"rappel_mission"`, `"web_search_results"`
  - `data` = Les données structurées (JSONB)
  - `status` = `"validated"` (uniquement)

**Quand sauvegarder** :
- **Après validation dans "Validation des besoins et use cases"** → `result_type="needs"`, `workflow_type="word_validation"`
- **Après validation dans "Validation des besoins et use cases"** → `result_type="use_cases"`, `workflow_type="word_validation"`
- **Après validation finale des besoins (workflow need_analysis)** → `result_type="needs"`, `workflow_type="need_analysis"` (si pas déjà validé via word_validation)
- **Après validation finale des use cases (workflow need_analysis)** → `result_type="use_cases"`, `workflow_type="need_analysis"` (si pas déjà validé via word_validation)
- **Après validation finale des enjeux** → `result_type="challenges"`, `workflow_type="executive_summary"`
- **Après validation finale des recommandations** → `result_type="recommendations"`, `workflow_type="executive_summary"`
- **Après validation finale des atouts** → `result_type="atouts"`, `workflow_type="atouts"`
- **Après validation finale de la maturité** → `result_type="maturity"`, `workflow_type="executive_summary"`
- **Après génération du rappel de mission** → `result_type="rappel_mission"`, `workflow_type="rappel_mission"`
- **Après recherche web (rappel mission ou atouts)** → `result_type="web_search_results"`, `workflow_type="rappel_mission"` ou `"atouts"`

**Logique** :
- Si le workflow n'est pas terminé → Ne rien sauvegarder
- Si l'utilisateur revient plus tard et le workflow n'est pas terminé → Redémarrer le workflow
- Seuls les résultats validés sont persistés

#### 3.2. **Documents (avec texte extrait)**
- Sauvegarder les documents uploadés dans la table `documents` :
  - `file_name`, `file_type`, `file_path`
  - **`extracted_text`** : **OBLIGATOIRE** pour transcripts, workshops, et word_report
  - `file_metadata` (informations supplémentaires : speakers, timestamps, etc.)

**Quand sauvegarder** :
- **Après upload de transcripts** → Extraire le texte et sauvegarder dans `extracted_text`
- **Après upload de workshops** → Extraire le texte et sauvegarder dans `extracted_text`
- **Après upload/génération du word_report** → Extraire le texte (besoins + use cases) et sauvegarder dans `extracted_text`
- Stocker le chemin du fichier ET le texte extrait

---

### 4. **Reprise de workflow - "Générer les Use Cases"**

**Comportement actuel** :
- L'utilisateur clique sur "Générer les Use Cases"
- Il doit uploader les fichiers et démarrer le workflow

**Comportement proposé** :

#### 4.1. **Vérification de l'état**
- Vérifier si un workflow `need_analysis` existe pour ce projet
- Vérifier si des résultats `needs` et `use_cases` existent avec `status="validated"`

#### 4.2. **Si résultats validés existent** :
- **Afficher directement la page finale** avec :
  - Les besoins validés (depuis `agent_results` avec `result_type="needs"`, `status="validated"`)
  - Les use cases validés (depuis `agent_results` avec `result_type="use_cases"`, `status="validated"`)
  - Un bouton "✏️ Modifier" pour modifier les résultats
  - Un bouton "🔄 Régénérer" pour tout recommencer (supprime les résultats et relance)

#### 4.3. **Si aucun résultat validé** :
- Comportement actuel : afficher le formulaire de démarrage
- **Si workflow en cours mais pas terminé** → Redémarrer le workflow (pas de reprise d'état intermédiaire)

**Interface proposée** :
```
┌─────────────────────────────────────────┐
│ 🔍 Générer les Use Cases                │
├─────────────────────────────────────────┤
│                                         │
│ ✅ Workflow terminé - Résultats disponibles │
│                                         │
│ 📋 Besoins identifiés (5)               │
│ [Afficher les besoins validés]         │
│                                         │
│ 💼 Use Cases générés (8)                │
│ [Afficher les use cases validés]       │
│                                         │
│ [✏️ Modifier] [🔄 Régénérer]            │
└─────────────────────────────────────────┘
```

---

### 5. **NOUVELLE SECTION : "Validation des besoins et use cases"**

**Position** : Nouvelle section dans la sidebar, située **au-dessus** de "Génération des Enjeux et Recommandations"

**Objectif** : Créer une source de vérité unique pour les besoins et use cases validés, réutilisable par tous les workflows suivants

**Fonctionnalités** :
1. **Upload du Word Report** :
   - Upload du fichier Word généré (depuis "Générer les Use Cases" ou uploadé manuellement)
   - Sauvegarde dans `documents` avec `file_type="word_report"` et `extracted_text`

2. **Extraction automatique** :
   - Utiliser `WordReportExtractor` pour extraire besoins et use cases
   - Afficher les résultats extraits

3. **Validation/Modification** :
   - Interface de validation (comme actuellement dans "Génération des Enjeux et Recommandations")
   - Permettre de modifier les besoins et use cases
   - Permettre d'ajouter/supprimer des éléments

4. **Sauvegarde** :
   - Sauvegarder les besoins validés dans `agent_results` :
     - `workflow_type="word_validation"` (nouveau type)
     - `result_type="needs"`, `status="validated"`
   - Sauvegarder les use cases validés dans `agent_results` :
     - `workflow_type="word_validation"`
     - `result_type="use_cases"`, `status="validated"`
   - Sauvegarder le texte extrait du Word dans `documents.extracted_text`

5. **Réutilisation** :
   - Ces données validées servent ensuite de base pour :
     - "Génération des Enjeux et Recommandations" (executive summary)
     - Tous les autres workflows qui ont besoin des besoins/use cases

**Avantages** :
- ✅ **Source de vérité unique** : Les besoins/use cases sont validés une seule fois
- ✅ **Réutilisable** : Tous les workflows suivants utilisent les mêmes données
- ✅ **Séparation des responsabilités** : L'extraction/validation est séparée de la génération executive summary
- ✅ **Plus logique** : Le flux est plus clair (validation → utilisation)

**Interface proposée** :
```
┌─────────────────────────────────────────┐
│ ✅ Validation des besoins et use cases │
├─────────────────────────────────────────┤
│                                         │
│ 📄 Rapport Word                         │
│ [Upload fichier .docx]                  │
│                                         │
│ 🔍 Extraction                          │
│ [Résultats extraits automatiquement]   │
│                                         │
│ ✏️ Validation/Modification              │
│ [Interface de validation]               │
│ [Besoins] [Use Cases]                  │
│                                         │
│ [✅ Valider et sauvegarder]             │
└─────────────────────────────────────────┘
```

### 6. **Reprise de workflow - "Génération des Enjeux et Recommandations"**

**Comportement modifié** :

- **Vérifier d'abord** si des besoins/use cases validés existent dans "Validation des besoins et use cases" :
  - `workflow_type="word_validation"`, `result_type="needs"`, `status="validated"`
  - `workflow_type="word_validation"`, `result_type="use_cases"`, `status="validated"`
- **Si oui** → Utiliser ces données validées (plus besoin d'uploader le Word dans cette section)
- **Si non** → Afficher un message : "⚠️ Veuillez d'abord valider les besoins et use cases dans la section 'Validation des besoins et use cases'"

- Vérifier si des résultats validés existent :
  - `challenges` (workflow_type="executive_summary", status="validated")
  - `recommendations` (workflow_type="executive_summary", status="validated")
  - `maturity` (workflow_type="executive_summary", status="validated")
- Si oui → Afficher directement la page finale avec tous les résultats
- Si non → Comportement actuel (redémarrer si workflow en cours mais pas terminé)

### 7. **Reprise de workflow - "Rappel de la mission"**

- Vérifier si un résultat `rappel_mission` existe (workflow_type="rappel_mission", status="validated")
- Si oui → Afficher directement le rappel de mission
- Si non → Comportement actuel

### 8. **Reprise de workflow - "Atouts de l'entreprise"**

- Vérifier si un résultat `atouts` existe (workflow_type="atouts", status="validated")
- Vérifier si `web_search_results` existe (workflow_type="atouts", status="validated")
- Si oui → Afficher directement les atouts et les résultats de recherche web
- Si non → Comportement actuel

---

### 9. **Modification des données**

#### 9.1. **Modifier les besoins**
- Bouton "✏️ Modifier" sur la page des besoins
- Permet de :
  - Supprimer des besoins
  - Ajouter des besoins manuellement
  - Modifier le texte des besoins
- Sauvegarder dans `agent_results` avec `status="validated"`

#### 9.2. **Modifier les use cases**
- Bouton "✏️ Modifier" sur la page des use cases
- Permet de :
  - Supprimer des use cases
  - Ajouter des use cases manuellement
  - Modifier le texte des use cases
- Sauvegarder dans `agent_results` avec `status="validated"`

#### 9.3. **Régénérer un workflow**
- Bouton "🔄 Régénérer"
- Supprime les résultats existants (`status="rejected"`)
- Relance le workflow depuis le début
- Crée un nouveau `thread_id`

---

### 10. **Gestion des documents**

#### 9.1. **Upload de documents**
- Quand l'utilisateur upload un fichier :
  1. Sauvegarder dans `documents` avec `project_id`
  2. Stocker le chemin du fichier
  3. Extraire le texte si possible (pour transcripts)
  4. Mettre à jour `st.session_state`

#### 9.2. **Affichage des documents existants**
- Dans la page "Upload de documents" :
  - Afficher la liste des documents déjà uploadés pour ce projet
  - Permettre de supprimer des documents
  - Permettre de ré-uploader

---

### 11. **Structure des données dans session_state**

**Nouveau** :
```python
st.session_state.current_project_id = None  # ID du projet sélectionné
st.session_state.current_project = None     # Objet Project
st.session_state.project_loaded = False    # Flag pour savoir si les données sont chargées
```

**Existant (à charger depuis DB)** :
```python
st.session_state.company_name = ...
st.session_state.uploaded_workshops = ...
st.session_state.uploaded_transcripts = ...
st.session_state.word_path = ...
st.session_state.workflow_state = ...
st.session_state.validated_needs = ...
st.session_state.validated_use_cases = ...
# etc.
```

---

### 12. **Fonctions à créer**

#### 12.1. **Gestion de projet**
- `load_project_list()` → Liste tous les projets (avec cache Streamlit)
- `create_new_project(company_name, company_info)` → Crée un nouveau projet
- `load_project_data(project_id)` → Charge toutes les données d'un projet (avec cache Streamlit)
  - Charge les documents avec `extracted_text`
  - Charge les résultats validés uniquement
- `save_project_data(project_id)` → Sauvegarde les modifications

#### 12.2. **Sauvegarde résultats (finaux uniquement)**
- `save_agent_result(project_id, workflow_type, result_type, data, status="validated")`
  - Sauvegarde uniquement les résultats finaux validés
- `load_agent_results(project_id, workflow_type, result_type, status="validated")` → Retourne les résultats validés
- `has_validated_results(project_id, workflow_type, result_type)` → Vérifie si des résultats validés existent

#### 12.3. **Gestion documents (avec texte)**
- `save_document(project_id, file_name, file_type, file_path, extracted_text, metadata)`
  - **extracted_text est obligatoire** pour transcripts, workshops, word_report
- `load_documents(project_id, file_type=None)` → Retourne les documents avec `extracted_text`
- `extract_text_from_file(file_path, file_type)` → Extrait le texte selon le type de fichier

---

### 13. **Ordre d'implémentation recommandé**

#### **Phase 1 : Sélection de projet (obligatoire)**
1. Ajouter le selectbox de projet dans la sidebar (en haut, obligatoire)
2. Créer `load_project_list()` avec cache Streamlit
3. Créer `create_new_project()` avec formulaire modal
4. Gérer le changement de projet (rechargement avec cache)

#### **Phase 2 : Sauvegarde des documents (avec texte)**
1. Créer `extract_text_from_file()` pour extraire le texte selon le type
2. Modifier l'upload de documents pour extraire et sauvegarder le texte
3. Sauvegarder dans `documents` avec `extracted_text` rempli
4. Tester avec transcripts, workshops, word_report

#### **Phase 3 : Chargement des données (avec cache)**
1. Créer `load_project_data(project_id)` avec cache Streamlit
2. Charger les documents existants avec `extracted_text`
3. Charger les agent results validés uniquement
4. Mapper vers `st.session_state`

#### **Phase 4 : Sauvegarde des résultats finaux**
1. Modifier les validations pour sauvegarder dans `agent_results`
2. Sauvegarder uniquement après validation finale (status="validated")
3. Gérer tous les types : needs, use_cases, challenges, recommendations, atouts, maturity, rappel_mission, web_search_results

#### **Phase 5 : Nouvelle section "Validation des besoins et use cases"**
1. Créer la nouvelle section dans la sidebar (au-dessus de "Génération des Enjeux et Recommandations")
2. Implémenter l'upload du Word Report
3. Implémenter l'extraction automatique (WordReportExtractor)
4. Implémenter l'interface de validation/modification
5. Sauvegarder les résultats validés dans `agent_results` avec `workflow_type="word_validation"`
6. Sauvegarder le texte extrait dans `documents.extracted_text`

#### **Phase 6 : Reprise de workflow**
1. Modifier "Générer les Use Cases" pour vérifier les résultats validés
2. Afficher la page finale si résultats existent
3. Modifier "Génération des Enjeux et Recommandations" pour utiliser les données de "Validation des besoins et use cases"
4. Même chose pour "Rappel de la mission"
5. Même chose pour "Atouts de l'entreprise"

#### **Phase 7 : Modification**
1. Ajouter les boutons "✏️ Modifier" et "🔄 Régénérer"
2. Implémenter la logique de modification (mise à jour dans DB)
3. Implémenter la logique de régénération (suppression + redémarrage)

---

### 14. **Points d'attention**

#### 14.1. **Sélection de projet obligatoire**
- **Pas de compatibilité avec l'existant** : L'utilisateur DOIT sélectionner ou créer un projet
- Si aucun projet n'est sélectionné → Afficher un écran de sélection/création obligatoire
- Bloquer l'accès aux autres pages tant qu'aucun projet n'est sélectionné

#### 14.2. **Performance avec cache Streamlit**
- Utiliser `@st.cache_data` pour `load_project_list()` et `load_project_data()`
- Invalider le cache lors de la sauvegarde de nouvelles données
- Éviter de recharger à chaque rerun

#### 14.3. **Gestion des erreurs**
- Gérer les cas où la DB n'est pas disponible (afficher message d'erreur)
- Gérer les cas où un projet n'a pas de données (comportement normal, afficher formulaire)
- Afficher des messages d'erreur clairs

#### 14.4. **Workflow non terminé**
- Si un workflow est en cours mais pas terminé → **Redémarrer le workflow**
- Ne pas sauvegarder les états intermédiaires
- Seuls les résultats finaux validés sont persistés

---

### 15. **Exemple de flux utilisateur**

#### **Scénario 1 : Nouveau projet**
1. Utilisateur arrive sur l'app → Écran de sélection/création obligatoire
2. Clique sur "➕ Nouveau projet"
3. Saisit le nom de l'entreprise
4. Upload les documents (transcripts, workshops)
5. **Les documents sont sauvegardés dans la DB avec le texte extrait**
6. Lance "Générer les Use Cases"
7. Le workflow démarre (pas de sauvegarde d'état intermédiaire)
8. **Les résultats sont sauvegardés uniquement après validation finale**

#### **Scénario 2 : Projet existant - Résultats validés**
1. Utilisateur sélectionne un projet existant
2. **Les données sont chargées depuis la DB (avec cache)** :
   - Documents avec texte extrait
   - Résultats validés uniquement
3. Clique sur "Générer les Use Cases"
4. **→ Affiche directement la page finale avec besoins et use cases (depuis DB)**
5. Peut modifier ou régénérer

#### **Scénario 2bis : Nouveau flux avec "Validation des besoins et use cases"**
1. Utilisateur sélectionne un projet
2. Clique sur "Validation des besoins et use cases"
3. Upload le Word Report généré
4. Extraction automatique des besoins et use cases
5. Validation/modification des résultats
6. Sauvegarde dans DB (`workflow_type="word_validation"`)
7. Clique sur "Génération des Enjeux et Recommandations"
8. **→ Utilise automatiquement les besoins/use cases validés (plus besoin d'uploader le Word)**

#### **Scénario 3 : Projet existant - Workflow en cours mais pas terminé**
1. Utilisateur sélectionne un projet
2. Clique sur "Générer les Use Cases"
3. **Aucun résultat validé trouvé**
4. **→ Affiche le formulaire de démarrage (redémarrer le workflow)**
5. Pas de reprise d'état intermédiaire

#### **Scénario 4 : Projet existant - Modification**
1. Utilisateur sélectionne un projet
2. Clique sur "Générer les Use Cases"
3. Voit les résultats existants (chargés depuis DB)
4. Clique sur "✏️ Modifier"
5. Modifie les besoins/use cases
6. **Les modifications sont sauvegardées dans la DB (mise à jour de `agent_results`)**

#### **Scénario 5 : Projet existant - Régénération**
1. Utilisateur sélectionne un projet
2. Clique sur "Générer les Use Cases"
3. Voit les résultats existants
4. Clique sur "🔄 Régénérer"
5. **Les résultats existants sont supprimés (status="rejected")**
6. Le workflow redémarre depuis le début

---

### 16. **Interface utilisateur proposée**

#### **Sidebar - Sélection de projet**
```
┌─────────────────────────────┐
│ 🤖 aikoGPT                  │
├─────────────────────────────┤
│                             │
│ 📁 Projet                    │
│ [Selectbox: Projet...]      │
│ [➕ Nouveau projet]          │
│                             │
│ ─────────────────────────── │
│                             │
│ Navigation                  │
│ [Accueil]                   │
│ ...                         │
└─────────────────────────────┘
```

#### **Page "Générer les Use Cases" - Workflow terminé**
```
┌─────────────────────────────────────────┐
│ 🔍 Générer les Use Cases                │
├─────────────────────────────────────────┤
│                                         │
│ ✅ Analyse terminée                     │
│                                         │
│ 📋 Besoins identifiés (5)               │
│ ┌─────────────────────────────────┐   │
│ │ • Besoin 1                      │   │
│ │ • Besoin 2                      │   │
│ │ ...                             │   │
│ └─────────────────────────────────┘   │
│                                         │
│ 💼 Use Cases générés (8)                │
│ ┌─────────────────────────────────┐   │
│ │ • Use Case 1                    │   │
│ │ • Use Case 2                    │   │
│ │ ...                             │   │
│ └─────────────────────────────────┘   │
│                                         │
│ [✏️ Modifier] [🔄 Régénérer]            │
└─────────────────────────────────────────┘
```

---

## ✅ Résumé

Ce plan permet de :
1. ✅ **Sélectionner/créer un projet** (obligatoire, pas de mode sans projet)
2. ✅ **Sauvegarder le texte extrait** pour transcripts, workshops, word_report
3. ✅ **Sauvegarder uniquement les résultats finaux validés** (pas d'états intermédiaires)
4. ✅ **Nouvelle section "Validation des besoins et use cases"** : Source de vérité unique réutilisable
5. ✅ **Afficher directement les résultats** si validés (besoins, use cases, enjeux, recommandations, atouts, maturité, rappel mission)
6. ✅ **Redémarrer le workflow** si pas terminé (pas de reprise d'état intermédiaire)
7. ✅ **Modifier les données** existantes
8. ✅ **Utiliser le cache Streamlit** pour les performances

**Points clés** :
- ❌ **Pas de sauvegarde d'états intermédiaires** → Si workflow pas terminé, redémarrer
- ✅ **Sauvegarde uniquement des résultats finaux validés** → Plus simple à gérer
- ✅ **Texte extrait obligatoire** → Pour transcripts, workshops, word_report
- ✅ **Projet obligatoire** → Pas de mode sans projet

**Prochaine étape** : Implémenter phase par phase selon l'ordre recommandé.

