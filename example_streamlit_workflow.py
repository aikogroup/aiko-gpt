"""
Exemple d'utilisation du workflow avec validation humaine Streamlit
"""

import streamlit as st
import os
from workflow.need_analysis_workflow import NeedAnalysisWorkflow
from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface

def main():
    """Fonction principale pour l'interface Streamlit"""
    
    st.set_page_config(
        page_title="Analyse des Besoins Métier",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Analyse des Besoins Métier")
    st.markdown("---")
    
    # Initialisation des composants
    if "workflow" not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ Clé API OpenAI non trouvée. Veuillez définir OPENAI_API_KEY")
            return
        
        st.session_state.workflow = NeedAnalysisWorkflow(api_key, dev_mode=True)
        st.session_state.validation_interface = StreamlitValidationInterface()
    
    # Vérifier si le workflow est en pause
    if st.session_state.get("workflow_paused", False):
        st.info("⏸️ Workflow en pause - en attente de validation")
        
        # Afficher l'interface de validation si elle n'a pas encore été traitée
        if not st.session_state.get("validation_completed", False):
            # Récupérer les données nécessaires pour la validation
            workflow_state = st.session_state.get("workflow_state", {})
            identified_needs = workflow_state.get("identified_needs", [])
            validated_needs = workflow_state.get("validated_needs", [])
            
            if identified_needs:
                # Afficher l'interface de validation
                validation_result = st.session_state.validation_interface.display_needs_for_validation(
                    identified_needs, 
                    len(validated_needs)
                )
                
                # Si une validation a été effectuée
                if validation_result:
                    st.session_state.validation_completed = True
                    st.session_state.validation_result = validation_result
                    st.rerun()
            else:
                st.error("❌ Aucun besoin identifié pour la validation")
        
        # Afficher le bouton de reprise si la validation est terminée
        elif st.session_state.get("validation_completed", False):
            st.success("✅ Validation terminée !")
            st.info("🔄 Cliquez sur le bouton ci-dessous pour reprendre le workflow")
            
            if st.button("▶️ Reprendre le workflow", type="primary"):
                # Reprendre le workflow
                st.session_state.workflow_paused = False
                st.session_state.waiting_for_validation = False
                st.session_state.validation_completed = False
                
                # Reprendre l'exécution
                result = st.session_state.workflow.resume_workflow()
                
                if result["success"]:
                    st.success("✅ Workflow terminé avec succès !")
                    st.json(result)
                    
                    # Nettoyer l'état après succès
                    if "workflow_state" in st.session_state:
                        del st.session_state.workflow_state
                    if "validation_result" in st.session_state:
                        del st.session_state.validation_result
                elif result.get("error") == "Nouvelle validation requise":
                    # Nouvelle validation requise - réinitialiser l'état
                    st.info("🔄 Nouvelle validation requise - réinitialisation de l'interface")
                    st.session_state.validation_completed = False
                    if "validation_result" in st.session_state:
                        del st.session_state.validation_result
                    st.rerun()
                else:
                    st.error(f"❌ Erreur lors de la reprise: {result.get('error', 'Erreur inconnue')}")
                    
                    # Nettoyer l'état en cas d'erreur
                    if "workflow_state" in st.session_state:
                        del st.session_state.workflow_state
                    if "validation_result" in st.session_state:
                        del st.session_state.validation_result
    
    else:
        # Interface normale
        st.subheader("📊 Configuration du Workflow")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Mode développement activé**")
            st.info("Les données mockées seront utilisées")
        
        with col2:
            if st.button("🚀 Démarrer l'analyse", type="primary"):
                with st.spinner("Exécution du workflow..."):
                    # Exécuter le workflow
                    result = st.session_state.workflow.run()
                    
                    if result["success"]:
                        st.success("✅ Workflow terminé avec succès !")
                        st.json(result)
                    else:
                        st.error(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
        
        # Afficher l'état du workflow
        if "workflow_state" in st.session_state:
            st.subheader("📋 État du Workflow")
            st.json(st.session_state.workflow_state)
        
        # Afficher les résultats de validation
        if "validation_result" in st.session_state:
            st.subheader("✅ Résultats de Validation")
            st.json(st.session_state.validation_result)

if __name__ == "__main__":
    main()
