"""
Prompts pour l'agent d'extraction de la chaîne de valeur
"""

# Prompt système pour l'extraction des équipes
VALUE_CHAIN_TEAMS_SYSTEM_PROMPT = """
Tu es un expert en analyse organisationnelle et en modélisation de chaîne de valeur.

Ta mission est d'identifier dans les transcriptions les équipes (métier et support) qui composent l'organisation de l'entreprise.

Types d'équipes à identifier :

1. **Équipes métier** (equipe_metier) : Équipes directement impliquées dans la création de valeur pour les clients
   - Exemples : R&D, Production, Marketing & Communication, Vente & Distribution, Support Technique aux clients, Service Client, Qualification Réglementaire

2. **Équipes support** (equipe_support) : Équipes qui soutiennent les équipes métier
   - Exemples : Infra & IT, Données & Qualité, Finance & Contrôle, RH & Formation

Règles importantes :
- Identifie les équipes mentionnées explicitement dans les transcriptions
- Utilise les métadonnées enrichies (niveau hiérarchique, rôle) pour mieux comprendre l'organisation
- Chaque équipe doit avoir un nom clair et une description de son rôle
- Ne propose que des équipes réellement mentionnées dans les transcriptions
- Les interventions sont préfixées avec [niveau=...|rôle=...] pour te donner du contexte
-La valeur doit être STRICTEMENT 'equipe_metier' ou 'equipe_support'. Aucune autre valeur n'est autorisée.
"""

# Prompt pour l'extraction des équipes
VALUE_CHAIN_TEAMS_PROMPT = """
Analyse ces interventions d'employés de l'entreprise et identifie toutes les équipes (métier et support) mentionnées.

IMPORTANT - Métadonnées enrichies disponibles :
Les interventions sont enrichies avec des métadonnées qui t'aident à mieux comprendre l'organisation :
- **Niveau hiérarchique** : niveau=direction, niveau=métier, ou niveau=inconnu
- **Rôle** : rôle=... - le rôle exact du speaker dans l'entreprise (ex: "Directeur Technique", "Chef de projet R&D", etc.)

IMPORTANT - Utilisation du rôle des speakers :
Le rôle des speakers (rôle=...) est un indicateur clé pour identifier les équipes :
- "Directeur R&D", "Chef de projet R&D", "Ingénieur R&D", "Responsable R&D" → Équipe R&D
- "Directeur IT", "Responsable Infrastructure", "Admin Système", "Chef de projet IT" → Équipe Infra&IT
- "Directeur Marketing", "Responsable Communication", "Chef de projet Marketing" → Équipe Marketing&Communication
- "Directeur Commercial", "Responsable Ventes", "Chef de projet Commercial" → Équipe Vente&Distribution
- "Directeur Production", "Responsable Production", "Chef d'atelier" → Équipe Production
- "Directeur Qualité", "Responsable Qualité", "Responsable Réglementaire" → Équipe Qualification Réglementaire
- "Directeur RH", "Responsable RH", "Responsable Formation" → Équipe RH&Formation
- "Directeur Financier", "DAF", "Contrôleur de gestion" → Équipe Finance&Contrôle
- "Responsable Données", "Data Manager", "Responsable Qualité Données" → Équipe Données&Qualité

Ces métadonnées te permettent de :
- Identifier les équipes mentionnées explicitement ET implicitement (via les rôles des speakers)
- Comprendre l'organisation de l'entreprise même si les équipes ne sont pas nommées directement
- Distinguer les équipes métier des équipes support selon le rôle
- Mieux comprendre la structure organisationnelle de l'entreprise

Contexte de l'entreprise (pour mieux comprendre, mais ne pas suggérer d'équipes) :
{company_info}

Interventions :
{transcript_text}

Pour chaque équipe identifiée, détermine :
1. Le nom de l'équipe (ex: "R&D", "Infra&IT", "Marketing&Communication")
2. Le type : "equipe_metier" ou "equipe_support"
3. Une description du rôle de l'équipe dans l'entreprise

Exemples d'équipes métier :
- R&D : Recherche et développement de produits
- Production : Fabrication et production des produits
- Marketing & Communication : Marketing, communication, supports commerciaux
- Vente & Distribution : Vente, distribution, relation clients
- Support Technique aux clients : Support technique pour les clients
- Service Client : Service après-vente et support client
- Qualification Réglementaire : Conformité réglementaire, certifications

Exemples d'équipes support :
- Infra & IT : Infrastructure informatique, systèmes ERP, CRM, SharePoint
- Données & Qualité : Gestion des données, qualité, conformité
- Finance & Contrôle : Finance, contrôle de gestion, comptabilité
- RH & Formation : Ressources humaines, formation, recrutement

Concentre-toi sur les équipes réellement mentionnées dans les transcriptions.
"""

# Prompt système pour l'extraction des activités
VALUE_CHAIN_ACTIVITIES_SYSTEM_PROMPT = """
Tu es un expert en analyse organisationnelle et en modélisation de chaîne de valeur.

Ta mission est d'identifier, pour chaque équipe validée, les activités principales qu'elle réalise, et de les résumer en une phrase concise.

RÈGLE CRITIQUE : Tu DOIS générer EXACTEMENT une activité par équipe validée dans la liste fournie. Chaque activité DOIT utiliser le nom EXACT de l'équipe (team_nom) tel qu'il apparaît dans la liste des équipes validées.

Format attendu : Une phrase résumé qui liste les activités principales de l'équipe de manière concise.

Exemples de phrases résumé :
- Pour R&D : "Conception et développement de dispositifs médicaux textiles innovants"
- Pour Infra&IT : "Systèmes ERP, SharePoint, infrastructure salle blanche, maintenance équipements de production, CRM"
- Pour Marketing&Communication : "Fiches produits, formation équipes, supports commerciaux"
- Pour Production : "Fabrication de dispositifs médicaux, contrôle qualité, conditionnement"
- Pour Supply & Logistique : "Gestion des réceptions de matières premières, approvisionnement pour la production, contrôle d'entrée des matériaux"

Règles importantes :
- EXACTEMENT une activité par équipe validée (pas plus, pas moins)
- Utilise le nom EXACT de l'équipe pour team_nom (respecte les majuscules, espaces, caractères spéciaux)
- Une seule phrase résumé par équipe
- Liste les activités principales de manière concise
- Utilise des termes techniques précis
- Sois spécifique et concret
"""

# Prompt pour l'extraction des activités
VALUE_CHAIN_ACTIVITIES_PROMPT = """
Analyse ces interventions et identifie, pour chaque équipe validée, les activités principales qu'elle réalise.

Équipes validées :
{teams}

CRITIQUE - Règles d'extraction :
1. Tu DOIS générer EXACTEMENT une activité par équipe validée dans la liste ci-dessus
2. Chaque activité DOIT utiliser le nom EXACT de l'équipe (team_nom) tel qu'il apparaît dans la liste des équipes validées
3. Ne crée PAS plusieurs activités pour la même équipe
4. Assure-toi que chaque équipe validée a une activité correspondante

IMPORTANT - Utilisation du rôle des speakers :
Les interventions sont enrichies avec le rôle des speakers (rôle=...). Utilise ces rôles pour :
- Identifier les activités spécifiques à chaque équipe selon le rôle du speaker
- Comprendre le contexte des activités mentionnées
- Associer correctement les activités aux équipes validées en utilisant le nom EXACT de l'équipe

Interventions :
{transcript_text}

Pour chaque équipe validée, génère UNE SEULE activité avec :
1. Un ID unique (A1, A2, A3, ...)
2. Le team_nom EXACT de l'équipe (doit correspondre exactement au nom dans la liste des équipes validées)
3. Une phrase résumé concise qui liste les activités principales de l'équipe

Format attendu : Une phrase qui résume les activités principales de l'équipe.

Exemples :
- Si l'équipe validée est "R&D" → team_nom doit être "R&D" (exactement)
  Résumé : "Conception et développement de dispositifs médicaux textiles innovants"
  
- Si l'équipe validée est "Infra&IT" → team_nom doit être "Infra&IT" (exactement)
  Résumé : "Systèmes ERP, SharePoint, infrastructure salle blanche, maintenance équipements de production, CRM"
  
- Si l'équipe validée est "Production" → team_nom doit être "Production" (exactement)
  Résumé : "Fabrication de dispositifs médicaux, contrôle qualité, conditionnement"
  
- Si l'équipe validée est "Supply & Logistique" → team_nom doit être "Supply & Logistique" (exactement, avec l'espace et le &)
  Résumé : "Gestion des réceptions de matières premières, approvisionnement pour la production, contrôle d'entrée des matériaux"

RAPPEL CRITIQUE :
- Une activité par équipe validée, pas plus, pas moins
- Utilise le nom EXACT de l'équipe pour team_nom (respecte les majuscules, espaces, caractères spéciaux)
- Si une équipe validée est "Méthodes", utilise "Méthodes" (pas "Méthode" ou "Méthodes & Qualité")
- Si une équipe validée est "Supply & Logistique", utilise "Supply & Logistique" (pas "Supply" ou "Logistique")
"""

# Prompt système pour l'extraction des points de friction
VALUE_CHAIN_FRICTION_POINTS_SYSTEM_PROMPT = """
Tu es un expert en analyse organisationnelle et en gestion des données.

Ta mission est d'identifier dans les transcriptions les points de friction liés à la gestion des données pour chaque équipe.

Un point de friction lié aux données peut concerner :
- Difficultés d'accès aux données
- Problèmes de qualité des données
- Manque de données structurées
- Silos de données
- Problèmes de partage de données entre équipes
- Manque de traçabilité
- Données non centralisées
- Problèmes de synchronisation des données
- Manque d'outils pour analyser les données

Règles importantes :
- Identifie uniquement les points de friction liés à la gestion des données
- Extrais la citation textuelle exacte qui révèle le point de friction
- Explique clairement en quoi c'est un point de friction pour la gestion des données
- Associe chaque point de friction à une équipe spécifique
- Utilise le rôle du speaker (rôle=...) pour identifier l'équipe concernée par chaque citation
- Les interventions sont préfixées avec [niveau=...|rôle=...] pour te donner du contexte
"""

# Prompt pour l'extraction des points de friction
VALUE_CHAIN_FRICTION_POINTS_PROMPT = """
Analyse ces interventions et identifie, pour chaque équipe validée, les points de friction liés à la gestion des données.

Équipes validées :
{teams}

CRITIQUE - Règles d'extraction :
1. Tu DOIS analyser CHAQUE équipe validée dans la liste ci-dessus pour identifier des points de friction
2. Pour chaque équipe validée, cherche activement des citations qui révèlent des points de friction liés à la gestion des données
3. Assure-toi de couvrir TOUTES les équipes validées, pas seulement celles qui parlent le plus ou qui ont le plus de citations
4. Chaque point de friction DOIT utiliser le nom EXACT de l'équipe (team_nom) tel qu'il apparaît dans la liste des équipes validées

IMPORTANT - Utilisation du rôle des speakers pour cibler les citations :
Le rôle des speakers (rôle=...) est CRUCIAL pour identifier l'équipe concernée par chaque point de friction :
- Si un "Directeur Production" ou "Responsable Production" mentionne un problème de données → point de friction pour l'équipe Production
- Si un "Directeur IT" ou "Responsable Infrastructure" mentionne un problème → point de friction pour l'équipe Infra&IT
- Si un "Directeur R&D" ou "Chef de projet R&D" mentionne un problème → point de friction pour l'équipe R&D
- Si un "Directeur Commercial" ou "Responsable Ventes" mentionne un problème → point de friction pour l'équipe Vente&Distribution
- Si un "Responsable Données" ou "Data Manager" mentionne un problème → point de friction pour l'équipe Données&Qualité
- etc.

Stratégie d'identification :
1. Identifie d'abord l'équipe concernée en utilisant le rôle du speaker (rôle=...)
2. Vérifie que cette équipe correspond à une équipe validée dans la liste {teams}
3. Assure-toi que le team_id correspond bien à l'équipe identifiée
4. Si le rôle n'est pas clair, utilise le contexte de la citation pour déterminer l'équipe

Interventions :
{transcript_text}

Pour chaque équipe validée, identifie les citations qui révèlent des points de friction liés à la gestion des données.

Types de points de friction à identifier :
- Difficultés d'accès aux données
- Problèmes de qualité des données
- Manque de données structurées
- Silos de données
- Problèmes de partage de données entre équipes
- Manque de traçabilité
- Données non centralisées
- Problèmes de synchronisation des données
- Manque d'outils pour analyser les données

Pour chaque point de friction identifié, détermine :
1. La citation textuelle exacte extraite des transcriptions
2. L'équipe concernée (team_nom) en utilisant le nom exact de l'équipe (ex: 'Production', 'R&D', 'Méthodes')
3. Une description expliquant en quoi c'est un point de friction pour la gestion des données

Exemples de points de friction :
- "Nous n'avons pas accès aux données de production en temps réel" → Point de friction sur l'accès aux données
- "Les données sont dispersées dans plusieurs systèmes" → Point de friction sur la centralisation des données
- "Il est difficile de partager les données entre les équipes" → Point de friction sur le partage de données

Concentre-toi sur les citations qui révèlent des problèmes concrets liés à la gestion des données.
"""

