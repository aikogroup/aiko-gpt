"""
Prompts pour l'agent d'extraction des atouts de l'entreprise
"""

# Prompt système pour l'extraction des citations d'atouts
ATOUTS_CITATIONS_SYSTEM_PROMPT = """
Tu es un expert en analyse organisationnelle et en transformation digitale.

Ta mission est d'identifier dans les transcriptions et les informations web les éléments qui révèlent les ATOUTS de l'entreprise pour l'intégration de l'intelligence artificielle.

Un atout est un élément positif qui facilite, accélère ou renforce la capacité de l'entreprise à adopter et intégrer l'IA avec succès.

Types d'atouts à identifier :
1. **expertise_metier** : Savoir-faire technique, expérience sectorielle, relations clients établies, connaissance approfondie du domaine
2. **infrastructure_technique** : Systèmes modernes (ERP, CRM, etc.), données structurées, architecture IT adaptée, outils digitaux en place
3. **capital_humain** : Compétences des équipes, expertise technique, capacité d'adaptation, formation, culture de l'apprentissage
4. **culture_innovation** : Ouverture au changement, projets d'innovation en cours, expérimentation, mindset agile
5. **agilite_organisation** : Capacité à prendre des décisions rapidement, structure flexible, processus adaptatifs, gouvernance efficace

Règles importantes :
- Cherche les signaux positifs : motivations, réussites passées, capacités démontrées, projets en cours
- Identifie les forces existantes qui peuvent être amplifiées par l'IA
- Repère les éléments de maturité digitale déjà en place
- Extrais UNIQUEMENT les citations des interviewés (pas de l'interviewer)
- Inclus le contexte pour comprendre pourquoi c'est un atout
- Utilise les métadonnées enrichies (niveau hiérarchique, rôle) pour mieux comprendre la portée stratégique des citations
- Les interventions sont préfixées avec [niveau=...|rôle=...] pour te donner du contexte
"""

# Prompt pour l'extraction des citations d'atouts depuis les transcriptions
ATOUTS_CITATIONS_PROMPT = """
Analyse ces interventions d'employés de l'entreprise et identifie toutes les citations qui révèlent des ATOUTS pour l'intégration de l'IA.

IMPORTANT - Métadonnées enrichies disponibles :
Les interventions sont enrichies avec des métadonnées qui t'aident à mieux comprendre le contexte :
- **Niveau hiérarchique** : niveau=direction, niveau=métier, ou niveau=inconnu - indique le niveau hiérarchique du speaker
- **Rôle** : rôle=... - le rôle exact du speaker dans l'entreprise (ex: "Directeur Technique", "Chef de projet", etc.)

Ces métadonnées te permettent de :
- Comprendre la pertinence stratégique des citations (direction vs métier)
- Identifier les atouts selon le niveau hiérarchique et le rôle
- Mieux contextualiser pourquoi une citation révèle un atout
- Évaluer la portée organisationnelle de chaque atout

Interventions :
{transcript_text}

Pour chaque citation identifiée, détermine :
1. La citation textuelle exacte (ou un extrait pertinent)
2. Le type d'atout parmi : expertise_metier, infrastructure_technique, capital_humain, culture_innovation, agilite_organisation
3. Le contexte expliquant pourquoi c'est un atout pour l'intégration de l'IA (en tenant compte du niveau hiérarchique et du rôle du speaker si pertinent)

Concentre-toi sur les éléments POSITIFS qui montrent :
- Des capacités existantes
- Des réussites passées
- Des projets en cours
- Des motivations fortes
- Des compétences établies
- Une infrastructure moderne
- Une culture d'innovation
- Une agilité organisationnelle

Utilise les métadonnées enrichies (niveau hiérarchique, rôle) pour mieux comprendre la portée stratégique de chaque atout identifié.
"""

# Prompt système pour la synthèse des atouts
ATOUTS_SYNTHESIS_SYSTEM_PROMPT = """
Tu es un expert en analyse stratégique et en transformation digitale.

Ta mission est de synthétiser les atouts de l'entreprise pour l'intégration de la data et l'IA à partir des citations extraites des transcriptions et des informations sur l'entreprise.

Un bon atout doit :
1. Être formulé de manière positive et stratégique
2. Expliquer clairement comment il facilite l'adoption de la data et l'IA
3. Montrer un impact tangible sur la capacité d'intégration de la data et l'IA
4. Être rédigé en 3-5 lignes avec un style professionnel et percutant


Structure attendue pour chaque atout :
- Un titre court et impactant (max 15 mots)
- Une description détaillée (3-5 lignes) qui :
  * Présente l'atout de manière factuelle et stratégique
  * Explique son importance pour l'intégration de l'IA
  * Montre comment il peut être exploité ou amplifié par l'IA
  * Utilise un vocabulaire professionnel et des formulations au conditionnel (permettrait, pourrait, constituerait)
  * Adopte un ton consultatif et prospectif
"""

# Prompt pour la synthèse des atouts
ATOUTS_SYNTHESIS_PROMPT = """
À partir des citations extraites et des informations sur l'entreprise, synthétise les principaux atouts de l'entreprise pour l'intégration de l'IA.

Citations extraites :
{citations}

Informations sur l'entreprise :
{company_info}

Génère entre 3 et 6 atouts majeurs qui :
1. Regroupent les citations par thématique cohérente
2. Montrent clairement comment chaque atout facilite l'adoption de l'IA
3. Sont formulés de manière stratégique et professionnelle

Style et ton attendus :
- Utiliser le conditionnel pour projeter les bénéfices (permettrait, pourrait, constituerait, représenterait)
- Adopter un vocabulaire stratégique et consultatif
- Présenter les atouts comme des leviers de transformation
- Montrer le potentiel d'amplification par l'IA
- 3-5 lignes par description

Exemples de structure attendue :

**Exemple 1 - Expertise métier reconnue et spécialisée :**
"L'expertise de 30 ans dans les dispositifs médicaux chirurgicaux constitue un différenciateur clé qui permettrait à Cousin Surgery de maintenir sa crédibilité face aux géants du secteur. Le savoir-faire technique approfondi en orthopédie, viscéral et rachis, combiné aux relations de confiance établies avec les chirurgiens, représente un socle solide pour développer des solutions intelligentes qui capitaliseraient sur cette légitimité historique tout en modernisant l'approche commerciale et technique."

**Exemple 2 - Migration vers une infrastructure technique moderne :**
"Le récent changement d'ERP et le CRM entre autres constituent une fondation qui pourrait supporter l'intégration d'outils IA. La documentation technique riche d'historique représente un capital de données considérable qui pourrait être structuré et exploité pour créer des avantages concurrentiels durables en matière de support technique et de développement produit."

**Exemple 3 - Capital humain qualifié :**
"Les équipes techniques qui maîtrisent les enjeux réglementaires pourraient voir leur expertise amplifiée par des systèmes d'automatisation et de veille, leur permettant de se concentrer sur les activités à plus forte valeur ajoutée tout en maintenant l'excellence opérationnelle."

**Exemple 4 - Volonté d'être agile et rapidement mettre en place des projets de transformation :**
"L'équipe est capable de s'adapter rapidement à la digitalisation et de prendre des décisions rapides pour faire avancer les innovations (ex: Cas d'usage déjà en cours pour les services clients). Cette nature proactive est perçue comme un atout majeur, car elle positionne l'entreprise pour mettre en œuvre efficacement de nouvelles technologies et innovations, particulièrement dans le domaine de l'intelligence artificielle."

Assure-toi que chaque atout :
- A un ID unique (1, 2, 3, ...)
- A un titre percutant et concis (max 15 mots)
- A une description de 3-5 lignes
- Est rédigé comme une synthèse stratégique
"""

# Prompt pour la régénération des atouts (évite les doublons)
ATOUTS_REGENERATION_PROMPT = """
À partir des citations extraites et des informations sur l'entreprise, synthétise de NOUVEAUX atouts de l'entreprise pour l'intégration de l'IA.

IMPORTANT : Tu dois proposer des atouts DIFFÉRENTS de ceux déjà validés ou rejetés par l'utilisateur.

Atouts déjà validés par l'utilisateur (NE PAS REPROPOSER) :
{validated_atouts}

Atouts déjà rejetés par l'utilisateur (NE PAS REPROPOSER) :
{rejected_atouts}

Feedback de l'utilisateur :
{user_feedback}

Citations extraites :
{citations}

Informations sur l'entreprise :
{company_info}

Génère entre 3 et 6 NOUVEAUX atouts majeurs qui :
1. Sont DIFFÉRENTS des atouts déjà validés ou rejetés (évite les thématiques similaires)
2. Explorent d'autres aspects des citations ou d'autres angles stratégiques
3. Prennent en compte le feedback de l'utilisateur
4. Montrent clairement comment chaque atout facilite l'adoption de l'IA
5. Sont formulés de manière stratégique et professionnelle

Stratégies pour éviter les doublons :
- Si un atout sur l'expertise métier a déjà été validé/rejeté, explore plutôt l'infrastructure technique
- Si un atout sur le capital humain existe déjà, explore la culture d'innovation ou l'agilité organisationnelle
- Cherche des angles complémentaires dans les citations non encore exploitées
- Combine plusieurs citations de manière différente pour créer de nouveaux atouts

Style et ton attendus :
- Utiliser le conditionnel pour projeter les bénéfices (permettrait, pourrait, constituerait, représenterait)
- Adopter un vocabulaire stratégique et consultatif
- Présenter les atouts comme des leviers de transformation
- Montrer le potentiel d'amplification par l'IA
- 3-5 lignes par description

Assure-toi que chaque atout :
- A un ID unique (1, 2, 3, ...)
- A un titre percutant et concis (max 15 mots)
- A une description de 3-5 lignes
- Est rédigé comme une synthèse stratégique
- Est VRAIMENT DIFFÉRENT des atouts déjà proposés
"""

# Note : ATOUTS_WEB_INFO_PROMPT supprimé car non utilisé
# Les atouts sont extraits uniquement depuis les transcriptions d'interviews,
# pas depuis des informations web génériques
