"""
Interface Streamlit pour la validation des enjeux et recommandations (Executive Summary)
"""

import streamlit as st
import json
from typing import List, Dict, Any, Optional


class StreamlitExecutiveValidation:
    """Interface de validation Streamlit pour Executive Summary"""
    
    def _map_besoins_to_titles(self, besoins_lies: List[str], extracted_needs: List[Dict[str, Any]]) -> List[str]:
        """
        Mappe les IDs/titres des besoins liés vers les titres réels (theme) des besoins.
        
        Args:
            besoins_lies: Liste des IDs ou titres dans besoins_lies
            extracted_needs: Liste des besoins extraits avec leur structure complète
            
        Returns:
            Liste des titres réels des besoins
        """
        # Créer un mapping: ID -> theme, et titre -> theme
        print(f"Extracted needs: {extracted_needs}")
        needs_map = {}
        for need in extracted_needs:
            theme = need.get('theme', '')
            # Mapper le theme lui-même
            if theme:
                needs_map[theme] = theme
            # Si le besoin a un ID, le mapper aussi
            need_id = need.get('id', '')
            if need_id:
                needs_map[need_id] = theme
        
        # Mapper chaque besoin lié vers son titre réel
        mapped_titles = []
        for besoin_lie in besoins_lies:
            # Chercher dans le mapping
            titre = needs_map.get(besoin_lie, besoin_lie)  # Si pas trouvé, garder l'original
            mapped_titles.append(titre)
        
        return mapped_titles
    
    def display_challenges_for_validation(
        self,
        identified_challenges: List[Dict[str, Any]],
        validated_challenges: List[Dict[str, Any]] = None,
        extracted_needs: List[Dict[str, Any]] = None,
        key_suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Affiche l'interface de validation des enjeux stratégiques.
        VERSION REFACTORISÉE: Suit le même pattern que display_needs_for_validation.
        
        Args:
            identified_challenges: Liste des 5 enjeux identifiés
            validated_challenges: Liste des enjeux déjà validés (optionnel)
            extracted_needs: Liste des besoins extraits pour mapper les titres
            key_suffix: Suffixe personnalisé pour les clés (ex: iteration_count)
            
        Returns:
            Résultat de la validation ou None si en attente
        """
        validated_challenges = validated_challenges or []
        validated_count = len(validated_challenges)
        extracted_needs = extracted_needs or []
        
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(identified_challenges))
        
        st.subheader("Validation des Enjeux Stratégiques")
        
        if validated_count > 0:
            st.success(f"Vous avez déjà validé {validated_count} enjeux")
            remaining = max(0, 5 - validated_count)
            if remaining > 0:
                st.info(f"Il vous faut valider {remaining} enjeux supplémentaires pour terminer")
            else:
                st.success("Vous avez atteint le minimum requis (5 enjeux)")
        
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
                besoins_lies = challenge.get("besoins_lies", [])
                
                # Mapper les besoins liés vers les titres
                besoins_titres = self._map_besoins_to_titles(besoins_lies, extracted_needs)
                
                # Initialiser les valeurs dans session_state si nécessaire
                titre_key = f"challenge_titre_{i}_{key_suffix}"
                desc_key = f"challenge_desc_{i}_{key_suffix}"
                
                if titre_key not in st.session_state:
                    st.session_state[titre_key] = original_titre
                if desc_key not in st.session_state:
                    st.session_state[desc_key] = original_description
                
                # Champ éditable pour le titre
                modified_titre = st.text_input(
                    f"**Titre** ({ch_id})",
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
                
                # Afficher les besoins liés (titres)
                if besoins_titres:
                    st.markdown("**Besoins liés:**")
                    for titre in besoins_titres:
                        st.text(f"• {titre}")
                else:
                    st.info("Aucun besoin lié")
                
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
                    besoins_lies = challenge.get("besoins_lies", [])
                    
                    # Mapper les besoins liés vers les titres
                    besoins_titres = self._map_besoins_to_titles(besoins_lies, extracted_needs)
                    
                    # Initialiser les valeurs dans session_state si nécessaire
                    titre_key = f"challenge_titre_{i+1}_{key_suffix}"
                    desc_key = f"challenge_desc_{i+1}_{key_suffix}"
                    
                    if titre_key not in st.session_state:
                        st.session_state[titre_key] = original_titre
                    if desc_key not in st.session_state:
                        st.session_state[desc_key] = original_description
                    
                    # Champ éditable pour le titre
                    modified_titre = st.text_input(
                        f"**Titre** ({ch_id})",
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
                    
                    # Afficher les besoins liés (titres)
                    if besoins_titres:
                        st.markdown("**Besoins liés:**")
                        for titre in besoins_titres:
                            st.text(f"• {titre}")
                    else:
                        st.info("Aucun besoin lié")
                    
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
        
        # Bouton de validation
        st.markdown("---")
        
        if st.button("✅ Valider la sélection", type="primary", disabled=selected_count == 0, width="stretch"):
            if selected_count == 0:
                st.warning("Veuillez sélectionner au moins un enjeu")
            else:
                # Lire l'état des checkboxes directement
                selected_challenges = []
                for i in range(1, len(identified_challenges) + 1):
                    checkbox_key = f"validate_challenge_{i}_{key_suffix}"
                    if st.session_state.get(checkbox_key, False):
                        selected_challenges.append(i)
                
                # Traiter la validation et retourner le résultat
                result = self._process_challenges_validation(
                    identified_challenges, 
                    selected_challenges, 
                    comments, 
                    validated_count, 
                    key_suffix
                )
                return result  # Retourner le résultat pour que app_api.py puisse l'envoyer à l'API
        
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
        success = total_validated >= 5
        
        result = {
            "validated_challenges": validated_new,  # Seulement les nouveaux enjeux validés
            "rejected_challenges": rejected_new,
            "challenges_feedback": comments,
            "success": success,  # Succès seulement si on atteint 5 enjeux au total
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
        recommendations: List[str],
        validated_recommendations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Affiche l'interface de validation des recommandations.
        
        Args:
            recommendations: Liste des 4 recommandations générées
            validated_recommendations: Liste des recommandations déjà validées (optionnel)
            
        Returns:
            Résultat de la validation
        """
        validated_recommendations = validated_recommendations or []
        
        st.header("💡 Validation des Recommandations")
        st.info("💡 Validez, modifiez ou rejetez les 4 recommandations générées. Vous devez valider au moins 4 recommandations.")
        
        # Afficher les recommandations déjà validées
        if validated_recommendations:
            st.success(f"✅ {len(validated_recommendations)} recommandations déjà validées")
            with st.expander("Voir les recommandations validées", expanded=False):
                for i, rec in enumerate(validated_recommendations, 1):
                    st.markdown(f"**{i}. {rec}**")
        
        # Interface de validation pour chaque recommandation
        validation_results = {
            "validated_recommendations": validated_recommendations.copy(),
            "rejected_recommendations": [],
            "recommendations_feedback": ""
        }
        
        # Recommandations à valider (exclure celles déjà validées)
        recommendations_to_validate = [r for r in recommendations if r not in validated_recommendations]
        
        if not recommendations_to_validate:
            st.success("✅ Toutes les recommandations ont été validées !")
            return validation_results
        
        st.subheader("Recommandations à valider")
        
        for i, recommendation in enumerate(recommendations_to_validate, 1):
            rec_index = recommendations.index(recommendation)
            
            with st.container():
                st.markdown(f"### Recommandation {rec_index + 1}")
                st.markdown(f"**{recommendation}**")
                
                # Options de validation
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"✅ Valider", key=f"validate_rec_{rec_index}", width="stretch"):
                        validation_results["validated_recommendations"].append(recommendation)
                        st.success("Recommandation validée !")
                        st.rerun()
                
                with col2:
                    if st.button(f"✏️ Modifier", key=f"edit_rec_{rec_index}", width="stretch"):
                        st.session_state[f"editing_rec_{rec_index}"] = True
                        st.rerun()
                
                with col3:
                    if st.button(f"❌ Rejeter", key=f"reject_rec_{rec_index}", width="stretch"):
                        validation_results["rejected_recommendations"].append(recommendation)
                        st.warning("Recommandation rejetée")
                        st.rerun()
                
                # Formulaire d'édition si en cours
                if st.session_state.get(f"editing_rec_{rec_index}", False):
                    with st.form(f"edit_rec_form_{rec_index}"):
                        new_recommendation = st.text_area(
                            "Recommandation",
                            value=recommendation,
                            key=f"rec_text_{rec_index}",
                            height=100
                        )
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("💾 Sauvegarder", width="stretch"):
                                validation_results["validated_recommendations"].append(new_recommendation)
                                st.session_state[f"editing_rec_{rec_index}"] = False
                                st.success("Recommandation modifiée et validée !")
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Annuler", width="stretch"):
                                st.session_state[f"editing_rec_{rec_index}"] = False
                                st.rerun()
                
                st.markdown("---")
        
        # Zone de feedback général
        st.subheader("💬 Feedback général")
        feedback = st.text_area(
            "Commentaires ou instructions pour la régénération des recommandations rejetées",
            key="recommendations_feedback",
            height=100,
            placeholder="Ex: Rendre la recommandation 2 plus concrète, ajouter une recommandation sur la formation..."
        )
        validation_results["recommendations_feedback"] = feedback
        
        # Résumé
        validated_count = len(validation_results["validated_recommendations"])
        rejected_count = len(validation_results["rejected_recommendations"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Recommandations validées", validated_count)
        with col2:
            st.metric("Recommandations rejetées", rejected_count)
        
        if validated_count >= 4:
            st.success("✅ Objectif atteint ! 4 recommandations validées.")
        else:
            st.warning(f"⚠️ {4 - validated_count} recommandation(s) supplémentaire(s) à valider pour continuer.")
        
        return validation_results

