

set -eux
 
if [ -f .env ]; then

  export $(cat .env | grep -v '^#' | xargs)

else

  echo ".env file not found. Using default values."

fi
 
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe ${CLOUDSQL_INSTANCE} --format="value(connectionName)")

if [[ -z "$INSTANCE_CONNECTION_NAME" ]]; then

    echo "Error: Unable to retrieve INSTANCE_CONNECTION_NAME"

    exit 1

fi

echo "Instance connection name: ${INSTANCE_CONNECTION_NAME}"
 
IMAGE_TAG="gcr.io/${GCP_PROJECT}/${PROJECT}:latest"
 
cd $PROJECT_PATH

gcloud builds submit --tag gcr.io/${GCP_PROJECT}/${PROJECT} --tag "${IMAGE_TAG}"
 
gcloud run deploy "${PROJECT}" \

  --image "gcr.io/${GCP_PROJECT}/${PROJECT}" \

  --platform managed \

  --region "${GCP_REGION}" \

  --allow-unauthenticated \

  --add-cloudsql-instances="${INSTANCE_CONNECTION_NAME}" \

  --set-env-vars "SOPHIARH_API_TOKEN_EXPIRATION=${SOPHIARH_API_TOKEN_EXPIRATION},TESSERACT_CMD=${TESSERACT_CMD}" \

  --set-secrets "SOPHIARH_DATABASE_URL=SOPHIARH_DATABASE_URL:latest,SOPHIARH_API_SECRET_KEY=SOPHIARH_API_SECRET_KEY:latest,NEUFTROISQUART_API_CLIENT_ID=NEUFTROISQUART_API_CLIENT_ID:latest,NEUFTROISQUART_API_CLIENT_SECRET=NEUFTROISQUART_API_CLIENT_SECRET:latest" \

  --port 8080
 
echo "Deployment complete."
 