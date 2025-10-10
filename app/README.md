# Application AIKO - Traitement d'Ateliers IA & Transcriptions

Interface Streamlit pour traiter des fichiers Excel d'ateliers IA et des PDFs de transcriptions, avec génération de rapports structurés et analyse des besoins métier.

## 🚀 Lancement de l'application

### Méthode 1: Script de lancement (recommandé)
```bash
cd /home/addeche/aiko/aikoGPT/app
python run.py
```

### Méthode 2: Commande Streamlit directe avec uv
```bash
cd /home/addeche/aiko/aikoGPT
uv run streamlit run app/app.py
```

### Méthode 3: Commande Streamlit classique
```bash
cd /home/addeche/aiko/aikoGPT
streamlit run app/app.py
```

L'application sera accessible sur: http://localhost:8501

## 📋 Format de fichier attendu

Votre fichier Excel doit contenir au moins 3 colonnes :
- **Atelier** : Nom de l'atelier
- **Use_Case** : Description du cas d'usage  
- **Objective** : Objectif du cas d'usage

## 🔧 Fonctionnalités

### Phase 1: Traitement d'Ateliers IA
- ✅ Upload de fichiers Excel (.xlsx, .xls)
- ✅ Traitement automatique avec IA (GPT-5-nano)
- ✅ Affichage des résultats structurés
- ✅ Téléchargement des résultats en JSON

### Phase 2: Traitement de Transcriptions PDF
- ✅ Upload multiple de fichiers PDF
- ✅ Parsing automatique des transcriptions
- ✅ Filtrage des parties intéressantes avec IA
- ✅ Analyse sémantique (besoins, frustrations, opportunités, citations)
- ✅ Métriques détaillées et téléchargement JSON

### Phase 3: Recherche Web
- ✅ Recherche d'informations sur les entreprises
- ✅ Collecte de données contextuelles (secteur, taille, CA, actualités)
- ✅ Affichage structuré des informations
- ✅ Téléchargement des résultats en JSON

### Phase 4: Analyse des Besoins (NOUVEAU)
- ✅ Intégration des résultats des 3 phases précédentes
- ✅ Analyse des besoins métier avec le workflow LangGraph
- ✅ Identification des besoins prioritaires
- ✅ Affichage des thèmes et statistiques
- ✅ Téléchargement de l'analyse complète

## 📊 Résultats

### Phase 1 - Ateliers IA
- Métriques globales (nombre d'ateliers, cas d'usage)
- Détail par atelier avec thème et cas d'usage
- Structure JSON téléchargeable

### Phase 2 - Transcriptions PDF
- **Métriques globales** : nombre de PDF traités, caractères analysés, parties sélectionnées
- **Analyse sémantique** : besoins exprimés, frustrations, opportunités, citations
- **Détail par PDF** : interventions, intervenants, analyse détaillée
- **Téléchargement JSON** : résultats complets structurés

### Phase 3 - Recherche Web
- **Informations entreprise** : description, secteur, taille, chiffre d'affaires
- **Actualités récentes** : développements et annonces
- **Métriques contextuelles** : données structurées sur l'entreprise
- **Téléchargement JSON** : informations complètes

### Phase 4 - Analyse des Besoins (NOUVEAU)
- **Besoins identifiés** : liste détaillée avec descriptions, priorités, thèmes
- **Métriques d'analyse** : nombre de besoins, thèmes, priorités élevées
- **Résumé thématique** : regroupement par thèmes et statistiques
- **Téléchargement JSON** : analyse complète des besoins métier

## 🛠️ Dépendances

L'application utilise :
- Streamlit pour l'interface
- WorkshopAgent pour le traitement des ateliers
- TranscriptAgent pour le traitement des transcriptions
- WebSearchAgent pour la recherche web
- NeedAnalysisWorkflow pour l'analyse des besoins
- OpenAI API pour l'analyse IA (GPT-5-nano)
- Pandas pour le traitement des données
- PDF parsing pour l'extraction de contenu
- LangGraph pour l'orchestration du workflow
