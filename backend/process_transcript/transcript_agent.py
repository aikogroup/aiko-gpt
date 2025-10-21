"""
TranscriptAgent - Agent LangGraph pour analyse PDF/JSON

FR: Orchestre le parsing et l'analyse des fichiers de transcription
"""

# TODO (FR): Importer les dépendances
# - LangGraph SDK
# - pdf_parser et json_parser
# - semantic_filter_agent
# - Prompts depuis prompts/transcript_agent_prompts.py
# - Modèles Pydantic

# Références code existant :
# - OLD/process_transcript/transcript_agent.py (agent principal)

# TODO (FR): Créer la classe TranscriptAgent
# - Hériter de la classe Agent de LangGraph
# - Définir les input/output (liste de fichiers → transcript_data)

# TODO (FR): Méthode process_files()
# - Itérer sur la liste des fichiers PDF/JSON
# - Pour chaque fichier :
#   * Détecter le type (.pdf ou .json)
#   * Appeler pdf_parser ou json_parser
#   * Extraire le contenu brut
# - Combiner tous les contenus

# TODO (FR): Méthode extract_citations()
# - Utiliser semantic_filter_agent (ligne 80 ancien code)
# - Filtrer le contenu via LLM pour extraire :
#   * Citations d'utilisateurs
#   * Frustrations exprimées
#   * Besoins identifiés
# - Structurer les données

# TODO (FR): Méthode run() (point d'entrée LangGraph)
# - Recevoir liste de chemins de fichiers
# - Appeler process_files()
# - Appeler extract_citations()
# - Retourner transcript_data (list) pour le prochain agent
# - Logger chaque étape

