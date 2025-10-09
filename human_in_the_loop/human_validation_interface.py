"""
Interface humaine pour la validation des besoins métier
"""

import json
import os
from typing import List, Dict, Any, Tuple


class HumanValidationInterface:
    """
    Interface pour la validation humaine des besoins métier
    """
    
    def __init__(self, state_file_path: str = "/home/addeche/aiko/aikoGPT/outputs/workflow_state.json"):
        """
        Initialise l'interface de validation humaine.
        
        Args:
            state_file_path: Chemin vers le fichier de sauvegarde de l'état
        """
        self.state_file_path = state_file_path
    
    def display_needs(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0) -> None:
        """
        Affiche les besoins identifiés pour validation.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
        """
        print("\n" + "="*80)
        print("🔍 VALIDATION DES BESOINS MÉTIER")
        print("="*80)
        
        if validated_count > 0:
            print(f"✅ Vous avez déjà validé {validated_count} besoins")
            print(f"🎯 Il vous faut valider au moins {max(0, 5 - validated_count)} besoins supplémentaires")
            print()
        
        print("📋 Voici les besoins identifiés :")
        print("-" * 80)
        
        for i, need in enumerate(identified_needs, 1):
            print(f"\n{i}. {need.get('title', 'N/A')}")
            print(f"   Thème: {need.get('theme', 'N/A')}")
            print(f"   Priorité: {need.get('priority', 'N/A')}")
            print(f"   Description: {need.get('description', 'N/A')}")
            
            if need.get('quotes'):
                print(f"   Citations ({len(need['quotes'])}):")
                for quote in need['quotes'][:2]:  # Afficher max 2 citations
                    print(f"     • \"{quote}\"")
                if len(need['quotes']) > 2:
                    print(f"     • ... et {len(need['quotes']) - 2} autres citations")
            print()
    
    def get_user_validation(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0) -> Tuple[List[int], str]:
        """
        Récupère la validation de l'utilisateur.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Tuple contenant (numéros_validés, commentaires)
        """
        self.display_needs(identified_needs, validated_count)
        
        print("="*80)
        print("🤔 VALIDATION REQUISE")
        print("="*80)
        
        remaining_needs = max(0, 5 - validated_count)
        print(f"Vous devez valider au moins {remaining_needs} besoins supplémentaires.")
        print()
        print("Instructions :")
        print("• Entrez les numéros des besoins que vous validez (ex: 1,3,5,7,9)")
        print("• Ajoutez des commentaires si nécessaire (ex: 1,3,5,7,9 - Les autres sont trop vagues)")
        print("• Appuyez sur Entrée pour valider")
        print()
        
        while True:
            try:
                user_input = input("Vos choix : ").strip()
                
                if not user_input:
                    print("❌ Veuillez entrer au moins un numéro")
                    continue
                
                # Séparer les numéros des commentaires
                if " - " in user_input:
                    numbers_part, comments = user_input.split(" - ", 1)
                    comments = comments.strip()
                else:
                    numbers_part = user_input
                    comments = ""
                
                # Parser les numéros
                numbers = []
                for num_str in numbers_part.split(","):
                    num_str = num_str.strip()
                    if num_str.isdigit():
                        num = int(num_str)
                        if 1 <= num <= len(identified_needs):
                            numbers.append(num)
                        else:
                            print(f"❌ Le numéro {num} n'est pas valide (doit être entre 1 et {len(identified_needs)})")
                            break
                    else:
                        print(f"❌ '{num_str}' n'est pas un numéro valide")
                        break
                else:
                    # Tous les numéros sont valides
                    if len(numbers) >= remaining_needs:
                        return numbers, comments
                    else:
                        print(f"❌ Vous devez valider au moins {remaining_needs} besoins (vous en avez sélectionné {len(numbers)})")
                        continue
                        
            except KeyboardInterrupt:
                print("\n\n❌ Validation annulée par l'utilisateur")
                return [], ""
            except Exception as e:
                print(f"❌ Erreur lors de la validation : {str(e)}")
                continue
    
    def save_workflow_state(self, state: Dict[str, Any]) -> None:
        """
        Sauvegarde l'état du workflow.
        
        Args:
            state: État du workflow à sauvegarder
        """
        try:
            # Créer le dossier outputs s'il n'existe pas
            os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)
            
            # Nettoyer l'état pour la sérialisation JSON
            clean_state = self._clean_state_for_serialization(state)
            
            # Sauvegarder l'état
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(clean_state, f, ensure_ascii=False, indent=2)
            
            print(f"💾 État sauvegardé dans {self.state_file_path}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {str(e)}")
    
    def _clean_state_for_serialization(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie l'état pour la sérialisation JSON en supprimant les objets non sérialisables.
        
        Args:
            state: État du workflow
            
        Returns:
            État nettoyé
        """
        clean_state = {}
        
        for key, value in state.items():
            if key == "messages":
                # Convertir les messages en dictionnaires simples
                clean_messages = []
                for msg in value:
                    if hasattr(msg, 'content') and hasattr(msg, 'type'):
                        clean_messages.append({
                            "type": msg.type,
                            "content": msg.content
                        })
                    else:
                        clean_messages.append(str(msg))
                clean_state[key] = clean_messages
            elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
                clean_state[key] = value
            else:
                # Convertir les autres objets en string
                clean_state[key] = str(value)
        
        return clean_state
    
    def load_workflow_state(self) -> Dict[str, Any]:
        """
        Charge l'état du workflow.
        
        Returns:
            État du workflow ou dictionnaire vide
        """
        try:
            if os.path.exists(self.state_file_path):
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"❌ Erreur lors du chargement : {str(e)}")
            return {}
    
    def clear_workflow_state(self) -> None:
        """
        Supprime le fichier d'état du workflow.
        """
        try:
            if os.path.exists(self.state_file_path):
                os.remove(self.state_file_path)
                print(f"🗑️ État supprimé : {self.state_file_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la suppression : {str(e)}")
    
    def validate_needs(self, identified_needs: List[Dict[str, Any]], validated_needs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processus complet de validation humaine.
        
        Args:
            identified_needs: Besoins identifiés à valider
            validated_needs: Besoins déjà validés (optionnel)
            
        Returns:
            Résultat de la validation
        """
        validated_needs = validated_needs or []
        validated_count = len(validated_needs)
        
        # Afficher les besoins et récupérer la validation
        selected_numbers, comments = self.get_user_validation(identified_needs, validated_count)
        
        if not selected_numbers:
            return {
                "validated_needs": [],
                "rejected_needs": [],
                "user_feedback": comments,
                "success": False,
                "total_validated": validated_count
            }
        
        # Extraire les besoins validés et rejetés
        validated_new = [identified_needs[i-1] for i in selected_numbers]
        rejected_numbers = [i for i in range(1, len(identified_needs) + 1) if i not in selected_numbers]
        rejected_new = [identified_needs[i-1] for i in rejected_numbers]
        
        # Combiner avec les besoins déjà validés
        all_validated = validated_needs + validated_new
        
        return {
            "validated_needs": all_validated,
            "rejected_needs": rejected_new,
            "user_feedback": comments,
            "success": len(all_validated) >= 5,
            "total_validated": len(all_validated),
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
