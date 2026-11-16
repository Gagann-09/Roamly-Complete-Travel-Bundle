# Roamly Buddy 2.3.1 — Phase 1 Foundation

### 2.3.1 patch

- Landing-page section links appear only on the public landing screen; they are hidden on login, registration, onboarding, dashboard, and profile screens.
- No authentication, Firestore data model, security rules, or page content was changed.

Roamly Buddy 2.3 adds a professional React website and Firebase-backed account/profile foundation to the existing Roamly 2.2 prototype. The original Python prototype and its trip-planning, community, buddy, expense, and photo-vault code are retained as a reference; they are not yet production-secured.

## Phase 1 scope in 2.3

- Professional responsive React + TypeScript website.
- Firebase Authentication integration for Google and email/password.
- Apple sign-in client integration is included, but the Apple provider must be configured in Firebase with Apple Developer credentials before it can work.
- Email verification and password reset.
- First-login traveller profile onboarding.
- Profile editing and account deletion.
- Firestore user documents keyed by Firebase Authentication UID.
- A restrictive Firestore rules file at `firestore.rules`.
- No hardcoded/demo people in the new Phase 1 website.
- No group-photo storage migration or Phase 2 implementation.

## Requirements

- Windows 10/11
- Node.js 20 or later (Node.js 22 LTS recommended)
- npm
- A Firebase project on the Spark plan

## Configure Firebase

The Firebase project selected for this build is `roamly-production-40a79` in `asia-south1` (Mumbai).

1. In Firebase Console, open **Project settings → General → Your apps → Roamly Web**.
2. Copy the web app configuration values. These are client configuration values, not service-account credentials.
3. In the `web` folder, copy `.env.example` to `.env.local`.
4. Fill in the actual values:

```env
VITE_FIREBASE_API_KEY=your-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=roamly-production-40a79.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=roamly-production-40a79
VITE_FIREBASE_STORAGE_BUCKET=your-value-from-firebase-config
VITE_FIREBASE_MESSAGING_SENDER_ID=your-value-from-firebase-config
VITE_FIREBASE_APP_ID=your-value-from-firebase-config
```

Do not add a Firebase Admin service-account JSON file or private key to this frontend project. Do not commit `.env.local`.

### Authentication providers

Firebase Console → Authentication → Sign-in method:

- Email/Password: enable.
- Google: enable and select the support email.
- Apple: the web OAuth client is implemented, but the provider is not enabled by this prototype setup. Apple Developer configuration (Services ID, Team ID, Key ID, private key, and return URL) is required before enabling it. Do not expect Apple login to work until those steps are completed.

Add the development hostname to Authentication → Settings → Authorized domains if Firebase does not already list it. The Vite development command uses `localhost`.

### Firestore rules

The existing initial owner-only rules were published during setup. This ZIP includes a stricter profile schema in `firestore.rules`.

Before testing profile writes, open Firestore → Rules, replace the editor contents with the contents of `firestore.rules`, and click **Publish**. These rules:

- allow a signed-in user to read only `/users/{their-own-uid}`;
- deny listing user documents;
- validate profile fields and types on create/update;
- allow a user to delete only their own profile document;
- deny every other collection by default.

No collection needs to be created manually. Firestore creates `users` when the first profile is saved.

## Run the new website

Open PowerShell in the extracted `travel-buddy` folder:

```powershell
cd web
npm install
Copy-Item .env.example .env.local
# Edit .env.local with the Firebase Web App values before starting.
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

The first screen is the professional Roamly landing page. Create an account or log in. Email/password registration sends an email verification link. After verification and sign-in, complete the three-step traveller profile. The profile is saved to Firestore under the authenticated Firebase UID.

## Existing prototype (preserved)

The previous prototype is retained at the root of this project. To run its local Python server separately:

```powershell
python server.py
```

Open `http://localhost:8000` for the original prototype. This legacy server is retained for feature reference and local testing only.

**Do not deploy the legacy Python server publicly yet.** Its API still trusts browser-generated `X-User-ID` values and has no Firebase ID-token verification or per-user trip ownership. The old social/photo APIs remain prototype-only. The new Phase 1 React website does not call those APIs.

Run the legacy regression suite from the root folder:

```powershell
python test.py
```

## What is not complete yet

- Firebase live end-to-end testing: requires the actual web configuration and browser access to the user's Firebase project.
- Apple provider: requires Apple Developer configuration and enabling the provider in Firebase.
- Production hosting and custom domain.
- Production security review, automated browser tests, monitoring, privacy policy, terms, and support contact.
- Migration of existing prototype trips/profiles into authenticated accounts.
- Phase 2 private group photo storage: explicitly not started.

## Security notes

- Firebase client configuration is not a server secret; Firestore Security Rules are the access boundary.
- The new app writes profile documents only under the authenticated Firebase UID.
- Profile documents are private to their owner in the current Phase 1 rules; public profile discovery is intentionally not enabled.
- The profile photo currently uses the Google/Apple provider photo URL when available. No photo upload/storage feature is included in Phase 1.
- Account deletion requires recent authentication. The app requests reauthentication before deleting the profile and Firebase account.
- A working build and real Firebase sign-in must be verified on the user's Windows environment after npm dependencies are installed and `.env.local` is configured.
