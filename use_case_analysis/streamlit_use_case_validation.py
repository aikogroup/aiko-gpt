"""
Interface Streamlit pour la validation humaine des cas d'usage IA
"""

import streamlit as st
import json
import logging
from typing import List, Dict, Any, Optional

# Configuration du logger
logger = logging.getLogger(__name__)


class StreamlitUseCaseValidation:
    """
    Interface Streamlit pour la validation humaine des cas d'usage IA.
    Permet de valider simultanément les Quick Wins et les Structuration IA.
    """
    
    def __init__(self):
        """Initialise l'interface de validation Streamlit"""
        logger.info("StreamlitUseCaseValidation initialisé")
    
    def display_use_cases_for_validation(
        self,
        quick_wins: List[Dict[str, Any]],
        structuration_ia: List[Dict[str, Any]],
        validated_qw_count: int = 0,
        validated_sia_count: int = 0,
        key_suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche les cas d'usage pour validation dans Streamlit.
        Validation simultanée des deux familles.
        
        Args:
            quick_wins: Liste des Quick Wins proposés
            structuration_ia: Liste des Structuration IA proposés
            validated_qw_count: Nombre de Quick Wins déjà validés
            validated_sia_count: Nombre de Structuration IA déjà validés
            key_suffix: Suffixe personnalisé pour les clés de checkbox (ex: iteration_count). Si None, utilise len(quick_wins)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(quick_wins))
        logger.info(f"Affichage de {len(quick_wins)} Quick Wins et {len(structuration_ia)} Structuration IA")
        
        # (Spinner retiré - géré par app_api.py pour un flux continu)
        
        st.title("Validation des Cas d'Usage IA")
        
        # Afficher le statut de validation
        col1, col2 = st.columns(2)
        
        with col1:
            if validated_qw_count >= 5:
                st.success(f"Quick Wins : {validated_qw_count}/5 validés")
            else:
                remaining_qw = 5 - validated_qw_count
                st.warning(f"Quick Wins : {validated_qw_count}/5 validés (encore {remaining_qw} requis)")
        
        with col2:
            if validated_sia_count >= 5:
                st.success(f"Structuration IA : {validated_sia_count}/5 validés")
            else:
                remaining_sia = 5 - validated_sia_count
                st.warning(f"Structuration IA : {validated_sia_count}/5 validés (encore {remaining_sia} requis)")
        
        st.markdown("---")
        
        # Section Quick Wins
        st.header("⚡ Quick Wins - Automatisation & assistance intelligente")
        st.caption("Solutions à faible complexité technique, mise en œuvre rapide (< 3 mois), ROI immédiat")
        
        # Afficher les Quick Wins - 2 par ligne
        for i in range(0, len(quick_wins), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier Quick Win de la ligne
            with col1:
                use_case = quick_wins[i]
                st.markdown(f"#### {use_case.get('titre', 'Titre non défini')}")
                st.markdown(f"**IA utilisée :** {use_case.get('ia_utilisee', 'Non spécifié')}")
                st.markdown(f"**Description :**")
                st.markdown(use_case.get('description', 'Description non disponible'))
                
                # Checkbox pour sélectionner ce Quick Win
                checkbox_key = f"validate_qw_{i+1}_{key_suffix}"
                is_selected = st.checkbox(f"Valider ce Quick Win", key=checkbox_key)
            
            # Deuxième Quick Win de la ligne (si existant)
            if i + 1 < len(quick_wins):
                with col2:
                    use_case = quick_wins[i + 1]
                    st.markdown(f"#### {use_case.get('titre', 'Titre non défini')}")
                    st.markdown(f"**IA utilisée :** {use_case.get('ia_utilisee', 'Non spécifié')}")
                    st.markdown(f"**Description :**")
                    st.markdown(use_case.get('description', 'Description non disponible'))
                    
                    # Checkbox pour sélectionner ce Quick Win
                    checkbox_key = f"validate_qw_{i+2}_{key_suffix}"
                    is_selected = st.checkbox(f"Valider ce Quick Win", key=checkbox_key)
            
            # Ligne de séparation fine entre les Quick Wins
            st.markdown("---")
        
        # Séparation visuelle forte entre les deux sections
        st.markdown("---")
        st.markdown("##")  # Espace supplémentaire
        
        # Section Structuration IA
        st.header("🔬 Structuration IA à moyen et long terme - Scalabilité & qualité prédictive")
        st.caption("Solutions à complexité moyenne/élevée, mise en œuvre progressive (3-12 mois), ROI moyen/long terme")
        
        # Afficher les Structuration IA - 2 par ligne
        for i in range(0, len(structuration_ia), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier Structuration IA de la ligne
            with col1:
                use_case = structuration_ia[i]
                st.markdown(f"#### {use_case.get('titre', 'Titre non défini')}")
                st.markdown(f"**IA utilisée :** {use_case.get('ia_utilisee', 'Non spécifié')}")
                st.markdown(f"**Description :**")
                st.markdown(use_case.get('description', 'Description non disponible'))
                
                # Checkbox pour sélectionner cette Structuration IA
                checkbox_key = f"validate_sia_{i+1}_{key_suffix}"
                is_selected = st.checkbox(f"Valider ce cas d'usage", key=checkbox_key)
            
            # Deuxième Structuration IA de la ligne (si existant)
            if i + 1 < len(structuration_ia):
                with col2:
                    use_case = structuration_ia[i + 1]
                    st.markdown(f"#### {use_case.get('titre', 'Titre non défini')}")
                    st.markdown(f"**IA utilisée :** {use_case.get('ia_utilisee', 'Non spécifié')}")
                    st.markdown(f"**Description :**")
                    st.markdown(use_case.get('description', 'Description non disponible'))
                    
                    # Checkbox pour sélectionner cette Structuration IA
                    checkbox_key = f"validate_sia_{i+2}_{key_suffix}"
                    is_selected = st.checkbox(f"Valider ce cas d'usage", key=checkbox_key)
            
            # Ligne de séparation fine entre les Structuration IA
            st.markdown("---")
        
        # Calculer le nombre de sélections en temps réel
        selected_qw_count = len([i for i in range(1, len(quick_wins) + 1) 
                                 if st.session_state.get(f"validate_qw_{i}_{key_suffix}", False)])
        selected_sia_count = len([i for i in range(1, len(structuration_ia) + 1) 
                                  if st.session_state.get(f"validate_sia_{i}_{key_suffix}", False)])
        
        # Afficher le nombre de sélections
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_qw_count > 0:
                st.info(f"{selected_qw_count} Quick Win(s) sélectionné(s)")
        
        with col2:
            if selected_sia_count > 0:
                st.info(f"{selected_sia_count} Structuration IA sélectionné(s)")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            placeholder="Ex: Les Quick Wins sélectionnés sont les plus pertinents pour notre contexte...",
            height=100
        )
        
        # Boutons d'action
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            can_validate = selected_qw_count > 0 or selected_sia_count > 0
            if st.button("Valider la sélection", type="primary", disabled=not can_validate):
                if not can_validate:
                    st.warning("Veuillez sélectionner au moins un cas d'usage")
                else:
                    # Lire l'état des checkboxes directement
                    selected_qw_indices = []
                    for i in range(1, len(quick_wins) + 1):
                        checkbox_key = f"validate_qw_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_qw_indices.append(i)
                    
                    selected_sia_indices = []
                    for i in range(1, len(structuration_ia) + 1):
                        checkbox_key = f"validate_sia_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_sia_indices.append(i)
                    
                    # Traiter la validation et retourner le résultat
                    result = self._process_validation(
                        quick_wins, 
                        structuration_ia,
                        selected_qw_indices,
                        selected_sia_indices,
                        comments,
                        validated_qw_count,
                        validated_sia_count
                    )
                    return result  # Retourner le résultat pour que app_api.py puisse l'envoyer à l'API
        
        with col2:
            if st.button("Recommencer", type="secondary"):
                # Réinitialiser les checkboxes
                for i in range(1, len(quick_wins) + 1):
                    checkbox_key = f"validate_qw_{i}_{key_suffix}"
                    if checkbox_key in st.session_state:
                        st.session_state[checkbox_key] = False
                
                for i in range(1, len(structuration_ia) + 1):
                    checkbox_key = f"validate_sia_{i}_{key_suffix}"
                    if checkbox_key in st.session_state:
                        st.session_state[checkbox_key] = False
                
                st.rerun()
        
        with col3:
            if st.button("Annuler", type="secondary"):
                # Réinitialiser les checkboxes
                for i in range(1, len(quick_wins) + 1):
                    checkbox_key = f"validate_qw_{i}_{key_suffix}"
                    if checkbox_key in st.session_state:
                        st.session_state[checkbox_key] = False
                
                for i in range(1, len(structuration_ia) + 1):
                    checkbox_key = f"validate_sia_{i}_{key_suffix}"
                    if checkbox_key in st.session_state:
                        st.session_state[checkbox_key] = False
                
                return {
                    "validated_quick_wins": [],
                    "validated_structuration_ia": [],
                    "rejected_quick_wins": [],
                    "rejected_structuration_ia": [],
                    "user_feedback": "Validation annulée",
                    "success": False,
                    "total_validated_qw": validated_qw_count,
                    "total_validated_sia": validated_sia_count
                }
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_validation(
        self,
        quick_wins: List[Dict[str, Any]],
        structuration_ia: List[Dict[str, Any]],
        selected_qw_indices: List[int],
        selected_sia_indices: List[int],
        comments: str,
        validated_qw_count: int,
        validated_sia_count: int
    ) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur.
        
        Args:
            quick_wins: Liste des Quick Wins proposés
            structuration_ia: Liste des Structuration IA proposés
            selected_qw_indices: Indices des Quick Wins sélectionnés
            selected_sia_indices: Indices des Structuration IA sélectionnés
            comments: Commentaires de l'utilisateur
            validated_qw_count: Nombre de Quick Wins déjà validés
            validated_sia_count: Nombre de Structuration IA déjà validés
            
        Returns:
            Résultat de la validation
        """
        logger.info(f"Traitement de la validation : {len(selected_qw_indices)} QW, {len(selected_sia_indices)} SIA")
        print(f"\n✅ [DEBUG UC] _process_validation - DÉBUT")
        print(f"📊 [DEBUG UC] selected_qw_indices: {selected_qw_indices}")
        print(f"📊 [DEBUG UC] selected_sia_indices: {selected_sia_indices}")
        print(f"📊 [DEBUG UC] validated_qw_count: {validated_qw_count}")
        print(f"📊 [DEBUG UC] validated_sia_count: {validated_sia_count}")
        
        # Extraire les cas d'usage validés et rejetés
        validated_qw = [quick_wins[i-1] for i in selected_qw_indices]
        rejected_qw_indices = [i for i in range(1, len(quick_wins) + 1) if i not in selected_qw_indices]
        rejected_qw = [quick_wins[i-1] for i in rejected_qw_indices]
        
        validated_sia = [structuration_ia[i-1] for i in selected_sia_indices]
        rejected_sia_indices = [i for i in range(1, len(structuration_ia) + 1) if i not in selected_sia_indices]
        rejected_sia = [structuration_ia[i-1] for i in rejected_sia_indices]
        
        # Calculer les totaux
        total_validated_qw = validated_qw_count + len(validated_qw)
        total_validated_sia = validated_sia_count + len(validated_sia)
        
        # Succès si au moins 5 dans chaque famille
        success = total_validated_qw >= 5 and total_validated_sia >= 5
        
        logger.info(f"Validation : QW={total_validated_qw}/5, SIA={total_validated_sia}/5, Succès={success}")
        
        result = {
            "validated_quick_wins": validated_qw,
            "validated_structuration_ia": validated_sia,
            "rejected_quick_wins": rejected_qw,
            "rejected_structuration_ia": rejected_sia,
            "user_feedback": comments,
            "success": success,
            "total_validated_qw": total_validated_qw,
            "total_validated_sia": total_validated_sia,
            "newly_validated_qw": validated_qw,
            "newly_validated_sia": validated_sia,
            "newly_rejected_qw": rejected_qw,
            "newly_rejected_sia": rejected_sia
        }
        
        print(f"💾 [DEBUG UC] Préparation du résultat")
        print(f"✅ [DEBUG UC] Résultat préparé - success={result['success']}, QW={result['total_validated_qw']}, SIA={result['total_validated_sia']}")
        
        # Nettoyer les clés de validation
        print(f"🧹 [DEBUG UC] Nettoyage des clés de validation")
        for key in list(st.session_state.keys()):
            if key.startswith("validate_qw_") or key.startswith("validate_sia_"):
                del st.session_state[key]
        print(f"✅ [DEBUG UC] Nettoyage terminé")
        
        if success:
            print(f"🎉 [DEBUG UC] Validation réussie")
        else:
            remaining_qw = max(0, 5 - total_validated_qw)
            remaining_sia = max(0, 5 - total_validated_sia)
            print(f"⚠️ [DEBUG UC] Validation partielle - QW restants={remaining_qw}, SIA restants={remaining_sia}")
        
        print(f"✅ [DEBUG UC] _process_validation - Retour du résultat")
        return result
    
    def validate_use_cases(
        self,
        quick_wins: List[Dict[str, Any]],
        structuration_ia: List[Dict[str, Any]],
        validated_quick_wins: List[Dict[str, Any]] = None,
        validated_structuration_ia: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processus de validation humaine dans Streamlit.
        
        Args:
            quick_wins: Quick Wins proposés à valider
            structuration_ia: Structuration IA proposés à valider
            validated_quick_wins: Quick Wins déjà validés (optionnel)
            validated_structuration_ia: Structuration IA déjà validés (optionnel)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        validated_quick_wins = validated_quick_wins or []
        validated_structuration_ia = validated_structuration_ia or []
        
        validated_qw_count = len(validated_quick_wins)
        validated_sia_count = len(validated_structuration_ia)
        
        # Afficher l'interface de validation
        return self.display_use_cases_for_validation(
            quick_wins,
            structuration_ia,
            validated_qw_count,
            validated_sia_count
        )

