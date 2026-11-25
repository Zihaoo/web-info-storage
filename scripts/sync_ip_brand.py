import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1] / "data/ip-brand-news"
site = "https://ip-brand-daily-radar.dazzlingfir5.chatgpt.site"
def api(route, method="GET"):
    with urlopen(Request(site + "/api/" + route, method=method), timeout=60) as response:
        return json.load(response)
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"))+"\n")
if os.environ.get("INITIAL_FEED"):
    feed = json.loads(Path(os.environ["INITIAL_FEED"]).read_text())
else:
    api("refresh", "POST")
    for _ in range(10):
        if not api("translate", "POST").get("translated"):
            break
    feed = api("feed")
if not feed.get("articles") or not isinstance(feed.get("health"), list):
    raise ValueError("Invalid feed")
latest = root / "latest.json"
old = json.loads(latest.read_text())["articles"] if latest.exists() else []
by_url = {a["url"]: a for a in old}
changed = []
for a in feed["articles"]:
    if a != by_url.get(a["url"]):
        changed.append(a)
    by_url[a["url"]] = a
now = datetime.now(timezone(timedelta(hours=8)))
stamp = now.isoformat(timespec="seconds")
daily = root / "daily" / (now.date().isoformat() + ".json")
delta = {a["url"]:a for a in json.loads(daily.read_text())["articles"]} if daily.exists() else {}
delta.update({a["url"]:a for a in changed})
meta = {"schemaVersion":1, "syncedAt":stamp, "health":feed["health"]}
save(daily, dict(meta,articles=list(delta.values())))
save(latest, dict(meta,articles=sorted(by_url.values(),key=lambda a:a["publishedAt"],reverse=True)))
