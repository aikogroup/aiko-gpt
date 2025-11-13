"""
Classificateur de speakers pour identifier interviewer/interviewé et direction/métier
"""
import logging
from typing import List, Dict, Any, Set, Optional
from openai import OpenAI
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import sys

# Ajouter le répertoire parent au path pour importer les prompts
sys.path.append(str(Path(__file__).parent.parent))
from prompts.speaker_identification_prompts import SPEAKER_IDENTIFICATION_AND_ROLE_EXTRACTION_PROMPT

load_dotenv()

logger = logging.getLogger(__name__)


class SpeakerClassifier:
    """Classificateur pour identifier le type et le niveau des speakers"""
    
    def __init__(self, api_key: str = None, interviewer_names: List[str] = None, cache_file: Optional[str] = None):
        """
        Initialise le classificateur
        
        Args:
            api_key: Clé API OpenAI (optionnelle)
            interviewer_names: Liste des noms d'interviewers (optionnelle, par défaut utilise les noms par défaut)
            cache_file: Chemin vers le fichier de cache persistant (optionnel, par défaut outputs/speaker_classification_cache.json)
        """
        # Configuration OpenAI
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("Clé API OpenAI non configurée")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        
        # Liste des interviewers par défaut
        if interviewer_names is None:
            interviewer_names = ["Christella Umuhoza", "Adrien Fabry"]
        
        self.interviewer_names = interviewer_names
        
        # Cache en mémoire pour la session (évite les appels LLM répétés dans la même session)
        self._classification_cache: Dict[str, str] = {}
        
        # Cache persistant entre les réunions - CHARGEMENT LAZY
        if cache_file is None:
            cache_file = "outputs/speaker_classification_cache.json"
        self.cache_file = Path(cache_file)
        self._persistent_cache: Optional[Dict[str, str]] = None  # Chargé de manière lazy
        self._persistent_cache_loaded = False  # Flag pour savoir si le cache a été chargé
        
        # Cache pour les rôles exacts (speaker_name -> role) - CHARGEMENT LAZY
        self._role_cache: Dict[str, str] = {}
        self._role_cache_file = Path("outputs/speaker_roles_cache.json")
        self._persistent_role_cache: Optional[Dict[str, str]] = None  # Chargé de manière lazy
        self._persistent_role_cache_loaded = False  # Flag pour savoir si le cache a été chargé
    
    def classify_speakers(self, interventions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classe les speakers et enrichit les interventions avec speaker_type et speaker_level
        
        Args:
            interventions: Liste des interventions parsées
            
        Returns:
            Liste des interventions enrichies avec speaker_type et speaker_level
        """
        if not interventions:
            return []
        
        logger.info(f"Classification de {len(interventions)} interventions")
        
        # Étape 1: Identifier les interviewers
        interviewer_names_set = self._identify_interviewers(interventions)
        logger.info(f"Interviewers identifiés: {interviewer_names_set}")
        
        # Étape 2: Identifier les speakers interviewés uniques pour classification direction/métier
        interviewee_speakers = set()
        for intervention in interventions:
            speaker = intervention.get("speaker", "")
            if speaker and speaker not in interviewer_names_set:
                interviewee_speakers.add(speaker)
        
        logger.info(f"Speakers interviewés à classifier: {len(interviewee_speakers)}")
        
        # Étape 3: Classifier chaque speaker interviewé (avec cache mémoire ET cache persistant)
        speaker_levels = {}
        new_classifications = {}  # Pour sauvegarder les nouvelles classifications
        
        # Charger le cache persistant de manière lazy si nécessaire
        if not self._persistent_cache_loaded:
            self._persistent_cache = self._load_persistent_cache()
            self._persistent_cache_loaded = True
        
        for speaker in interviewee_speakers:
            # Vérifier d'abord le cache en mémoire (session courante)
            if speaker in self._classification_cache:
                speaker_levels[speaker] = self._classification_cache[speaker]
                logger.info(f"✓ {speaker}: {speaker_levels[speaker]} (depuis cache session)")
            # Sinon, vérifier le cache persistant (réunions précédentes)
            elif self._persistent_cache and speaker in self._persistent_cache:
                speaker_levels[speaker] = self._persistent_cache[speaker]
                self._classification_cache[speaker] = speaker_levels[speaker]  # Mettre aussi dans le cache session
                logger.info(f"✓ {speaker}: {speaker_levels[speaker]} (depuis cache persistant)")
            else:
                # Collecter TOUTES les interventions de ce speaker pour le contexte
                speaker_interventions = [
                    interv for interv in interventions 
                    if interv.get("speaker") == speaker
                ]
                level = self._classify_interviewee_level(speaker, speaker_interventions)
                speaker_levels[speaker] = level
                self._classification_cache[speaker] = level  # Cache session
                new_classifications[speaker] = level  # Pour sauvegarder dans le cache persistant
                logger.info(f"✓ {speaker}: {level} (nouvelle classification)")
        
        # Sauvegarder les nouvelles classifications dans le cache persistant
        if new_classifications:
            self._save_to_persistent_cache(new_classifications)
        
        # Étape 4: Enrichir les interventions
        enriched_interventions = []
        for intervention in interventions:
            enriched = intervention.copy()
            speaker = intervention.get("speaker", "")
            
            # Déterminer speaker_type
            if speaker in interviewer_names_set:
                enriched["speaker_type"] = "interviewer"
                enriched["speaker_level"] = None  # Pas de niveau pour l'interviewer
            else:
                enriched["speaker_type"] = "interviewé"
                enriched["speaker_level"] = speaker_levels.get(speaker, "inconnu")
            
            enriched_interventions.append(enriched)
        
        logger.info(f"Classification terminée: {len([i for i in enriched_interventions if i['speaker_type'] == 'interviewer'])} interviewers, "
                   f"{len([i for i in enriched_interventions if i['speaker_type'] == 'interviewé'])} interviewés")
        
        return enriched_interventions
    
    def _identify_interviewers(self, interventions: List[Dict[str, Any]]) -> Set[str]:
        """
        Identifie les noms des interviewers dans les interventions
        
        Args:
            interventions: Liste des interventions
            
        Returns:
            Ensemble des noms d'interviewers identifiés
        """
        interviewer_names_found = set()
        
        # Créer un set de tous les speakers uniques
        all_speakers = {interv.get("speaker", "") for interv in interventions if interv.get("speaker")}
        
        # Vérifier chaque speaker contre la liste des interviewers (match partiel insensible à la casse)
        for speaker in all_speakers:
            speaker_lower = speaker.lower()
            for interviewer_name in self.interviewer_names:
                interviewer_lower = interviewer_name.lower()
                # Match partiel: vérifier si le nom de l'interviewer est contenu dans le speaker ou vice versa
                if interviewer_lower in speaker_lower or speaker_lower in interviewer_lower:
                    interviewer_names_found.add(speaker)
                    break
        
        return interviewer_names_found
    
    def _classify_interviewee_level(self, speaker_name: str, context: List[Dict[str, Any]]) -> str:
        """
        Utilise un LLM pour extraire le poste d'un speaker depuis TOUTES ses interventions
        et classifier son niveau hiérarchique (direction/métier)
        
        Args:
            speaker_name: Nom du speaker
            context: Liste de TOUTES les interventions de ce speaker
            
        Returns:
            "direction", "métier" ou "inconnu"
        """
        if not context:
            return "inconnu"
        
        # Préparer TOUTES les interventions (pas seulement 5) pour trouver les présentations
        # Les présentations sont souvent au début, mais pas toujours
        all_interventions_text = "\n".join([
            f"- {interv.get('text', '')}"
            for interv in context
        ])
        
        prompt = f"""Tu dois identifier le poste/titre d'une personne à partir de ses interventions dans une réunion de conseil.

Nom de la personne: {speaker_name}

Interventions de cette personne:
{all_interventions_text}

INSTRUCTIONS IMPORTANTES :
1. Cherche spécifiquement les phrases où la personne se présente ou mentionne son poste (ex: "je me présente [nom], DG de...", "je suis directeur de...", "mon rôle est...", "je travaille en tant que...")
2. Si tu trouves un poste/titre clair (DG, Directeur, CEO, PDG, CTO, responsable, manager, collaborateur, etc.), détermine s'il s'agit d'un poste de direction (stratégique, management, C-level) ou de métier (opérationnel)
3. Si aucune information claire sur le poste n'est trouvée dans les interventions, réponds "inconnu" - NE PAS INVENTER un poste
4. Ne pas se baser uniquement sur le style de parole ou le contenu des interventions, mais sur les informations explicites de poste/titre

Réponds UNIQUEMENT par "direction", "métier" ou "inconnu".
- "direction" : si le poste est stratégique/management (DG, Directeur général, CEO, PDG, CTO, Directeur de [fonction], etc.)
- "métier" : si le poste est opérationnel (collaborateur, responsable opérationnel, etc.)
- "inconnu" : si aucun poste clair n'est mentionné dans les interventions"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            result = response.output_text.strip().lower()
            
            # Valider la réponse
            if "direction" in result:
                return "direction"
            elif "métier" in result or "metier" in result:
                return "métier"
            elif "inconnu" in result:
                return "inconnu"
            else:
                logger.warning(f"Réponse LLM inattendue pour {speaker_name}: {result}, utilisation de 'inconnu' par défaut")
                return "inconnu"
                
        except Exception as e:
            logger.error(f"Erreur lors de la classification LLM pour {speaker_name}: {e}")
            return "inconnu"  # Valeur par défaut en cas d'erreur
    
    def _load_persistent_cache(self) -> Dict[str, str]:
        """
        Charge le cache persistant depuis le fichier JSON.
        CHARGEMENT LAZY : appelé seulement quand nécessaire, pas dans __init__.
        
        Returns:
            Dictionnaire speaker_name -> level
        """
        if not self.cache_file.exists():
            logger.info(f"Cache persistant non trouvé: {self.cache_file}, création d'un nouveau cache")
            return {}
        
        try:
            # Lecture synchrone simple - maintenant appelée seulement quand nécessaire
            # (pas dans __init__ donc pas de blocking call au démarrage)
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            logger.info(f"Cache persistant chargé: {len(cache)} speakers")
            return cache
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache persistant: {e}")
            return {}
    
    def _save_to_persistent_cache(self, new_classifications: Dict[str, str]):
        """
        Sauvegarde les nouvelles classifications dans le cache persistant
        
        Args:
            new_classifications: Dictionnaire speaker_name -> level à sauvegarder
        """
        if not new_classifications:
            return
        
        try:
            # Créer le répertoire s'il n'existe pas
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Charger le cache existant depuis le fichier (pour éviter les problèmes de concurrence)
            current_cache = self._load_persistent_cache()
            
            # Mettre à jour avec les nouvelles classifications
            current_cache.update(new_classifications)
            
            # Sauvegarder
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(current_cache, f, ensure_ascii=False, indent=2)
            
            # Mettre à jour aussi le cache en mémoire (charger si nécessaire)
            if not self._persistent_cache_loaded:
                self._persistent_cache = current_cache
                self._persistent_cache_loaded = True
            else:
                self._persistent_cache.update(new_classifications)
            
            logger.info(f"Cache persistant mis à jour: {len(new_classifications)} nouvelles classifications sauvegardées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache persistant: {e}")
    
    def extract_speaker_role(self, speaker_name: str, context: List[Dict[str, Any]], known_roles: Optional[Dict[str, str]] = None) -> str:
        """
        Extrait le rôle exact (titre de poste) d'un speaker à partir de ses interventions via LLM
        
        Args:
            speaker_name: Nom du speaker
            context: Liste de toutes les interventions de ce speaker
            known_roles: Dictionnaire optionnel de speaker_name -> role pour réutiliser les rôles déjà connus
            
        Returns:
            Le rôle exact du speaker (ex: "Directrice Commerciale") ou chaîne vide si non trouvé
        """
        if not context:
            return ""
        
        # Vérifier d'abord les rôles connus passés en paramètre
        if known_roles and speaker_name in known_roles:
            role = known_roles[speaker_name]
            logger.info(f"✓ {speaker_name}: {role} (depuis rôles connus)")
            return role
        
        # Vérifier le cache en mémoire
        if speaker_name in self._role_cache:
            role = self._role_cache[speaker_name]
            logger.info(f"✓ {speaker_name}: {role} (depuis cache session)")
            return role
        
        # Charger le cache persistant des rôles de manière lazy si nécessaire
        if not self._persistent_role_cache_loaded:
            self._persistent_role_cache = self._load_persistent_role_cache()
            self._persistent_role_cache_loaded = True
        
        # Vérifier le cache persistant
        if self._persistent_role_cache and speaker_name in self._persistent_role_cache:
            role = self._persistent_role_cache[speaker_name]
            self._role_cache[speaker_name] = role  # Mettre aussi dans le cache session
            logger.info(f"✓ {speaker_name}: {role} (depuis cache persistant)")
            return role
        
        # Extraire le rôle via LLM
        all_interventions_text = "\n".join([
            f"- {interv.get('text', '')}"
            for interv in context
        ])
        
        prompt = f"""Tu dois extraire le titre de poste exact d'une personne à partir de ses interventions dans une réunion de conseil.

Nom de la personne: {speaker_name}

Interventions de cette personne:
{all_interventions_text}

INSTRUCTIONS IMPORTANTES :
1. Cherche spécifiquement les phrases où la personne se présente ou mentionne son poste (ex: "je me présente [nom], Directrice Commerciale de...", "je suis Directeur des ventes", "mon rôle est Directeur Marketing", "je travaille en tant que Responsable RH")
2. Si tu trouves un titre de poste clair et explicite, retourne-le exactement tel qu'il est mentionné (ex: "Directrice Commerciale", "Directeur des ventes", "Responsable RH")
3. Si le titre est mentionné de manière incomplète mais que tu peux le compléter logiquement (ex: "je suis directeur" -> "Directeur"), tu peux le compléter
4. Si aucune information claire sur le poste n'est trouvée dans les interventions, réponds UNIQUEMENT "NON_TROUVE" - NE PAS INVENTER un poste
5. Ne pas se baser uniquement sur le style de parole ou le contenu des interventions, mais sur les informations explicites de poste/titre
6. Réponds UNIQUEMENT par le titre de poste exact (ex: "Directrice Commerciale") ou "NON_TROUVE" si aucun titre n'est trouvé"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            result = response.output_text.strip()
            
            # Valider la réponse
            if result.upper() == "NON_TROUVE" or not result:
                logger.info(f"✗ {speaker_name}: Aucun rôle trouvé")
                return ""
            else:
                # Sauvegarder dans les caches
                self._role_cache[speaker_name] = result
                self._save_to_persistent_role_cache({speaker_name: result})
                logger.info(f"✓ {speaker_name}: {result} (nouvelle extraction)")
                return result
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du rôle LLM pour {speaker_name}: {e}")
            return ""  # Valeur par défaut en cas d'erreur
    
    def _load_persistent_role_cache(self) -> Dict[str, str]:
        """
        Charge le cache persistant des rôles depuis le fichier JSON.
        CHARGEMENT LAZY : appelé seulement quand nécessaire, pas dans __init__.
        
        Returns:
            Dictionnaire speaker_name -> role
        """
        if not self._role_cache_file.exists():
            logger.info(f"Cache persistant des rôles non trouvé: {self._role_cache_file}, création d'un nouveau cache")
            return {}
        
        try:
            # Lecture synchrone simple - maintenant appelée seulement quand nécessaire
            # (pas dans __init__ donc pas de blocking call au démarrage)
            with open(self._role_cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            logger.info(f"Cache persistant des rôles chargé: {len(cache)} speakers")
            return cache
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache persistant des rôles: {e}")
            return {}
    
    def _save_to_persistent_role_cache(self, new_roles: Dict[str, str]):
        """
        Sauvegarde les nouveaux rôles dans le cache persistant
        
        Args:
            new_roles: Dictionnaire speaker_name -> role à sauvegarder
        """
        if not new_roles:
            return
        
        try:
            # Créer le répertoire s'il n'existe pas
            self._role_cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Charger le cache existant depuis le fichier
            current_cache = self._load_persistent_role_cache()
            
            # Mettre à jour avec les nouveaux rôles
            current_cache.update(new_roles)
            
            # Sauvegarder
            with open(self._role_cache_file, 'w', encoding='utf-8') as f:
                json.dump(current_cache, f, ensure_ascii=False, indent=2)
            
            # Mettre à jour aussi le cache en mémoire (charger si nécessaire)
            if not self._persistent_role_cache_loaded:
                self._persistent_role_cache = current_cache
                self._persistent_role_cache_loaded = True
            else:
                self._persistent_role_cache.update(new_roles)
            
            logger.info(f"Cache persistant des rôles mis à jour: {len(new_roles)} nouveaux rôles sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache persistant des rôles: {e}")
    
    def identify_and_extract_speakers_with_roles(
        self, 
        all_speakers: List[str], 
        interventions: List[Dict[str, Any]],
        interviewer_names_set: Set[str],
        known_roles: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Identifie les vrais noms de speakers ET extrait leurs rôles en un seul appel LLM
        
        Args:
            all_speakers: Liste de tous les speakers extraits par le parser (peut contenir des faux positifs)
            interventions: Liste de toutes les interventions pour contexte
            interviewer_names_set: Set des noms d'interviewers (ne seront pas traités)
            known_roles: Dictionnaire optionnel de speaker_name -> role pour réutiliser les rôles déjà connus
            
        Returns:
            Liste de dictionnaires avec {"name": str, "role": str, "is_interviewer": bool}
        """
        if not all_speakers or not interventions:
            return []
        
        # Filtrer les interviewers de la liste (ils seront ajoutés séparément)
        candidate_speakers = [s for s in all_speakers if s not in interviewer_names_set]
        
        if not candidate_speakers:
            # Seulement des interviewers, retourner juste eux
            return [
                {"name": name, "role": "", "is_interviewer": True}
                for name in interviewer_names_set
            ]
        
        # Préparer TOUTES les interventions de chaque speaker candidat (sans restriction)
        # Grouper les interventions par speaker
        interventions_by_speaker = {}
        for intervention in interventions:
            speaker = intervention.get("speaker", "")
            if speaker in candidate_speakers:
                if speaker not in interventions_by_speaker:
                    interventions_by_speaker[speaker] = []
                interventions_by_speaker[speaker].append(intervention)
        
        # Construire le texte avec TOUTES les interventions de chaque speaker
        all_interventions_text = []
        for speaker, speaker_intervs in interventions_by_speaker.items():
            all_interventions_text.append(f"\n=== {speaker} ===")
            for interv in speaker_intervs:
                text = interv.get('text', '').strip()
                if text:
                    all_interventions_text.append(f"{text}")
        
        all_interventions = "\n".join(all_interventions_text)
        
        # Construire la liste des rôles connus pour référence
        known_roles_text = ""
        if known_roles:
            known_roles_text = "\n\nRôles déjà connus pour référence:\n"
            for name, role in known_roles.items():
                if name in candidate_speakers:
                    known_roles_text += f"- {name}: {role}\n"
        
        # Formater la liste des candidats
        candidate_speakers_text = "\n".join(f"- {speaker}" for speaker in candidate_speakers)
        
        # Construire le prompt
        prompt = SPEAKER_IDENTIFICATION_AND_ROLE_EXTRACTION_PROMPT.format(
            candidate_speakers=candidate_speakers_text,
            all_interventions=all_interventions,
            known_roles_text=known_roles_text
        )
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[{
                    "role": "user",
                    "content": [{
                        "type": "input_text",
                        "text": prompt
                    }]
                }]
            )
            
            result_text = response.output_text.strip()
            
            # Parser le JSON
            # Nettoyer le texte (enlever markdown code blocks si présent)
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result_json = json.loads(result_text)
            
            # Construire la liste finale
            speakers_list = []
            
            # D'abord, ajouter les interviewers
            for interviewer_name in interviewer_names_set:
                speakers_list.append({
                    "name": interviewer_name,
                    "role": "",
                    "is_interviewer": True
                })
            
            # Ensuite, ajouter les speakers identifiés par le LLM
            for speaker_data in result_json.get("speakers", []):
                name = speaker_data.get("name", "").strip()
                role = speaker_data.get("role", "").strip()
                
                if not name:
                    continue
                
                # Normaliser "NON_TROUVE" en chaîne vide
                if role.upper() == "NON_TROUVE":
                    role = ""
                
                # Vérifier si le rôle est dans les rôles connus (priorité)
                if known_roles and name in known_roles:
                    role = known_roles[name]
                
                # Sauvegarder dans le cache si un rôle a été trouvé
                if role:
                    self._role_cache[name] = role
                    self._save_to_persistent_role_cache({name: role})
                
                speakers_list.append({
                    "name": name,
                    "role": role,
                    "is_interviewer": False
                })
            
            logger.info(f"✓ Identification LLM: {len(candidate_speakers)} candidats → {len([s for s in speakers_list if not s['is_interviewer']])} vrais speakers")
            
            return speakers_list
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON de la réponse LLM: {e}")
            logger.error(f"Réponse reçue: {result_text[:500]}")
            # Fallback: retourner les interviewers seulement
            return [
                {"name": name, "role": "", "is_interviewer": True}
                for name in interviewer_names_set
            ]
        except Exception as e:
            logger.error(f"Erreur lors de l'identification/extraction LLM des speakers: {e}")
            # Fallback: retourner les interviewers seulement
            return [
                {"name": name, "role": "", "is_interviewer": True}
                for name in interviewer_names_set
            ]
    
    def set_interviewer_names(self, interviewer_names: List[str]):
        """
        Met à jour la liste des noms d'interviewers
        
        Args:
            interviewer_names: Nouvelle liste des noms d'interviewers
        """
        self.interviewer_names = interviewer_names
        logger.info(f"Liste des interviewers mise à jour: {interviewer_names}")

