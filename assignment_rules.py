"""Rule-based persona assignment (draft for coder review).

Rules are unordered predicates; overlaps and non-matches are reported for
consensus adjudication. A precedence order (RULES order) gives a provisional
single assignment. Includes Kluge stage-3 homogeneity check:
mean within- vs between-type simple-matching similarity in the attribute space.
"""

# ===== IMPORTS =====
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

import persona_clustering as pc

# ===== CONFIGURATION & CONSTANTS =====
ACTIVE = pc.ACTIVE_A  # 12 active indicators = attribute space

# Rule set v2 (post coder review, 18.07.2026):
#  - "Programme Navigator" dropped; FellowProg is a secondary descriptor only.
#  - Public Communicator extended: spoken OR written contribution to discourse.
#  - No precedence order: every multi-match goes to coder consensus.
RULES = {
    "Industry Mover":      lambda d: d.Industry == 1,
    "Policy Shaper":       lambda d: d.Policy == 1,
    "Academic Researcher": lambda d: (d.ResearchAct == 1) |
                                     ((d.PubResearch == 1) & ((d.FurtherEd == 1) | (d.IndivFellow == 1))),
    "Public Communicator": lambda d: (((d.Speaker == 1) | (d.Writing == 1) | (d.Influencer == 1)) &
                                      ((d.PubTheory == 1) | (d.Teaching == 1) | (d.PubDebate == 1))) |
                                     ((d.PubDebate == 1) & (d.PubTheory == 1)),
}
QUIET_MAX_FLAGS = 2  # residual rule: no other rule matched and at most this many flags

# ===== CORE FUNCTIONS =====

def apply_rules(df):
    hits = pd.DataFrame({name: rule(df).astype(int) for name, rule in RULES.items()},
                        index=df.index)
    residual = (hits.sum(axis=1) == 0) & (df[ACTIVE].sum(axis=1) <= QUIET_MAX_FLAGS)
    hits["Frontline Clinician"] = residual.astype(int)
    assigned = hits.apply(
        lambda r: next(n for n in hits.columns if r[n]) if r.sum() == 1 else "ADJUDICATION",
        axis=1)
    return hits, assigned


def homogeneity(df, labels):
    """Mean within- vs between-type simple-matching similarity (attribute space)."""
    sim = 1 - squareform(pdist(df[ACTIVE].values, metric="hamming"))
    same = np.equal.outer(labels.values, labels.values)
    off = ~np.eye(len(df), dtype=bool)
    return sim[same & off].mean(), sim[~same].mean()


def adjudication_worksheet(df, hits, assigned):
    """Worksheet for the coder consensus meeting: flags + career context."""
    work = pd.read_excel(pc.HERE / "data" / "Overview_evaluation_cleaned_Claude.xlsx",
                         sheet_name="Work (all Cohorts)")
    work.columns = [str(c).strip() for c in work.columns]
    work["ID"] = pd.to_numeric(work["ID"], errors="coerce")
    career = work.set_index("ID")["Career after Fellowship"]
    adj = df[assigned == "ADJUDICATION"]
    return pd.DataFrame({
        "ID": adj.ID, "Cohort": adj.Cohort,
        "matched_rules": hits.loc[adj.index].apply(
            lambda r: "; ".join(n for n in hits.columns if r[n]) or "none", axis=1),
        "active_flags": adj[ACTIVE].apply(
            lambda r: ", ".join(c for c in ACTIVE if r[c] == 1), axis=1),
        "career": adj.ID.map(career).astype(str).str.slice(0, 150),
        "consensus_persona": "", "rationale": "",
    })

# ===== MAIN EXECUTION =====

def main():
    df = pc.load(pc.HERE / "data" / "Overview_evaluation_cleaned_Claude.xlsx")
    hits, assigned = apply_rules(df)

    print("Eindeutige Zuordnungen:")
    print(assigned[assigned != "ADJUDICATION"].value_counts().to_string())
    print(f"\nKonsensfälle: {(assigned == 'ADJUDICATION').sum()}")

    within, between = homogeneity(df[assigned != "ADJUDICATION"],
                                  assigned[assigned != "ADJUDICATION"])
    print(f"Homogenitätscheck (nur Eindeutige): within={within:.2f}, between={between:.2f}")

    df[["ID", "Cohort"]].assign(persona=assigned).to_csv(
        pc.OUT / "assignments_rules.csv", index=False)
    adjudication_worksheet(df, hits, assigned).to_csv(
        pc.OUT / "adjudication_worksheet.csv", index=False)
    print("\ngespeichert: results/assignments_rules.csv, results/adjudication_worksheet.csv")


if __name__ == "__main__":
    main()
