#!/bin/bash

set -eux

# Charger les variables d'environnement depuis deploy/.env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${SCRIPT_DIR}/.env" ]; then
  echo "📋 Chargement des variables depuis deploy/.env"
  export $(cat "${SCRIPT_DIR}/.env" | grep -v '^#' | xargs)
else
  echo "⚠️  Fichier deploy/.env non trouvé. Utilisation des valeurs par défaut ou variables d'environnement système."
fi

# Variables requises (à définir dans deploy/.env)
# GCP_PROJECT: ID du projet GCP
# GCP_REGION: Région GCP (ex: europe-west1)
# PROJECT_PATH: Chemin du projet (optionnel, par défaut: parent du script)

# Valeurs par défaut pour Artifact Registry
ARTIFACT_REGISTRY_REPO=${ARTIFACT_REGISTRY_REPO:-"aiko-gpt-repo"}
ARTIFACT_REGISTRY_LOCATION=${ARTIFACT_REGISTRY_LOCATION:-"${GCP_REGION:-europe-west1}"}

# Noms des services Cloud Run
API_SERVICE_NAME=${API_SERVICE_NAME:-"aiko-gpt-api"}
STREAMLIT_SERVICE_NAME=${STREAMLIT_SERVICE_NAME:-"aiko-gpt-streamlit"}

echo "🚀 Déploiement de aikoGPT sur GCP"
echo "📍 Projet: ${GCP_PROJECT}"
echo "📍 Région: ${GCP_REGION}"
echo "📍 Repository Artifact Registry: ${ARTIFACT_REGISTRY_REPO}"
echo "📍 Service API: ${API_SERVICE_NAME}"
echo "📍 Service Streamlit: ${STREAMLIT_SERVICE_NAME}"

# Vérifier que GCP_PROJECT est défini
if [ -z "${GCP_PROJECT:-}" ]; then
  echo "❌ ERREUR: GCP_PROJECT n'est pas défini dans deploy/.env"
  exit 1
fi

# Forcer l'utilisation du bon projet GCP pour toutes les commandes
echo "🔧 Configuration du projet GCP: ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}" --quiet

# Se déplacer dans le répertoire du projet
if [ -n "${PROJECT_PATH:-}" ]; then
  cd "${PROJECT_PATH}"
else
  cd "${PROJECT_ROOT}"
fi

# Créer le repository Artifact Registry s'il n'existe pas
echo ""
echo "📦 Vérification/création du repository Artifact Registry..."
if ! gcloud artifacts repositories describe "${ARTIFACT_REGISTRY_REPO}" \
    --project="${GCP_PROJECT}" \
    --location="${ARTIFACT_REGISTRY_LOCATION}" \
    --format="value(name)" &>/dev/null; then
  echo "📦 Création du repository Artifact Registry..."
  gcloud artifacts repositories create "${ARTIFACT_REGISTRY_REPO}" \
    --project="${GCP_PROJECT}" \
    --repository-format=docker \
    --location="${ARTIFACT_REGISTRY_LOCATION}" \
    --description="Repository Docker pour aikoGPT"
else
  echo "✅ Repository Artifact Registry existe déjà"
fi

# Configurer l'authentification Docker pour Artifact Registry
echo "🔐 Configuration de l'authentification Docker..."
gcloud auth configure-docker "${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev" --quiet

# ==================== DÉPLOIEMENT API ====================
echo ""
echo "🏗️  ========== DÉPLOIEMENT API =========="
API_IMAGE_NAME="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT}/${ARTIFACT_REGISTRY_REPO}/${API_SERVICE_NAME}"
API_IMAGE_TAG="${API_IMAGE_NAME}:latest"

echo "🏗️  Construction de l'image Docker pour l'API..."
gcloud builds submit \
  --project="${GCP_PROJECT}" \
  --config="${PROJECT_ROOT}/cloudbuild.api.yaml" \
  --region="${ARTIFACT_REGISTRY_LOCATION}" \
  --substitutions="_IMAGE_NAME=${API_IMAGE_NAME},_IMAGE_TAG=latest" \
  "${PROJECT_ROOT}"

# Préparer les options de déploiement pour l'API
API_DEPLOY_OPTS=(
  --image "${API_IMAGE_TAG}"
  --platform managed
  --region "${GCP_REGION}"
  --allow-unauthenticated
  --port 8080
  --memory 2Gi
  --cpu 2
  --timeout 900
)

# Ajouter les secrets pour l'API
API_SECRETS="OPENAI_API_KEY=API_KEY_OPENAI:latest,LANGSMITH_API_KEY=API_KEY_LANGSMITH:latest,PERPLEXITY_API_KEY=API_KEY_PERPLEXITY:latest"
API_DEPLOY_OPTS+=(--set-secrets "${API_SECRETS}")

# Ajouter les variables d'environnement pour l'API
API_ENV_VARS=""
[ -n "${DEV_MODE:-}" ] && API_ENV_VARS="${API_ENV_VARS}DEV_MODE=${DEV_MODE},"
[ -n "${OPENAI_MODEL:-}" ] && API_ENV_VARS="${API_ENV_VARS}OPENAI_MODEL=${OPENAI_MODEL}"
API_ENV_VARS=$(echo "${API_ENV_VARS}" | sed 's/,$//')
if [ -n "${API_ENV_VARS}" ]; then
  API_DEPLOY_OPTS+=(--set-env-vars "${API_ENV_VARS}")
fi

# Déployer l'API sur Cloud Run
echo "🚀 Déploiement de l'API sur Cloud Run..."
gcloud run deploy "${API_SERVICE_NAME}" \
  --project="${GCP_PROJECT}" \
  "${API_DEPLOY_OPTS[@]}"

# Récupérer l'URL de l'API
API_URL=$(gcloud run services describe "${API_SERVICE_NAME}" \
  --project="${GCP_PROJECT}" \
  --region="${GCP_REGION}" \
  --format='value(status.url)')
echo "✅ API déployée: ${API_URL}"

# ==================== DÉPLOIEMENT STREAMLIT ====================
echo ""
echo "🏗️  ========== DÉPLOIEMENT STREAMLIT =========="
STREAMLIT_IMAGE_NAME="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT}/${ARTIFACT_REGISTRY_REPO}/${STREAMLIT_SERVICE_NAME}"
STREAMLIT_IMAGE_TAG="${STREAMLIT_IMAGE_NAME}:latest"

echo "🏗️  Construction de l'image Docker pour Streamlit..."
gcloud builds submit \
  --project="${GCP_PROJECT}" \
  --config="${PROJECT_ROOT}/cloudbuild.streamlit.yaml" \
  --region="${ARTIFACT_REGISTRY_LOCATION}" \
  --substitutions="_IMAGE_NAME=${STREAMLIT_IMAGE_NAME},_IMAGE_TAG=latest" \
  "${PROJECT_ROOT}"

# Préparer les options de déploiement pour Streamlit
STREAMLIT_DEPLOY_OPTS=(
  --image "${STREAMLIT_IMAGE_TAG}"
  --platform managed
  --region "${GCP_REGION}"
  --allow-unauthenticated
  --port 8080
  --memory 1Gi
  --cpu 1
  --timeout 300
)

# Ajouter les variables d'environnement pour Streamlit
STREAMLIT_ENV_VARS="API_URL=${API_URL}"
[ -n "${DEV_MODE:-}" ] && STREAMLIT_ENV_VARS="${STREAMLIT_ENV_VARS},DEV_MODE=${DEV_MODE}"
[ -n "${AUTH_USERNAME:-}" ] && STREAMLIT_ENV_VARS="${STREAMLIT_ENV_VARS},AUTH_USERNAME=${AUTH_USERNAME}"
[ -n "${AUTH_PASSWORD:-}" ] && STREAMLIT_ENV_VARS="${STREAMLIT_ENV_VARS},AUTH_PASSWORD=${AUTH_PASSWORD}"
STREAMLIT_DEPLOY_OPTS+=(--set-env-vars "${STREAMLIT_ENV_VARS}")

# Déployer Streamlit sur Cloud Run
echo "🚀 Déploiement de Streamlit sur Cloud Run..."
gcloud run deploy "${STREAMLIT_SERVICE_NAME}" \
  --project="${GCP_PROJECT}" \
  "${STREAMLIT_DEPLOY_OPTS[@]}"

# Récupérer l'URL de Streamlit
STREAMLIT_URL=$(gcloud run services describe "${STREAMLIT_SERVICE_NAME}" \
  --project="${GCP_PROJECT}" \
  --region="${GCP_REGION}" \
  --format='value(status.url)')

# ==================== RÉSUMÉ ====================
echo ""
echo "✅ ========== DÉPLOIEMENT TERMINÉ =========="
echo "📍 API URL: ${API_URL}"
echo "📍 Streamlit URL: ${STREAMLIT_URL}"
echo ""
echo "📖 Documentation API: ${API_URL}/docs"
echo "🌐 Interface utilisateur: ${STREAMLIT_URL}"
