"""Re-pull the live numbers behind content.CLAIMS and print them next to the ledger. Report only.

Usage: uv run python scripts/refresh_claims.py

Not covered, re-read by hand in a browser: X view counts, hackathon placings.
"""

import json
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import content  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_json(url):
    return json.loads(fetch(url))


def npm_downloads(package, start):
    data = fetch_json(f"https://api.npmjs.org/downloads/range/{start}:{date.today().isoformat()}/{package}")
    return sum(day["downloads"] for day in data["downloads"])


def substack_posts(base):
    # Pages can overlap, so key posts by id rather than counting rows.
    posts, offset = {}, 0
    while True:
        page = fetch_json(f"{base}/api/v1/archive?sort=new&limit=12&offset={offset}")
        if not page:
            return list(posts.values())
        posts.update((post["id"], post) for post in page)
        offset += len(page)


def substack_post_count(base):
    return len(substack_posts(base))


def substack_subscribers(base):
    match = re.search(r'freeSubscriberCountOrderOfMagnitude\\":\\"([^\\"]+)', fetch(f"{base}/about"))
    return match.group(1) if match else "not found"


def shoal_bylined_reports():
    posts = substack_posts("https://www.shoal.gg")
    mine = sorted(p["post_date"][:10] for p in posts
                  if any(b.get("handle") == "wizzdom" for b in p.get("publishedBylines", [])))
    return f"{len(mine)} bylined wizzdom of {len(posts)} posts ({mine[0]} to {mine[-1]})" if mine else "0 bylined"


def flashbots_forum():
    topics = fetch_json("https://collective.flashbots.net/topics/created-by/wisdom.json")["topic_list"]["topics"]
    pbs = next((t["views"] for t in topics if t["slug"] == "the-6-99-without-pbs"), "not found")
    return f"{sum(t['views'] for t in topics)} views across {len(topics)} topics; the-6-99-without-pbs {pbs}"


def modelcards():
    text = re.sub(r"<[^>]+>", " ", fetch("https://modelcards.net"))
    text = " ".join(text.split())
    wanted = {
        "single-lab": r"(\d+)\s*%\s*of frontier benchmarks",
        "distinct benchmarks": r"(\d[\d,]*) distinct benchmark",
        "documents": r"(\d[\d,]*) public (?:model cards|documents)",
    }
    return "; ".join(f"{k} {(re.search(p, text) or [None, 'not found'])[1]}" for k, p in wanted.items())


def ecdsafail():
    raw = subprocess.run(["ecdsafail", "submissions", "--all"], capture_output=True, text=True).stdout
    rows, unparsed = [], []
    for line in re.sub(r"\x1b\[[0-9;]*m", "", raw).splitlines():
        if not re.match(r"^[0-9a-f]{7}\s", line):
            continue
        fields = re.split(r"\s{2,}", line.strip())
        if len(fields) != 8:
            unparsed.append(line)
            continue
        rows.append(fields)

    total = defaultdict(int)
    drops = []
    for submission, solver, status, _score, _metrics, diff, _commit, _created in rows:
        if status == "promoted" and diff != "n/a":
            change = int(diff.split()[0])
            total[solver] += change
            drops.append((change, submission))
    ranking = [solver for solver, _ in sorted(total.items(), key=lambda item: item[1])]
    drop_rank = [s for _, s in sorted(drops)].index("df59687") + 1 if drops else None
    rank = ranking.index("owizdom") + 1 if "owizdom" in ranking else None
    return (f"rows {len(rows)} parsed, {len(unparsed)} unparsed; {len({r[1] for r in rows})} solvers; "
            f"owizdom {rank} of {len(ranking)} promoted solvers; df59687 drop {drop_rank} of {len(drops)}")


CHECKS = [
    ("npm-downloads", lambda: f"create-eigenbox {npm_downloads('create-eigenbox', '2026-06-01')}, "
                              f"@parallel-labs/mind-agent {npm_downloads('@parallel-labs/mind-agent', '2026-01-20')}"),
    ("parallel-posts", lambda: f"{substack_post_count('https://parallelresearch.substack.com')} posts"),
    ("shoal-reports", shoal_bylined_reports),
    ("shoal-subscribers", lambda: substack_subscribers("https://www.shoal.gg")),
    ("decentralised-subscribers", lambda: substack_subscribers("https://www.decentralised.co")),
    ("flashbots-forum-views", flashbots_forum),
    ("modelcards", modelcards),
    ("ecdsafail-rank", ecdsafail),
]


def main():
    ledger = {claim["id"]: claim for claim in content.CLAIMS}
    for claim_id, check in CHECKS:
        try:
            live = check()
        except Exception as err:  # network or CLI failure: report it, keep going
            live = f"ERROR {type(err).__name__}: {err}"
        claim = ledger.get(claim_id, {"value": "(not in ledger)", "as_of": "-"})
        print(f"{claim_id}\n  ledger ({claim['as_of']}): {claim['value']}\n  live   ({date.today()}): {live}\n")


if __name__ == "__main__":
    main()
