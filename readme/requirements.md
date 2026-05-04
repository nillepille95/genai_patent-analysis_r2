# Requirements Specification

## 1. Project Overview

### 1.1 Project Title
AI-based Patent Analysis, Design-Around, and Innovation Recommendation

### 1.2 Business Context
The project is developed for Fuyao Europe to support patent understanding, product-risk assessment, design-around exploration, and innovation discovery. The system should help users analyze patent documents, compare them with product designs, identify overlap risks, and generate improvement or innovation suggestions.

### 1.3 Core Goal
Build an AI-supported software system that:
- reads and structures patent documents,
- compares product designs against patent content,
- highlights potential patent conflicts,
- suggests lower-risk design alternatives,
- identifies innovation opportunities across patent sets.

### 1.4 Development Principle
The project is phase-driven. Phase 1 is the dependency for all later phases. The implementation must therefore prioritize data extraction, normalization, and traceable storage before advanced analysis.

## 2. Problem Statement

Patent documents are long, technical, and difficult to compare manually against product designs. Teams need a system that can reduce this effort by extracting technical features from patents, mapping them to product features, and producing explainable risk and recommendation outputs.

## 3. Scope

### 3.1 In Scope
- Patent document ingestion
- Patent text parsing and feature extraction
- Structured patent storage
- Product design input through text and simplified annotations
- Patent-to-product comparison
- Risk scoring and conflict highlighting
- Design-around suggestion generation
- Multi-patent pattern analysis for innovation directions
- Dashboard or interface for search, review, and visualization
- Explainable outputs with traceability back to source text

### 3.2 Out of Scope for Initial Version
- Full CAD-native integration
- Automated legal compliance or legal advice
- Fully autonomous decision-making without human review
- Production-scale enterprise deployment

## 4. Stakeholders

- Project team
- Fuyao Europe partner representatives
- Future engineering/design users
- Academic evaluators

## 5. User Roles

### 5.1 Analyst
- Uploads or selects patent documents
- Reviews extracted technical features
- Runs comparison and risk analysis

### 5.2 Design Engineer
- Provides product design descriptions or feature lists
- Reviews risk overlaps
- Examines design-around suggestions

### 5.3 Project Evaluator or Product Owner
- Reviews KPIs, output quality, and usability
- Validates whether the system meets project objectives

## 6. System Objectives by Phase

### 6.1 Phase 1: Patent Understanding and Data Structuring
Objective: transform raw patent text into structured, reusable data.

The system must:
- ingest patent documents, at minimum claims and descriptions,
- extract technical features from patent text,
- preserve links between extracted features and their source passages,
- store patents and extracted features in a structured schema,
- support search and retrieval of patents and features.

Outputs:
- structured patent records,
- extracted feature lists,
- source-linked evidence spans,
- database schema or data model.

### 6.2 Phase 2: Risk Identification
Objective: detect potential overlap between a product design and patent content.

The system must:
- accept product design input as text, key-feature lists, or simplified descriptions,
- normalize design features into the same comparison format used for patents,
- compare product features against patent features,
- identify direct and partial overlaps,
- flag critical features that may create conflict risk,
- assign explainable risk scores.

Outputs:
- overlap report,
- matched feature pairs,
- conflict highlights,
- per-patent and overall risk score,
- reasoning trace for each score.

### 6.3 Phase 3: Design Improvement Suggestions
Objective: recommend lower-risk alternative design directions.

The system must:
- use risk-analysis results as input,
- generate alternative design ideas that reduce identified overlap,
- explain why each suggestion may reduce patent risk,
- present suggestions in a structured format,
- support feasibility review from an engineering perspective.

Outputs:
- alternative design suggestions,
- rationale for each suggestion,
- risk-reduction explanation,
- feasibility notes or review fields.

### 6.4 Phase 4: Innovation Opportunities
Objective: discover new opportunities by analyzing multiple patents together.

The system must:
- analyze multiple patents as a collection,
- identify common patterns, clusters, and feature concentration areas,
- detect potential white-space or gap areas,
- suggest innovation directions or new idea themes.

Outputs:
- cluster or pattern insights,
- gap analysis summaries,
- innovation opportunity recommendations.

## 7. Functional Requirements

### 7.1 Patent Ingestion
- The system shall accept patent files or patent text input.
- The system shall store document metadata such as title, patent identifier, source, and section type when available.
- The system shall separate at least claims, description, and optional abstract sections.

### 7.2 Feature Extraction
- The system shall extract candidate technical features from claims and descriptions.
- The system shall distinguish between raw extracted phrases and normalized feature representations.
- The system shall retain source references for each extracted feature.
- The system shall allow manual review or correction of extracted features.

### 7.3 Structured Storage
- The system shall store patents, sections, extracted features, normalized features, and source evidence in a queryable format.
- The system shall support one-to-many relationships between patents and features.
- The system shall support future extension to embeddings, tags, and similarity scores.

### 7.4 Product Design Input
- The system shall accept product input as free text, bullet-point features, or simplified annotations.
- The system shall parse design input into normalized features comparable to patent features.
- The system shall support saving and reusing product design profiles.

### 7.5 Comparison Engine
- The system shall compare normalized design features with normalized patent features.
- The system shall support direct, semantic, and partial-match comparison logic.
- The system shall output evidence-backed match results.

### 7.6 Risk Scoring
- The system shall compute a risk score for each patent relative to a product design.
- The system shall expose the factors that contributed to the score.
- The system shall mark high-risk feature overlaps explicitly.
- The scoring logic shall be transparent enough to justify results to users.

### 7.7 Suggestion Generation
- The system shall generate design-around suggestions only after risk detection has been completed.
- The system shall tie each suggestion to one or more specific risk findings.
- The system shall produce clear reasoning for why the suggestion may lower conflict risk.

### 7.8 Innovation Analysis
- The system shall support analysis across multiple patents, not just single patent comparisons.
- The system shall identify repeated technical themes and underexplored spaces.
- The system shall produce structured innovation recommendations.

### 7.9 User Interface
- The system shall provide a dashboard for browsing patents and results.
- The system shall provide search and filtering on patents and features.
- The system shall display extracted features, risk results, and suggestions in a readable form.
- The system shall visualize comparisons and highlight conflict areas.

## 8. Non-Functional Requirements

### 8.1 Usability
- Outputs must be easy to interpret by non-ML specialists.
- The interface must minimize effort for reviewing features and risks.

### 8.2 Explainability
- Every important output must link back to source evidence or explicit scoring logic.
- AI-generated suggestions must include rationale.

### 8.3 Performance
- Phase 1 parsing and Phase 2 comparison should respond fast enough for interactive review on small to medium datasets.
- Search and retrieval should feel immediate for the prototype dataset.

### 8.4 Scalability
- The architecture must allow later growth in dataset size and model sophistication.
- Storage design must support adding more patents without schema redesign.

### 8.5 Security
- Sensitive partner-related design data must be protected.
- Access to internal data should be limited in a real deployment context.

### 8.6 Maintainability
- The codebase must be modular by pipeline stage.
- Models, prompts, extractors, and scoring logic should be replaceable independently.

## 9. Assumptions

- The first version will work primarily on text-based patent documents.
- Product design input will initially be simplified into text or manually extracted features.
- Human review is required before treating any risk result as actionable.
- Legal review remains outside the system.

## 10. Constraints and Risks

### 10.1 Constraints
- Patent language is technical and ambiguous.
- Labeled evaluation data may be limited.
- Full CAD handling is not currently a must-have.

### 10.2 Project Risks
- Weak extraction quality in Phase 1 will degrade all later phases.
- Poor explainability may reduce trust in risk outputs.
- Scope creep into legal automation or full CAD workflows may delay delivery.

## 11. Data Model Requirements

The first development iteration should support at least the following entities:

- `Patent`
  - `id`
  - `title`
  - `patent_number`
  - `source`
  - `partner_domain`
  - `raw_text`

- `PatentSection`
  - `id`
  - `patent_id`
  - `section_type`
  - `section_text`

- `ExtractedFeature`
  - `id`
  - `patent_id`
  - `section_id`
  - `raw_feature_text`
  - `normalized_feature`
  - `confidence`
  - `evidence_span`

- `ProductDesign`
  - `id`
  - `name`
  - `raw_description`
  - `normalized_features`

- `RiskAssessment`
  - `id`
  - `product_design_id`
  - `patent_id`
  - `risk_score`
  - `risk_level`
  - `reasoning_summary`

- `FeatureMatch`
  - `id`
  - `risk_assessment_id`
  - `design_feature`
  - `patent_feature_id`
  - `match_type`
  - `match_score`
  - `evidence`

- `DesignSuggestion`
  - `id`
  - `risk_assessment_id`
  - `suggestion_text`
  - `rationale`
  - `feasibility_note`

- `InnovationInsight`
  - `id`
  - `scope`
  - `pattern_summary`
  - `gap_summary`
  - `recommendation`

## 12. Logical Architecture

The software should be organized into the following modules:

### 12.1 Ingestion Module
- reads patent source files,
- cleans and splits sections,
- stores raw patent content.

### 12.2 NLP Extraction Module
- extracts technical features,
- normalizes terminology,
- attaches confidence and evidence.

### 12.3 Data Storage Layer
- persists patent, design, and analysis data,
- exposes retrieval methods for later modules.

### 12.4 Comparison and Risk Module
- compares product and patent features,
- computes overlap and risk scores,
- produces explainable findings.

### 12.5 Recommendation Module
- generates design-around suggestions,
- formats structured outputs,
- links suggestions to risks.

### 12.6 Innovation Analysis Module
- aggregates multiple patents,
- detects patterns and gaps,
- proposes innovation directions.

### 12.7 Interface Layer
- dashboard,
- search and filtering,
- review screens for extraction and risk outputs.

## 13. End-to-End Workflow

1. User uploads or selects one or more patent documents.
2. System parses the documents into sections.
3. System extracts and normalizes technical features.
4. User reviews the extracted structured data if needed.
5. User submits a product design description or feature list.
6. System extracts and normalizes product features.
7. System compares product features with patent features.
8. System produces risk scores and overlap explanations.
9. System generates design-around suggestions for risky overlaps.
10. System optionally analyzes multiple patents for innovation opportunities.
11. User reviews outputs in the dashboard.

## 14. KPI and Evaluation Requirements

The system should be evaluated against the following criteria:

- Extraction Accuracy
  - how well technical features are identified from patents
- Risk Identification Quality
  - how well potential conflicts are detected
- Suggestion Quality
  - usefulness and feasibility of design suggestions
- Innovation Relevance
  - whether proposed new directions are meaningful and practical
- Usability
  - clarity and usefulness from a user perspective

Prototype evaluation should include:
- a small benchmark patent set,
- a set of example product descriptions,
- manual expert review or rubric-based scoring,
- comparison of system output against expected or reviewed findings.

## 15. Prioritization

### Must Have
- Patent ingestion
- Patent section parsing
- Technical feature extraction
- Structured patent database or schema
- Product design input
- Patent-product comparison
- Explainable risk scoring

### Should Have
- Design-around suggestion generation
- Dashboard with search and filtering
- Manual review support for extracted features

### Could Have
- Innovation opportunity analysis
- Advanced visualization
- Embedding-based similarity improvement

### Won't Have for Now
- Full CAD integration
- Legal compliance automation

## 16. Development-Ready Acceptance Criteria

### For Phase 1
- A patent can be loaded into the system and stored.
- The system can display claims and description as separate sections.
- The system can extract a usable list of technical features.
- Each extracted feature is traceable to source text.

### For Phase 2
- A product description can be entered and stored.
- The system can compare product features to patent features.
- The system can produce a risk score and explain it with matched evidence.

### For Phase 3
- The system can generate at least one structured design-around suggestion from a risk result.
- Each suggestion references the risk finding it addresses.

### For Phase 4
- The system can analyze a set of patents together and produce at least one pattern or gap insight.

## 17. Transition to Software Development

This section translates the requirements into an implementation path.

### Step 1: Define the prototype boundary
Build the first usable version around:
- text-based patents,
- text-based product design input,
- one end-to-end flow covering Phase 1 and Phase 2.

Reason:
This delivers the minimum meaningful product and unlocks later suggestion modules.

### Step 2: Freeze the first data schema
Implement the core entities:
- `Patent`
- `PatentSection`
- `ExtractedFeature`
- `ProductDesign`
- `RiskAssessment`
- `FeatureMatch`

Reason:
The schema is the contract between ingestion, extraction, comparison, and UI.

### Step 3: Build the ingestion pipeline
Development tasks:
- add patent file loading,
- parse raw text into sections,
- persist raw and cleaned content,
- create test fixtures with sample patents.

Deliverable:
a repeatable patent import pipeline.

### Step 4: Implement feature extraction
Development tasks:
- define extraction rules or prompts,
- generate normalized features,
- store evidence spans and confidence values,
- create an evaluation script for extraction quality.

Deliverable:
structured patent features ready for downstream comparison.

### Step 5: Implement product-design parsing
Development tasks:
- accept free-text design descriptions,
- normalize product features into the same format as patent features,
- store reusable design profiles.

Deliverable:
comparable product-design feature sets.

### Step 6: Build the comparison and scoring engine
Development tasks:
- define feature matching logic,
- distinguish direct, partial, and semantic matches,
- compute a transparent risk score,
- store match evidence.

Deliverable:
per-patent risk assessments with explanations.

### Step 7: Create the first review interface
Development tasks:
- show patents and extracted features,
- show submitted product design features,
- show risk results and matched evidence,
- support filtering and search.

Deliverable:
a usable prototype dashboard for demonstration.

### Step 8: Add design-around suggestions
Development tasks:
- feed risk findings into a recommendation module,
- return structured suggestion outputs,
- capture rationale and optional feasibility notes.

Deliverable:
Phase 3 prototype output.

### Step 9: Add innovation analysis
Development tasks:
- aggregate feature patterns across patents,
- identify clusters or gaps,
- produce structured opportunity suggestions.

Deliverable:
Phase 4 prototype output.

### Step 10: Add evaluation and demo readiness
Development tasks:
- define benchmark examples,
- measure extraction and risk quality,
- collect qualitative feedback,
- prepare sample workflows for partner review.

Deliverable:
evaluation-ready project package.

## 18. Recommended Initial Engineering Backlog

### Epic A: Foundation
- Set up project structure
- Choose storage approach
- Create data schema
- Add sample patent dataset

### Epic B: Patent Processing
- Patent loader
- Section parser
- Feature extractor
- Feature-review support

### Epic C: Risk Analysis
- Product input parser
- Feature matcher
- Risk scoring service
- Risk explanation formatter

### Epic D: Recommendations
- Suggestion generation service
- Feasibility annotation support

### Epic E: UI
- Patent browser
- Feature viewer
- Risk dashboard
- Search and filtering

### Epic F: Evaluation
- Benchmark set
- KPI scripts
- Demo scenarios

## 19. Open Questions to Resolve Before Coding Expands

- What patent source format will be used most often: PDF, text export, or manual copy?
- Will the first version use rule-based extraction, LLM extraction, or a hybrid approach?
- How should risk scoring be calibrated: weighted rules, similarity thresholds, or model-based classification?
- How much manual review should the system support in the prototype?
- What level of design-feasibility assessment is realistic within the course scope?

## 20. Definition of Done for the First Coding Milestone

The first milestone is complete when:
- a patent can be ingested,
- features can be extracted and stored,
- a product description can be entered,
- a risk report can be generated with explainable evidence,
- the result can be reviewed in a simple interface or structured output view.

This milestone should be treated as the handoff point from requirements engineering into active implementation of the core product.
