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
        VERSION CORRIGÉE: Gère correctement l'état entre les recharges.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Résultat de la validation
        """
        # Afficher un spinner si on est en train de valider
        if st.session_state.get('is_validating', False):
            print(f"🔄 [DEBUG] Spinner activé - validation en cours")
            with st.spinner("Traitement de votre validation en cours..."):
                import time
                time.sleep(0.5)  # Petit délai pour que le spinner soit visible
            # Réinitialiser le flag
            st.session_state.is_validating = False
            print(f"✅ [DEBUG] Flag is_validating réinitialisé")
        
        st.subheader("Validation des Besoins Métier")
        
        if validated_count > 0:
            st.success(f"Vous avez déjà validé {validated_count} besoins")
            remaining = max(0, 5 - validated_count)
            if remaining > 0:
                st.info(f"Il vous faut valider {remaining} besoins supplémentaires pour terminer")
            else:
                st.success("Vous avez atteint le minimum requis (5 besoins)")
        
        st.markdown("---")
        
        # CSS pour améliorer la séparation visuelle
        st.markdown("""
            <style>
            .need-container {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                background-color: #fafafa;
                min-height: 200px;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Ne pas nettoyer les clés ici pour éviter les conflits de timing
        # Les clés seront nettoyées après validation
        
        # Afficher les besoins avec des checkboxes - 2 par ligne
        for i in range(0, len(identified_needs), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier besoin de la ligne
            with col1:
                need = identified_needs[i]
                theme = need.get('theme', 'Thème non défini')
                quotes = need.get('quotes', [])
                
                with st.container():
                    st.markdown('<div class="need-container">', unsafe_allow_html=True)
                    st.markdown(f"### {theme}")
                    
                    if quotes:
                        st.markdown("**Citations:**")
                        for j, quote in enumerate(quotes, 1):
                            st.markdown(f"• {quote}")
                    else:
                        st.info("Aucune citation disponible")
                    
                    # Checkbox pour sélectionner ce besoin avec une clé unique
                    checkbox_key = f"validate_need_{i+1}_{len(identified_needs)}"
                    is_selected = st.checkbox(f"Valider ce besoin", key=checkbox_key)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Deuxième besoin de la ligne (si existant)
            if i + 1 < len(identified_needs):
                with col2:
                    need = identified_needs[i + 1]
                    theme = need.get('theme', 'Thème non défini')
                    quotes = need.get('quotes', [])
                    
                    with st.container():
                        st.markdown('<div class="need-container">', unsafe_allow_html=True)
                        st.markdown(f"### {theme}")
                        
                        if quotes:
                            st.markdown("**Citations:**")
                            for j, quote in enumerate(quotes, 1):
                                st.markdown(f"• {quote}")
                        else:
                            st.info("Aucune citation disponible")
                        
                        # Checkbox pour sélectionner ce besoin avec une clé unique
                        checkbox_key = f"validate_need_{i+2}_{len(identified_needs)}"
                        is_selected = st.checkbox(f"Valider ce besoin", key=checkbox_key)
                        st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Calculer le nombre de sélections en temps réel
        selected_count = 0
        selected_needs_list = []
        
        for i in range(1, len(identified_needs) + 1):
            checkbox_key = f"validate_need_{i}_{len(identified_needs)}"
            is_selected = st.session_state.get(checkbox_key, False)
            if is_selected:
                selected_count += 1
                selected_needs_list.append(i)
        
        # Afficher le nombre de besoins sélectionnés
        if selected_count > 0:
            st.info(f"{selected_count} besoin(s) sélectionné(s)")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            placeholder="Ex: Les besoins sélectionnés sont les plus prioritaires pour notre entreprise...",
            height=100
        )
        
        # Boutons d'action - TOUJOURS VISIBLES
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Valider la sélection", type="primary", disabled=selected_count == 0):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un besoin")
                else:
                    # Lire l'état des checkboxes directement
                    selected_needs = []
                    for i in range(1, len(identified_needs) + 1):
                        checkbox_key = f"validate_need_{i}_{len(identified_needs)}"
                        if st.session_state.get(checkbox_key, False):
                            selected_needs.append(i)
                    
                    # Marquer qu'on est en train de valider
                    st.session_state.is_validating = True
                    
                    # Traiter la validation
                    result = self._process_validation(identified_needs, selected_needs, comments, validated_count)
                    # Note: st.rerun() est appelé dans _process_validation, donc on n'atteint jamais cette ligne
        
        with col2:
            if st.button("Recommencer", type="secondary"):
                # Réinitialiser les checkboxes et l'état
                for i in range(1, len(identified_needs) + 1):
                    if f"validate_need_{i}" in st.session_state:
                        st.session_state[f"validate_need_{i}"] = False
                st.session_state.selected_needs = set()
                st.rerun()
        
        with col3:
            if st.button("Annuler", type="secondary"):
                # Réinitialiser les checkboxes et l'état
                for i in range(1, len(identified_needs) + 1):
                    if f"validate_need_{i}" in st.session_state:
                        st.session_state[f"validate_need_{i}"] = False
                st.session_state.selected_needs = set()
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
        VERSION CORRIGÉE: Gère correctement l'état et les messages.
        
        Args:
            identified_needs: Liste des besoins identifiés
            selected_numbers: Numéros des besoins sélectionnés
            comments: Commentaires de l'utilisateur
            validated_count: Nombre de besoins déjà validés
            
        Returns:
            Résultat de la validation
        """
        print(f"\n✅ [DEBUG] _process_validation - DÉBUT")
        print(f"📊 [DEBUG] selected_numbers: {selected_numbers}")
        print(f"📊 [DEBUG] validated_count: {validated_count}")
        print(f"📊 [DEBUG] comments: {comments[:50] if comments else 'Aucun'}")
        
        # Vérifier qu'au moins un besoin est sélectionné
        if len(selected_numbers) == 0:
            print(f"❌ [DEBUG] Aucun besoin sélectionné")
            st.error("Vous devez sélectionner au moins un besoin à valider")
            return None
        
        # Extraire les besoins validés et rejetés
        validated_new = [identified_needs[i-1] for i in selected_numbers]
        rejected_numbers = [i for i in range(1, len(identified_needs) + 1) if i not in selected_numbers]
        rejected_new = [identified_needs[i-1] for i in rejected_numbers]
        
        print(f"📊 [DEBUG] validated_new: {len(validated_new)} besoins")
        print(f"📊 [DEBUG] rejected_new: {len(rejected_new)} besoins")
        
        # Calculer le total
        total_validated = validated_count + len(validated_new)
        success = total_validated >= 5
        
        print(f"📊 [DEBUG] total_validated: {total_validated}")
        print(f"📊 [DEBUG] success: {success}")
        
        result = {
            "validated_needs": validated_new,  # Seulement les nouveaux besoins validés
            "rejected_needs": rejected_new,
            "user_feedback": comments,
            "success": success,  # Succès seulement si on atteint 5 besoins au total
            "total_validated": total_validated,
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
        
        print(f"💾 [DEBUG] Sauvegarde du résultat dans session_state.validation_result")
        # Sauvegarder le résultat dans session_state
        st.session_state.validation_result = result
        print(f"✅ [DEBUG] Résultat sauvegardé - success={result['success']}, total_validated={result['total_validated']}")
        
        # Nettoyer l'état des sélections et les clés de validation
        print(f"🧹 [DEBUG] Nettoyage des clés de validation")
        st.session_state.selected_needs = set()
        for key in list(st.session_state.keys()):
            if key.startswith("validate_need_"):
                del st.session_state[key]
        print(f"✅ [DEBUG] Nettoyage terminé")
        
        if result["success"]:
            st.success(f"Validation réussie - {total_validated} besoins validés au total")
            print(f"🎉 [DEBUG] Validation réussie - {total_validated} besoins validés")
        else:
            remaining = 5 - total_validated
            st.warning(f"Validation partielle : {total_validated} besoins validés (il reste {remaining} besoins à valider)")
            print(f"⚠️ [DEBUG] Validation partielle - il reste {remaining} besoins à valider")
        
        # Forcer le rechargement de l'interface pour afficher le bouton "Reprendre le workflow"
        print(f"🔄 [DEBUG] Appel de st.rerun()...")
        st.rerun()
        
        print(f"✅ [DEBUG] _process_validation - FIN (cette ligne ne devrait jamais s'afficher)")
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
            st.success("État sauvegardé")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde : {str(e)}")
    
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
            st.success("État supprimé")
    
    def validate_needs(self, identified_needs: List[Dict[str, Any]], validated_needs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processus de validation humaine dans Streamlit.
        VERSION SIMPLIFIÉE: Évite les conflits avec LangGraph.
        
        Args:
            identified_needs: Besoins identifiés à valider
            validated_needs: Besoins déjà validés (optionnel)
            
        Returns:
            Résultat de la validation
        """
        validated_needs = validated_needs or []
        validated_count = len(validated_needs)
        
        # Afficher l'interface de validation
        return self.display_needs_for_validation(identified_needs, validated_count)
    
    def display_workflow_resume_button(self) -> bool:
        """
        Affiche un bouton pour reprendre le workflow après validation.
        
        Returns:
            True si le workflow doit être repris, False sinon
        """
        if st.session_state.get("workflow_paused", False) and st.session_state.get("validation_result"):
            st.success("Validation terminée")
            st.info("Cliquez sur le bouton ci-dessous pour reprendre le workflow")
            
            if st.button("Reprendre le workflow", type="primary"):
                return True
        
        return False
