"""
Système de tracking des tokens d'API OpenAI
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TokenTracker:
    """
    Classe pour tracker les tokens des appels API.
    Compatible avec LangGraph Studio (pas d'opérations bloquantes synchrones).
    """
    
    def __init__(self, output_dir: str = "outputs/token_tracking"):
        """
        Initialise le tracker.
        
        Args:
            output_dir: Répertoire de sauvegarde des rapports
        """
        self.output_dir = Path(output_dir)
        # ⚠️ Ne pas créer le dossier ici pour compatibilité LangGraph Studio
        # Il sera créé lors de la sauvegarde si nécessaire
        
        self.session_stats = {
            "session_start": datetime.now().isoformat(),
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "calls_by_agent": {},
            "calls_detail": []
        }
    
    def track_response(
        self, 
        response: Any, 
        agent_name: str,
        operation: str,
        model: str = "gpt-5-nano"
    ) -> Dict[str, Any]:
        """
        Track une réponse d'API et compte les tokens.
        
        Args:
            response: Objet response de l'API OpenAI
            agent_name: Nom de l'agent (ex: "need_analysis", "workshop")
            operation: Type d'opération (ex: "analyze_needs", "parse_workshop")
            model: Nom du modèle utilisé
            
        Returns:
            Dict avec les statistiques de cet appel
        """
        try:
            # Extraction des informations d'usage depuis la réponse
            usage = self._extract_usage(response)
            
            if not usage:
                logger.warning(f"Impossible d'extraire les informations d'usage pour {agent_name}")
                return {}
            
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            
            # Création du record
            call_record = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "operation": operation,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
            
            # Mise à jour des statistiques globales
            self._update_session_stats(call_record)
            
            # Log
            logger.info(
                f"📊 [{agent_name}] {operation} - "
                f"Tokens: {input_tokens:,} in + {output_tokens:,} out = {total_tokens:,} total"
            )
            
            return call_record
            
        except Exception as e:
            logger.error(f"Erreur lors du tracking: {e}", exc_info=True)
            return {}
    
    def _extract_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """
        Extrait les informations d'usage depuis la réponse API.
        
        Args:
            response: Objet response de l'API
            
        Returns:
            Dict avec input_tokens, output_tokens
        """
        # Tentative 1: Attribut usage direct
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'input_tokens') and hasattr(usage, 'output_tokens'):
                return {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens
                }
            # Format alternatif (prompt_tokens, completion_tokens)
            elif hasattr(usage, 'prompt_tokens') and hasattr(usage, 'completion_tokens'):
                return {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens
                }
        
        # Tentative 2: Dictionnaire
        if isinstance(response, dict):
            if 'usage' in response:
                usage = response['usage']
                return {
                    "input_tokens": usage.get('input_tokens') or usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('output_tokens') or usage.get('completion_tokens', 0)
                }
        
        return None
    
    def _update_session_stats(self, call_record: Dict[str, Any]):
        """
        Met à jour les statistiques de session.
        
        Args:
            call_record: Enregistrement d'un appel
        """
        self.session_stats["total_calls"] += 1
        self.session_stats["total_input_tokens"] += call_record["input_tokens"]
        self.session_stats["total_output_tokens"] += call_record["output_tokens"]
        self.session_stats["total_tokens"] += call_record["total_tokens"]
        
        # Statistiques par agent
        agent_name = call_record["agent_name"]
        if agent_name not in self.session_stats["calls_by_agent"]:
            self.session_stats["calls_by_agent"][agent_name] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        
        self.session_stats["calls_by_agent"][agent_name]["calls"] += 1
        self.session_stats["calls_by_agent"][agent_name]["input_tokens"] += call_record["input_tokens"]
        self.session_stats["calls_by_agent"][agent_name]["output_tokens"] += call_record["output_tokens"]
        self.session_stats["calls_by_agent"][agent_name]["total_tokens"] += call_record["total_tokens"]
        
        # Ajout du détail
        self.session_stats["calls_detail"].append(call_record)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé de la session en cours.
        
        Returns:
            Dict avec les statistiques de session
        """
        return {
            "session_start": self.session_stats["session_start"],
            "total_calls": self.session_stats["total_calls"],
            "total_input_tokens": self.session_stats["total_input_tokens"],
            "total_output_tokens": self.session_stats["total_output_tokens"],
            "total_tokens": self.session_stats["total_tokens"],
            "calls_by_agent": self.session_stats["calls_by_agent"]
        }
    
    def print_summary(self):
        """
        Affiche un résumé formaté de la session.
        """
        summary = self.get_session_summary()
        
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DES TOKENS")
        print("="*70)
        print(f"🕐 Session démarrée: {summary['session_start']}")
        print(f"📞 Nombre d'appels API: {summary['total_calls']}")
        print(f"🔤 Tokens totaux: {summary['total_tokens']:,}")
        print(f"   ├─ Input:  {summary['total_input_tokens']:,}")
        print(f"   └─ Output: {summary['total_output_tokens']:,}")
        
        if summary['calls_by_agent']:
            print("\n📊 Détails par agent:")
            for agent_name, stats in summary['calls_by_agent'].items():
                print(f"   • {agent_name}:")
                print(f"     ├─ Appels: {stats['calls']}")
                print(f"     ├─ Input tokens: {stats['input_tokens']:,}")
                print(f"     ├─ Output tokens: {stats['output_tokens']:,}")
                print(f"     └─ Total tokens: {stats['total_tokens']:,}")
        
        print("="*70 + "\n")
    
    def save_report(self, filename: str = None):
        """
        Sauvegarde le rapport complet en JSON.
        Crée le dossier de sortie si nécessaire.
        
        Args:
            filename: Nom du fichier (auto-généré si None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"token_report_{timestamp}.json"
        
        # Créer le dossier uniquement lors de la sauvegarde
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Rapport sauvegardé: {filepath}")
        return str(filepath)


# Instance globale du tracker (optionnel)
_global_tracker = None

def get_global_tracker() -> TokenTracker:
    """
    Retourne l'instance globale du tracker (singleton).
    
    Returns:
        Instance de TokenTracker
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenTracker()
    return _global_tracker

