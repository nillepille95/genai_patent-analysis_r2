from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .bootstrap import bootstrap_demo_data, import_patent_document, import_product_design
from .config import Settings, load_settings
from .database import initialize_database
from .models import PatentDocumentInput, ProductDesignInput
from .repository import PatentAnalysisRepository
from .services.extraction import FeatureExtractor
from .services.innovation import InnovationService
from .services.llm import OpenRouterClient
from .services.normalization import TextNormalizer
from .services.risk import RiskAnalyzer
from .services.suggestions import SuggestionService


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    repository: PatentAnalysisRepository
    extractor: FeatureExtractor
    risk_analyzer: RiskAnalyzer
    suggestion_service: SuggestionService
    innovation_service: InnovationService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    if settings.app.auto_init_db:
        initialize_database(settings.database.path)

    repository = PatentAnalysisRepository(settings.database.path)
    normalizer = TextNormalizer(settings.analysis.canonical_terms)
    llm_client = OpenRouterClient(settings.openrouter)
    extractor = FeatureExtractor(settings, normalizer, llm_client)
    services = ServiceContainer(
        settings=settings,
        repository=repository,
        extractor=extractor,
        risk_analyzer=RiskAnalyzer(settings, normalizer),
        suggestion_service=SuggestionService(llm_client),
        innovation_service=InnovationService(),
    )

    bootstrap_demo_data(settings, repository, extractor)

    app = FastAPI(title=settings.app.name)
    app.state.services = services
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    def render_template(request: Request, name: str, context: dict) -> HTMLResponse:
        base_context = {
            "request": request,
            "app_name": settings.app.name,
        }
        base_context.update(context)
        return templates.TemplateResponse(request=request, name=name, context=base_context)

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        metrics = repository.get_dashboard_metrics()
        recent_patents = repository.list_patents(limit=5)
        recent_assessments = repository.list_recent_assessments(limit=5)
        latest_innovation = repository.get_latest_innovation_insight()
        return render_template(
            request,
            "dashboard.html",
            {
                "title": "Dashboard",
                "metrics": metrics,
                "recent_patents": recent_patents,
                "recent_assessments": recent_assessments,
                "latest_innovation": latest_innovation,
                "nav": "dashboard",
                "settings_path": str(settings.config_path.relative_to(settings.root_dir)),
            },
        )

    @app.get("/patents", response_class=HTMLResponse)
    async def patent_list(request: Request, q: str = ""):
        patents = repository.list_patents(q)
        return render_template(
            request,
            "patents.html",
            {"title": "Patents", "patents": patents, "query": q, "nav": "patents"},
        )

    @app.post("/patents")
    async def create_patent(
        title: str = Form(...),
        patent_number: str = Form(""),
        source: str = Form("manual-entry"),
        partner_domain: str = Form("automotive glazing"),
        abstract_text: str = Form(""),
        claims_text: str = Form(""),
        description_text: str = Form(""),
    ):
        if not any(text.strip() for text in (abstract_text, claims_text, description_text)):
            raise HTTPException(status_code=400, detail="At least one patent section is required.")

        document = PatentDocumentInput(
            title=title,
            patent_number=patent_number,
            source=source,
            partner_domain=partner_domain,
            sections={
                "abstract": abstract_text,
                "claims": claims_text,
                "description": description_text,
            },
        )
        try:
            patent_id = import_patent_document(repository, extractor, document)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return RedirectResponse(url=f"/patents/{patent_id}", status_code=303)

    @app.get("/patents/{patent_id}", response_class=HTMLResponse)
    async def patent_detail(request: Request, patent_id: int):
        detail = repository.get_patent_detail(patent_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Patent not found.")
        return render_template(
            request,
            "patent_detail.html",
            {
                "title": detail["patent"]["title"],
                "detail": detail,
                "nav": "patents",
            },
        )

    @app.get("/designs", response_class=HTMLResponse)
    async def design_list(request: Request):
        designs = repository.list_product_designs()
        return render_template(
            request,
            "designs.html",
            {"title": "Product Designs", "designs": designs, "nav": "designs"},
        )

    @app.post("/designs")
    async def create_design(
        name: str = Form(...),
        raw_description: str = Form(...),
    ):
        design = ProductDesignInput(name=name, raw_description=raw_description)
        design_id = import_product_design(repository, extractor, design)
        return RedirectResponse(url=f"/designs/{design_id}", status_code=303)

    @app.get("/designs/{design_id}", response_class=HTMLResponse)
    async def design_detail(request: Request, design_id: int):
        detail = repository.get_product_design(design_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Product design not found.")
        return render_template(
            request,
            "design_detail.html",
            {
                "title": detail["design"]["name"],
                "detail": detail,
                "nav": "designs",
            },
        )

    @app.get("/analysis", response_class=HTMLResponse)
    async def analysis_home(request: Request):
        patents = repository.list_patents(limit=100)
        designs = repository.list_product_designs()
        assessments = repository.list_recent_assessments(limit=10)
        return render_template(
            request,
            "analysis.html",
            {
                "title": "Risk Analysis",
                "patents": patents,
                "designs": designs,
                "assessments": assessments,
                "nav": "analysis",
            },
        )

    @app.post("/analysis/run")
    async def run_analysis(
        product_design_id: int = Form(...),
        patent_id: int = Form(...),
    ):
        design_detail_record = repository.get_product_design(product_design_id)
        patent_detail_record = repository.get_patent_detail(patent_id)
        if design_detail_record is None or patent_detail_record is None:
            raise HTTPException(status_code=404, detail="Design or patent not found.")

        design = design_detail_record["design"]
        patent = patent_detail_record["patent"]
        design_features = design_detail_record["features"]
        patent_features = patent_detail_record["features"]

        result = services.risk_analyzer.analyze(
            design_name=design["name"],
            patent_title=patent["title"],
            design_features=design_features,
            patent_features=patent_features,
        )
        suggestions = services.suggestion_service.build_suggestions(
            design_name=design["name"],
            patent_title=patent["title"],
            risk_level=result["risk_level"],
            matches=result["matches"],
        )
        assessment_id = repository.create_risk_assessment(
            product_design_id=product_design_id,
            patent_id=patent_id,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            reasoning_summary=result["reasoning_summary"],
            matches=result["matches"],
            suggestions=suggestions,
        )
        return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=303)

    @app.get("/assessments/{assessment_id}", response_class=HTMLResponse)
    async def assessment_detail(request: Request, assessment_id: int):
        detail = repository.get_assessment_detail(assessment_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Assessment not found.")
        return render_template(
            request,
            "assessment_detail.html",
            {
                "title": f"Assessment {assessment_id}",
                "detail": detail,
                "nav": "analysis",
            },
        )

    @app.get("/innovation", response_class=HTMLResponse)
    async def innovation_page(request: Request):
        patents_with_features = repository.list_patents_with_features()
        live_summary = services.innovation_service.analyze(patents_with_features)
        latest_innovation = repository.get_latest_innovation_insight()
        return render_template(
            request,
            "innovation.html",
            {
                "title": "Innovation Opportunities",
                "insight": live_summary,
                "latest_innovation": latest_innovation,
                "nav": "innovation",
            },
        )

    @app.post("/innovation/run")
    async def run_innovation():
        patents_with_features = repository.list_patents_with_features()
        insight = services.innovation_service.analyze(patents_with_features)
        insight_id = repository.save_innovation_insight(insight)
        return RedirectResponse(url=f"/innovation?saved={insight_id}", status_code=303)

    return app
