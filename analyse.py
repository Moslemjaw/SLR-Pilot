import json, glob, sys, collections
D = sys.argv[1]
def load(r):
    out = {}
    for f in sorted(glob.glob(f"{D}/reviewer{r}_*.json")):
        for p in json.load(open(f)): out[int(p["n"])] = p
    return out
A, B = load("A"), load("B")
ns = sorted(set(A) & set(B))
print("papers:", len(ns))
# --- inclusion agreement + Cohen's kappa
a = [A[n]["decision"] for n in ns]; b = [B[n]["decision"] for n in ns]
po = sum(x == y for x, y in zip(a, b)) / len(ns)
pa = a.count("include") / len(ns); pb = b.count("include") / len(ns)
pe = pa * pb + (1 - pa) * (1 - pb)
kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
print(f"inclusion: agree {po:.2f}, kappa {kappa:.2f}")
print("disagreements:", [(n, A[n]["decision"], B[n]["decision"]) for n in ns if A[n]["decision"] != B[n]["decision"]])
full = {n: (A[n].get("full_text_read"), B[n].get("full_text_read")) for n in ns}
print("full text read (A,B):", full)
# --- quality score differences
diffs = [abs(float(A[n]["quality_total"]) - float(B[n]["quality_total"])) for n in ns]
print("quality |A-B| mean %.2f, max %.1f" % (sum(diffs) / len(diffs), max(diffs)))
print("quality A/B:", [(n, A[n]["quality_total"], B[n]["quality_total"]) for n in ns])
# --- extraction field agreement (set overlap)
def norm(v):
    if v is None: return set()
    if isinstance(v, list): return {str(x).strip().lower() for x in v}
    return {s.strip().lower() for s in str(v).split("|")} if "|" in str(v) else {str(v).strip().lower()}
fields = ["domain", "contribution_type", "styles", "communication", "quality_attributes", "privacy_approach",
          "explainability_approach", "inference_location", "training_location", "allocation_strategy",
          "validation_method", "baseline", "code_available"]
both = [n for n in ns if A[n]["decision"] == "include" and B[n]["decision"] == "include"]
print("\nfield agreement on", len(both), "papers both included (exact match / mean Jaccard):")
fa = {}
for f in fields:
    ex, jac = 0, 0
    for n in both:
        x, y = norm(A[n]["extraction"].get(f)), norm(B[n]["extraction"].get(f))
        ex += x == y; jac += len(x & y) / len(x | y) if (x | y) else 1
    fa[f] = (ex / len(both), jac / len(both)); print(f"  {f:24s} {ex}/{len(both)}  J={jac/len(both):.2f}")
json.dump({"kappa": kappa, "agree": po, "field_agreement": fa, "both_included": both}, open("/home/claude/slr_pilot/agreement.json", "w"), indent=1)
# --- consensus tables (only values both reviewers gave)
def table(f):
    c = collections.Counter()
    for n in both:
        for v in norm(A[n]["extraction"].get(f)) & norm(B[n]["extraction"].get(f)): c[v] += 1
    return c
print()
for f in ["domain", "styles", "quality_attributes", "privacy_approach", "explainability_approach",
          "inference_location", "allocation_strategy", "validation_method", "code_available", "baseline"]:
    print(f, dict(table(f).most_common()))

# --- second pass: treat None / Not reported / empty as the same, drop free-text notes in brackets
import re
def norm2(v):
    s = norm(v)
    out = set()
    for x in s:
        x = re.sub(r"\(.*?\)", "", x).split(";")[0].strip()
        if x.startswith("not reported") or x in ("none", "", "null"): x = "none/not reported"
        out.add(x)
    return out or {"none/not reported"}
print("\nafter fixing 'None vs Not reported' and free-text notes:")
fa2 = {}
for f in fields:
    ex = sum(norm2(A[n]["extraction"].get(f)) == norm2(B[n]["extraction"].get(f)) for n in both)
    jac = sum(len(norm2(A[n]["extraction"].get(f)) & norm2(B[n]["extraction"].get(f))) /
              len(norm2(A[n]["extraction"].get(f)) | norm2(B[n]["extraction"].get(f))) for n in both)
    fa2[f] = (ex / len(both), jac / len(both)); print(f"  {f:24s} {ex}/{len(both)}  J={jac/len(both):.2f}")
d = json.load(open("/home/claude/slr_pilot/agreement.json")); d["field_agreement_fixed"] = fa2
json.dump(d, open("/home/claude/slr_pilot/agreement.json", "w"), indent=1)
