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
    
    def _on_checkbox_change(self):
        """Callback pour les changements de checkbox - force un rerun"""
        # Forcer un rerun explicite pour mettre à jour les boutons
        st.rerun()
    
    def display_use_cases_for_validation(
        self,
        use_cases: List[Dict[str, Any]],
        validated_count: int = 0,
        key_suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche les cas d'usage pour validation dans Streamlit.
        Liste unifiée sans distinction de catégorie.
        
        Args:
            use_cases: Liste des cas d'usage proposés
            validated_count: Nombre de cas d'usage déjà validés
            key_suffix: Suffixe personnalisé pour les clés de checkbox. Si None, utilise len(use_cases)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(use_cases))
        logger.info(f"Affichage de {len(use_cases)} cas d'usage")
        
        # IMPORTANT: Ne nettoyer que lors de l'affichage initial, pas lors des reruns causés par les callbacks
        # Utiliser un flag pour savoir si cette liste de use cases a déjà été initialisée
        initialization_flag = f"use_cases_initialized_{key_suffix}"
        
        # Si c'est la première fois qu'on affiche cette liste de use cases avec ce key_suffix
        if initialization_flag not in st.session_state:
            # Nettoyer TOUTES les anciennes clés de validation pour réinitialiser les checkboxes
            # Cela garantit que les checkboxes sont toujours réinitialisées quand de nouveaux use cases sont affichés
            for key in list(st.session_state.keys()):
                if (key.startswith("validate_uc_") or 
                    key.startswith("uc_titre_") or key.startswith("uc_desc_") or key.startswith("uc_famille_")):
                    del st.session_state[key]
            # Marquer comme initialisé
            st.session_state[initialization_flag] = True
        
        # (Spinner retiré - géré par app_api.py pour un flux continu)
        
        st.title("Validation des Cas d'Usage")
        
        # Afficher le statut de validation
        if validated_count > 0:
            st.info(f"Vous avez déjà validé {validated_count} cas d'usage")
        
        st.markdown("---")
        
        # Section Cas d'usage
        st.header("Cas d'Usage")
        
        # Afficher les cas d'usage avec champs éditables - 2 par ligne
        for i in range(0, len(use_cases), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier cas d'usage de la ligne
            with col1:
                use_case = use_cases[i]
                original_titre = use_case.get('titre', 'Titre non défini')
                original_description = use_case.get('description', 'Description non disponible')
                # Convertir None en '' pour toujours avoir une string
                original_famille = use_case.get('famille') or ''
                
                # Initialiser les valeurs dans session_state APRÈS le nettoyage
                # Ne réinitialiser que si la clé n'existe pas encore pour préserver les modifications
                titre_key = f"uc_titre_{i}_{key_suffix}"
                desc_key = f"uc_desc_{i}_{key_suffix}"
                famille_key = f"uc_famille_{i}_{key_suffix}"
                if titre_key not in st.session_state:
                    st.session_state[titre_key] = original_titre
                if desc_key not in st.session_state:
                    st.session_state[desc_key] = original_description
                if famille_key not in st.session_state:
                    st.session_state[famille_key] = original_famille  # Toujours initialiser (sera '' si None)
                
                # TOUJOURS afficher le champ famille (même s'il est vide)
                st.markdown("**Famille :**")
                modified_famille = st.text_input(
                    "Famille",
                    key=famille_key,
                    label_visibility="hidden"
                )
                
                # Champ éditable pour le titre (ne pas passer value pour éviter le warning)
                modified_titre = st.text_input(
                    "**Titre**",
                    key=titre_key,
                    label_visibility="visible"
                )
                
                # Champ éditable pour la description
                st.markdown("**Description :**")
                modified_description = st.text_area(
                    "Description",
                    key=desc_key,
                    height=120,
                    label_visibility="hidden"
                )
                
                # Checkbox pour sélectionner ce cas d'usage avec une clé unique
                checkbox_key = f"validate_uc_{i+1}_{key_suffix}"
                # Initialiser à False si la clé n'existe pas encore (première fois)
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                # Créer la checkbox (la valeur sera lue depuis session_state)
                is_selected = st.checkbox(f"Valider ce cas d'usage", key=checkbox_key, on_change=self._on_checkbox_change)
            
            # Deuxième cas d'usage de la ligne (si existant)
            if i + 1 < len(use_cases):
                with col2:
                    use_case = use_cases[i + 1]
                    original_titre = use_case.get('titre', 'Titre non défini')
                    original_description = use_case.get('description', 'Description non disponible')
                    # Convertir None en '' pour toujours avoir une string
                    original_famille = use_case.get('famille') or ''
                    
                    # Initialiser les valeurs dans session_state APRÈS le nettoyage
                    # Ne réinitialiser que si la clé n'existe pas encore pour préserver les modifications
                    titre_key = f"uc_titre_{i+1}_{key_suffix}"
                    desc_key = f"uc_desc_{i+1}_{key_suffix}"
                    famille_key = f"uc_famille_{i+1}_{key_suffix}"
                    if titre_key not in st.session_state:
                        st.session_state[titre_key] = original_titre
                    if desc_key not in st.session_state:
                        st.session_state[desc_key] = original_description
                    if famille_key not in st.session_state:
                        st.session_state[famille_key] = original_famille  # Toujours initialiser (sera '' si None)
                    
                    # TOUJOURS afficher le champ famille (même s'il est vide)
                    st.markdown("**Famille :**")
                    modified_famille = st.text_input(
                        "Famille",
                        key=famille_key,
                        label_visibility="hidden"
                    )
                    
                    # Champ éditable pour le titre (ne pas passer value pour éviter le warning)
                    modified_titre = st.text_input(
                        "**Titre**",
                        key=titre_key,
                        label_visibility="visible"
                    )
                    
                    # Champ éditable pour la description
                    st.markdown("**Description :**")
                    modified_description = st.text_area(
                        "Description",
                        key=desc_key,
                        height=120,
                        label_visibility="hidden"
                    )
                    
                    # Checkbox pour sélectionner ce cas d'usage avec une clé unique
                    checkbox_key = f"validate_uc_{i+2}_{key_suffix}"
                    # Initialiser à False si la clé n'existe pas encore (première fois)
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = False
                    # Créer la checkbox (la valeur sera lue depuis session_state)
                    is_selected = st.checkbox(f"Valider ce cas d'usage", key=checkbox_key, on_change=self._on_checkbox_change)
            
            # Ligne de séparation fine entre les cas d'usage
            st.markdown("---")
        
        # Afficher le nombre de sélections
        st.markdown("---")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            placeholder="Ex: Les cas d'usage sélectionnés sont les plus pertinents pour notre contexte...",
            height=100
        )
        
        # Boutons de validation
        st.markdown("---")
        
        # IMPORTANT: Recalculer selected_count juste avant d'afficher les boutons
        # pour s'assurer que la valeur est à jour après le rerun
        selected_count = 0
        for i in range(1, len(use_cases) + 1):
            checkbox_key = f"validate_uc_{i}_{key_suffix}"
            is_selected = st.session_state.get(checkbox_key, False)
            if is_selected:
                selected_count += 1
        
        # Afficher le nombre de sélections
        if selected_count > 0:
            st.info(f"{selected_count} cas d'usage sélectionné(s)")
        
        col1, col2 = st.columns(2)
        
        # Utiliser une clé dynamique basée sur selected_count pour forcer la mise à jour des boutons
        button_key_suffix = f"_{selected_count}_{key_suffix}"
        
        with col1:
            if st.button("✅ Valider et régénérer des use cases", type="primary", disabled=selected_count == 0, use_container_width=True, key=f"validate_continue{button_key_suffix}"):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un cas d'usage")
                else:
                    # Lire l'état des checkboxes directement
                    selected_indices = []
                    for i in range(1, len(use_cases) + 1):
                        checkbox_key = f"validate_uc_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_indices.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_validation(
                        use_cases,
                        selected_indices,
                        comments,
                        validated_count,
                        key_suffix
                    )
                    result["use_case_user_action"] = "continue_use_cases"
                    return result  # Retourner le résultat pour que app_api.py puisse l'envoyer à l'API
        
        with col2:
            if st.button("✅ Valider et finaliser", type="secondary", disabled=selected_count == 0, use_container_width=True, key=f"validate_finalize{button_key_suffix}"):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un cas d'usage")
                else:
                    # Lire l'état des checkboxes directement
                    selected_indices = []
                    for i in range(1, len(use_cases) + 1):
                        checkbox_key = f"validate_uc_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_indices.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_validation(
                        use_cases,
                        selected_indices,
                        comments,
                        validated_count,
                        key_suffix
                    )
                    result["use_case_user_action"] = "finalize_use_cases"
                    return result  # Retourner le résultat pour que app_api.py puisse l'envoyer à l'API
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_validation(
        self,
        use_cases: List[Dict[str, Any]],
        selected_indices: List[int],
        comments: str,
        validated_count: int,
        key_suffix: str = None
    ) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur.
        
        Args:
            use_cases: Liste des cas d'usage proposés
            selected_indices: Indices des cas d'usage sélectionnés
            comments: Commentaires de l'utilisateur
            validated_count: Nombre de cas d'usage déjà validés
            key_suffix: Suffixe pour les clés
            
        Returns:
            Résultat de la validation
        """
        logger.info(f"Traitement de la validation : {len(selected_indices)} cas d'usage")
        print(f"\n✅ [DEBUG UC] _process_validation - DÉBUT")
        print(f"📊 [DEBUG UC] selected_indices: {selected_indices}")
        print(f"📊 [DEBUG UC] validated_count: {validated_count}")
        
        # Extraire les cas d'usage validés avec les modifications de l'utilisateur
        validated_uc = []
        for selected_idx in selected_indices:
            idx = selected_idx - 1  # Convertir en index 0-based
            original_uc = use_cases[idx]
            
            # Lire les valeurs modifiées depuis session_state
            titre_key = f"uc_titre_{idx}_{key_suffix}"
            desc_key = f"uc_desc_{idx}_{key_suffix}"
            famille_key = f"uc_famille_{idx}_{key_suffix}"
            modified_titre = st.session_state.get(titre_key, original_uc.get('titre', ''))
            modified_description = st.session_state.get(desc_key, original_uc.get('description', ''))
            # Convertir None en '' pour toujours avoir une string
            modified_famille = st.session_state.get(famille_key, original_uc.get('famille') or '')
            
            # Créer le use case modifié (conserver l'id, ia_utilisee et famille modifiée)
            # Si la famille modifiée est vide, utiliser None pour le champ famille
            famille_value = modified_famille.strip() if modified_famille and modified_famille.strip() else None
            modified_uc = {
                'id': original_uc.get('id', ''),
                'titre': modified_titre.strip() if modified_titre.strip() else original_uc.get('titre', ''),
                'description': modified_description.strip() if modified_description.strip() else original_uc.get('description', ''),
                'ia_utilisee': original_uc.get('ia_utilisee', ''),  # Conserver l'original
                'famille': famille_value  # Utiliser la famille modifiée ou None si vide
            }
            validated_uc.append(modified_uc)
        
        # Pour les rejetés, on garde les originaux
        rejected_indices = [i for i in range(1, len(use_cases) + 1) if i not in selected_indices]
        rejected_uc = [use_cases[i-1] for i in rejected_indices]
        
        # Calculer le total
        total_validated = validated_count + len(validated_uc)
        
        logger.info(f"Validation : {total_validated} cas d'usage validés au total")
        
        result = {
            "validated_use_cases": validated_uc,
            "rejected_use_cases": rejected_uc,
            "user_feedback": comments,
            "total_validated": total_validated,
            "newly_validated": validated_uc,
            "newly_rejected": rejected_uc
        }
        
        print(f"💾 [DEBUG UC] Préparation du résultat")
        print(f"✅ [DEBUG UC] Résultat préparé - total_validated={result['total_validated']}")
        
        # Nettoyer l'état des sélections et les clés de validation + modification
        print(f"🧹 [DEBUG UC] Nettoyage des clés de validation et modification")
        st.session_state.selected_use_cases = set()
        for key in list(st.session_state.keys()):
            if (key.startswith("validate_uc_") or 
                key.startswith("uc_titre_") or 
                key.startswith("uc_desc_") or 
                key.startswith("uc_famille_") or 
                key.startswith("use_cases_initialized_")):
                del st.session_state[key]
        print(f"✅ [DEBUG UC] Nettoyage terminé")
        
        print(f"🎉 [DEBUG UC] Validation - {total_validated} cas d'usage validés au total")
        
        print(f"✅ [DEBUG UC] _process_validation - Retour du résultat")
        return result
    
    def validate_use_cases(
        self,
        use_cases: List[Dict[str, Any]],
        validated_use_cases: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processus de validation humaine dans Streamlit.
        
        Args:
            use_cases: Cas d'usage proposés à valider
            validated_use_cases: Cas d'usage déjà validés (optionnel)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        validated_use_cases = validated_use_cases or []
        
        validated_count = len(validated_use_cases)
        
        # Afficher l'interface de validation
        return self.display_use_cases_for_validation(
            use_cases,
            validated_count
        )

