"""Persona clustering of NHS Clinical AI Fellowship alumni (n=57).

Pipeline: MCA on binary indicators -> Ward clustering in MCA factor space.
k chosen by silhouette scan; validated by bootstrap Jaccard stability,
leave-one-out sensitivity, and a PAM/simple-matching cross-check.

Variants:  A = 12 active variables
           B = Speaker+Writing+Influencer merged into PublicEngage (11 active)
"""

# ===== IMPORTS =====
from pathlib import Path

import numpy as np
import pandas as pd
import prince
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from scipy.stats import hypergeom
from sklearn.metrics import adjusted_rand_score, silhouette_score

# ===== CONFIGURATION & CONSTANTS =====
RNG = np.random.default_rng(2026)
HERE = Path(__file__).parent
OUT = HERE / "results"

SHORT = {  # original column -> short name
    "ID": "ID", "Career after Fellowship": "Career",
    "Industry (part/full time)": "Industry", "Teaching": "Teaching",
    "Further Education (PhD, M.Sc. or PGDip) in AI during or after Fellowship": "FurtherEd",
    "Fellowships Programmes": "FellowProg",
    "Individual AI-related Research Fellowships": "IndivFellow",
    "Contribution to Research": "PubResearch", "Contribution to Debate": "PubDebate",
    "Contribution to Theory": "PubTheory", "Speaker": "Speaker", "Writing": "Writing",
    "Policy": "Policy", "Influencer": "Influencer", "Research": "ResearchAct",
    "MedTech": "MedTech",
}
ACTIVE_A = ["Industry", "Teaching", "FurtherEd", "FellowProg", "IndivFellow",
            "PubResearch", "PubDebate", "PubTheory", "Speaker", "Writing",
            "Policy", "ResearchAct"]
ACTIVE_B = ["Industry", "Teaching", "FurtherEd", "FellowProg", "IndivFellow",
            "PubResearch", "PubDebate", "PubTheory", "PublicEngage",
            "Policy", "ResearchAct"]
PASSIVE = ["Career", "Influencer", "MedTech", "Cohort"]
K_RANGE = range(2, 7)

# ===== CORE FUNCTIONS =====

def load(path):
    df = pd.read_excel(path, sheet_name="Overview")
    df.columns = [SHORT[c.strip()] for c in df.columns]
    df["Cohort"] = pd.cut(df["ID"], [0, 11, 28, 57], labels=[1, 2, 3]).astype(int)
    df["PublicEngage"] = df[["Speaker", "Writing", "Influencer"]].max(axis=1)
    return df


def mca_coords(X, inertia_target=0.80):
    """Row coordinates on MCA components covering >= inertia_target."""
    ncp = X.shape[1]  # binary vars: total dims = 2J - J = J
    mca = prince.MCA(n_components=ncp, random_state=0).fit(X.astype(str))
    cum = mca.eigenvalues_.cumsum() / mca.eigenvalues_.sum()
    keep = max(2, int(np.searchsorted(cum, inertia_target)) + 1)
    return mca.transform(X.astype(str)).values[:, :keep], mca


def ward_labels(coords, k):
    return fcluster(linkage(coords, method="ward"), k, criterion="maxclust")


def silhouette_scan(coords):
    return {k: silhouette_score(coords, ward_labels(coords, k)) for k in K_RANGE}


def boot_jaccard(X, k, B=500):
    """Cluster-wise bootstrap stability (Hennig's clusterboot scheme)."""
    ref = ward_labels(mca_coords(X)[0], k)
    clusters = [set(np.where(ref == c)[0]) for c in range(1, k + 1)]
    scores = np.zeros(k)
    for _ in range(B):
        idx = RNG.choice(len(X), len(X), replace=True)
        lab = ward_labels(mca_coords(X.iloc[idx])[0], k)
        boot = [set(idx[lab == c]) for c in range(1, k + 1)]
        present = set(idx)
        for i, c in enumerate(clusters):
            c_in = c & present
            scores[i] += max((len(c_in & b) / len(c_in | b) if c_in | b else 0)
                             for b in boot)
    return scores / B


def loo_ari(X, k):
    """Mean ARI between full solution and each leave-one-out solution."""
    ref = ward_labels(mca_coords(X)[0], k)
    aris = []
    for i in range(len(X)):
        keep = np.arange(len(X)) != i
        lab = ward_labels(mca_coords(X.iloc[keep])[0], k)
        aris.append(adjusted_rand_score(ref[keep], lab))
    return np.mean(aris), np.min(aris)


def pam(dist, k, n_init=20):
    """Compact PAM (k-medoids) on a precomputed distance matrix."""
    n, best = len(dist), (np.inf, None)
    for _ in range(n_init):
        med = list(RNG.choice(n, k, replace=False))
        while True:
            lab = np.argmin(dist[:, med], axis=1)
            new = [np.arange(n)[lab == j][np.argmin(dist[np.ix_(lab == j, lab == j)].sum(0))]
                   if (lab == j).any() else med[j] for j in range(k)]
            if set(new) == set(med):
                break
            med = new
        cost = dist[np.arange(n), np.array(med)[lab]].sum()
        if cost < best[0]:
            best = (cost, lab + 1)
    return best[1]

# ===== ANALYSIS FUNCTIONS =====

def profile(df, labels, active):
    """Prevalence (%) per cluster, with hypergeometric enrichment p-values."""
    out, n = [], len(df)
    for var in active + PASSIVE:
        row = {"variable": var, "overall": df[var].mean()}
        for c in sorted(set(labels)):
            sub = df.loc[labels == c, var]
            row[f"C{c} (n={sub.size})"] = sub.mean()
            K, x = int(df[var].sum()), int(sub.sum())
            row[f"C{c} p"] = min(hypergeom.sf(x - 1, n, K, sub.size),
                                 hypergeom.cdf(x, n, K, sub.size)) * 2
        out.append(row)
    return pd.DataFrame(out).round(3)


def run_variant(name, df, active):
    X = df[active]
    coords, mca = mca_coords(X)
    sil = silhouette_scan(coords)
    k = max(sil, key=sil.get)
    labels = ward_labels(coords, k)
    jac = boot_jaccard(X, k)
    ari_mean, ari_min = loo_ari(X, k)
    pam_lab = pam(squareform(pdist(X.values, metric="hamming")), k)
    report = [
        f"=== Variant {name}: {len(active)} active vars, MCA dims kept: {coords.shape[1]} ===",
        f"silhouette by k: { {k_: round(s, 3) for k_, s in sil.items()} }  -> k={k}",
        f"cluster sizes: {np.bincount(labels)[1:].tolist()}",
        f"bootstrap Jaccard per cluster (B=500): {jac.round(2).tolist()}",
        f"leave-one-out ARI: mean={ari_mean:.2f}, min={ari_min:.2f}",
        f"ARI vs PAM/simple-matching: {adjusted_rand_score(labels, pam_lab):.2f}",
    ]
    prof = profile(df, labels, active)
    assign = df[["ID", "Cohort"]].assign(cluster=labels, pam_cluster=pam_lab)
    return "\n".join(report), prof, assign, sil

# ===== MAIN EXECUTION =====

def main():
    OUT.mkdir(exist_ok=True)
    df = load(HERE / "data" / "Overview_evaluation_cleaned_Claude.xlsx")
    summary = [f"n = {len(df)}, cohorts: {df['Cohort'].value_counts().sort_index().tolist()}"]
    for name, active in [("A", ACTIVE_A), ("B", ACTIVE_B)]:
        report, prof, assign, _ = run_variant(name, df, active)
        summary.append(report)
        prof.to_csv(OUT / f"profile_{name}.csv", index=False)
        assign.to_csv(OUT / f"assignments_{name}.csv", index=False)
    text = "\n\n".join(summary)
    (OUT / "summary.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
