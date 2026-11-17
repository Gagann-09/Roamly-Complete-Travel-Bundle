# Roamly Buddy 2.3.2 — Authenticated Explore Prototype

## What's included

- Responsive React + TypeScript landing, Firebase authentication, and traveller onboarding.
- Google and email/password authentication, email verification, and password reset.
- Traveller profile stored in Firestore under the signed-in Firebase UID.
- A clear **Explore Roamly** action after profile completion.
- Explore workspace connected to that Firebase account:
  - AI trip planner with day-wise itinerary, budget estimates, map, and conversational edits.
  - Community trip discovery, group creation, and joining.
  - Travel-buddy discovery with like/pass and mutual matching.
  - Members-only group spaces with shared expense entry and equal split calculations.
  - My trips, joined communities, and mutual matches.
- Group photo upload/storage is intentionally disabled and postponed.
- Trip records are scoped to their authenticated Firebase UID.
- Backend verifies Firebase ID tokens using Firebase Admin SDK.

## Firebase project

The configured project is `roamly-production-40a79`, in `asia-south1` (Mumbai). Keep Firestore on the default database. No additional database is required.

### Web configuration

In `web/.env.local`, use the Firebase Web App configuration from Firebase Console → Project settings → General → Your apps. Copy `.env.example` and fill in the values. Never put a service-account JSON or private key in this file.

### Authentication

Enable Email/Password and Google in Firebase Console → Authentication → Sign-in method. Apple sign-in remains optional and requires Apple Developer configuration. Ensure `localhost` is an authorised domain.

### Firestore rules

Publish the included `firestore.rules` in Firestore → Rules. The current rules allow each user to read and write only their own `/users/{uid}` profile. Other Firestore collections remain denied; the prototype's trip/community data is stored by the local Python backend.

### Backend token verification

The Python API verifies Firebase ID tokens. Install its dependency:

```powershell
# From the project root
py -m pip install -r requirements.txt
```

Create a Firebase service-account credential in Firebase Console → Project settings → Service accounts. Store the downloaded JSON **outside this project folder**. Then set Application Default Credentials in the PowerShell window used to run the backend:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\secure\roamly-firebase-admin.json"
$env:FIREBASE_PROJECT_ID="roamly-production-40a79"
py server.py
```

Do not commit or share the service-account file. Do not enable `ROAMLY_TEST_MODE` outside automated tests.

## Run locally

Use two PowerShell terminals.

**Terminal 1 — backend**, from the project root:

```powershell
py -m pip install -r requirements.txt
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\secure\roamly-firebase-admin.json"
$env:FIREBASE_PROJECT_ID="roamly-production-40a79"
py server.py
```

**Terminal 2 — frontend:**

```powershell
cd web
npm install
Copy-Item .env.example .env.local
# Fill web/.env.local with your Firebase Web App values.
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`. Vite proxies `/api` requests to the local Python API on port 8000. Sign in, complete the profile, and select **Explore Roamly**.

## Test

From the project root:

```powershell
py -m pip install -r requirements.txt
py test.py
```

The automated test suite uses a test-only identity stub. The running application does not. Do not set `ROAMLY_TEST_MODE=1` in a real run.

Frontend production build:

```powershell
cd web
npm run build
```

## Important prototype boundaries

- The Python backend stores trips, community profiles, groups, swipes, and expenses in local JSON files. Back up `data/` before replacing the local environment.
- Firebase Authentication tokens are verified server-side. Trip records are scoped to their owner. Group-space and expense endpoints check membership.
- The prototype does not yet provide managed cloud hosting, cross-device database persistence for trip/community data, moderation, reporting/blocking, private messaging, or real-time notifications.
- Group photo upload and storage are removed from this version. No photo bytes are accepted or persisted.
- The rule-based itinerary planner works without an AI key. Claude enhancement remains optional through `ANTHROPIC_API_KEY`.
- Map tiles require an internet connection. Estimated budgets and activity details are prototype estimates, not live quotes.
- Do not expose the Python server publicly until deployment hardening, rate limiting, monitoring, and a full security review are completed.

## Security files

- `firestore.rules` protects per-user profile documents.
- `web/.env.local` and service-account credentials must remain local and untracked.
- The ZIP intentionally excludes `.env.local`, `node_modules`, `.git`, generated data, and Python caches.
