# Spécification des Agents pour le Générateur de Rapport IA

## 🧩 Présentation du Projet

Ce projet vise à créer un **générateur de rapports assisté par IA** à usage interne pour une société de conseil spécialisée en Intelligence Artificielle.

Les utilisateurs peuvent uploader :
- des **fichiers Excel** résumant les ateliers de co-conception IA (cas d'usage, objectifs et bénéfices)
- des **transcriptions de réunions (PDF)** contenant les noms des intervenants, les horodatages et le texte des interventions


L'outil réalise les étapes suivantes :  
1. Ingestion et structuration des données  
2. Analyse thématique et des besoins  
3. Recherche web pour le contexte de l'entreprise  
4. Génération d'un **rapport en deux parties** :  
   - **Besoins identifiés & Citations**  
   - **Cas d'usage IA priorisés**  
5. Étape de **validation humaine**  
6. Export final du rapport approuvé

Frontend : **Streamlit**  
Backend : **LangGraph** avec orchestration multi-agent
Model : gpt-5-nano


---

flowchart LR
    %% Entrées multiples
    subgraph Inputs
        X1[📊 Excel Workshop Files] 
        X2[📄 PDF Transcripts] 
        X3[🌐 Company Info]
    end

    %% Agents de parsing
    subgraph Parsing
        WA[🧾 Workshop Agent] 
        TA[🧾 Transcript Agent] 
        WSA[🌐 Web Search Agent]
    end

    %% Analyse des besoins
    NA[🔍 Needs Analysis Agent]

    %% Génération et validation
    RG[💡 Report Generation Agent (2 sections)]
    HV[👤 Human Validation Agent]
    FR[📄 Final Report Agent]

    %% Flux multiples
    X1 --> |Batch processing| WA
    X2 --> |Batch processing| TA
    X3 --> WSA

    %% Convergence vers Needs Analysis
    WA --> NA
    TA --> NA
    WSA --> NA

    %% Suite du flux
    NA --> RG
    RG --> HV
    HV -->|Accepted| FR
    HV -->|Rejected| RG



# 📦 Détail des Agents
## 🧾 Workshop Agent

Rôle : Traiter et structurer les fichiers Excel des ateliers IA
Entrées : Excel uploadé par l'utilisateur avec 3 colonnes. Les noms ne sont pas fixes, mais dans la colonne A nous trouverons le nom de l'atelier, en colonne B le Use Case et en colonne C l'objectif ou le gain.
Sorties : JSON structuré avec cas d'usage, objectifs et bénéfices

Exemple de sortie :

{
  "workshop_id": "W123",
  "theme": "Optimisation des process",
  "use_cases": [
    {
      "title": "Automatisation du reporting",
      "objective": "Réduire le temps de reporting de 50%",
      "benefits": ["gain de temps", "moins d'erreurs"]
    }
  ]
}


### Traitement :

Extraction des lignes pertinentes
Nettoyage et normalisation des données
Résumé des points clés pour l'analyse des besoins
Supporte le traitement de plusieurs fichiers simultanément (batch)

## 🧾 Transcript Agent

Rôle : Traiter et structurer les fichiers PDF de transcriptions
Entrées : PDF uploadé par l'utilisateur
Sorties : JSON structuré avec speakers, timestamps et texte

Exemple de sortie :

[
  {
    "speaker": "Alice",
    "timestamp": "10:05",
    "text": "Nous devons automatiser le reporting pour gagner du temps."
  },
  {
    "speaker": "Bob",
    "timestamp": "10:07",
    "text": "Oui, et réduire les erreurs humaines."
  }
]


### Traitement :

Extraction texte et horodatages
Nettoyage et segmentation par intervenant
Supporte plusieurs PDF en parallèle

## 🌐 Web Search Agent

Rôle : Collecter des informations contextuelles sur l’entreprise
Entrées : Nom de l’entreprise ou informations initiales
Sorties : JSON avec description, secteur, chiffre d’affaires, taille et actualités

Exemple de sortie :

{
  "company_name": "TechAI",
  "sector": "Conseil en IA",
  "size": "50-100 employés",
  "revenue": "5M EUR",
  "description": "TechAI accompagne les entreprises dans la mise en place de solutions IA.",
  "recent_news": ["Lancement d'une nouvelle offre de recommandation IA"]
}


### Traitement :

Recherche web automatisée

Normalisation des données collectées

## 🔍 Needs Analysis Agent

Rôle : Identifier les besoins et prioriser les insights
Entrées : JSON du Workshop Agent, Transcript Agent, Web Search Agent
Sorties : JSON avec besoins identifiés et citations clés

Exemple de sortie :

{
  "identified_needs": [
    {
      "theme": "Automatisation",
      "quotes": [
        "Nous devons automatiser le reporting pour gagner du temps.",
        "Réduire les erreurs humaines."
      ]
    }
  ]
}


### Traitement :

Fusion des inputs des trois agents

Analyse thématique et extraction des besoins

Préparation pour la génération du rapport

💡 Report Generation Agent (2 sections)

Rôle : Générer le rapport final en deux sections
Entrées : Output du Needs Analysis Agent
Sorties : Rapport structuré (Markdown / PDF)

Exemple de sortie (Markdown) :

# Rapport IA

## Besoins identifiés & Citations
- Automatisation
  - "Nous devons automatiser le reporting pour gagner du temps."
  - "Réduire les erreurs humaines."

## Cas d'usage IA priorisés
1. Automatisation du reporting
2. Détection d'anomalies


### Traitement :

Génération en deux sections

Préparation pour validation humaine

## 👤 Human Validation Agent

Rôle : Vérifier et approuver le rapport généré
Entrées : Rapport généré
Sorties : Validation acceptée/rejetée

Notes :

Si rejeté → boucle vers le Report Generation Agent pour modification

## 📄 Final Report Agent

Rôle : Exporter le rapport final approuvé
Entrées : Rapport validé
Sorties : PDF / Markdown final, avec branding et résumé

###Traitement :
Ajout de logo, date, résumé
Export en formats multiples



