# ProteinDesign Insight

ProteinDesign Insight is a deployable Streamlit MVP for transparent computational triage of AI-designed and de novo protein candidates. It is designed around a target → candidate → analysis → prioritization → experiment → feedback loop and keeps computed/model-derived values distinct from experimental observations.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

The application uses SQLite at `data/protein_design_insight.db` and creates the database on first run. No API keys are required.

## Scientific scope

The included demo project is synthetic and illustrative. Its sequences and coordinate files are test fixtures, not biological claims or experimental evidence. The application only reports metrics it can calculate from supplied inputs; unavailable values remain unavailable. Priority scores are for experimental testing triage, not predictions of binding success.

The current analysis engine supports FASTA and lightweight PDB/mmCIF parsing, sequence metrics, coordinate-based structure QC, interface contacts, pairwise target/off-target comparisons when structures are available, state comparisons, sequence clustering, transparent weighted ranking, feedback import, failure summaries, project exports, and PDF reports. The module boundaries are intentionally independent from the Streamlit UI so heavier structure predictors or external model runners can be added later.

## Layout

- `app.py`: Streamlit entry point and workflow shell
- `core/`: storage, validation, sequence/structure/interface/specificity/conformation/diversity/ranking/feedback/report logic
- `pages/`: Streamlit navigation wrappers
- `data/demo/`: clearly labeled synthetic demo project
- `tests/`: unit tests for validation, parsing, scoring, clustering, feedback, reports, and malformed data

## Limitations

No docking, molecular dynamics, AlphaFold/ESMFold inference, or wet-lab interpretation is bundled. pLDDT and PAE are shown only when supplied as metadata. Hydrogen bonds and salt bridges are geometric heuristics and should be treated as calculated indicators, not proof of interaction.
