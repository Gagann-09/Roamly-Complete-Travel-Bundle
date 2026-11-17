import json, os, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error
from server import check

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def main():
    port = free_port()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "PORT": str(port), "DATA_FILE": td + "/trips.json",
               "SOCIAL_FILE": td + "/social.json", "ANTHROPIC_API_KEY": "", "ROAMLY_TEST_MODE": "1"}
        server = subprocess.Popen([sys.executable, "server.py"], cwd=os.path.dirname(__file__), env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f"http://127.0.0.1:{port}"
        def call(method, path, body=None, uid="u1"):
            headers = {"Content-Type": "application/json"}
            if uid: headers["X-User-ID"] = uid
            req = urllib.request.Request(base + path, json.dumps(body).encode() if body is not None else None,
                                         headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=3) as response:
                    return response.status, json.loads(response.read())
            except urllib.error.HTTPError as error:
                return error.code, json.loads(error.read())
        def ok(condition, name):
            print(("PASS " if condition else "FAIL ") + name, flush=True)
            if not condition: raise AssertionError(name)
        try:
            ready = False
            for _ in range(40):
                if server.poll() is not None: raise RuntimeError("Server exited during startup.")
                try: call("GET", "/api/health"); ready = True; break
                except Exception: time.sleep(.15)
            if not ready: raise RuntimeError("Server did not become ready.")
            ok(call("GET", "/api/health")[1]["ai_configured"] is False, "health, AI not configured")
            try: check([[0], [1]], "goa", expected_days=3); wrong_days = False
            except ValueError: wrong_days = True
            ok(wrong_days, "AI validation rejects wrong requested day count")
            try: check([[True]], "goa"); bool_index = False
            except ValueError: bool_index = True
            ok(bool_index, "AI validation rejects boolean activity indices")
            c, trip = call("POST", "/api/trips", {"prompt": "4 day relaxed foodie trip to Goa for 3 people on a budget"})
            ok(c == 201 and len(trip["days"]) == 4 and trip["travelers"] == 3 and trip["tier"] == "budget" and trip["pace"] == "relaxed" and trip["engine"] == "rules", "NL prompt parsed and trip created")
            ok(all(len(day["items"]) == 2 for day in trip["days"]) and trip["budget"]["total"] > 0, "relaxed pace and budget computed")
            ok(call("POST", "/api/trips", {"prompt": "trip to Paris"})[0] == 422, "unknown destination rejected")
            ok(call("POST", "/api/trips", {"destination": "goa", "days": 99})[0] == 422, "days out of range rejected")
            ok(call("POST", "/api/trips", {"destination": "goa", "interests": ["x"]})[0] == 422, "bad interest rejected")
            tid = trip["id"]; before = trip["budget"]["total"]
            ok(call("GET", "/api/trips", uid="u2")[1] == [], "trips isolated to authenticated account")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "add a day"})
            ok(len(t["days"]) == 5, "chat adds a day")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "remove day 1"})
            ok(len(t["days"]) == 4, "chat removes a day")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "more adventure"})
            ok(any(x["cat"] == "adventure" for d in t["days"] for x in d["items"]), "chat adds requested interest")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "upgrade to luxury"})
            ok(t["tier"] == "mid" and t["budget"]["total"] > before, "upgrade changes one budget tier")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "make it cheaper"})
            ok(t["tier"] == "budget", "cheaper lowers budget tier")
            _, t = call("POST", f"/api/trips/{tid}/chat", {"message": "blah"})
            ok("could not map" in t["messages"][-1]["text"], "unknown chat request reported honestly")
            count = len(t["days"][0]["items"])
            _, t = call("DELETE", f"/api/trips/{tid}/days/0/items/0")
            ok(len(t["days"][0]["items"]) == count - 1, "activity removal endpoint")
            ok(call("POST", f"/api/trips/{tid}/chat", {"message": ""})[0] == 422, "empty chat rejected")
            ok(call("GET", "/api/trips/nope")[0] == 404, "missing trip returns 404")
            # Community profile, group creation/join, and mutual swipe.
            ok(call("POST", "/api/social/profile", {"name": "Asha", "home": "Bengaluru", "interests": ["food"], "destinations": ["goa"]}, "u1")[0] == 200, "traveler profile creation")
            ok(call("POST", "/api/social/profile", {"name": "Ravi", "home": "Mysuru", "interests": ["food"], "destinations": ["goa"]}, "u2")[0] == 200, "second traveler profile creation")
            ok(call("POST", "/api/social/groups", {"destination": "goa", "date": "2000-01-01", "days": 3, "capacity": 4}, "u1")[0] == 422, "past group-trip date rejected")
            c, snap = call("POST", "/api/social/groups", {"destination": "goa", "date": "2026-12-10", "days": 3, "capacity": 4, "title": "Goa food crawl"}, "u1")
            gid = snap["groups"][0]["id"]
            ok(c == 201 and len(snap["groups"]) == 1, "community trip creation")
            c, joined = call("POST", f"/api/social/groups/{gid}/join", {}, "u2")
            ok(c == 200 and len(joined["groups"][0]["members"]) == 2, "traveler joins community trip")
            ok(call("POST", f"/api/social/groups/{gid}/photos", {"name": "disabled.png"})[0] == 404, "group photo storage endpoint is disabled")
            ok(call("GET", f"/api/social/groups/{gid}/space", uid="u3")[0] == 403, "non-member cannot access group space")
            c, expense = call("POST", f"/api/social/groups/{gid}/expenses", {"title": "Hotel", "amount": 1200}, "u1")
            ok(c == 201 and expense["expense"]["amount"] == 1200, "group member adds shared expense")
            space = call("GET", f"/api/social/groups/{gid}/space", uid="u2")[1]
            ok(space["total"] == 1200 and len(space["balances"]) == 2 and space["balances"][0]["share"] == 600, "expense split equally across group members")
            ok(call("POST", f"/api/social/groups/{gid}/expenses", {"title": "Unauthorized", "amount": 99}, "u3")[0] == 403, "non-member cannot add expenses")
            ok(call("GET", f"/api/social/groups/{gid}/space", uid="u3")[0] == 403, "non-member cannot access group space")
            call("POST", "/api/social/swipe", {"target_id": "u2", "direction": "like"}, "u1")
            c, matched = call("POST", "/api/social/swipe", {"target_id": "u1", "direction": "like"}, "u2")
            ok(c == 200 and matched["matched"], "mutual swipe creates a match")
            # Verify trip persistence after server restart.
            server.terminate(); server.wait(timeout=3)
            server = subprocess.Popen([sys.executable, "server.py"], cwd=os.path.dirname(__file__), env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ready = False
            for _ in range(40):
                if server.poll() is not None: raise RuntimeError("Server failed to restart.")
                try: call("GET", "/api/health"); ready = True; break
                except Exception: time.sleep(.15)
            if not ready: raise RuntimeError("Restarted server did not become ready.")
            ok(call("GET", f"/api/trips/{tid}")[1]["days"] == t["days"], "trip survives server restart")
            ok(call("DELETE", f"/api/trips/{tid}")[0] == 200 and call("GET", "/api/trips")[1] == [], "trip deletion")
            print("ALL CHECKS PASSED", flush=True)
        finally:
            if server.poll() is None:
                server.terminate()
                try: server.wait(timeout=3)
                except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()
