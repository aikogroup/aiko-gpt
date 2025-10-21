#!/bin/bash
# Script de préparation pour LangGraph Studio

echo "🔧 Préparation de l'environnement LangGraph Studio..."

# Créer les dossiers nécessaires
echo "📁 Création des dossiers de sortie..."
mkdir -p outputs/token_tracking

# Vérifier que .env existe
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé !"
    echo "💡 Créez un fichier .env avec OPENAI_API_KEY=votre_cle"
    exit 1
fi

echo "✅ Préparation terminée !"
echo ""
echo "🚀 Lancez maintenant LangGraph Studio avec :"
echo "   uv run langgraph dev --allow-blocking"
echo ""
echo "📌 Note: Le flag --allow-blocking est nécessaire car le projet utilise"
echo "   des opérations de fichiers (mkdir, file I/O) pour le tracking des tokens."

