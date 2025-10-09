"""
Interface mock pour la validation humaine des besoins métier
Utilisée pour les tests automatisés
"""

import json
import os
from typing import List, Dict, Any, Tuple
from human_in_the_loop.human_validation_interface import HumanValidationInterface


class MockHumanValidationInterface(HumanValidationInterface):
    """
    Interface mock pour la validation humaine des besoins métier
    Simule les réponses utilisateur pour les tests automatisés
    """
    
    def __init__(self, state_file_path: str = "/home/addeche/aiko/aikoGPT/outputs/workflow_state.json", 
                 mock_responses: List[str] = None):
        """
        Initialise l'interface mock de validation humaine.
        
        Args:
            state_file_path: Chemin vers le fichier de sauvegarde de l'état
            mock_responses: Liste des réponses simulées (optionnel)
        """
        super().__init__(state_file_path)
        
        # Réponses par défaut pour les tests
        self.mock_responses = mock_responses or [
            "1,2,3,4,5",  # Première validation
            "6,7,8,9,10", # Deuxième validation si nécessaire
            "1,2,3,4,5,6,7,8,9,10"  # Validation complète
        ]
        self.response_index = 0
    
    def get_user_validation(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0) -> Tuple[List[int], str]:
        """
        Simule la validation de l'utilisateur avec des réponses prédéfinies.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Tuple contenant (numéros_validés, commentaires)
        """
        print(f"\n🤖 SIMULATION - Validation automatique (itération {self.response_index + 1})")
        print(f"📊 Besoins identifiés: {len(identified_needs)}")
        print(f"✅ Déjà validés: {validated_count}")
        
        # Afficher les besoins pour information
        self.display_needs(identified_needs, validated_count)
        
        # Utiliser la réponse mock
        if self.response_index < len(self.mock_responses):
            mock_input = self.mock_responses[self.response_index]
            self.response_index += 1
        else:
            # Si on a épuisé les réponses, valider tous les besoins disponibles
            mock_input = ",".join(str(i) for i in range(1, min(len(identified_needs) + 1, 11)))
        
        print(f"🤖 Réponse simulée: {mock_input}")
        
        # Parser la réponse comme dans l'interface normale
        try:
            # Séparer les numéros des commentaires
            if " - " in mock_input:
                numbers_part, comments = mock_input.split(" - ", 1)
                comments = comments.strip()
            else:
                numbers_part = mock_input
                comments = f"Validation automatique (test {self.response_index})"
            
            # Parser les numéros
            numbers = []
            for num_str in numbers_part.split(","):
                num_str = num_str.strip()
                if num_str.isdigit():
                    num = int(num_str)
                    if 1 <= num <= len(identified_needs):
                        numbers.append(num)
            
            print(f"✅ Besoins sélectionnés: {numbers}")
            print(f"💬 Commentaires: {comments}")
            
            return numbers, comments
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing de la réponse mock: {str(e)}")
            # Fallback: valider les premiers besoins
            fallback_numbers = list(range(1, min(6, len(identified_needs) + 1)))
            return fallback_numbers, "Validation automatique (fallback)"
    
    def display_needs(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0) -> None:
        """
        Affiche les besoins identifiés pour validation (version simplifiée pour les tests).
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
        """
        print(f"\n📋 Besoins identifiés ({len(identified_needs)}):")
        print("-" * 60)
        
        for i, need in enumerate(identified_needs, 1):
            print(f"{i}. {need.get('title', 'N/A')} - {need.get('theme', 'N/A')}")
        
        if validated_count > 0:
            print(f"\n✅ Déjà validés: {validated_count}")
            print(f"🎯 Besoins supplémentaires requis: {max(0, 5 - validated_count)}")
    
    def set_mock_responses(self, responses: List[str]) -> None:
        """
        Définit les réponses mock à utiliser.
        
        Args:
            responses: Liste des réponses simulées
        """
        self.mock_responses = responses
        self.response_index = 0
    
    def reset_responses(self) -> None:
        """
        Remet à zéro l'index des réponses.
        """
        self.response_index = 0
