# Explication des variables dans les prompts Executive Summary

Ce document explique d'où viennent toutes les variables entre `{}` dans les prompts `executive_summary_prompts.py`, à quoi elles font référence et sous quelle forme elles sont injectées.

## IDENTIFY_CHALLENGES_PROMPT

### `{interviewer_note}`
- **Origine** : `ExecutiveSummaryState.interviewer_note` (ligne 476 dans `executive_summary_workflow.py`)
- **Format** : `str` - Texte libre saisi par l'utilisateur
- **Valeur par défaut** : `"Aucune note de l'interviewer"` si vide
- **Injection** : Ligne 115 dans `executive_summary_agent.py`
- **Contenu** : Note contextuelle et insights clés de l'interviewer

### `{transcript_content}`
- **Origine** : `ExecutiveSummaryState.transcript_enjeux_citations` (ligne 473 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_citations()` (lignes 771-782)
- **Format de sortie** : Une ligne par citation : `"{speaker}: {citation}"`
- **Structure source** : Liste de dicts avec clés `speaker`, `citation`, `timestamp`, `contexte`, `speaker_type`, `speaker_level`
- **Injection** : Ligne 108 dans `executive_summary_agent.py`
- **Exemple** : 
  ```
  Jean Dupont: Nous avons besoin d'automatiser la gestion des stocks
  Marie Martin: La qualité des données est un enjeu majeur
  ```

### `{workshop_content}`
- **Origine** : `ExecutiveSummaryState.workshop_enjeux_citations` (ligne 474 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_workshop_info()` (lignes 784-796)
- **Format de sortie** : Une ligne par information : `"{atelier} - {use_case}: {objectif}"`
- **Structure source** : Liste de dicts avec clés `atelier`, `use_case`, `objectif`, `type`
- **Injection** : Ligne 109 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  Atelier Production - Automatisation stocks: Réduire les erreurs de saisie
  Atelier Qualité - Traçabilité: Améliorer la conformité réglementaire
  ```

### `{final_needs}`
- **Origine** : `ExecutiveSummaryState.extracted_needs` (ligne 475 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_needs()` (lignes 356-367 dans `executive_summary_agent.py`)
- **Format de sortie** : Liste numérotée des titres uniquement : `"{i}. {titre}"`
- **Structure source** : Liste de dicts avec clés `titre` (ou `theme` en fallback)
- **Injection** : Ligne 110 dans `executive_summary_agent.py` (après formatage)
- **Exemple** :
  ```
  1. Automatisation de la gestion des stocks
  2. Amélioration de la qualité des données
  3. Optimisation des processus qualité
  ```
- **Note importante** : Seuls les TITRES sont passés, pas les descriptions ni les citations

## REGENERATE_CHALLENGES_PROMPT

### `{previous_challenges}`
- **Origine** : Concaténation de `validated_challenges` + `rejected_challenges` (lignes 86-90 dans `executive_summary_agent.py`)
- **Format** : `str` - Formaté via `_format_challenges()` (lignes 382-394)
- **Format de sortie** : Une ligne par enjeu : `"- {id}: {titre}\n  {description}"`
- **Structure source** : Liste de dicts avec clés `id`, `titre`, `description`, `besoins_lies`
- **Injection** : Ligne 101 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  - E1: Capitalisation des connaissances internes
    Transformer le capital intellectuel...
  - E2: Optimisation opérationnelle
    Améliorer l'efficacité des processus...
  ```

### `{rejected_challenges}`
- **Origine** : `ExecutiveSummaryState.rejected_challenges` (ligne 479 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_challenges()` (lignes 382-394)
- **Format de sortie** : Même format que `previous_challenges`
- **Injection** : Ligne 102 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucun"` si vide

### `{challenges_feedback}`
- **Origine** : `ExecutiveSummaryState.challenges_feedback` (ligne 481 dans `executive_summary_workflow.py`)
- **Format** : `str` - Texte libre saisi par l'utilisateur
- **Injection** : Ligne 103 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucun commentaire"` si vide

### `{validated_challenges}`
- **Origine** : `ExecutiveSummaryState.validated_challenges` (ligne 480 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_challenges()` (lignes 382-394)
- **Format de sortie** : Même format que `previous_challenges`
- **Injection** : Ligne 104 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucun"` si vide

### `{validated_count}`
- **Origine** : Calculé depuis `len(validated_challenges)` (ligne 97 dans `executive_summary_agent.py`)
- **Format** : `int` converti implicitement en `str`
- **Injection** : Ligne 105 dans `executive_summary_agent.py`

### `{rejected_count}`
- **Origine** : Calculé depuis `len(rejected_challenges)` (ligne 98 dans `executive_summary_agent.py`)
- **Format** : `int` converti implicitement en `str`
- **Injection** : Ligne 106 dans `executive_summary_agent.py`

### `{interviewer_note}`, `{transcript_content}`, `{workshop_content}`, `{final_needs}`
- **Même origine et format que dans IDENTIFY_CHALLENGES_PROMPT**
- **Injection** : Lignes 107-110 dans `executive_summary_agent.py`

## EVALUATE_MATURITY_PROMPT

### `{transcript_content}`
- **Origine** : `ExecutiveSummaryState.transcript_maturite_citations` (ligne 589 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_maturite_citations()` (lignes 798-810)
- **Format de sortie** : Une ligne par citation : `"[{type_info}] {speaker}: {citation}"`
- **Structure source** : Liste de dicts avec clés `speaker`, `citation`, `type_info` (peut être `outils_digitaux`, `processus_automatises`, `gestion_donnees`, `culture_numérique`)
- **Injection** : Ligne 193 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  [outils_digitaux] Jean Dupont: Nous utilisons Excel pour la gestion des stocks
  [gestion_donnees] Marie Martin: Les données sont dispersées dans plusieurs systèmes
  ```

### `{workshop_content}`
- **Origine** : `ExecutiveSummaryState.workshop_maturite_citations` (ligne 590 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_workshop_maturite()` (lignes 812-824)
- **Format de sortie** : Une ligne par information : `"[{type_info}] {atelier} - {use_case}"`
- **Structure source** : Liste de dicts avec clés `atelier`, `use_case`, `type_info`
- **Injection** : Ligne 194 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  [processus_automatises] Atelier Production - Gestion stocks: Automatisation existante
  [culture_numérique] Atelier Qualité - Formation: Besoin d'acculturation IA
  ```

### `{final_needs}`
- **Origine** : `ExecutiveSummaryState.extracted_needs` (ligne 591 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_needs()` (lignes 356-367)
- **Format de sortie** : Liste numérotée des titres (même format que dans IDENTIFY_CHALLENGES_PROMPT)
- **Injection** : Ligne 195 dans `executive_summary_agent.py`

### `{final_use_cases}`
- **Origine** : `ExecutiveSummaryState.extracted_use_cases` (ligne 592 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_use_cases()` (lignes 369-380)
- **Format de sortie** : Liste numérotée avec titre et description : `"{i}. {titre}:\n   {description}"`
- **Structure source** : Liste de dicts avec clés `titre`, `description`, `famille` (optionnel)
- **Injection** : Ligne 196 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  1. Automatisation de la gestion des stocks:
     Système automatisé pour gérer les stocks en temps réel...
  
  2. Analyse prédictive des besoins:
     Utilisation de modèles ML pour prévoir les besoins...
  ```

## GENERATE_RECOMMENDATIONS_PROMPT

### `{maturite_ia}`
- **Origine** : `ExecutiveSummaryState.maturity_score` et `maturity_summary` (lignes 621-624 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté ligne 254 dans `executive_summary_agent.py`
- **Format de sortie** : `"Échelle: {echelle}/5\n{phrase_resumant}"`
- **Structure source** : Dict avec clés `echelle` (int 1-5) et `phrase_resumant` (str)
- **Injection** : Ligne 293 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  Échelle: 3/5
  L'entreprise utilise des outils digitaux de base (Excel, ERP) mais manque de centralisation des données et d'automatisation avancée.
  ```

### `{final_needs}`
- **Même origine et format que dans EVALUATE_MATURITY_PROMPT**
- **Injection** : Ligne 294 dans `executive_summary_agent.py`

### `{final_use_cases}`
- **Même origine et format que dans EVALUATE_MATURITY_PROMPT**
- **Injection** : Ligne 295 dans `executive_summary_agent.py`

### `{recommendations_feedback}`
- **Origine** : `ExecutiveSummaryState.recommendations_feedback` (ligne 630 dans `executive_summary_workflow.py`)
- **Format** : `str` - Texte libre saisi par l'utilisateur
- **Injection** : Ligne 296 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucun commentaire spécifique. Génère des recommandations adaptées à la maturité IA et aux besoins identifiés."` si vide

## REGENERATE_RECOMMENDATIONS_PROMPT

### `{previous_recommendations}`
- **Origine** : Concaténation de `validated_recommendations` + `rejected_recommendations` (lignes 262-266 dans `executive_summary_agent.py`)
- **Format** : `str` - Formaté via `_format_recommendations()` (lignes 396-420)
- **Format de sortie** : Une ligne par recommandation : `"- {id}: {titre}\n  {description}"` (si titre et description présents)
- **Structure source** : Liste de dicts avec clés `id`, `titre`, `description`
- **Injection** : Ligne 277 dans `executive_summary_agent.py`
- **Exemple** :
  ```
  - R1: Fiabiliser et centraliser les données
    Mettre en place une infrastructure de données unifiée...
  - R2: Acculturer les équipes aux IA simples
    Former les collaborateurs aux outils d'IA accessibles...
  ```

### `{rejected_recommendations}`
- **Origine** : `ExecutiveSummaryState.rejected_recommendations` (ligne 628 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_recommendations()` (lignes 396-420)
- **Format de sortie** : Même format que `previous_recommendations`
- **Injection** : Ligne 278 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucune"` si vide

### `{recommendations_feedback}`
- **Origine** : `ExecutiveSummaryState.recommendations_feedback` (ligne 630 dans `executive_summary_workflow.py`)
- **Format** : `str` - Texte libre saisi par l'utilisateur
- **Injection** : Ligne 279 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucun commentaire"` si vide

### `{validated_recommendations}`
- **Origine** : `ExecutiveSummaryState.validated_recommendations` (ligne 629 dans `executive_summary_workflow.py`)
- **Format** : `str` - Formaté via `_format_recommendations()` (lignes 396-420)
- **Format de sortie** : Même format que `previous_recommendations`
- **Injection** : Ligne 280 dans `executive_summary_agent.py`
- **Valeur par défaut** : `"Aucune"` si vide

### `{validated_count}`
- **Origine** : Calculé depuis `len(validated_recommendations)` (ligne 273 dans `executive_summary_agent.py`)
- **Format** : `int` converti implicitement en `str`
- **Injection** : Ligne 281 dans `executive_summary_agent.py`

### `{rejected_count}`
- **Origine** : Calculé depuis `len(rejected_recommendations)` (ligne 274 dans `executive_summary_agent.py`)
- **Format** : `int` converti implicitement en `str`
- **Injection** : Ligne 282 dans `executive_summary_agent.py`

### `{maturite_ia}`, `{final_needs}`, `{final_use_cases}`
- **Même origine et format que dans GENERATE_RECOMMENDATIONS_PROMPT**
- **Injection** : Lignes 283-285 dans `executive_summary_agent.py`

## EXTRACT_ENJEUX_CITATIONS_PROMPT

### `{transcript_text}`
- **Origine** : Formaté depuis les interventions intéressantes extraites par `TranscriptEnjeuxAgent.extract_citations()` (ligne 70 dans `transcript_enjeux_agent.py`)
- **Format** : `str` - Formaté via `_prepare_transcript_text()` (lignes 84-102 dans `transcript_enjeux_agent.py`)
- **Format de sortie** : Une ligne par intervention : `"[{i}] type={speaker_type} {timestamp} {speaker}: {text}"`
- **Structure source** : Liste de dicts avec clés `speaker`, `timestamp`, `text`, `speaker_type`
- **Injection** : Ligne 109 dans `transcript_enjeux_agent.py`
- **Note** : Ce prompt est utilisé dans `TranscriptEnjeuxAgent`, pas directement dans `ExecutiveSummaryAgent`

## EXTRACT_MATURITE_CITATIONS_PROMPT

### `{transcript_text}`
- **Même origine et format que dans EXTRACT_ENJEUX_CITATIONS_PROMPT**
- **Note** : Utilisé dans `TranscriptMaturiteAgent` (similaire à `TranscriptEnjeuxAgent`)

## EXTRACT_WORKSHOP_ENJEUX_PROMPT

### `{workshop_data}`
- **Origine** : Formaté depuis les données d'atelier extraites par `WorkshopEnjeuxAgent.extract_informations()` (ligne 89 dans `workshop_enjeux_agent.py`)
- **Format** : `str` - Formaté via `_prepare_workshop_text()` (lignes 142-154 dans `workshop_enjeux_agent.py`)
- **Format de sortie** : 
  ```
  Atelier: {theme}
  - {title}: {objective}
  - {title}: {objective}
  ```
- **Structure source** : Dict avec clés `theme`, `use_cases` (liste de dicts avec `title`, `objective`)
- **Injection** : Ligne 92 dans `workshop_enjeux_agent.py`
- **Note** : Ce prompt est utilisé dans `WorkshopEnjeuxAgent`, pas directement dans `ExecutiveSummaryAgent`

## EXTRACT_WORKSHOP_MATURITE_PROMPT

### `{workshop_data}`
- **Même origine et format que dans EXTRACT_WORKSHOP_ENJEUX_PROMPT**
- **Note** : Utilisé dans `WorkshopMaturiteAgent` (similaire à `WorkshopEnjeuxAgent`)

## WORD_REPORT_EXTRACTION_PROMPT

### `{word_text}`
- **Origine** : Texte extrait depuis un fichier Word via `WordReportExtractor.extract_from_word()` (ligne 319 dans `executive_summary_workflow.py`)
- **Format** : `str` - Texte brut extrait du document Word
- **Note** : Ce prompt est utilisé dans `WordReportExtractor`, pas directement dans `ExecutiveSummaryAgent`
- **Note importante** : Ce prompt ne sera plus utilisé si on charge les données depuis la BDD au lieu d'extraire depuis le Word

## Résumé des flux de données

### Pour les enjeux (challenges)
1. **Citations transcripts** : `transcript_files` → `TranscriptEnjeuxAgent.extract_citations()` → `transcript_enjeux_citations` → `_format_citations()` → `transcript_content`
2. **Citations workshops** : `workshop_files` → `WorkshopEnjeuxAgent.extract_informations()` → `workshop_enjeux_citations` → `_format_workshop_info()` → `workshop_content`
3. **Besoins** : `extracted_needs` (depuis Word ou BDD) → `_format_needs()` → `final_needs` (titres uniquement)

### Pour la maturité
1. **Citations transcripts** : `transcript_files` → `TranscriptMaturiteAgent.extract_citations()` → `transcript_maturite_citations` → `_format_maturite_citations()` → `transcript_content`
2. **Citations workshops** : `workshop_files` → `WorkshopMaturiteAgent.extract_informations()` → `workshop_maturite_citations` → `_format_workshop_maturite()` → `workshop_content`
3. **Besoins** : `extracted_needs` → `_format_needs()` → `final_needs`
4. **Use cases** : `extracted_use_cases` → `_format_use_cases()` → `final_use_cases` (titres + descriptions)

### Pour les recommandations
1. **Maturité** : `maturity_score` + `maturity_summary` → formatage → `maturite_ia`
2. **Besoins** : `extracted_needs` → `_format_needs()` → `final_needs`
3. **Use cases** : `extracted_use_cases` → `_format_use_cases()` → `final_use_cases`

## Points d'attention pour le tri

Actuellement, **aucun tri explicite** n'est appliqué sur les données avant leur injection dans les prompts :

1. **`final_needs`** : Les besoins sont formatés dans l'ordre de la liste source (pas de tri alphabétique)
2. **`final_use_cases`** : Les use cases sont formatés dans l'ordre de la liste source (pas de tri par famille ou titre)
3. **`transcript_content`** : Les citations sont formatées dans l'ordre de la liste source (pas de tri par timestamp ou speaker)
4. **`workshop_content`** : Les informations sont formatées dans l'ordre de la liste source (pas de tri par atelier)

**Recommandation** : Ajouter un tri cohérent avant le formatage pour garantir un ordre prévisible dans les prompts.

