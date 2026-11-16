# Roamly — AI Travel Buddy Prototype

A zero-dependency Python travel-planning prototype with a redesigned planner and an early travel-social experience.

## Run on Windows 11

1. Extract the ZIP.
2. Open PowerShell in the `travel-buddy` folder.
3. Run:

```powershell
python server.py
```

4. Open <http://localhost:8000>.

Requires Python 3.9 or later. No Python packages are required.

## Product experience

### 1. Discover
- Destination inspiration and shortcuts into trip planning.
- Preview of community trip invitations.

### 2. AI Planner
- Natural-language trip requests with optional form overrides.
- Day-by-day itinerary, activity map, estimated budget, and typical best-season guidance.
- Conversational refinement and activity removal.
- Saved trips persist in `data/trips.json`.
- Rule-based planner works without an API key.

### 3. Travel Communities
- Create a traveler profile.
- Publish a trip invitation with destination, date, duration, group capacity, and trip vibe.
- Browse and join group trips.
- Community data persists in `data/social.json`.

### 4. Find Buddies
- Six built-in demo traveler cards appear immediately, even before profile setup.
- Demo cards include sample portraits, destinations, interests, budgets, and travel styles.
- Demo likes and passes are stored locally in the browser; selected sample profiles show a clearly labelled simulated mutual match.
- Discover other real profiles on the same server after creating a traveler profile.
- Like or pass on profiles.
- A mutual like creates a match.
- Matching is based on explicit swipes; destination and interests are displayed for user comparison.

### 5. Group Trip Space — Shared Budget + Photo Vault
- Each joined trip has a dedicated group space.
- Add shared expenses with a description and amount.
- Expenses are divided equally across current group members.
- See total spend, each member's contribution, and net balance.
- Upload JPG, PNG, and WebP photos (maximum 5 MB each).
- Group photos are stored on the server and served only after a group-membership check.
- Each group is limited to 100 photos in this prototype.

### 6. My Trips and Profile
- Reopen and delete saved itineraries.
- See joined communities and mutual matches.
- Edit travel interests, preferred destinations, budget style, and pace.

## Optional Claude integration

The Claude API integration is optional. Without `ANTHROPIC_API_KEY`, trip creation and chat use the deterministic rule-based planner.

PowerShell example:

```powershell
$env:ANTHROPIC_API_KEY = "your-api-key"
$env:ANTHROPIC_MODEL = "your-supported-model-id"
python server.py
```

Never commit an API key or share it in screenshots. The live Claude path requires an API key and internet access; it has not been verified in this prototype environment.

## Tests

Run the backend regression suite:

```powershell
python test.py
```

The backend regression suite currently covers 31 checks, including:
- Existing itinerary and AI-fallback workflows
- Profile creation, group creation, and joining
- Mutual swipe matching
- Equal expense splitting and non-member denial
- Group photo upload, member retrieval, and non-member denial
- Persistence across server restart

## Important prototype limitations

- **Prototype-only group privacy:** group-space APIs check membership, but membership relies on a browser-generated `X-User-ID`. Users can spoof this ID. This is not secure authentication.
- **Do not upload sensitive photos:** production privacy requires verified login, secure sessions, authorization, HTTPS, private object storage, upload scanning, and audit controls.
- **Not production-ready for strangers:** no identity verification, moderation, reporting, blocking, or abuse prevention.
- **No private messaging:** a mutual match is recorded, but there is no chat or contact exchange.
- **Same-server community only:** profiles and groups are visible only to users connecting to this running server. This is not a deployed public network.
- **No real-time notifications:** refresh the community view to see new posts and matches.
- **No live availability or bookings:** activity data, costs, coordinates, and climate descriptions are approximate.
- **Map requires internet:** Leaflet and OpenStreetMap tiles load externally.
- **AI availability:** without a configured API key, the planner is deterministic. Do not describe rule-based output as live LLM output.
- **Destination catalogue:** Goa, Jaipur, Munnar, Rishikesh, and Hampi, with eight curated activities each.

## Architecture

- Python standard library HTTP server
- One HTML frontend with CSS and JavaScript
- JSON persistence: `data/trips.json` and `data/social.json`
- Group photo files: `data/group_photos/<group-id>/`
- Existing itinerary endpoints under `/api/trips`
- Social, group-space, expense, and photo endpoints under `/api/social`
- Optional Anthropic Messages API integration with deterministic fallback

This is a demonstration prototype, not a production travel marketplace or a verified travel-safety service.
