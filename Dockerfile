# Dockerfile pour aikoGPT - API FastAPI
# Ce fichier est conservé pour compatibilité, utilisez Dockerfile.api pour le déploiement
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Installer uv pour la gestion des dépendances
RUN pip install --no-cache-dir uv

# Copier les fichiers de configuration des dépendances
COPY pyproject.toml uv.lock ./

# Installer les dépendances avec uv
RUN uv sync --frozen --no-dev

# Copier le reste de l'application
COPY . .

# Créer le répertoire pour les uploads
RUN mkdir -p /tmp/aiko_uploads && chmod 777 /tmp/aiko_uploads

# Exposer le port 8080 (Cloud Run utilise ce port par défaut)
EXPOSE 8080

# Variable d'environnement pour Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Utiliser le Python de l'environnement uv
ENV PATH="/app/.venv/bin:$PATH"

# Commande pour démarrer l'API
# Utiliser uvicorn directement avec le module api.langgraph_api
CMD ["uvicorn", "api.langgraph_api:app", "--host", "0.0.0.0", "--port", "8080"]

