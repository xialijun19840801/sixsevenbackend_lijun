# Joke API - FastAPI with Firebase

A FastAPI backend service with a web UI for testing. Users can login with Firebase, add jokes (with setup and punchline), and unauthenticated users can view all jokes. Uses Firebase Firestore for storage.

## Features

- ✅ FastAPI REST API backend
- ✅ Firebase Authentication (Email/Password)
- ✅ Firebase Firestore for data storage
- ✅ Web UI for testing APIs
- ✅ Authenticated users can add jokes
- ✅ Unauthenticated users can view all jokes

## Project Structure

```
sixsevenbackend_lijun/
├── main.py                 # FastAPI application entry point
├── routes.py               # API route definitions
├── models.py               # Pydantic models
├── firebase_service.py     # Firestore service layer
├── firebase/
│   ├── __init__.py
│   ├── config.py          # Firebase configuration
│   ├── firebase_init.py    # Firebase initialization
│   └── auth.py            # Authentication middleware
├── static/
│   ├── index.html         # Web UI
│   ├── app.js             # Frontend JavaScript
│   └── styles.css         # Styles
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication:
   - Go to **Authentication** > **Get started**
   - Enable **Email/Password** sign-in method
3. Create Firestore Database:
   - Go to **Firestore Database** > **Create database**
   - Start in **test mode** (for development)
4. Download Service Account Key:
   - Go to **Project Settings** > **Service Accounts**
   - Click **Generate new private key**
   - Save the JSON file as `firebase-service-account.json` in the project root

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### 4. Update Firebase Config in Frontend

Edit `static/index.html` and update the Firebase config object with your project's configuration:

```javascript
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};
```

### 5. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at:
- API: `http://localhost:8000`
- Web UI: `http://localhost:8000/static/index.html`
- API Docs: `http://localhost:8000/docs`

## API Endpoints

### POST /api/login

Verify Firebase ID token and return user information.

**Request Body:**
```json
{
  "token": "firebase_id_token"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user_id": "user_id",
  "user_email": "user@example.com"
}
```

### POST /api/jokes

Add a new joke (requires authentication).

**Headers:**
```
Authorization: Bearer <firebase_id_token>
```

**Request Body:**
```json
{
  "setup": "Why did the chicken cross the road?",
  "punchline": "To get to the other side!"
}
```

**Response:**
```json
{
  "joke_id": "joke_id",
  "setup": "Why did the chicken cross the road?",
  "punchline": "To get to the other side!",
  "user_id": "user_id",
  "user_email": "user@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/jokes

Get all jokes (no authentication required).

**Response:**
```json
{
  "jokes": [
    {
      "joke_id": "joke_id",
      "setup": "Why did the chicken cross the road?",
      "punchline": "To get to the other side!",
      "user_id": "user_id",
      "user_email": "user@example.com",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

## Using the Web UI

1. Open `http://localhost:8000/static/index.html` in your browser
2. **Register/Login**: Use the login form to create an account or sign in
3. **Add Jokes**: Once logged in, you can add jokes using the form
4. **View Jokes**: All jokes are displayed below (works even when not logged in)
5. **Refresh**: Click the "Refresh" button to reload the jokes list

## Firestore Data Structure

### jokes Collection

Each document contains:
- `setup` (string): The joke setup
- `punchline` (string): The joke punchline
- `user_id` (string): Firebase user ID
- `user_email` (string): User's email
- `created_at` (timestamp): Creation timestamp

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing with curl

**Login:**
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"token": "your_firebase_id_token"}'
```

**Add Joke:**
```bash
curl -X POST http://localhost:8000/api/jokes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_firebase_id_token" \
  -d '{"setup": "Test setup", "punchline": "Test punchline"}'
```

**Get All Jokes:**
```bash
curl http://localhost:8000/api/jokes
```

## Security Notes

- Keep your `firebase-service-account.json` file secure and never commit it to version control
- Configure CORS origins appropriately for production
- Set up proper Firestore security rules for production
- Consider adding rate limiting for production use

## License

MIT License

