# GenAI — Patent Analysis, Design-Around & Innovation Recommendation

**Partner:** Fuyao Europe (Leingarten)

**Contact:** jinmian.shi@fuyaogroup.eu

**Sync:** Monthly with partner

---

## Project Goal

Build an AI-supported system that reads and understands patent documents, compares them with product designs, identifies potential risks, and suggests design improvements and innovation directions.

---

## The 4 Phases

| Phase | Focus | Output |
|-------|-------|--------|
| 1 | Patent Understanding & Data Structuring | Structured patent database |
| 2 | Risk Identification | Risk scores & conflict highlights |
| 3 | Design Improvement Suggestions | Alternative design ideas |
| 4 | Innovation Opportunities | New idea directions from patent gaps |

> Each phase depends on the previous one. Phase 1 is the critical bottleneck — nothing works without clean structured data.

---

## Functional Requirements

### Phase 1 — Data & NLP
- Collect patent documents (claims, descriptions)
- Extract key technical features using NLP
- Store in a structured database/schema

### Phase 2 — Risk Detection
- Accept product design inputs (text, CAD annotations)
- Compare product features vs. patent features
- Detect overlaps, flag conflicts, generate risk scores

### Phase 3 — Design Suggestions
- Generate alternative design ideas based on risk output
- Ensure engineering feasibility
- Provide clear, structured reasoning

### Phase 4 — Innovation Analysis
- Analyze patterns across multiple patents
- Identify gaps and new idea directions

### User Interface
- Dashboard showing patent features, risk analysis, and suggestions
- Search, filtering, and visualization

---

## Non-Functional Requirements

- **Usability** — intuitive, low effort, clear outputs
- **Performance** — fast queries and analysis
- **Scalability** — handles large patent datasets
- **Explainability** — transparent AI outputs (critical for trust)
- **Security** — protect sensitive IP data
- **Maintainability** — modular architecture for easy iteration

---

## Team Split (6 People)

| Person | Role | Responsibilities |
|--------|------|-----------------|
| 1 | NLP / Data | Phase 1: patent collection, feature extraction, database |
| 2 | Risk Detection | Phase 2: comparison logic, conflict detection, risk scoring |
| 3 | Design Suggestions | Phase 3: alternative design generation, feasibility checks |
| 4 | Innovation Analysis | Phase 4: pattern recognition, gap identification |
| 5 | UI / Frontend | Dashboard, visualization, search & filtering |
| 6 | Evaluation & Integration | KPIs, user feedback, documentation, partner sync |

> Persons 1 & 2 should work closely together. Person 5 can prototype with dummy data early. Person 6 owns the monthly Fuyao sync.

---

## KPIs

- **Extraction Accuracy** — how correctly key features are identified from patents
- **Risk Detection Quality** — how well conflicts are detected
- **Suggestion Quality** — usefulness and feasibility (evaluated by experts)
- **Innovation Relevance** — whether proposed ideas are meaningful and practical
- **Usability** — clarity and usefulness from a user perspective

---

## Priority (MoSCoW)

- **Must have** — patent parsing (Phase 1) + risk detection (Phase 2)
- **Should have** — design improvement suggestions (Phase 3)
- **Could have** — innovation analysis (Phase 4), visual analytics
- **Won't have (now)** — full CAD integration, legal compliance automation

---

## Key Risks

- Data quality and availability of patent datasets
- NLP model performance on technical language
- CAD input support — confirm early if team has expertise
- Scope creep — stick to 4 phases, defer extras

---

## Additional Considerations

- Legal compliance with IP laws
- Explainability is essential for user trust in AI outputs
- Build modular — easier to iterate and scale
- Document everything for traceability with the partner