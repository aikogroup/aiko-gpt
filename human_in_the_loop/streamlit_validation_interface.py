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
    
    def display_needs_for_validation(self, identified_needs: List[Dict[str, Any]], validated_count: int = 0, key_suffix: str = None) -> Dict[str, Any]:
        """
        Affiche les besoins identifiés pour validation dans Streamlit.
        VERSION CORRIGÉE: Gère correctement l'état entre les recharges.
        
        Args:
            identified_needs: Liste des besoins identifiés
            validated_count: Nombre de besoins déjà validés
            key_suffix: Suffixe personnalisé pour les clés de checkbox (ex: iteration_count). Si None, utilise len(identified_needs)
            
        Returns:
            Résultat de la validation
        """
        # Utiliser un suffixe personnalisé ou la longueur de la liste
        if key_suffix is None:
            key_suffix = str(len(identified_needs))
        # (Spinner retiré - géré par app_api.py pour un flux continu)
        
        st.subheader("Validation des Besoins Métier")
        
        if validated_count > 0:
            st.success(f"Vous avez déjà validé {validated_count} besoins")
            remaining = max(0, 5 - validated_count)
            if remaining > 0:
                st.info(f"Il vous faut valider {remaining} besoins supplémentaires pour terminer")
            else:
                st.success("Vous avez atteint le minimum requis (5 besoins)")
        
        st.markdown("---")
        
        # Ne pas nettoyer les clés ici pour éviter les conflits de timing
        # Les clés seront nettoyées après validation
        
        # Afficher les besoins avec des champs éditables - 2 par ligne
        for i in range(0, len(identified_needs), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier besoin de la ligne
            with col1:
                need = identified_needs[i]
                original_theme = need.get('theme', 'Thème non défini')
                original_quotes = need.get('quotes', [])
                
                # Initialiser les valeurs dans session_state si nécessaire
                theme_key = f"need_theme_{i}_{key_suffix}"
                if theme_key not in st.session_state:
                    st.session_state[theme_key] = original_theme
                
                # Champ éditable pour le thème (ne pas passer value pour éviter le warning)
                modified_theme = st.text_input(
                    "**Thème**",
                    key=theme_key,
                    label_visibility="visible"
                )
                
                # Citations éditables
                if original_quotes:
                    st.markdown("**Citations:**")
                    modified_quotes = []
                    for j, quote in enumerate(original_quotes):
                        quote_key = f"need_quote_{i}_{j}_{key_suffix}"
                        if quote_key not in st.session_state:
                            st.session_state[quote_key] = quote
                        
                        modified_quote = st.text_area(
                            f"Citation {j+1}",
                            key=quote_key,
                            height=60,
                            label_visibility="collapsed"
                        )
                        if modified_quote.strip():  # Ne garder que les citations non vides
                            modified_quotes.append(modified_quote)
                else:
                    st.info("Aucune citation disponible")
                    modified_quotes = []
                
                # Checkbox pour sélectionner ce besoin avec une clé unique
                checkbox_key = f"validate_need_{i+1}_{key_suffix}"
                is_selected = st.checkbox(f"Valider ce besoin", key=checkbox_key)
            
            # Deuxième besoin de la ligne (si existant)
            if i + 1 < len(identified_needs):
                with col2:
                    need = identified_needs[i + 1]
                    original_theme = need.get('theme', 'Thème non défini')
                    original_quotes = need.get('quotes', [])
                    
                    # Initialiser les valeurs dans session_state si nécessaire
                    theme_key = f"need_theme_{i+1}_{key_suffix}"
                    if theme_key not in st.session_state:
                        st.session_state[theme_key] = original_theme
                    
                    # Champ éditable pour le thème (ne pas passer value pour éviter le warning)
                    modified_theme = st.text_input(
                        "**Thème**",
                        key=theme_key,
                        label_visibility="visible"
                    )
                    
                    # Citations éditables
                    if original_quotes:
                        st.markdown("**Citations:**")
                        modified_quotes = []
                        for j, quote in enumerate(original_quotes):
                            quote_key = f"need_quote_{i+1}_{j}_{key_suffix}"
                            if quote_key not in st.session_state:
                                st.session_state[quote_key] = quote
                            
                            modified_quote = st.text_area(
                                f"Citation {j+1}",
                                key=quote_key,
                                height=60,
                                label_visibility="collapsed"
                            )
                            if modified_quote.strip():  # Ne garder que les citations non vides
                                modified_quotes.append(modified_quote)
                    else:
                        st.info("Aucune citation disponible")
                        modified_quotes = []
                    
                    # Checkbox pour sélectionner ce besoin avec une clé unique
                    checkbox_key = f"validate_need_{i+2}_{key_suffix}"
                    is_selected = st.checkbox(f"Valider ce besoin", key=checkbox_key)
            
            # Ligne de séparation fine entre les besoins
            st.markdown("---")
        
        # Calculer le nombre de sélections en temps réel
        selected_count = 0
        selected_needs_list = []
        
        for i in range(1, len(identified_needs) + 1):
            checkbox_key = f"validate_need_{i}_{key_suffix}"
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
        
        # Bouton de validation
        st.markdown("---")
        
        if st.button("✅ Valider la sélection", type="primary", disabled=selected_count == 0, use_container_width=True):
            if selected_count == 0:
                st.warning("Veuillez sélectionner au moins un besoin")
            else:
                # Lire l'état des checkboxes directement
                selected_needs = []
                for i in range(1, len(identified_needs) + 1):
                    checkbox_key = f"validate_need_{i}_{key_suffix}"
                    if st.session_state.get(checkbox_key, False):
                        selected_needs.append(i)
                
                # Traiter la validation et retourner le résultat
                result = self._process_validation(identified_needs, selected_needs, comments, validated_count, key_suffix)
                return result  # Retourner le résultat pour que app_api.py puisse l'envoyer à l'API
        
        # Retour par défaut (en attente de validation)
        return None
    
    def _process_validation(self, identified_needs: List[Dict[str, Any]], selected_numbers: List[int], comments: str, validated_count: int, key_suffix: str = None) -> Dict[str, Any]:
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
        
        # Extraire les besoins validés avec les modifications de l'utilisateur
        validated_new = []
        for selected_num in selected_numbers:
            idx = selected_num - 1  # Convertir en index 0-based
            original_need = identified_needs[idx]
            
            # Lire les valeurs modifiées depuis session_state
            theme_key = f"need_theme_{idx}_{key_suffix}"
            modified_theme = st.session_state.get(theme_key, original_need.get('theme', ''))
            
            # Lire les citations modifiées
            original_quotes = original_need.get('quotes', [])
            modified_quotes = []
            for j in range(len(original_quotes)):
                quote_key = f"need_quote_{idx}_{j}_{key_suffix}"
                modified_quote = st.session_state.get(quote_key, '')
                if modified_quote.strip():  # Ne garder que les citations non vides
                    modified_quotes.append(modified_quote.strip())
            
            # Créer le besoin modifié
            modified_need = {
                'theme': modified_theme.strip() if modified_theme.strip() else original_need.get('theme', ''),
                'quotes': modified_quotes if modified_quotes else original_need.get('quotes', [])
            }
            
            validated_new.append(modified_need)
        
        # Pour les rejetés, on garde les originaux (pas besoin de modifications)
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
        
        print(f"💾 [DEBUG] Préparation du résultat")
        print(f"✅ [DEBUG] Résultat préparé - success={result['success']}, total_validated={result['total_validated']}")
        
        # Nettoyer l'état des sélections et les clés de validation + modification
        print(f"🧹 [DEBUG] Nettoyage des clés de validation et modification")
        st.session_state.selected_needs = set()
        for key in list(st.session_state.keys()):
            if key.startswith("validate_need_") or key.startswith("need_theme_") or key.startswith("need_quote_"):
                del st.session_state[key]
        print(f"✅ [DEBUG] Nettoyage terminé")
        
        if result["success"]:
            print(f"🎉 [DEBUG] Validation réussie - {total_validated} besoins validés")
        else:
            remaining = 5 - total_validated
            print(f"⚠️ [DEBUG] Validation partielle - il reste {remaining} besoins à valider")
        
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
