"""SLR database search: OpenAlex + Semantic Scholar (both free).
Runs the protocol's search string, saves every record with its abstract, removes duplicates.
Usage:  python3 search.py            -> writes results/search_results.csv and results/search_log.txt
Optional: export OPENALEX_API_KEY=... and/or S2_API_KEY=... if the free limits are hit."""
import csv, datetime, json, os, re, sys, time, urllib.parse, urllib.request

MAILTO = "moslemjawich@gmail.com"
YEAR_FROM = 2018
os.makedirs("results", exist_ok=True)
LOG = open("results/search_log.txt", "a", encoding="utf-8")
def log(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {msg}"; print(line); LOG.write(line + "\n"); LOG.flush()

# ---- the protocol's three groups (Section 3.2). OpenAlex stems words itself, so no * wildcards there.
AIOT = ['"Artificial Intelligence of Things"', 'AIoT', '"AI-IoT"', 'AIoMT', '"Intelligent IoT"']
AI = ['AI', '"artificial intelligence"', '"machine learning"', '"deep learning"', '"neural network"',
      '"federated learning"', '"edge intelligence"', '"edge AI"', 'TinyML', '"explainable AI"', 'XAI', 'MLOps']
IOT = ['IoT', '"Internet of Things"', 'IIoT', 'IoMT', '"cyber-physical system"']
ARCH = ['architecture', 'microservice', 'microservices', '"service-oriented"', 'serverless',
        '"design pattern"', '"model-driven"', 'framework']
EDGE = ['edge', 'fog', '"cloud-edge"', '"edge-cloud"', '"cloud continuum"', '"compute continuum"',
        'osmotic', 'federated', '"on-device"']
G = lambda terms: "(" + " OR ".join(terms) + ")"
OPENALEX_QUERIES = {   # split in two so each query stays short; results are merged
    "OA-1 AIoT terms": f"{G(AIOT)} AND {G(ARCH)} AND {G(EDGE)}",
    "OA-2 AI + IoT":   f"{G(AI)} AND {G(IOT)} AND {G(ARCH)} AND {G(EDGE)}",
}

def get_json(url, headers=None, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"SLR-search (mailto:{MAILTO})", **(headers or {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "ignore")
            if e.code in (429, 500, 502, 503, 504):
                wait = 5 * (i + 1); log(f"  HTTP {e.code}, retrying in {wait}s"); time.sleep(wait); continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except Exception as e:
            wait = 5 * (i + 1); log(f"  {e}, retrying in {wait}s"); time.sleep(wait)
    raise RuntimeError("gave up after retries: " + url[:150])

def abstract_from_index(inv):
    if not inv: return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs: pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))

def openalex(name, query):
    rows, cursor, page = [], "*", 0
    base = "https://api.openalex.org/works?"
    params = {"filter": f"title_and_abstract.search:{query},publication_year:>{YEAR_FROM - 1}",
              "per_page": 200, "mailto": MAILTO,
              "select": "id,doi,display_name,publication_year,type,primary_location,abstract_inverted_index,cited_by_count,language"}
    if os.environ.get("OPENALEX_API_KEY"): params["api_key"] = os.environ["OPENALEX_API_KEY"]
    while cursor:
        params["cursor"] = cursor
        data = get_json(base + urllib.parse.urlencode(params))
        if page == 0: log(f"{name}: OpenAlex reports {data['meta']['count']} records")
        for w in data["results"]:
            loc = (w.get("primary_location") or {}).get("source") or {}
            rows.append({"source_db": "OpenAlex", "query": name, "id": w["id"], "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
                         "title": w.get("display_name") or "", "year": w.get("publication_year"), "type": w.get("type"),
                         "venue": loc.get("display_name") or "", "language": w.get("language"),
                         "cited_by": w.get("cited_by_count"), "abstract": abstract_from_index(w.get("abstract_inverted_index"))})
        cursor = data["meta"].get("next_cursor"); page += 1
        if page % 10 == 0: log(f"  ...{len(rows)} downloaded")
        time.sleep(0.2)
    log(f"{name}: downloaded {len(rows)}")
    return rows

# Semantic Scholar bulk search syntax: + AND, | OR, "phrase", ( ), * prefix wildcard
S2 = lambda terms: "(" + " | ".join(terms) + ")"
S2_ARCH = ['architect*', 'microservice*', '"service-oriented"', 'serverless', '"design pattern"', '"model-driven"', 'framework*']
S2_QUERY = f"({S2(AIOT)} | ({S2(AI)} + {S2(IOT)})) + {S2(S2_ARCH)} + {S2(EDGE)}"

def semantic_scholar():
    rows, token, first = [], None, True
    headers = {"x-api-key": os.environ["S2_API_KEY"]} if os.environ.get("S2_API_KEY") else {}
    while True:
        p = {"query": S2_QUERY, "year": f"{YEAR_FROM}-", "fields": "title,abstract,year,venue,externalIds,publicationTypes,citationCount"}
        if token: p["token"] = token
        data = get_json("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(p), headers)
        if first: log(f"S2: Semantic Scholar reports {data.get('total')} records"); first = False
        for w in data.get("data") or []:
            ext = w.get("externalIds") or {}
            rows.append({"source_db": "SemanticScholar", "query": "S2", "id": w.get("paperId"), "doi": (ext.get("DOI") or "").lower(),
                         "title": w.get("title") or "", "year": w.get("year"), "type": ";".join(w.get("publicationTypes") or []),
                         "venue": w.get("venue") or "", "language": "", "cited_by": w.get("citationCount"),
                         "abstract": w.get("abstract") or ""})
        token = data.get("token")
        if not token: break
        log(f"  ...{len(rows)} downloaded"); time.sleep(1.5)
    log(f"S2: downloaded {len(rows)}")
    return rows

def norm_title(t): return re.sub(r"[^a-z0-9]", "", (t or "").lower())

if __name__ == "__main__":
    log("=== Search started. Protocol string v1.1 (Section 3.2) ===")
    allrows = []
    for name, q in OPENALEX_QUERIES.items():
        log(f"{name} query: {q}")
        try: allrows += openalex(name, q)
        except Exception as e: log(f"{name} FAILED: {e}")
    log(f"S2 query: {S2_QUERY}")
    try: allrows += semantic_scholar()
    except Exception as e: log(f"S2 FAILED: {e}")
    json.dump(allrows, open("results/raw_records.json", "w"))
    # de-duplicate: same DOI, or same normalised title
    seen, unique = {}, []
    for r in allrows:
        keys = [k for k in ("doi:" + r["doi"] if r["doi"] else None, "t:" + norm_title(r["title"])) if k and len(k) > 6]
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit is not None:
            u = unique[hit]; u["found_in"] = ";".join(sorted(set(u["found_in"].split(";") + [r["source_db"]])))
            if not u["abstract"] and r["abstract"]: u["abstract"] = r["abstract"]
            if not u["doi"] and r["doi"]: u["doi"] = r["doi"]
            continue
        r = {**r, "found_in": r["source_db"]}; unique.append(r)
        for k in keys: seen[k] = len(unique) - 1
    unique = [r for r in unique if (r["year"] or 0) >= YEAR_FROM]
    for i, r in enumerate(unique, 1): r["record_id"] = f"R{i:05d}"
    cols = ["record_id", "title", "year", "venue", "type", "doi", "found_in", "cited_by", "language", "abstract"]
    with open("results/search_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(unique)
    log(f"TOTAL downloaded {len(allrows)}; after removing duplicates {len(unique)}; "
        f"with abstract {sum(1 for r in unique if r['abstract'])}")
    log("Saved results/search_results.csv  <- send this file (and search_log.txt) back")
