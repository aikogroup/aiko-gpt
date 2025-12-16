"""
Interface Streamlit pour la validation des enjeux et recommandations (Executive Summary)
"""

import streamlit as st
import json
from typing import List, Dict, Any, Optional


class StreamlitExecutiveValidation:
    """Interface de validation Streamlit pour Executive Summary"""
    
    def display_challenges_for_validation(
        self,
        identified_challenges: List[Dict[str, Any]],
        validated_challenges: List[Dict[str, Any]] = None,
        key_suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche l'interface de validation des enjeux stratégiques.
        VERSION REFACTORISÉE: Suit le même pattern que display_needs_for_validation.
        
        Args:
            identified_challenges: Liste des 5 enjeux identifiés
            validated_challenges: Liste des enjeux déjà validés (optionnel)
            key_suffix: Suffixe personnalisé pour les clés (ex: iteration_count)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        validated_challenges = validated_challenges or []
        validated_count = len(validated_challenges)
        
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(identified_challenges))
        
        # NE PLUS nettoyer les clés de session_state automatiquement
        # Cela empêchait les checkboxes de conserver leur état
        # Le nettoyage se fait uniquement après validation dans _process_challenges_validation
        
        st.subheader("Validation des Enjeux Stratégiques")
        
        if validated_count > 0:
            st.info(f"Vous avez déjà validé {validated_count} enjeu(x)")
        
        st.markdown("---")
        
        # Afficher les enjeux avec des champs éditables - 2 par ligne
        for i in range(0, len(identified_challenges), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier enjeu de la ligne
            with col1:
                challenge = identified_challenges[i]
                ch_id = challenge.get("id", "")
                original_titre = challenge.get("titre", "Titre non défini")
                original_description = challenge.get("description", "")
                
                # Initialiser les valeurs dans session_state si nécessaire
                titre_key = f"challenge_titre_{i}_{key_suffix}"
                desc_key = f"challenge_desc_{i}_{key_suffix}"
                
                if titre_key not in st.session_state:
                    st.session_state[titre_key] = original_titre
                if desc_key not in st.session_state:
                    st.session_state[desc_key] = original_description
                
                # Champ éditable pour le titre (sans afficher l'ID)
                modified_titre = st.text_input(
                    f"**Enjeu {i+1}**",
                    key=titre_key,
                    label_visibility="visible"
                )
                
                # Champ éditable pour la description
                modified_description = st.text_area(
                    "**Description**",
                    key=desc_key,
                    label_visibility="visible",
                    height=100
                )
                
                # Checkbox pour sélectionner cet enjeu
                checkbox_key = f"validate_challenge_{i+1}_{key_suffix}"
                is_selected = st.checkbox(f"Valider cet enjeu", key=checkbox_key)
            
            # Deuxième enjeu de la ligne (si existant)
            if i + 1 < len(identified_challenges):
                with col2:
                    challenge = identified_challenges[i + 1]
                    ch_id = challenge.get("id", "")
                    original_titre = challenge.get("titre", "Titre non défini")
                    original_description = challenge.get("description", "")
                    
                    # Initialiser les valeurs dans session_state si nécessaire
                    titre_key = f"challenge_titre_{i+1}_{key_suffix}"
                    desc_key = f"challenge_desc_{i+1}_{key_suffix}"
                    
                    if titre_key not in st.session_state:
                        st.session_state[titre_key] = original_titre
                    if desc_key not in st.session_state:
                        st.session_state[desc_key] = original_description
                    
                    # Champ éditable pour le titre (sans afficher l'ID)
                    modified_titre = st.text_input(
                        f"**Enjeu {i+2}**",
                        key=titre_key,
                        label_visibility="visible"
                    )
                    
                    # Champ éditable pour la description
                    modified_description = st.text_area(
                        "**Description**",
                        key=desc_key,
                        label_visibility="visible",
                        height=100
                    )
                    
                    # Checkbox pour sélectionner cet enjeu
                    checkbox_key = f"validate_challenge_{i+2}_{key_suffix}"
                    is_selected = st.checkbox(f"Valider cet enjeu", key=checkbox_key)
            
            # Ligne de séparation fine entre les enjeux
            st.markdown("---")
        
        # Calculer le nombre de sélections en temps réel
        selected_count = 0
        selected_challenges_list = []
        
        for i in range(1, len(identified_challenges) + 1):
            checkbox_key = f"validate_challenge_{i}_{key_suffix}"
            is_selected = st.session_state.get(checkbox_key, False)
            if is_selected:
                selected_count += 1
                selected_challenges_list.append(i)
        
        # Afficher le nombre d'enjeux sélectionnés
        if selected_count > 0:
            st.info(f"{selected_count} enjeu(x) sélectionné(s)")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments_key = f"challenges_comments_{key_suffix}"
        if comments_key not in st.session_state:
            st.session_state[comments_key] = ""
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            key=comments_key,
            placeholder="Ex: Les enjeux sélectionnés sont les plus prioritaires pour notre entreprise...",
            height=100
        )
        
        # Boutons de validation
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Valider et proposer de nouveaux enjeux", type="primary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un enjeu")
                else:
                    # Lire l'état des checkboxes directement
                    selected_challenges = []
                    for i in range(1, len(identified_challenges) + 1):
                        checkbox_key = f"validate_challenge_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_challenges.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_challenges_validation(
                        identified_challenges, 
                        selected_challenges, 
                        comments, 
                        validated_count, 
                        key_suffix
                    )
                    result["challenges_user_action"] = "continue_challenges"
                    return result
        
        with col2:
            if st.button("✅ Valider et passer aux recommandations", type="secondary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins un enjeu")
                else:
                    # Lire l'état des checkboxes directement
                    selected_challenges = []
                    for i in range(1, len(identified_challenges) + 1):
                        checkbox_key = f"validate_challenge_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_challenges.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_challenges_validation(
                        identified_challenges, 
                        selected_challenges, 
                        comments, 
                        validated_count, 
                        key_suffix
                    )
                    result["challenges_user_action"] = "continue_to_maturity"
                    return result
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_challenges_validation(
        self, 
        identified_challenges: List[Dict[str, Any]], 
        selected_numbers: List[int], 
        comments: str, 
        validated_count: int, 
        key_suffix: str = None
    ) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur pour les enjeux.
        
        Args:
            identified_challenges: Liste des enjeux identifiés
            selected_numbers: Numéros des enjeux sélectionnés
            comments: Commentaires de l'utilisateur
            validated_count: Nombre d'enjeux déjà validés
            key_suffix: Suffixe pour les clés
            
        Returns:
            Résultat de la validation
        """
        # Vérifier qu'au moins un enjeu est sélectionné
        if len(selected_numbers) == 0:
            st.error("Vous devez sélectionner au moins un enjeu à valider")
            return None
        
        # Extraire les enjeux validés avec les modifications de l'utilisateur
        validated_new = []
        for selected_num in selected_numbers:
            idx = selected_num - 1  # Convertir en index 0-based
            original_challenge = identified_challenges[idx]
            
            # Lire les valeurs modifiées depuis session_state
            titre_key = f"challenge_titre_{idx}_{key_suffix}"
            desc_key = f"challenge_desc_{idx}_{key_suffix}"
            modified_titre = st.session_state.get(titre_key, original_challenge.get("titre", ""))
            modified_description = st.session_state.get(desc_key, original_challenge.get("description", ""))
            
            # Créer l'enjeu modifié
            modified_challenge = {
                "id": original_challenge.get("id", ""),
                "titre": modified_titre.strip() if modified_titre.strip() else original_challenge.get("titre", ""),
                "description": modified_description.strip() if modified_description.strip() else original_challenge.get("description", ""),
                "besoins_lies": original_challenge.get("besoins_lies", [])  # Garder les besoins liés originaux
            }
            
            validated_new.append(modified_challenge)
        
        # Pour les rejetés, on garde les originaux
        rejected_numbers = [i for i in range(1, len(identified_challenges) + 1) if i not in selected_numbers]
        rejected_new = [identified_challenges[i-1] for i in rejected_numbers]
        
        # Calculer le total
        total_validated = validated_count + len(validated_new)
        
        result = {
            "validated_challenges": validated_new,  # Seulement les nouveaux enjeux validés
            "rejected_challenges": rejected_new,
            "challenges_feedback": comments,
            "total_validated": total_validated,
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
        
        # Nettoyer l'état des sélections et les clés de validation + modification
        for key in list(st.session_state.keys()):
            if key.startswith("validate_challenge_") or key.startswith("challenge_titre_") or key.startswith("challenge_desc_") or key.startswith("challenges_comments_"):
                if key_suffix in key:
                    del st.session_state[key]
        
        return result
    
    def display_recommendations_for_validation(
        self,
        recommendations: List[Dict[str, Any]],
        validated_recommendations: List[Dict[str, Any]] = None,
        key_suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche l'interface de validation des recommandations.
        VERSION REFACTORISÉE: Suit le même pattern que display_challenges_for_validation avec checkboxes.
        
        Args:
            recommendations: Liste des recommandations générées (format dict avec id, titre, description)
            validated_recommendations: Liste des recommandations déjà validées (optionnel, format dict)
            key_suffix: Suffixe personnalisé pour les clés (ex: iteration_count)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        validated_recommendations = validated_recommendations or []
        validated_count = len(validated_recommendations)
        
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(recommendations))
        
        # NE PLUS nettoyer les clés de session_state automatiquement
        # Cela empêchait les checkboxes de conserver leur état
        # Le nettoyage se fait uniquement après validation dans _process_recommendations_validation
        
        st.subheader("Validation des Recommandations")
        
        if validated_count > 0:
            st.info(f"Vous avez déjà validé {validated_count} recommandation(s)")
        
        st.markdown("---")
        
        # Afficher les recommandations avec des champs éditables - 2 par ligne
        for i in range(0, len(recommendations), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Première recommandation de la ligne
            with col1:
                recommendation = recommendations[i]
                
                # Gérer les deux formats : dict (nouveau) ou string (ancien)
                if isinstance(recommendation, dict):
                    original_titre = recommendation.get("titre", "")
                    original_description = recommendation.get("description", "")
                else:
                    # Ancien format string - convertir
                    original_titre = str(recommendation)
                    original_description = ""
                
                # Initialiser les valeurs dans session_state si nécessaire
                titre_key = f"recommendation_titre_{i}_{key_suffix}"
                desc_key = f"recommendation_desc_{i}_{key_suffix}"
                
                if titre_key not in st.session_state:
                    st.session_state[titre_key] = original_titre
                if desc_key not in st.session_state:
                    st.session_state[desc_key] = original_description
                
                # Champ éditable pour le titre
                modified_titre = st.text_input(
                    f"**Recommandation {i+1} - Titre**",
                    key=titre_key,
                    label_visibility="visible"
                )
                
                # Champ éditable pour la description
                modified_description = st.text_area(
                    "**Description**",
                    key=desc_key,
                    label_visibility="visible",
                    height=80
                )
                
                # Checkbox pour sélectionner cette recommandation
                checkbox_key = f"validate_recommendation_{i+1}_{key_suffix}"
                # Initialiser la checkbox à False si elle n'existe pas
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                is_selected = st.checkbox(f"Valider cette recommandation", key=checkbox_key)
            
            # Deuxième recommandation de la ligne (si existante)
            if i + 1 < len(recommendations):
                with col2:
                    recommendation = recommendations[i + 1]
                    
                    # Gérer les deux formats : dict (nouveau) ou string (ancien)
                    if isinstance(recommendation, dict):
                        original_titre = recommendation.get("titre", "")
                        original_description = recommendation.get("description", "")
                    else:
                        # Ancien format string - convertir
                        original_titre = str(recommendation)
                        original_description = ""
                    
                    # Initialiser les valeurs dans session_state si nécessaire
                    titre_key = f"recommendation_titre_{i+1}_{key_suffix}"
                    desc_key = f"recommendation_desc_{i+1}_{key_suffix}"
                    
                    if titre_key not in st.session_state:
                        st.session_state[titre_key] = original_titre
                    if desc_key not in st.session_state:
                        st.session_state[desc_key] = original_description
                    
                    # Champ éditable pour le titre
                    modified_titre = st.text_input(
                        f"**Recommandation {i+2} - Titre**",
                        key=titre_key,
                        label_visibility="visible"
                    )
                    
                    # Champ éditable pour la description
                    modified_description = st.text_area(
                        "**Description**",
                        key=desc_key,
                        label_visibility="visible",
                        height=80
                    )
                    
                    # Checkbox pour sélectionner cette recommandation
                    checkbox_key = f"validate_recommendation_{i+2}_{key_suffix}"
                    # Initialiser la checkbox à False si elle n'existe pas
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = False
                    is_selected = st.checkbox(f"Valider cette recommandation", key=checkbox_key)
            
            # Ligne de séparation fine entre les recommandations
            st.markdown("---")
        
        # Calculer le nombre de sélections en temps réel
        selected_count = 0
        selected_recommendations_list = []
        
        for i in range(1, len(recommendations) + 1):
            checkbox_key = f"validate_recommendation_{i}_{key_suffix}"
            is_selected = st.session_state.get(checkbox_key, False)
            if is_selected:
                selected_count += 1
                selected_recommendations_list.append(i)
        
        # Afficher le nombre de recommandations sélectionnées
        if selected_count > 0:
            st.info(f"{selected_count} recommandation(s) sélectionnée(s)")
        
        # Zone de commentaires
        st.subheader("Commentaires (optionnel)")
        comments_key = f"recommendations_comments_{key_suffix}"
        if comments_key not in st.session_state:
            st.session_state[comments_key] = ""
        comments = st.text_area(
            "Ajoutez des commentaires sur votre sélection :",
            key=comments_key,
            placeholder="Ex: Les recommandations sélectionnées sont les plus pertinentes pour notre entreprise...",
            height=100
        )
        
        # Boutons de validation
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Valider et proposer de nouvelles recommandations", type="primary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins une recommandation")
                else:
                    # Lire l'état des checkboxes directement
                    selected_recommendations = []
                    for i in range(1, len(recommendations) + 1):
                        checkbox_key = f"validate_recommendation_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_recommendations.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_recommendations_validation(
                        recommendations, 
                        selected_recommendations, 
                        comments, 
                        validated_count, 
                        key_suffix
                    )
                    result["recommendations_user_action"] = "continue_recommendations"
                    return result
        
        with col2:
            if st.button("✅ Valider et finaliser le rapport", type="secondary", disabled=selected_count == 0, use_container_width=True):
                if selected_count == 0:
                    st.warning("Veuillez sélectionner au moins une recommandation")
                else:
                    # Lire l'état des checkboxes directement
                    selected_recommendations = []
                    for i in range(1, len(recommendations) + 1):
                        checkbox_key = f"validate_recommendation_{i}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            selected_recommendations.append(i)
                    
                    # Traiter la validation et retourner le résultat avec l'action
                    result = self._process_recommendations_validation(
                        recommendations, 
                        selected_recommendations, 
                        comments, 
                        validated_count, 
                        key_suffix
                    )
                    result["recommendations_user_action"] = "continue_to_finalize"
                    return result
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_recommendations_validation(
        self, 
        recommendations: List[Dict[str, Any]], 
        selected_numbers: List[int], 
        comments: str, 
        validated_count: int, 
        key_suffix: str = None
    ) -> Dict[str, Any]:
        """
        Traite la validation de l'utilisateur pour les recommandations.
        
        Args:
            recommendations: Liste des recommandations identifiées (format dict avec id, titre, description)
            selected_numbers: Numéros des recommandations sélectionnées
            comments: Commentaires de l'utilisateur
            validated_count: Nombre de recommandations déjà validées
            key_suffix: Suffixe pour les clés
            
        Returns:
            Résultat de la validation
        """
        # Vérifier qu'au moins une recommandation est sélectionnée
        if len(selected_numbers) == 0:
            st.error("Vous devez sélectionner au moins une recommandation à valider")
            return None
        
        # Extraire les recommandations validées avec les modifications de l'utilisateur
        validated_new = []
        for selected_num in selected_numbers:
            idx = selected_num - 1  # Convertir en index 0-based
            original_recommendation = recommendations[idx]
            
            # Lire les valeurs modifiées depuis session_state
            titre_key = f"recommendation_titre_{idx}_{key_suffix}"
            desc_key = f"recommendation_desc_{idx}_{key_suffix}"
            
            # Gérer les deux formats : dict (nouveau) ou string (ancien)
            if isinstance(original_recommendation, dict):
                original_id = original_recommendation.get("id", "")
                original_titre = original_recommendation.get("titre", "")
                original_description = original_recommendation.get("description", "")
            else:
                # Ancien format string - convertir
                original_id = ""
                original_titre = str(original_recommendation)
                original_description = ""
            
            modified_titre = st.session_state.get(titre_key, original_titre)
            modified_description = st.session_state.get(desc_key, original_description)
            
            # Créer la recommandation modifiée
            validated_new.append({
                "id": original_id,
                "titre": modified_titre.strip() if modified_titre.strip() else original_titre,
                "description": modified_description.strip() if modified_description.strip() else original_description
            })
        
        # Pour les rejetées, on garde les originaux (convertir en dict si nécessaire)
        rejected_numbers = [i for i in range(1, len(recommendations) + 1) if i not in selected_numbers]
        rejected_new = []
        for i in rejected_numbers:
            idx = i - 1
            original_rec = recommendations[idx]
            if isinstance(original_rec, dict):
                rejected_new.append(original_rec)
            else:
                # Ancien format string - convertir en dict
                rejected_new.append({
                    "id": "",
                    "titre": str(original_rec),
                    "description": ""
                })
        
        # Calculer le total
        total_validated = validated_count + len(validated_new)
        
        result = {
            "validated_recommendations": validated_new,  # Seulement les nouvelles recommandations validées
            "rejected_recommendations": rejected_new,
            "recommendations_feedback": comments,
            "total_validated": total_validated,
            "newly_validated": validated_new,
            "newly_rejected": rejected_new
        }
        
        # Nettoyer l'état des sélections et les clés de validation + modification
        for key in list(st.session_state.keys()):
            if key.startswith("validate_recommendation_") or key.startswith("recommendation_titre_") or key.startswith("recommendation_desc_") or key.startswith("recommendations_comments_"):
                if key_suffix in key:
                    del st.session_state[key]
        
        return result
    
    def display_word_extraction_for_validation(
        self,
        extracted_data: Dict[str, List[Dict[str, Any]]],
        key_suffix: str = "word_extraction"
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche l'interface de validation de l'extraction du Word.
        
        Args:
            extracted_data: Dict avec 'final_needs' et 'final_use_cases'
            key_suffix: Suffixe pour les clés Streamlit
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        final_needs = extracted_data.get("final_needs", [])
        final_use_cases = extracted_data.get("final_use_cases", [])
        
        st.subheader("📋 Validation de l'Extraction du Rapport Word")
        st.info("💡 Vérifiez et modifiez si nécessaire les besoins et cas d'usage extraits du rapport Word.")
        
        st.markdown("---")
        
        # ========== SECTION BESOINS ==========
        st.markdown("### 🔹 Besoins Identifiés")
        
        if not final_needs:
            st.warning("⚠️ Aucun besoin identifié dans le rapport Word.")
        else:
            # Afficher les besoins avec possibilité de modification
            for i, need in enumerate(final_needs):
                with st.expander(f"**Besoin {i+1}**", expanded=True):
                    # Initialiser les valeurs dans session_state
                    titre_key = f"need_titre_{i}_{key_suffix}"
                    
                    original_titre = need.get("titre", "")
                    
                    if titre_key not in st.session_state:
                        st.session_state[titre_key] = original_titre
                    
                    # Champ éditable pour le titre uniquement
                    modified_titre = st.text_input(
                        "**Titre du besoin**",
                        key=titre_key,
                        label_visibility="visible"
                    )
                    
        
        st.markdown("---")
        
        # ========== SECTION CAS D'USAGE PAR FAMILLE ==========
        st.markdown("### 🎯 Cas d'Usage par Famille")
        
        if not final_use_cases:
            st.warning("⚠️ Aucun cas d'usage identifié dans le rapport Word.")
        else:
            # Grouper les use cases par famille
            use_cases_by_family: Dict[str, List[Dict[str, Any]]] = {}
            use_cases_without_family: List[Dict[str, Any]] = []
            
            for uc in final_use_cases:
                famille = uc.get("famille")
                if famille:
                    if famille not in use_cases_by_family:
                        use_cases_by_family[famille] = []
                    use_cases_by_family[famille].append(uc)
                else:
                    use_cases_without_family.append(uc)
            
            # Afficher les familles avec leurs use cases
            for famille_name, use_cases in use_cases_by_family.items():
                with st.expander(f"**📁 Famille: {famille_name}** ({len(use_cases)} cas d'usage)", expanded=True):
                    # Champ éditable pour le nom de la famille
                    famille_key = f"famille_name_{famille_name}_{key_suffix}"
                    if famille_key not in st.session_state:
                        st.session_state[famille_key] = famille_name
                    
                    modified_famille_name = st.text_input(
                        "**Nom de la famille**",
                        key=famille_key,
                        label_visibility="visible"
                    )
                    
                    st.markdown("---")
                    
                    # Afficher les use cases de cette famille
                    for j, uc in enumerate(use_cases):
                        st.markdown(f"#### Cas d'usage {j+1}")
                        
                        # Initialiser les valeurs dans session_state
                        uc_titre_key = f"uc_titre_{famille_name}_{j}_{key_suffix}"
                        uc_desc_key = f"uc_desc_{famille_name}_{j}_{key_suffix}"
                        
                        original_uc_titre = uc.get("titre", "")
                        original_uc_desc = uc.get("description", "")
                        
                        if uc_titre_key not in st.session_state:
                            st.session_state[uc_titre_key] = original_uc_titre
                        if uc_desc_key not in st.session_state:
                            st.session_state[uc_desc_key] = original_uc_desc
                        
                        # Champ éditable pour le titre
                        modified_uc_titre = st.text_input(
                            "**Titre du cas d'usage**",
                            key=uc_titre_key,
                            label_visibility="visible"
                        )
                        
                        # Champ éditable pour la description
                        modified_uc_desc = st.text_area(
                            "**Description**",
                            key=uc_desc_key,
                            label_visibility="visible",
                            height=80
                        )
                        
                        if j < len(use_cases) - 1:
                            st.markdown("---")
            
            # Afficher les use cases sans famille
            if use_cases_without_family:
                with st.expander(f"**📁 Autres cas d'usage** (sans famille) ({len(use_cases_without_family)} cas d'usage)", expanded=True):
                    for j, uc in enumerate(use_cases_without_family):
                        st.markdown(f"#### Cas d'usage {j+1}")
                        
                        # Initialiser les valeurs dans session_state
                        uc_titre_key = f"uc_titre_no_family_{j}_{key_suffix}"
                        uc_desc_key = f"uc_desc_no_family_{j}_{key_suffix}"
                        uc_famille_key = f"uc_famille_no_family_{j}_{key_suffix}"
                        
                        original_uc_titre = uc.get("titre", "")
                        original_uc_desc = uc.get("description", "")
                        
                        if uc_titre_key not in st.session_state:
                            st.session_state[uc_titre_key] = original_uc_titre
                        if uc_desc_key not in st.session_state:
                            st.session_state[uc_desc_key] = original_uc_desc
                        if uc_famille_key not in st.session_state:
                            st.session_state[uc_famille_key] = ""
                        
                        # Champ éditable pour le titre
                        modified_uc_titre = st.text_input(
                            "**Titre du cas d'usage**",
                            key=uc_titre_key,
                            label_visibility="visible"
                        )
                        
                        # Champ éditable pour la description
                        modified_uc_desc = st.text_area(
                            "**Description**",
                            key=uc_desc_key,
                            label_visibility="visible",
                            height=80
                        )
                        
                        # Champ optionnel pour ajouter une famille
                        modified_uc_famille = st.text_input(
                            "**Famille** (optionnel)",
                            key=uc_famille_key,
                            label_visibility="visible",
                            placeholder="Ex: Automatisation, Analyse de données..."
                        )
                        
                        if j < len(use_cases_without_family) - 1:
                            st.markdown("---")
        
        st.markdown("---")
        
        # Bouton de validation
        if st.button("✅ Valider l'extraction et continuer", type="primary", use_container_width=True):
            # Construire les données validées
            validated_needs = []
            for i in range(len(final_needs)):
                titre_key = f"need_titre_{i}_{key_suffix}"
                
                validated_needs.append({
                    "titre": st.session_state.get(titre_key, final_needs[i].get("titre", "")),
                    "description": ""  # Les quotes ne sont plus affichées ni modifiables
                })
            
            validated_use_cases = []
            
            # Traiter les use cases par famille
            for famille_name, use_cases in use_cases_by_family.items():
                famille_key = f"famille_name_{famille_name}_{key_suffix}"
                modified_famille_name = st.session_state.get(famille_key, famille_name)
                
                for j, uc in enumerate(use_cases):
                    uc_titre_key = f"uc_titre_{famille_name}_{j}_{key_suffix}"
                    uc_desc_key = f"uc_desc_{famille_name}_{j}_{key_suffix}"
                    
                    validated_use_cases.append({
                        "titre": st.session_state.get(uc_titre_key, uc.get("titre", "")),
                        "description": st.session_state.get(uc_desc_key, uc.get("description", "")),
                        "famille": modified_famille_name if modified_famille_name else None
                    })
            
            # Traiter les use cases sans famille
            for j, uc in enumerate(use_cases_without_family):
                uc_titre_key = f"uc_titre_no_family_{j}_{key_suffix}"
                uc_desc_key = f"uc_desc_no_family_{j}_{key_suffix}"
                uc_famille_key = f"uc_famille_no_family_{j}_{key_suffix}"
                
                famille = st.session_state.get(uc_famille_key, "").strip()
                validated_use_cases.append({
                    "titre": st.session_state.get(uc_titre_key, uc.get("titre", "")),
                    "description": st.session_state.get(uc_desc_key, uc.get("description", "")),
                    "famille": famille if famille else None
                })
            
            # Nettoyer les clés de session_state
            for key in list(st.session_state.keys()):
                if key_suffix in key and (key.startswith("need_") or key.startswith("uc_") or key.startswith("famille_name_")):
                    del st.session_state[key]
            
            return {
                "validated_needs": validated_needs,
                "validated_use_cases": validated_use_cases,
                "extraction_validated": True
            }
        
        # Retour par défaut (en attente de validation)
        return None

