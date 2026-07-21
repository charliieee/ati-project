# ati-project
Alumni Personas of the NHS Fellowship in Clinical AI - 
This Repository is part of our Alan Turing PhD Enrichment Scheme Project 2026, Research Project MRC Advancing Biomedical Data Science Careers (ABDC). 

Analysis code for the persona component of:
Mobilising Clinical AI Skills: A Mixed-Methods Evaluation of a National Medical Professional Upskilling Programme. Sophie Perret and Kathryn Woodward. [journal name], [year]. DOI: [tba]

The study constructs a typology of post-fellowship professional profiles of all 57 alumni of the first three cohorts of the NHS Fellowship in Clinical AI, based on a systematic digital footprint analysis supplemented by an alumni survey. Type construction follows Kluge's four-stage model of empirically grounded type construction; the five resulting types are characterised as personas (Embedded Clinician, Academic Researcher, Public Communicator, Policy Shaper, Industry Mover).

## Supplementary Information in General
| # | document | Purpose |
|------|--------|---------|
| 1 | `coreq_checklist.docx` | COREQ-Checklist |
| 2 | `gramms_checklist.docx` | GRAMMS-Checklist |

## Supplementary Information on Type Construction (RQ1)
| # | document | Purpose |
|------|--------|---------|
| 1 | `survey.docx` | interview questions for the semi-structured interviews |
| 2 | Pipeline | description on how to run the scripts used in in the type construction |
| 3 | `methods_detailed.docx` | document containing the exploratory cluster analysis in detail; stability assessment; rule-based classification procedure in detail |
| 4 | `figures_detailed.pdf` | supplementary figures: Fig. S1 Bootstrap-Stability; Fig. S2 MCA-Karte; Fig. S3 Continuum; Fig. S4 Heatmap  |
| 5 | `tables_detailed.pdf` | supplementary tables: Table S1 Codebook; Table S2 Assignment rules; Table S3 Stability metrics; Table S4 Adjudication summary; Table S5 Type x Indicator prevalence |

### Pipeline
Scripts are run from the repository root in this order:

| Step | script | Purpose |
|------|--------|---------|
| 1 | `persona_clustering.py` | Exploratory cluster analysis (stage 2): MCA + Ward on 12 binary indicators, silhouette scan k=2–6, bootstrap Jaccard stability (B=500), leave-one-out ARI, PAM cross-check. Writes cluster profiles and assignments. |
| 2 | `assignment_rules.py` | Rule-based persona assignment (stage 4): applies the five assignment rules without precedence, reports unambiguous matches (41/57) and consensus cases (16/57), computes the within/between-type homogeneity check, and builds the adjudication worksheet for the coder consensus meeting.|
| 3 | `make_adjudication_xlsx.py` | Formats the adjudication worksheet as an Excel workbook for the consensus meeting (guiding questions per rule combination, documented rationale as audit trail).|
| 4 | `make_supp_data.py` | Freezes all numbers for the paper (publication categories, activity counts, per-persona statistics) and renders Supplementary Figures S1–S3. |
| 5 | `make_report_figs.py`, <br> `make_report_figs.py`, <br> `make_personas_docx.js` | Internal report figures and Word deliverables (persona profiles, Supplementary Information). |

The permutation test against marginal-preserving null data and the aggregated dimension-score sensitivity analysis are documented in the Supplementary Methods; both reuse the functions in `persona_clustering.py`.

### Data availability
Individual-level data are not included in this repository. The study population is small (n = 57) and professionally identifiable; person-level footprint records, survey responses and the ID mapping are therefore not shared. Aggregated data underlying all tables and figures are available in the paper and its Supplementary Information. Requests for further data access can be directed to the corresponding author and are subject to ethical approval.

Scripts expect the (non-public) source workbook at `data/Overview_evaluation_cleaned.xlsx` with the sheets `Overview`, `Work (all Cohorts)`, `Publications (1st–3rd Cohort)` and `AI Activities (1st–3rd Cohort)`; outputs are written to `results/`.

### Requirements
Python ≥ 3.10 with `pandas`, `numpy`, `scipy`, `scikit-learn`, `prince`,
`matplotlib`, `openpyxl`. Document generation additionally uses Node.js with the
`docx` package.

```bash
pip install pandas numpy scipy scikit-learn prince matplotlib openpyxl
python persona_clustering.py
python assignment_rules.py
python make_supp_data.py
```

Random seeds are fixed (bootstrap and permutation procedures use `numpy.random.default_rng(2026)`); results in the paper are exactly reproducible given the source data. 

## Supplementary Information Interviews (RQ 2)
| # | document | Purpose |
|------|--------|---------|
| 1 | `interview-guide.docx` | interview questions for the semi-structured interviews |

## Citation
If you use this code, please cite the paper above. [BibTeX to be added on publication]

## License
[MIT]
