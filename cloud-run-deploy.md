# Cloud Run Deployment Guide

## Prerequisites
- Google Cloud SDK installed and configured
- Docker installed (for local testing)
- A Google Cloud project with Cloud Run API enabled

## Building the Docker Image

### Local Build (for testing)
```bash
docker build -t joke-api .
docker run -p 8080:8080 \
  -e FIREBASE_CREDENTIALS_PATH=/app/firebase-service-account.json \
  -e FIREBASE_STORAGE_BUCKET=your-bucket-name \
  -v $(pwd)/firebase-service-account.json:/app/firebase-service-account.json \
  joke-api
```

### Build and Push to Google Container Registry
```bash
# Set your project ID
export PROJECT_ID=your-project-id
export SERVICE_NAME=joke-api
export REGION=us-central1

# Build and push the image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}
```

## Deploying to Cloud Run

### Option 1: Using Application Default Credentials (Recommended)
If your Cloud Run service account has the necessary Firebase permissions, you can use Application Default Credentials:

```bash
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_STORAGE_BUCKET=your-bucket-name \
  --service-account your-service-account@your-project.iam.gserviceaccount.com
```

### Option 2: Using Service Account JSON File
If you need to use a specific service account JSON file:

1. **Create a Secret in Secret Manager:**
```bash
gcloud secrets create firebase-service-account \
  --data-file=firebase-service-account.json
```

2. **Deploy with Secret:**
```bash
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_STORAGE_BUCKET=your-bucket-name \
  --set-secrets FIREBASE_CREDENTIALS_PATH=firebase-service-account:latest \
  --update-secrets FIREBASE_CREDENTIALS_PATH=/app/firebase-service-account.json
```

### Option 3: Using Environment Variable (Base64 Encoded)
You can also provide the service account JSON as a base64-encoded environment variable:

```bash
# Encode the service account file
export FIREBASE_CREDENTIALS_B64=$(cat firebase-service-account.json | base64)

# Deploy
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_STORAGE_BUCKET=your-bucket-name \
  --set-env-vars FIREBASE_CREDENTIALS_B64=${FIREBASE_CREDENTIALS_B64}
```

Then update `firebase/firebase_init.py` to decode it if needed.

## Environment Variables

Required environment variables:
- `FIREBASE_STORAGE_BUCKET`: Your Firebase storage bucket name (e.g., `sixseven-7f96d.firebasestorage.app`)
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase service account JSON file (if using file-based auth)

Optional:
- `PORT`: Port to listen on (Cloud Run sets this automatically, default: 8080)

## Notes

- Cloud Run automatically sets the `PORT` environment variable
- The app listens on `0.0.0.0` to accept connections from Cloud Run
- For production, consider:
  - Setting `--min-instances=1` to avoid cold starts
  - Adjusting `--max-instances` based on traffic
  - Using `--cpu` and `--memory` flags to optimize performance
  - Setting up proper CORS origins instead of `allow_origins=["*"]`

## Example Full Deployment Command

```bash
gcloud run deploy joke-api \
  --image gcr.io/${PROJECT_ID}/joke-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_STORAGE_BUCKET=sixseven-7f96d.firebasestorage.app \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300
```

