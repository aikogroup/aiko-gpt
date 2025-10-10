"""
Interface Streamlit pour la validation humaine des besoins métier
"""

import streamlit as st
import json
from typing import List, Dict, Any, Tuple


class StreamlitValidationInterface:
    """
    Interface Streamlit pour la validation humaine des besoins métier
    """
    
    def __init__(self):
        """Initialise l'interface de validation Streamlit"""
        pass
    
    def display_needs_for_validation(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0) -> Dict[str, Any]:
        """
        Affiche les besoins identifiés pour validation dans Streamlit.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Résultat de la validation
        """
        st.subheader("🔍 Validation des Besoins Métier")
        
        if validated_count > 0:
            st.success(f"✅ Vous avez déjà validé {validated_count} besoins")
            remaining = max(0, 5 - validated_count)
            st.info(f"🎯 Il vous faut valider au moins {remaining} besoins supplémentaires")
        
        st.markdown("---")
        
        # Afficher les besoins avec des checkboxes
        selected_needs = []
        
        for i, need in enumerate(identified_needs, 1):
            theme = need.get('theme', 'Thème non défini')
            quotes = need.get('quotes', [])
            
            with st.expander(f"🔹 {theme}", expanded=False):
                st.markdown(f"**Thème:** {theme}")
                
                if quotes:
                    st.markdown("**Citations:**")
                    for j, quote in enumerate(quotes, 1):
                        st.markdown(f"• {quote}")
                else:
                    st.info("Aucune citation disponible")
                
                # Checkbox pour valider ce besoin
                if st.checkbox(f"✅ Valider ce besoin", key=f"validate_need_{i}"):
                    selected_needs.append(i)
        
        st.markdown("---")
        
        # Zone de commentaires
        st.subheader("💬 Commentaires (optionnel)")
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            placeholder="Ex: Les besoins sélectionnés sont les plus prioritaires pour notre entreprise...",
            height=100
        )
        
        # Boutons d'action
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("✅ Valider la sélection", type="primary"):
                return self._process_validation(identified_needs, selected_needs, comments, validated_count)
        
        with col2:
            if st.button("🔄 Recommencer", type="secondary"):
                st.rerun()
        
        with col3:
            if st.button("❌ Annuler", type="secondary"):
                return {
                    "validated_needs": [],
                    "rejected_needs": [],
                    "user_feedback": "Validation annulée",
                    "success": False,
                    "total_validated": validated_count
                }
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_validation(self, identified_needs: List[Dict[str, Any]], selected_numbers: List[int], comments: str, validated_count: int) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur.
        
        Args:
            identified_needs: Liste des besoins identifiés
            selected_numbers: Numéros des besoins sélectionnés
            comments: Commentaires de l'utilisateur
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Résultat de la validation
        """
        remaining_needs = max(0, 5 - validated_count)
        
        if len(selected_numbers) < remaining_needs:
            st.error(f"❌ Vous devez valider au moins {remaining_needs} besoins (vous en avez sélectionné {len(selected_numbers)})")
            return None
        
        # Extraire les besoins validés et rejetés
        validated_new = [identified_needs[i-1] for i in selected_numbers]
        rejected_numbers = [i for i in range(1, len(identified_needs) + 1) if i not in selected_numbers]
        rejected_new = [identified_needs[i-1] for i in rejected_numbers]
        
        # Calculer le total
        total_validated = validated_count + len(validated_new)
        
        result = {
            "validated_needs": validated_new,  # Seulement les nouveaux besoins validés
            "rejected_needs": rejected_new,
            "user_feedback": comments,
            "success": total_validated >= 5,
            "total_validated": total_validated,
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
        
        if result["success"]:
            st.success(f"✅ Validation réussie ! {total_validated} besoins validés au total")
        else:
            st.warning(f"⚠️ Validation partielle : {total_validated} besoins validés (minimum 5 requis)")
        
        return result
    
    def save_workflow_state(self, state: Dict[str, Any]) -> None:
        """
        Sauvegarde l'état du workflow.
        
        Args:
            state: État du workflow à sauvegarder
        """
        try:
            # Sauvegarder dans session_state pour Streamlit
            st.session_state.workflow_state = state
            st.success("💾 État sauvegardé")
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
    
    def load_workflow_state(self) -> Dict[str, Any]:
        """
        Charge l'état du workflow depuis session_state.
        
        Returns:
            État du workflow ou dictionnaire vide
        """
        return st.session_state.get("workflow_state", {})
    
    def clear_workflow_state(self) -> None:
        """
        Supprime l'état du workflow de session_state.
        """
        if "workflow_state" in st.session_state:
            del st.session_state.workflow_state
            st.success("🗑️ État supprimé")
    
    def validate_needs(self, identified_needs: List[Dict[str, Any]], validated_needs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processus complet de validation humaine dans Streamlit.
        
        Args:
            identified_needs: Besoins identifiés à valider
            validated_needs: Besoins déjà validés (optionnel)
            
        Returns:
            Résultat de la validation
        """
        validated_needs = validated_needs or []
        validated_count = len(validated_needs)
        
        # Afficher l'interface de validation
        result = self.display_needs_for_validation(identified_needs, validated_count)
        
        if result is None:
            # En attente de validation
            return {
                "validated_needs": [],
                "rejected_needs": [],
                "user_feedback": "",
                "success": False,
                "total_validated": validated_count
            }
        
        return result
