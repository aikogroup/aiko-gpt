# ==================================
# FR: Dockerfile Backend Python + LangGraph
# ==================================

FROM python:3.11-slim

# FR: Définir le répertoire de travail
WORKDIR /app

# FR: Installer UV (gestionnaire de dépendances moderne)
RUN pip install --no-cache-dir uv

# FR: Copier les fichiers de dépendances
COPY requirements.txt .

# FR: Installer les dépendances avec UV
RUN uv pip install --system -r requirements.txt

# FR: Copier le code source
COPY . .

# FR: Créer les dossiers nécessaires
RUN mkdir -p /app/temp /app/outputs

# FR: Exposer le port
EXPOSE 8000

# FR: Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# FR: Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# FR: Commande de démarrage
# TODO (FR): Adapter selon l'implémentation finale (FastAPI, Flask, etc.)
CMD ["python", "main.py"]
# Alternative si FastAPI :
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

