import json, os, re, math, uuid, time, threading, urllib.request
from datetime import date as date_cls
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from data import DEST, C, TIERS

ROOT = Path(__file__).parent
DB = Path(os.environ.get("DATA_FILE", ROOT / "data" / "trips.json"))
SOCIAL_DB = Path(os.environ.get("SOCIAL_FILE", ROOT / "data" / "social.json"))
LOCK = threading.Lock()

def social_load():
    try:
        data = json.loads(SOCIAL_DB.read_text())
        if isinstance(data, dict):
            data.setdefault("profiles", {}); data.setdefault("groups", {}); data.setdefault("swipes", {}); data.setdefault("expenses", {})
            return data
    except (FileNotFoundError, ValueError):
        pass
    return {"profiles": {}, "groups": {}, "swipes": {}, "expenses": {}}

def social_save(data):
    SOCIAL_DB.parent.mkdir(parents=True, exist_ok=True)
    tmp = SOCIAL_DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    tmp.replace(SOCIAL_DB)

def public_profile(profile):
    return {k: profile.get(k) for k in ("id", "name", "bio", "home", "interests", "destinations", "budget", "pace", "created")}

def social_snapshot(data, uid):
    profile = data["profiles"].get(uid)
    groups = sorted(data["groups"].values(), key=lambda g: -g.get("created", 0))
    visible = []
    for group in groups:
        owner = data["profiles"].get(group["owner"], {})
        visible.append({**group, "host": owner.get("name", "Traveler"), "hosted": group.get("owner") == uid, "joined": uid in group.get("members", [])})
    buddies = []
    for pid, p in data["profiles"].items():
        if pid == uid: continue
        swipe = data["swipes"].get(uid, {}).get(pid)
        if swipe == "pass": continue
        reciprocal = data["swipes"].get(pid, {}).get(uid) == "like"
        buddies.append({**public_profile(p), "liked": swipe == "like", "matched": swipe == "like" and reciprocal})
    matches = [b for b in buddies if b["matched"]]
    return {"profile": public_profile(profile) if profile else None, "groups": visible, "buddies": buddies, "matches": matches}

PACE = {"relaxed": "me", "balanced": "mae", "packed": "maae"}
TORD = ["budget", "mid", "luxury"]
KW = {"food": r"food|eat|restaurant|cuisine", "adventure": r"advent|thrill|adrenaline", "relax": r"beach|chill|spa|relax(?!ed pace)",
      "culture": r"histor|museum|cultur|heritage", "nature": r"nature|hike|trek|outdoor", "nightlife": r"night|party|club|bar"}
STOP = {"beach", "night", "walk", "tour", "ride", "lunch", "show", "hill", "falls", "visit"}

class Err(Exception):
    def __init__(s, code, msg): s.code, s.msg = code, msg

def load():
    try: return json.loads(DB.read_text())
    except (FileNotFoundError, ValueError): return {}
def save(db):
    DB.parent.mkdir(parents=True, exist_ok=True); tmp = DB.with_suffix(".tmp"); tmp.write_text(json.dumps(db)); tmp.replace(DB)

def parse(p):
    s, o = p.lower(), {}
    s = s.replace("kerala", "munnar")
    for k, d in DEST.items():
        if k in s or d["name"].lower().split(" (")[0] in s: o["destination"] = k
    if (r := re.search(r"(\d+)\s*-?\s*(?:day|night)", s)): o["days"] = int(r[1])
    if (r := re.search(r"(\d+)\s*(?:people|persons|adults|travell?ers|pax|friends)", s)): o["travelers"] = int(r[1])
    elif "couple" in s: o["travelers"] = 2
    elif re.search(r"solo|alone", s): o["travelers"] = 1
    elif "family" in s: o["travelers"] = 4
    if re.search(r"cheap|budget|backpack", s): o["tier"] = "budget"
    elif re.search(r"luxur|premium|splurge", s): o["tier"] = "luxury"
    if re.search(r"relaxed|slow|easy", s): o["pace"] = "relaxed"
    elif re.search(r"packed|busy|everything", s): o["pace"] = "packed"
    o["interests"] = [c for c, rx in KW.items() if re.search(rx, s)]
    return o

def build(dest, n, interests, pace, tier, used=None):
    acts, used, days = DEST[dest]["acts"], used if used is not None else set(), []
    def score(j):
        a = acts[j]; return (3 if a[1] in interests else 0) - (a[2] / 500 if tier == "budget" and a[2] > 1000 else 0)
    for _ in range(n):
        day = []
        for s in PACE[pace]:
            pool = [j for j in range(len(acts)) if j not in used]
            best = sorted([j for j in pool if acts[j][4] == s] or pool, key=lambda j: -score(j))
            if best: used.add(best[0]); day.append(best[0])
        day.sort(key=lambda j: "mae".index(acts[j][4])); days.append(day)
    return days

def swap(day, k, acts, used, pred):
    for j, a in enumerate(acts):
        if j not in used and pred(a): used.discard(day[k]); used.add(j); day[k] = j; return True
    return False

def edit(t, msg):
    m, acts, days, out = msg.lower(), DEST[t["dest"]]["acts"], t["days"], []
    used = {i for d in days for i in d}
    if (r := re.search(r"(?:remove|drop|delete) day (\d+)", m)) and 1 <= int(r[1]) <= len(days) and len(days) > 1:
        for i in days.pop(int(r[1]) - 1): used.discard(i)
        out.append(f"Removed day {r[1]}.")
    elif re.search(r"shorten|one less day|fewer days", m) and len(days) > 1:
        for i in days.pop(): used.discard(i)
        out.append("Removed the last day.")
    if (r := re.search(r"\badd (?:a |one |(\d) )?(?:more |extra )?days?\b|\bextend", m)) and len(days) < 7:
        k = min(int(r[1] or 1), 7 - len(days)); days += build(t["dest"], k, t["interests"], t["pace"], t["tier"], used); out.append(f"Added {k} day(s).")
    if re.search(r"cheap|budget|save|afford", m):
        if t["tier"] != "budget": t["tier"] = TORD[TORD.index(t["tier"]) - 1]; out.append(f"Switched stay and food to the {t['tier']} level.")
        n = 0
        for d in days:
            for k, i in enumerate(d):
                if acts[i][2] > 1000 and (swap(d, k, acts, used, lambda a, s=acts[i][4]: a[2] <= 1000 and a[4] == s) or swap(d, k, acts, used, lambda a: a[2] <= 1000)): n += 1
        if n: out.append(f"Replaced {n} costly activit{'y' if n == 1 else 'ies'}.")
    elif re.search(r"luxur|upgrade|premium|splurge", m) and t["tier"] != "luxury":
        t["tier"] = TORD[TORD.index(t["tier"]) + 1]; out.append(f"Upgraded stay and food to the {t['tier']} level.")
    cats = [c for c, rx in KW.items() if re.search(rx, m)] if re.search(r"more|focus|love|into|extra", m) else []
    if cats:
        t["interests"] = list(dict.fromkeys(t["interests"] + cats)); n = 0
        for d in days:
            for k, i in enumerate(d):
                if acts[i][1] not in cats and swap(d, k, acts, used, lambda a: a[1] in cats): n += 1; break
        out.append(f"Swapped in {n} {'/'.join(cats)} activit{'y' if n == 1 else 'ies'}." if n else f"No unused {'/'.join(cats)} activities are left for {DEST[t['dest']]['name']}.")
    if re.search(r"slow|relaxed pace|fewer activities|less packed|take it easy|lighter", m):
        n = 0
        for d in days:
            while len(d) > 2: used.discard(d.pop()); n += 1
        t["pace"] = "relaxed"; out.append(f"Removed {n} activities for a slower pace." if n else "The plan is already light.")
    elif re.search(r"packed|busier|more activities|squeeze", m):
        n = 0
        for d in days:
            free = [j for j in range(len(acts)) if j not in used]
            if len(d) < 4 and free: d.append(free[0]); used.add(free[0]); n += 1
        out.append(f"Added {n} activities." if n else "No unused activities are left.")
    if re.search(r"remove|skip|drop|delete|without", m):
        hit = [i for i, a in enumerate(acts) if any(w in m for w in re.findall(r"[a-z]{4,}", a[0].lower()) if w not in STOP)]
        if len(hit) == 1:
            for d in days:
                if hit[0] in d: d.remove(hit[0]); out.append(f"Removed “{acts[hit[0]][0]}”.")
    for d in days: d.sort(key=lambda j: "mae".index(acts[j][4]))
    return " ".join(out)

def ai(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key: return None
    body = {"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"), "max_tokens": 1500, "messages": [{"role": "user", "content": prompt}],
            "system": 'You are a travel planner. Reply with JSON only: {"days":[[activity_index,...],...],"reply":"short note"}. Use only indices from the catalog, each at most once, max 5 per day, 1-7 days.'}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(), {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    txt = json.load(urllib.request.urlopen(req, timeout=45))["content"][0]["text"]
    j = json.loads(re.search(r"\{.*\}", txt, re.S)[0])
    return j["days"], str(j.get("reply", ""))[:500]

def check(days, dest, expected_days=None):
    flat = [i for d in days for i in d] if isinstance(days, list) and all(isinstance(d, list) for d in days) else None
    if flat is None or not 1 <= len(days) <= 7 or any(len(d) > 5 for d in days): raise ValueError("bad shape")
    if expected_days is not None and len(days) != expected_days: raise ValueError("wrong day count")
    if any(type(i) is not int or not 0 <= i < len(DEST[dest]["acts"]) for i in flat) or len(set(flat)) != len(flat): raise ValueError("bad indices")

def catalog(dest): return "\n".join(f"{i}|{a[0]}|{a[1]}|INR {a[2]}|{a[4]}" for i, a in enumerate(DEST[dest]["acts"]))

def view(t):
    d = DEST[t["dest"]]; acts = d["acts"]; n = len(t["days"]); tv = t["travelers"]; T = TIERS[t["tier"]]
    days = [{"n": k + 1, "items": [dict(zip(("name", "cat", "cost", "hrs", "slot", "lat", "lng", "desc"), acts[i]), idx=i) for i in day]} for k, day in enumerate(t["days"])]
    b = {"stay": round(T["stay"] * d["mult"] * math.ceil(tv / 2) * max(n - 1, 1)), "food": round(T["food"] * d["mult"] * tv * n),
         "move": round(T["move"] * d["mult"] * n), "acts": sum(acts[i][2] for day in t["days"] for i in day) * tv}
    b["total"] = sum(b.values()); b["per_person"] = round(b["total"] / tv)
    return {**{k: t[k] for k in ("id", "dest", "travelers", "tier", "pace", "interests", "engine", "messages", "created")},
            "title": f"{n} day{'s' if n > 1 else ''} in {d['name']}", "name": d["name"], "best": d["best"], "climate": d["climate"], "center": [d["lat"], d["lng"]], "days": days, "budget": b}

def create(p):
    parsed = parse(str(p.get("prompt") or "")[:500])
    g = lambda k, dflt: p.get(k) if p.get(k) not in (None, "") else parsed.get(k, dflt)
    dest = g("destination", None)
    if dest not in DEST: raise Err(422, "I could not find a destination. Name one of: " + ", ".join(d["name"] for d in DEST.values()) + ".")
    try: n, tv = int(g("days", 3)), int(g("travelers", 2))
    except (TypeError, ValueError): raise Err(422, "Days and travelers must be numbers.")
    if not 1 <= n <= 7: raise Err(422, "Days must be between 1 and 7.")
    if not 1 <= tv <= 10: raise Err(422, "Travelers must be between 1 and 10.")
    tier, pace, ints = g("tier", "mid"), g("pace", "balanced"), g("interests", []) or []
    if tier not in TIERS or pace not in PACE: raise Err(422, "Invalid budget level or pace.")
    if not isinstance(ints, list) or any(i not in C for i in ints): raise Err(422, "Invalid interests.")
    t = {"id": uuid.uuid4().hex[:10], "dest": dest, "travelers": tv, "tier": tier, "pace": pace, "interests": ints, "created": int(time.time()), "messages": [], "engine": "rules"}
    note = "Built with the rule-based planner."
    try:
        r = ai(f"Plan {n} days in {DEST[dest]['name']} for {tv} travelers, {tier} budget, {pace} pace, interests: {ints}. Request: {p.get('prompt','')}\nCatalog (index|name|category|cost|slot):\n{catalog(dest)}")
        if r: check(r[0], dest, n); t["days"], t["engine"], note = r[0], "claude", r[1] or "Planned with Claude."
    except Exception as e: note = f"AI unavailable ({type(e).__name__}); used the rule-based planner."
    if "days" not in t: t["days"] = build(dest, n, ints, pace, tier)
    t["messages"].append({"role": "assistant", "text": note + " Ask me to change anything."})
    return t

def chat(t, msg):
    t["messages"].append({"role": "user", "text": msg}); done = None
    try:
        r = ai(f"Current plan (day lists of indices): {json.dumps(t['days'])}\nDestination {DEST[t['dest']]['name']}. User request: {msg}\nCatalog:\n{catalog(t['dest'])}")
        if r: check(r[0], t["dest"]); t["days"], t["engine"], done = r[0], "claude", r[1] or "Updated."
    except Exception as e: done = None; t["engine"] = "rules"; t["messages"].append({"role": "assistant", "text": f"AI unavailable ({type(e).__name__}); using rules."})
    if done is None:
        t["engine"] = "rules"
        done = edit(t, msg) or "I could not map that to a change. Try: “add a day”, “make it cheaper”, “more food”, “slow it down”, “remove day 2”, or “remove the jeep safari”."
    t["messages"].append({"role": "assistant", "text": done})

class H(BaseHTTPRequestHandler):
    def out(s, code, obj, ct="application/json"):
        b = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        s.send_response(code); s.send_header("Content-Type", ct); s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
    def auth_uid(s):
        if os.environ.get("ROAMLY_TEST_MODE") == "1":
            return s.headers.get("X-User-ID", "")[:128]
        header = s.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise Err(401, "Sign in to Roamly to continue.")
        try:
            import firebase_admin
            from firebase_admin import auth as firebase_auth
            if not firebase_admin._apps:
                try:
                    firebase_admin.initialize_app(options={"projectId": os.environ.get("FIREBASE_PROJECT_ID", "roamly-production-40a79")})
                except Exception:
                    raise Err(503, "Configure GOOGLE_APPLICATION_CREDENTIALS for Firebase Admin before using Explore.")
            try:
                claims = firebase_auth.verify_id_token(header[7:].strip(), check_revoked=True)
                return str(claims["uid"])
            except Exception:
                raise Err(401, "Your sign-in token is invalid or expired. Sign in again.")
        except ImportError:
            raise Err(503, "Install requirements.txt to enable Firebase token verification.")
    def body(s):
        n = int(s.headers.get("Content-Length") or 0)
        if n > 8_000_000: raise Err(413, "Upload too large. Maximum request size is 8 MB.")
        try: j = json.loads(s.rfile.read(n) or b"{}")
        except ValueError: raise Err(400, "Invalid JSON.")
        if not isinstance(j, dict): raise Err(400, "Body must be a JSON object.")
        return j
    def route(s, meth):
        path = s.path.split("?")[0].rstrip("/") or "/"
        try:
            if meth == "GET" and path == "/": return s.out(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            if meth == "GET" and path == "/api/health": return s.out(200, {"ok": True, "ai_configured": bool(os.environ.get("ANTHROPIC_API_KEY"))})
            if meth == "GET" and path == "/api/destinations": return s.out(200, {"destinations": [{"id": k, "name": d["name"], "best": d["best"]} for k, d in DEST.items()], "interests": list(C)})
            uid = s.auth_uid()
            with LOCK:
                db = load()
                if path == "/api/trips":
                    if meth == "GET": return s.out(200, sorted((view(t) for t in db.values() if t.get("owner_uid") == uid), key=lambda v: -v["created"]))
                    if meth == "POST": t = create(s.body()); t["owner_uid"] = uid; db[t["id"]] = t; save(db); return s.out(201, view(t))
                if (m := re.fullmatch(r"/api/trips/([\w-]+)", path)):
                    t = db.get(m[1])
                    if not t or t.get("owner_uid") != uid: raise Err(404, "Trip not found.")
                    if meth == "GET": return s.out(200, view(t))
                    if meth == "DELETE": del db[m[1]]; save(db); return s.out(200, {"deleted": m[1]})
                if (m := re.fullmatch(r"/api/trips/([\w-]+)/chat", path)) and meth == "POST":
                    t = db.get(m[1]); msg = str(s.body().get("message", "")).strip()
                    if not t or t.get("owner_uid") != uid: raise Err(404, "Trip not found.")
                    if not 1 <= len(msg) <= 500: raise Err(422, "Message must be 1 to 500 characters.")
                    chat(t, msg); save(db); return s.out(200, view(t))
                if (m := re.fullmatch(r"/api/trips/([\w-]+)/days/(\d+)/items/(\d+)", path)) and meth == "DELETE":
                    t = db.get(m[1])
                    if not t or t.get("owner_uid") != uid: raise Err(404, "Trip not found.")
                    d, i = int(m[2]), int(m[3])
                    if d >= len(t["days"]) or i >= len(t["days"][d]): raise Err(404, "Activity not found.")
                    t["days"][d].pop(i); save(db); return s.out(200, view(t))
            # Authenticated community APIs; Firebase ID tokens are verified server-side.
            if path == "/api/social" and meth == "GET":
                
                return s.out(200, social_snapshot(social_load(), uid))
            # Group spaces: membership is checked on every request.
            if (m := re.fullmatch(r"/api/social/groups/([\w-]+)/space", path)) and meth == "GET":
                data = social_load(); group = data["groups"].get(m[1])
                if not group: raise Err(404, "Trip group not found.")
                if uid not in group.get("members", []): raise Err(403, "Only trip members can open this group space.")
                members = [{"id": mid, "name": data["profiles"].get(mid, {}).get("name", "Traveler")} for mid in group["members"]]
                expenses = data["expenses"].get(m[1], [])
                paid = {mid: 0 for mid in group["members"]}
                for expense in expenses:
                    if expense["payer_id"] in paid: paid[expense["payer_id"]] += expense["amount"]
                total = sum(x["amount"] for x in expenses); share = total / max(len(members), 1)
                balances = [{"id": mid, "name": data["profiles"].get(mid, {}).get("name", "Traveler"), "paid": round(paid[mid], 2), "share": round(share, 2), "balance": round(paid[mid]-share, 2)} for mid in group["members"]]
                return s.out(200, {"group": {"id": group["id"], "title": group["title"], "destination_name": group["destination_name"], "date": group["date"], "members": members}, "expenses": expenses, "total": round(total, 2), "balances": balances})
            if (m := re.fullmatch(r"/api/social/groups/([\w-]+)/expenses", path)) and meth == "POST":
                data = social_load(); group = data["groups"].get(m[1])
                if not group: raise Err(404, "Trip group not found.")
                if uid not in group.get("members", []): raise Err(403, "Only trip members can add expenses.")
                body = s.body(); title = str(body.get("title", "")).strip()[:80]
                try: amount = round(float(body.get("amount")), 2)
                except (TypeError, ValueError): raise Err(422, "Enter a valid expense amount.")
                if not title or not math.isfinite(amount) or not 0 < amount <= 10_000_000: raise Err(422, "Enter a description and an amount above ₹0.")
                expense = {"id": uuid.uuid4().hex[:10], "title": title, "amount": amount, "payer_id": uid, "payer": data["profiles"].get(uid, {}).get("name", "Traveler"), "created": int(time.time())}
                data["expenses"].setdefault(m[1], []).append(expense); social_save(data)
                return s.out(201, {"expense": expense})
            if path == "/api/social/profile" and meth == "POST":
                body = s.body(); 
                name = str(body.get("name", "")).strip()[:40]
                if not uid or len(name) < 2: raise Err(422, "Add a name with at least 2 characters.")
                interests = body.get("interests", [])
                destinations = body.get("destinations", [])
                allowed_dest = set(DEST)
                if not isinstance(interests, list) or any(x not in C for x in interests): raise Err(422, "Choose valid interests.")
                if not isinstance(destinations, list) or any(x not in allowed_dest for x in destinations): raise Err(422, "Choose valid destinations.")
                data = social_load()
                old = data["profiles"].get(uid, {})
                data["profiles"][uid] = {"id": uid, "name": name, "bio": str(body.get("bio", "")).strip()[:240],
                    "home": str(body.get("home", "")).strip()[:60], "interests": interests[:6], "destinations": destinations[:5],
                    "budget": body.get("budget", "mid") if body.get("budget") in TIERS else "mid",
                    "pace": body.get("pace", "balanced") if body.get("pace") in PACE else "balanced",
                    "created": old.get("created", int(time.time()))}
                social_save(data); return s.out(200, social_snapshot(data, uid))
            if path == "/api/social/groups" and meth == "POST":
                body = s.body(); data = social_load()
                profile = data["profiles"].get(uid)
                if not profile: raise Err(403, "Create your traveler profile first.")
                dest = body.get("destination")
                try: days = int(body.get("days", 3)); capacity = int(body.get("capacity", 6))
                except (TypeError, ValueError): raise Err(422, "Days and group size must be numbers.")
                date = str(body.get("date", "")).strip()[:20]
                try:
                    start_date = date_cls.fromisoformat(date)
                except (TypeError, ValueError):
                    raise Err(422, "Enter a valid trip start date.")
                if dest not in DEST or not 1 <= days <= 7 or not 2 <= capacity <= 12 or start_date < date_cls.today():
                    raise Err(422, "Choose a destination, a future date, 1–7 days, and group size of 2–12.")
                gid = uuid.uuid4().hex[:10]
                group = {"id": gid, "owner": uid, "destination": dest, "destination_name": DEST[dest]["name"],
                    "date": date, "days": days, "capacity": capacity, "title": str(body.get("title", "")).strip()[:80] or f"{days} days in {DEST[dest]['name']}",
                    "description": str(body.get("description", "")).strip()[:240], "vibe": str(body.get("vibe", "balanced"))[:30],
                    "members": [uid], "created": int(time.time())}
                data["groups"][gid] = group; social_save(data); return s.out(201, social_snapshot(data, uid))
            if (m := re.fullmatch(r"/api/social/groups/([\w-]+)/join", path)) and meth == "POST":
                data = social_load(); group = data["groups"].get(m[1])
                if not data["profiles"].get(uid): raise Err(403, "Create your traveler profile first.")
                if not group: raise Err(404, "Trip group not found.")
                if uid == group["owner"]: raise Err(422, "You already host this trip.")
                if uid not in group["members"]:
                    if len(group["members"]) >= group["capacity"]: raise Err(409, "This trip group is full.")
                    group["members"].append(uid); social_save(data)
                return s.out(200, social_snapshot(data, uid))
            if path == "/api/social/swipe" and meth == "POST":
                body = s.body(); 
                target = str(body.get("target_id", ""))[:80]; direction = body.get("direction")
                data = social_load()
                if not data["profiles"].get(uid): raise Err(403, "Create your traveler profile first.")
                if target == uid or target not in data["profiles"]: raise Err(404, "Traveler not found.")
                if direction not in ("like", "pass"): raise Err(422, "Swipe must be like or pass.")
                data["swipes"].setdefault(uid, {})[target] = direction
                social_save(data)
                snap = social_snapshot(data, uid)
                match = next((x for x in snap["matches"] if x["id"] == target), None)
                return s.out(200, {"matched": bool(match), "snapshot": snap})
            raise Err(404, "Not found.")
        except Err as e: s.out(e.code, {"error": e.msg})
        except Exception as e: print("ERROR", repr(e)); s.out(500, {"error": "Internal server error."})
    do_GET = lambda s: s.route("GET"); do_POST = lambda s: s.route("POST"); do_DELETE = lambda s: s.route("DELETE")
    def log_message(s, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Travel Buddy on http://localhost:{port}  (AI: {'Claude' if os.environ.get('ANTHROPIC_API_KEY') else 'rule-based fallback'})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
