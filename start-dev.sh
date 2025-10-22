#!/bin/bash

# FR: Script de démarrage développement
# Usage: ./start-dev.sh

set -e

echo "🧹 Nettoyage des ports..."
lsof -ti:2024 -ti:3000 -ti:3001 -ti:3002 | xargs kill -9 2>/dev/null || true

echo ""
echo "🚀 Démarrage du backend (LangGraph Server)..."
cd "$(dirname "$0")"
uv run langgraph dev &
BACKEND_PID=$!

echo "⏳ Attente du backend (10 secondes)..."
sleep 10

echo ""
echo "🎨 Démarrage du frontend (Next.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services démarrés !"
echo "   - Backend API: http://localhost:2024"
echo "   - Frontend:    http://localhost:3000"
echo ""
echo "🛑 Appuyez sur Ctrl+C pour arrêter tous les services"

# FR: Fonction de nettoyage
cleanup() {
    echo ""
    echo "🛑 Arrêt des services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    lsof -ti:2024 -ti:3000 | xargs kill -9 2>/dev/null || true
    echo "✅ Services arrêtés"
    exit 0
}

trap cleanup INT TERM

# FR: Attendre indéfiniment
wait

