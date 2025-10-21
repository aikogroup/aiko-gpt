"""
TranscriptAgent Implementation - Parsing PDF/JSON et filtrage sémantique

FR: Implémentation complète du TranscriptAgent avec parsing PDF/JSON et appel OpenAI
"""

import logging
import json
from typing import Dict, Any, List
from pathlib import Path
from openai import OpenAI

# FR: Imports pour parsing PDF
try:
    import pypdfium2 as pdfium
    PDF_PARSER = "pypdfium2"
except ImportError:
    try:
        import PyPDF2
        PDF_PARSER = "PyPDF2"
    except ImportError:
        PDF_PARSER = None

from models.graph_state import NeedAnalysisState
from prompts.transcript_agent_prompts import (
    TRANSCRIPT_SEMANTIC_FILTER_SYSTEM_PROMPT,
    TRANSCRIPT_EXTRACTION_USER_PROMPT
)

logger = logging.getLogger(__name__)


def parse_pdf_file(file_path: str) -> str:
    """
    FR: Parse un fichier PDF et extrait son contenu texte
    
    Args:
        file_path: Chemin vers le fichier PDF
        
    Returns:
        str: Contenu texte du PDF
        
    Raises:
        ImportError: Si aucune bibliothèque PDF n'est disponible
        FileNotFoundError: Si le fichier n'existe pas
    """
    logger.info(f"📄 Parsing fichier PDF: {file_path}")
    
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Fichier PDF introuvable: {file_path}")
    
    if PDF_PARSER is None:
        raise ImportError("Aucune bibliothèque PDF disponible (pypdfium2 ou PyPDF2)")
    
    try:
        if PDF_PARSER == "pypdfium2":
            # FR: Utiliser pypdfium2 (préféré)
            pdf = pdfium.PdfDocument(file_path)
            text_parts = []
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                textpage = page.get_textpage()
                text = textpage.get_text_range()
                text_parts.append(text)
            full_text = "\n\n".join(text_parts)
            
        else:  # PyPDF2
            # FR: Fallback vers PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                full_text = "\n\n".join(text_parts)
        
        logger.info(f"✅ PDF parsé : {len(full_text)} caractères extraits")
        return full_text
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du parsing PDF: {e}")
        raise


def parse_json_file(file_path: str) -> str:
    """
    FR: Parse un fichier JSON et le convertit en texte structuré
    
    Args:
        file_path: Chemin vers le fichier JSON
        
    Returns:
        str: Contenu JSON formaté en texte
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        json.JSONDecodeError: Si le JSON est invalide
    """
    logger.info(f"📄 Parsing fichier JSON: {file_path}")
    
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Fichier JSON introuvable: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # FR: Convertir en texte formaté
        formatted_text = json.dumps(data, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ JSON parsé : {len(formatted_text)} caractères")
        return formatted_text
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erreur JSON invalide: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors du parsing JSON: {e}")
        raise


def filter_with_openai(text_content: str, source_file: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Filtre sémantique du contenu avec OpenAI pour extraire citations, frustrations, besoins
    
    Args:
        text_content: Contenu texte à analyser
        source_file: Nom du fichier source (pour traçabilité)
        config: Configuration (contient model, etc.)
        
    Returns:
        Dict: Données filtrées (citations, frustrations, expressed_needs)
    """
    logger.info(f"🤖 Filtrage sémantique avec OpenAI pour {source_file}...")
    
    try:
        # FR: Limiter la taille du texte si trop long (max ~15k tokens pour le contexte)
        max_chars = 50000  # ~12k tokens approximativement
        if len(text_content) > max_chars:
            logger.warning(f"⚠️ Texte trop long ({len(text_content)} chars), troncature à {max_chars}")
            text_content = text_content[:max_chars] + "\n\n[... TEXTE TRONQUÉ ...]"
        
        # FR: Créer le client OpenAI
        client = OpenAI()
        
        # FR: Appeler OpenAI avec les prompts
        response = client.chat.completions.create(
            model=config.get("configurable", {}).get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": TRANSCRIPT_SEMANTIC_FILTER_SYSTEM_PROMPT},
                {"role": "user", "content": TRANSCRIPT_EXTRACTION_USER_PROMPT.format(
                    raw_content=text_content
                )}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # FR: Parser la réponse JSON
        result = json.loads(response.choices[0].message.content)
        
        # FR: Ajouter le nom du fichier source aux citations
        if "citations" in result:
            for citation in result["citations"]:
                if "source" not in citation or not citation["source"]:
                    citation["source"] = source_file
        
        logger.info(f"✅ Filtrage terminé - {len(result.get('citations', []))} citations extraites")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du filtrage OpenAI: {e}")
        # FR: Retourner structure vide en cas d'erreur
        return {
            "citations": [],
            "frustrations": [],
            "expressed_needs": []
        }


def transcript_agent(state: NeedAnalysisState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Agent LangGraph pour analyser les fichiers PDF/JSON (transcriptions)
    
    Args:
        state: État actuel du workflow LangGraph
        config: Configuration LangGraph
        
    Returns:
        Dict: Mise à jour de l'état avec transcript_data
    """
    logger.info("📝 TranscriptAgent - Début analyse PDF/JSON")
    
    pdf_json_file_paths = state.get("pdf_json_file_paths", [])
    
    if not pdf_json_file_paths:
        logger.warning("⚠️ Aucun fichier PDF/JSON fourni, skip")
        return {
            "transcript_data": [],
            "current_step": "transcript_skipped",
            "errors": ["Aucun fichier PDF/JSON fourni"]
        }
    
    all_transcript_data = []
    errors = []
    
    for file_path in pdf_json_file_paths:
        try:
            logger.info(f"📄 Traitement de {file_path}...")
            
            # FR: Déterminer le type de fichier
            file_extension = Path(file_path).suffix.lower()
            source_name = Path(file_path).name
            
            # FR: Parser le fichier selon son type
            if file_extension == ".pdf":
                if PDF_PARSER is None:
                    logger.error(f"❌ Aucune bibliothèque PDF disponible pour {file_path}")
                    errors.append(f"Bibliothèque PDF manquante pour {source_name}")
                    continue
                text_content = parse_pdf_file(file_path)
                
            elif file_extension == ".json":
                text_content = parse_json_file(file_path)
                
            else:
                logger.warning(f"⚠️ Type de fichier non supporté: {file_extension}")
                errors.append(f"Type de fichier non supporté: {source_name}")
                continue
            
            # FR: Filtrage sémantique avec OpenAI
            filtered_data = filter_with_openai(text_content, source_name, config)
            
            # FR: Ajouter les données filtrées
            all_transcript_data.append({
                "source": source_name,
                "file_path": file_path,
                "citations": filtered_data.get("citations", []),
                "frustrations": filtered_data.get("frustrations", []),
                "expressed_needs": filtered_data.get("expressed_needs", []),
                "parsed": True
            })
            
            logger.info(f"✅ {source_name} traité avec succès")
            
        except FileNotFoundError as e:
            logger.error(f"❌ Fichier introuvable: {e}")
            errors.append(f"Fichier introuvable: {Path(file_path).name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue pour {file_path}: {e}")
            errors.append(f"Erreur lors du traitement de {Path(file_path).name}")
    
    # FR: Résumé
    logger.info("✅ TranscriptAgent - Analyse terminée")
    logger.info(f"📊 {len(all_transcript_data)} fichiers traités, {len(errors)} erreurs")
    
    return {
        "transcript_data": all_transcript_data,
        "current_step": "transcript_completed",
        "errors": errors
    }

