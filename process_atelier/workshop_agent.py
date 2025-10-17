"""
Workshop Agent - Traitement des fichiers Excel d'ateliers IA
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from prompts.workshop_agent_prompts import (
    WORKSHOP_ANALYSIS_PROMPT,
    USE_CASE_CONSOLIDATION_PROMPT
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

class UseCase(BaseModel):
    """Modèle pour un cas d'usage"""
    title: str = Field(description="Titre du cas d'usage")
    objective: str = Field(description="Objectif ou gain attendu")
    benefits: List[str] = Field(default_factory=list, description="Liste des bénéfices")

class WorkshopAnalysisResponse(BaseModel):
    """Modèle pour la réponse d'analyse d'un atelier"""
    theme: str = Field(description="Thème principal de l'atelier")
    use_cases: List[UseCase] = Field(description="Liste des cas d'usage consolidés")

class WorkshopData(BaseModel):
    """Modèle pour les données d'un atelier"""
    workshop_id: str = Field(description="Identifiant unique de l'atelier")
    theme: str = Field(description="Thème de l'atelier")
    use_cases: List[UseCase] = Field(description="Liste des cas d'usage")

class WorkshopAgent:
    """Agent de traitement des fichiers Excel d'ateliers"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialise l'agent avec la clé API OpenAI"""
        # Utilisation de la clé API depuis les variables d'environnement
        import os
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être définie dans les variables d'environnement ou passée en paramètre")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        
    def parse_excel(self, file_path: str) -> pd.DataFrame:
        """
        Parse un fichier Excel et retourne un DataFrame nettoyé
        
        Args:
            file_path: Chemin vers le fichier Excel
            
        Returns:
            DataFrame nettoyé avec les colonnes standardisées
        """
        logger.info(f"Parsing du fichier Excel: {file_path}")
        
        try:
            # Lecture du fichier Excel
            df = pd.read_excel(file_path)
            
            # Log des colonnes originales
            logger.info(f"Colonnes détectées: {df.columns.tolist()}")
            logger.info(f"Nombre de lignes: {len(df)}")
            
            # Standardisation des noms de colonnes (première lettre de chaque colonne)
            if len(df.columns) >= 3:
                df.columns = ['Atelier', 'Use_Case', 'Objective']
            else:
                raise ValueError("Le fichier Excel doit contenir au moins 3 colonnes")
            
            # Nettoyage des données
            df = df.dropna(subset=['Atelier'])  # Supprimer les lignes sans atelier
            df = df.fillna('')  # Remplacer les NaN par des chaînes vides
            
            logger.info(f"Données nettoyées - {len(df)} lignes restantes")
            logger.info("Premières lignes du fichier parsé:")
            logger.info(f"\n{df.head()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing du fichier Excel: {e}")
            raise
    
    def group_by_workshop(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Groupe les données par atelier
        
        Args:
            df: DataFrame nettoyé
            
        Returns:
            Dictionnaire avec les ateliers comme clés
        """
        logger.info("Groupement des données par atelier")
        
        workshops = {}
        for atelier in df['Atelier'].unique():
            if atelier and atelier.strip():  # Ignorer les ateliers vides
                workshop_data = df[df['Atelier'] == atelier]
                workshops[atelier] = workshop_data
                logger.info(f"Atelier '{atelier}': {len(workshop_data)} cas d'usage")
        
        return workshops
    
    def _process_single_workshop(self, atelier_name: str, workshop_df: pd.DataFrame, workshop_id: str) -> WorkshopData:
        """
        Traite un seul atelier avec le LLM (fonction helper pour la parallélisation)
        
        Args:
            atelier_name: Nom de l'atelier
            workshop_df: DataFrame des cas d'usage de cet atelier
            workshop_id: Identifiant unique de l'atelier
            
        Returns:
            WorkshopData structuré
        """
        logger.info(f"Traitement de l'atelier: {atelier_name}")
        
        # Préparation des données pour le LLM
        use_cases_text = []
        for _, row in workshop_df.iterrows():
            use_case = row['Use_Case']
            objective = row['Objective']
            if use_case and use_case.strip():
                use_cases_text.append(f"- {use_case}: {objective}")
        
        # Utilisation du prompt depuis workshop_agent_prompts.py
        user_prompt = USE_CASE_CONSOLIDATION_PROMPT.format(
            atelier_name=atelier_name,
            use_cases_text=chr(10).join(use_cases_text)
        )
        
        try:
            # Appel à l'API OpenAI Responses avec structured output
            # Utilisation du paramètre 'instructions' pour le system prompt
            response = self.client.responses.parse(
                model=self.model,
                instructions=WORKSHOP_ANALYSIS_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                text_format=WorkshopAnalysisResponse
            )
            
            # Extraction de la réponse structurée
            parsed_response = response.output_parsed
            
            logger.info(f"Réponse structurée pour {atelier_name}:")
            logger.info(f"Thème: {parsed_response.theme}")
            logger.info(f"Nombre de cas d'usage: {len(parsed_response.use_cases)}")
            
            # Création de l'objet WorkshopData
            workshop_result = WorkshopData(
                workshop_id=workshop_id,
                theme=parsed_response.theme,
                use_cases=parsed_response.use_cases
            )
            
            logger.info(f"Atelier {atelier_name} traité avec succès avec structured output")
            return workshop_result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement LLM pour {atelier_name}: {e}", exc_info=True)
            # Fallback: création d'un atelier basique
            workshop_result = WorkshopData(
                workshop_id=workshop_id,
                theme=atelier_name,
                use_cases=[]
            )
            return workshop_result
    
    def aggregate_use_cases_with_llm(self, workshops: Dict[str, pd.DataFrame]) -> List[WorkshopData]:
        """
        Utilise un LLM pour rassembler et structurer les cas d'usage par atelier
        PARALLÉLISÉ : Traite tous les ateliers en parallèle pour gagner du temps
        
        Args:
            workshops: Dictionnaire des ateliers groupés
            
        Returns:
            Liste des données d'ateliers structurées
        """
        logger.info(f"Agrégation des cas d'usage avec LLM (PARALLÉLISÉE pour {len(workshops)} ateliers)")
        
        workshop_results = []
        
        # 🚀 PARALLÉLISATION : Traiter tous les ateliers en même temps
        with ThreadPoolExecutor(max_workers=len(workshops)) as executor:
            # Soumettre tous les ateliers pour traitement parallèle
            future_to_atelier = {}
            for idx, (atelier_name, workshop_df) in enumerate(workshops.items(), 1):
                workshop_id = f"W{idx:03d}"
                future = executor.submit(self._process_single_workshop, atelier_name, workshop_df, workshop_id)
                future_to_atelier[future] = atelier_name
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_atelier):
                atelier_name = future_to_atelier[future]
                try:
                    workshop_result = future.result()
                    workshop_results.append(workshop_result)
                    logger.info(f"✓ Atelier '{atelier_name}' terminé")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement de '{atelier_name}': {e}")
                    # Créer un résultat fallback
                    workshop_results.append(WorkshopData(
                        workshop_id=f"W{len(workshop_results) + 1:03d}",
                        theme=atelier_name,
                        use_cases=[]
                    ))
        
        logger.info(f"✅ Traitement parallèle terminé: {len(workshop_results)} ateliers traités")
        return workshop_results
    
    def process_workshop_file(self, file_path: str) -> List[WorkshopData]:
        """
        Traite un fichier Excel d'atelier complet
        
        Args:
            file_path: Chemin vers le fichier Excel
            
        Returns:
            Liste des données d'ateliers structurées
        """
        logger.info(f"Début du traitement du fichier: {file_path}")
        
        # 1. Parsing du fichier Excel
        df = self.parse_excel(file_path)
        
        # 2. Groupement par atelier
        workshops = self.group_by_workshop(df)
        
        # 3. Agrégation avec LLM
        workshop_results = self.aggregate_use_cases_with_llm(workshops)
        
        logger.info(f"Traitement terminé: {len(workshop_results)} ateliers traités")
        
        return workshop_results
    
    def save_results(self, results: List[WorkshopData], output_path: str):
        """
        Sauvegarde les résultats en JSON
        
        Args:
            results: Liste des données d'ateliers
            output_path: Chemin de sauvegarde
        """
        logger.info(f"Sauvegarde des résultats vers: {output_path}")
        
        # Conversion en dictionnaire pour la sérialisation JSON
        results_dict = [result.model_dump() for result in results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        
        logger.info("Résultats sauvegardés avec succès")

def main():
    """Fonction principale pour tester l'agent"""
    # Configuration
    input_file = "inputs/atelier_exemple.xlsx"
    output_file = "outputs/workshop_results.json"
    
    # Création du dossier de sortie si nécessaire
    Path("outputs").mkdir(exist_ok=True)
    
    # Initialisation de l'agent
    agent = WorkshopAgent()
    
    try:
        # Traitement du fichier
        results = agent.process_workshop_file(input_file)
        
        # Sauvegarde des résultats
        agent.save_results(results, output_file)
        
        # Affichage des résultats
        print(f"\n=== RÉSULTATS DU TRAITEMENT ===")
        print(f"Nombre d'ateliers traités: {len(results)}")
        
        for result in results:
            print(f"\n--- Atelier: {result.theme} (ID: {result.workshop_id}) ---")
            print(f"Nombre de cas d'usage: {len(result.use_cases)}")
            for i, use_case in enumerate(result.use_cases, 1):
                print(f"  {i}. {use_case.title}")
                print(f"     Objectif: {use_case.objective}")
                if use_case.benefits:
                    print(f"     Bénéfices: {', '.join(use_case.benefits)}")
        
        print(f"\nRésultats sauvegardés dans: {output_file}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {e}")
        raise

if __name__ == "__main__":
    main()
