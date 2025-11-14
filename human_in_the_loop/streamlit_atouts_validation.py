"""
Interface Streamlit pour la validation humaine des atouts de l'entreprise
"""

import streamlit as st
import json
from typing import List, Dict, Any


class StreamlitAtoutsValidation:
    """
    Interface Streamlit pour la validation humaine des atouts de l'entreprise
    """
    
    def __init__(self):
        """Initialise l'interface de validation Streamlit"""
        pass
    
    def _on_checkbox_change(self):
        """Callback pour les changements de checkbox - force un rerun"""
        # Ne rien faire - le simple fait d'avoir un callback force Streamlit à recalculer
        pass
    
    def display_atouts_for_validation(self, proposed_atouts: List[Dict[str, Any]], validated_count: int = 0, key_suffix: str = None) -> Dict[str, Any]:
        """
        Affiche les atouts proposés pour validation dans Streamlit.
        
        Args:
            proposed_atouts: Liste des atouts proposés
            validated_count: Nombre d'atouts déjà validés
            key_suffix: Suffixe personnalisé pour les clés de checkbox (ex: iteration_count). Si None, utilise len(proposed_atouts)
            
        Returns:
            Résultat de la validation
        """
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(proposed_atouts))
        
        # IMPORTANT: Ne nettoyer que lors de l'affichage initial, pas lors des reruns causés par les callbacks
        # Utiliser un flag pour savoir si cette liste d'atouts a déjà été initialisée
        initialization_flag = f"atouts_initialized_{key_suffix}"
        
        # Si c'est la première fois qu'on affiche cette liste d'atouts avec ce key_suffix
        if initialization_flag not in st.session_state:
            # Nettoyer TOUTES les anciennes clés de validation pour réinitialiser les checkboxes
            # Cela garantit que les checkboxes sont toujours réinitialisées quand de nouveaux atouts sont affichés
            for key in list(st.session_state.keys()):
                if (key.startswith("validate_atout_") or 
                    key.startswith("atout_titre_") or 
                    key.startswith("atout_description_")):
                    del st.session_state[key]
            # Marquer comme initialisé
            st.session_state[initialization_flag] = True
        
        st.subheader("Validation des Atouts de l'Entreprise")
        
        if validated_count > 0:
            st.info(f"Vous avez déjà validé {validated_count} atout(s)")
        
        st.markdown("---")
        
        # Afficher les atouts avec des champs éditables - 2 par ligne
        for i in range(0, len(proposed_atouts), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier atout de la ligne
            with col1:
                atout = proposed_atouts[i]
                original_titre = atout.get('titre', 'Titre non défini')
                original_description = atout.get('description', 'Description non définie')
                atout_id = atout.get('id', i + 1)
                
                # Initialiser les valeurs dans session_state APRÈS le nettoyage
                # Réinitialiser toujours avec la valeur originale pour forcer la mise à jour
                titre_key = f"atout_titre_{i}_{key_suffix}"
                description_key = f"atout_description_{i}_{key_suffix}"
                st.session_state[titre_key] = original_titre
                st.session_state[description_key] = original_description
                
                # Afficher l'ID de l'atout
                st.markdown(f"**Atout #{atout_id}**")
                
                # Champ éditable pour le titre
                modified_titre = st.text_input(
                    "**Titre**",
                    key=titre_key,
                    label_visibility="visible"
                )
                
                # Champ éditable pour la description (text_area pour texte multiligne)
                modified_description = st.text_area(
                    "**Description**",
                    key=description_key,
                    height=150,
                    label_visibility="visible"
                )
                
                # Checkbox pour sélectionner cet atout avec une clé unique
                checkbox_key = f"validate_atout_{i+1}_{key_suffix}"
                # Initialiser à False si la clé n'existe pas encore (première fois)
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                # Créer la checkbox (la valeur sera lue depuis session_state)
                is_selected = st.checkbox(f"Valider cet atout", key=checkbox_key, on_change=self._on_checkbox_change)
            
            # Deuxième atout de la ligne (si existant)
            if i + 1 < len(proposed_atouts):
                with col2:
                    atout = proposed_atouts[i + 1]
                    original_titre = atout.get('titre', 'Titre non défini')
                    original_description = atout.get('description', 'Description non définie')
                    atout_id = atout.get('id', i + 2)
                    
                    # Initialiser les valeurs dans session_state APRÈS le nettoyage
                    # Réinitialiser toujours avec la valeur originale pour forcer la mise à jour
                    titre_key = f"atout_titre_{i+1}_{key_suffix}"
                    description_key = f"atout_description_{i+1}_{key_suffix}"
                    st.session_state[titre_key] = original_titre
                    st.session_state[description_key] = original_description
                    
                    # Afficher l'ID de l'atout
                    st.markdown(f"**Atout #{atout_id}**")
                    
                    # Champ éditable pour le titre
                    modified_titre = st.text_input(
                        "**Titre**",
                        key=titre_key,
                        label_visibility="visible"
                    )
                    
                    # Champ éditable pour la description (text_area pour texte multiligne)
                    modified_description = st.text_area(
                        "**Description**",
                        key=description_key,
                        height=150,
                        label_visibility="visible"
                    )
                    
                    # Checkbox pour sélectionner cet atout avec une clé unique
                    checkbox_key = f"validate_atout_{i+2}_{key_suffix}"
                    # Initialiser à False si la clé n'existe pas encore (première fois)
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = False
                    # Créer la checkbox (la valeur sera lue depuis session_state)
                    is_selected = st.checkbox(f"Valider cet atout", key=checkbox_key, on_change=self._on_checkbox_change)
            
            # Ligne de séparation fine entre les atouts
            st.markdown("---")
        
        # Calculer le nombre de sélections en temps réel
        selected_count = 0
        selected_atouts_list = []
        
        for i in range(1, len(proposed_atouts) + 1):
            checkbox_key = f"validate_atout_{i}_{key_suffix}"
            is_selected = st.session_state.get(checkbox_key, False)
            if is_selected:
                selected_count += 1
                selected_atouts_list.append(i)
        
        # Afficher le nombre d'atouts sélectionnés
        if selected_count > 0:
            st.info(f"{selected_count} atout(s) sélectionné(s)")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            placeholder="Ex: Les atouts sélectionnés sont les plus pertinents pour notre stratégie IA...",
            height=100
        )
        
        # Boutons de validation
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Valider et proposer de nouveaux atouts", type="primary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un atout")
                else:
                    # Lire l'état des checkboxes directement
                    selected_atouts = []
                    for i in range(1, len(proposed_atouts) + 1):
                        checkbox_key = f"validate_atout_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_atouts.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_validation(proposed_atouts, selected_atouts, comments, validated_count, key_suffix)
                    result["atouts_user_action"] = "continue_atouts"
                    return result
        
        with col2:
            if st.button("✅ Valider et finaliser", type="secondary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un atout")
                else:
                    # Lire l'état des checkboxes directement
                    selected_atouts = []
                    for i in range(1, len(proposed_atouts) + 1):
                        checkbox_key = f"validate_atout_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_atouts.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_validation(proposed_atouts, selected_atouts, comments, validated_count, key_suffix)
                    result["atouts_user_action"] = "finalize_atouts"
                    return result
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_validation(self, proposed_atouts: List[Dict[str, Any]], selected_numbers: List[int], comments: str, validated_count: int, key_suffix: str = None) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur.
        
        Args:
            proposed_atouts: Liste des atouts proposés
            selected_numbers: Numéros des atouts sélectionnés
            comments: Commentaires de l'utilisateur
            validated_count: Nombre d'atouts déjà validés
            key_suffix: Suffixe pour les clés session_state
            
        Returns:
            Résultat de la validation
        """
        print(f"\n✅ [DEBUG] _process_validation - DÉBUT")
        print(f"📊 [DEBUG] selected_numbers: {selected_numbers}")
        print(f"📊 [DEBUG] validated_count: {validated_count}")
        print(f"📊 [DEBUG] comments: {comments[:50] if comments else 'Aucun'}")
        
        # Vérifier qu'au moins un atout est sélectionné
        if len(selected_numbers) == 0:
            print(f"❌ [DEBUG] Aucun atout sélectionné")
            st.error("Vous devez sélectionner au moins un atout à valider")
            return None
        
        # Extraire les atouts validés avec les modifications de l'utilisateur
        validated_new = []
        for selected_num in selected_numbers:
            idx = selected_num - 1  # Convertir en index 0-based
            original_atout = proposed_atouts[idx]
            
            # Lire les valeurs modifiées depuis session_state
            titre_key = f"atout_titre_{idx}_{key_suffix}"
            description_key = f"atout_description_{idx}_{key_suffix}"
            modified_titre = st.session_state.get(titre_key, original_atout.get('titre', ''))
            modified_description = st.session_state.get(description_key, original_atout.get('description', ''))
            
            # Créer l'atout modifié
            modified_atout = {
                'id': original_atout.get('id', selected_num),
                'titre': modified_titre.strip() if modified_titre.strip() else original_atout.get('titre', ''),
                'description': modified_description.strip() if modified_description.strip() else original_atout.get('description', '')
            }
            
            validated_new.append(modified_atout)
        
        # Pour les rejetés, on garde les originaux (pas besoin de modifications)
        rejected_numbers = [i for i in range(1, len(proposed_atouts) + 1) if i not in selected_numbers]
        rejected_new = [proposed_atouts[i-1] for i in rejected_numbers]
        
        print(f"📊 [DEBUG] validated_new: {len(validated_new)} atouts")
        print(f"📊 [DEBUG] rejected_new: {len(rejected_new)} atouts")
        
        # Calculer le total
        total_validated = validated_count + len(validated_new)
        
        print(f"📊 [DEBUG] total_validated: {total_validated}")
        
        result = {
            "validated_atouts": validated_new,  # Seulement les nouveaux atouts validés
            "rejected_atouts": rejected_new,
            "user_feedback": comments,
            "total_validated": total_validated,
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
        
        print(f"💾 [DEBUG] Préparation du résultat")
        print(f"✅ [DEBUG] Résultat préparé - total_validated={result['total_validated']}")
        
        # Nettoyer l'état des sélections et les clés de validation + modification
        print(f"🧹 [DEBUG] Nettoyage des clés de validation et modification")
        for key in list(st.session_state.keys()):
            if (key.startswith("validate_atout_") or 
                key.startswith("atout_titre_") or 
                key.startswith("atout_description_") or 
                key.startswith("atouts_initialized_")):
                del st.session_state[key]
        print(f"✅ [DEBUG] Nettoyage terminé")
        
        print(f"🎉 [DEBUG] Validation - {total_validated} atouts validés au total")
        
        print(f"✅ [DEBUG] _process_validation - Retour du résultat")
        return result
    
    def save_workflow_state(self, state: Dict[str, Any]) -> None:
        """
        Sauvegarde l'état du workflow.
        
        Args:
            state: État du workflow à sauvegarder
        """
        try:
            # Sauvegarder dans session_state pour Streamlit
            st.session_state.atouts_workflow_state = state
            st.success("État sauvegardé")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde : {str(e)}")
    
    def load_workflow_state(self) -> Dict[str, Any]:
        """
        Charge l'état du workflow depuis session_state.
        
        Returns:
            État du workflow ou dictionnaire vide
        """
        return st.session_state.get("atouts_workflow_state", {})
    
    def clear_workflow_state(self) -> None:
        """
        Supprime l'état du workflow de session_state.
        """
        if "atouts_workflow_state" in st.session_state:
            del st.session_state.atouts_workflow_state
            st.success("État supprimé")

