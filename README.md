# ProteinDesign-Eval

An explainable, research-oriented platform for evaluating and experimentally prioritizing de novo / AI-designed protein candidates.

## MVP

The current build includes a complete seeded demo workflow:

**Upload → QC → Analyze → Visualize → Compare → Prioritize → Export → Experiment → Feedback → Failure Analysis → Learning**

The frontend is a React + TypeScript + Vite app. The backend is a FastAPI service boundary with modular Python analysis contracts in `analysis/`.

## Run

```bash
npm install
npm run dev
```

Optional API:

```bash
uvicorn backend.main:app --reload
```

## Scientific integrity

Every result is intended to be labeled as `Calculated`, `Model-derived`, `Experimental`, or `Unavailable`. The priority score is a transparent computational ranking, not an experimental success probability. Failure analysis is association-only until validated with sufficient data.

## Repository structure

- `frontend` — reserved for a future extracted frontend package; MVP UI currently lives in `src/`
- `backend` — FastAPI routes for projects, targets, candidates, analyses, feedback, datasets, reports, and exports
- `analysis` — modular Python analysis and ranking contracts
- `data/demo` — reserved for project seed files
- `data/schemas` — reserved for input schemas
- `tests` — reserved for API and scientific unit tests
- `docs` — reserved for methodology notes
- `scripts`, `notebooks`, `docker` — extension points for production workflows