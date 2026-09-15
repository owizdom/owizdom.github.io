import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

OWNED_PAGES = ["index.html", "about.html", "random/wins.html"]

def retired_phrases():
    # Phrases that must never appear on the site live in a private file outside the repo.
    path = os.environ.get("SITE_RETIRED_FILE")
    if not path:
        return []
    lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    return [line.strip().lower() for line in lines if line.strip() and not line.startswith("#")]

BANNED_WORDS = [
    "delve", "leverage", "leveraging", "seamless", "seamlessly", "robust",
    "tapestry", "realm", "beacon", "showcase", "harness", "cutting-edge",
    "game-changing", "meticulous", "meticulously", "nuanced", "multifaceted",
    "intricate", "underscore", "bolster", "illuminate", "facilitate",
    "paradigm", "swiftly", "comprehensive", "adept",
]

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def load(dist, page):
    return BeautifulSoup((dist / page).read_text(encoding="utf-8"), "html.parser")


def visible_text(soup):
    for el in soup(["script", "style", "noscript", "template"]):
        el.decompose()
    return soup.get_text(" ", strip=True)


def attribute_text(soup):
    values = []
    for el in soup.find_all(True):
        for value in el.attrs.values():
            values.append(" ".join(value) if isinstance(value, list) else str(value))
    return " ".join(values)


def number_tokens(text):
    return {t.replace(",", "") for t in NUMBER.findall(text)}


def html_pages(dist):
    return sorted(p.relative_to(dist).as_posix() for p in dist.rglob("*.html"))


def test_t1_build_succeeds(build, dist):
    assert build.returncode == 0, build.stdout[-2000:] + build.stderr[-2000:]
    for page in ("index.html", "about.html"):
        assert (dist / page).is_file(), f"missing dist/{page}"


def test_t2_no_blocked_phrases_in_any_built_file(build, dist):
    phrases = retired_phrases()
    hits = []
    for path in dist.rglob("*"):
        if not path.is_file() or path.suffix not in {".html", ".css", ".js", ".txt", ".xml", ".svg", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        hits += [f"{path.relative_to(dist)}: {phrase}" for phrase in phrases if re.search(rf"\b{re.escape(phrase)}\b", text)]
    assert not hits


def test_t3_no_retired_claims(build, dist):
    hits = []
    for page in html_pages(dist):
        soup = load(dist, page)
        text = " ".join((attribute_text(soup) + " " + visible_text(soup)).lower().split())
        hits += [f"{page}: {phrase}" for phrase in retired_phrases() if phrase in text]
    assert not hits


def test_t4_owned_pages_have_no_em_dash_or_ai_vocabulary(build, dist):
    hits = []
    for page in OWNED_PAGES:
        raw = (dist / page).read_text(encoding="utf-8")
        text = visible_text(BeautifulSoup(raw, "html.parser"))
        if "—" in text or "&mdash;" in raw:
            hits.append(f"{page}: em dash")
        for word in BANNED_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                hits.append(f"{page}: {word}")
    assert not hits


def h2_titles(soup):
    return [h.get_text(" ", strip=True).lower() for h in soup.find_all("h2")]


def test_t5_index_sections_in_order(build, dist):
    titles = h2_titles(load(dist, "index.html"))
    wanted = ["now", "selected work", "before", "recognition"]
    missing = [w for w in wanted if w not in titles]
    assert not missing, titles
    positions = [titles.index(w) for w in wanted]
    assert positions == sorted(positions), titles


def test_t5_about_sections(build, dist):
    titles = h2_titles(load(dist, "about.html"))
    for wanted in ("work experience", "stack", "writing"):
        assert wanted in titles, titles


def test_t6_headline_and_lab_title(build, dist):
    soup = load(dist, "index.html")
    headline = soup.find(id="headline")
    assert headline is not None, "no #headline"
    assert "Research Engineer" in headline.get_text(" ", strip=True)
    now = soup.find(id="now")
    assert now is not None, "no #now"
    rows = [r.get_text(" ", strip=True) for r in now.select("[data-role-row]")]
    lab = [r for r in rows if "Free Systems Lab" in r]
    assert lab, rows
    assert all("Research Fellow" in r for r in lab), lab


def test_t7_claims_ledger_is_complete():
    import content

    assert content.CLAIMS, "CLAIMS is empty"
    seen = set()
    for claim in content.CLAIMS:
        assert {"id", "value", "source", "as_of"} <= set(claim), claim
        assert claim["id"] not in seen, f"duplicate claim id {claim['id']}"
        seen.add(claim["id"])
        source = str(claim["source"]).strip()
        assert source, claim
        date.fromisoformat(claim["as_of"])
        if source.startswith("docs/"):
            assert (ROOT / source).exists(), f"capture missing: {source}"


def test_t7_rendered_numbers_are_claims(build, dist):
    import content

    allowed = set()
    for claim in content.CLAIMS:
        allowed |= number_tokens(str(claim["value"]))

    bad = []
    for page, minimum_scopes in (("index.html", 5), ("about.html", 4)):
        soup = load(dist, page)
        for el in soup.select("time, code, [data-literal]"):
            el.decompose()
        scopes = soup.select("[data-claims]")
        assert len(scopes) >= minimum_scopes, f"{page}: {len(scopes)} [data-claims] scopes"
        for scope in scopes:
            for token in number_tokens(scope.get_text(" ", strip=True)):
                if re.fullmatch(r"20[12]\d", token):
                    continue
                if token not in allowed:
                    bad.append(f"{page}: {token}")
    assert not bad, sorted(set(bad))


def test_t8_selected_work_order(build, dist):
    soup = load(dist, "index.html")
    names = [el.get("data-project", "").strip().lower() for el in soup.select("#work [data-project]")]
    assert names[:5] == ["bob is alive", "swarm mind", "vanta", "eigenbox", "mind agent"], names


def test_t9_links_are_well_formed(build, dist):
    bad = []
    for page in html_pages(dist):
        for a in load(dist, page).find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#"):
                continue
            if href.startswith("/"):
                path = href.split("#")[0].split("?")[0].strip("/")
                candidates = [dist / "index.html"] if not path else [
                    dist / path, dist / f"{path}.html", dist / path / "index.html"
                ]
                if not any(c.is_file() for c in candidates):
                    bad.append(f"{page}: {href}")
                continue
            url = urlparse(href)
            if url.scheme == "mailto":
                if "@" not in url.path:
                    bad.append(f"{page}: {href}")
            elif url.scheme not in ("https", "http") or not url.netloc or " " in href:
                bad.append(f"{page}: {href}")
    assert not bad
