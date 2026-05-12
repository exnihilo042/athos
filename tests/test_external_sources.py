from core import external_sources


def test_external_sources_catalog_includes_repos_and_academic_sources():
    catalog = external_sources.catalog()
    source_ids = {source["id"] for source in catalog["open_source"]}
    academic_ids = {source["id"] for source in catalog["academic"]}

    assert {"garrytan/gstack", "garrytan/gbrain", "fathah/hermes-desktop"} <= source_ids
    assert "w3c-prov-2013" in academic_ids
    assert catalog["summary"]["mit_sources"] == 3


def test_imported_patterns_are_deduplicated():
    patterns = external_sources.imported_patterns()

    assert "provider_model_profile_registry" in patterns
    assert "compiled_truth_plus_append_only_timeline" in patterns
