from __future__ import annotations

from .config import Settings
from .models import PatentDocumentInput, ProductDesignInput
from .repository import PatentAnalysisRepository
from .services.extraction import FeatureExtractor
from .sources import build_source_registry


def import_patent_document(
    repository: PatentAnalysisRepository,
    extractor: FeatureExtractor,
    document: PatentDocumentInput,
) -> int:
    extracted_features_by_section = {
        section_type: extractor.extract_section_features(section_text, section_type)
        for section_type, section_text in document.sections.items()
        if section_text.strip()
    }
    return repository.create_patent(document, extracted_features_by_section)


def import_product_design(
    repository: PatentAnalysisRepository,
    extractor: FeatureExtractor,
    design: ProductDesignInput,
) -> int:
    extracted_features = extractor.extract_product_features(design.raw_description)
    return repository.create_product_design(design, extracted_features)


def bootstrap_demo_data(
    settings: Settings,
    repository: PatentAnalysisRepository,
    extractor: FeatureExtractor,
) -> None:
    source_registry = build_source_registry(settings)
    source = source_registry.get(settings.app.default_patent_source)
    if source is None:
        return

    bundle = source.load_bundle()

    if settings.app.auto_seed_demo and repository.count_patents() == 0:
        for document in bundle.patents:
            import_patent_document(repository, extractor, document)

    if settings.app.auto_seed_demo and repository.count_product_designs() == 0:
        for design in bundle.product_designs:
            import_product_design(repository, extractor, design)

