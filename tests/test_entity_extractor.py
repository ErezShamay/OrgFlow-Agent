from app.agent.entity_extractor import EntityExtractor


def test_extract_project_name():
    extractor = EntityExtractor()

    result = extractor.extract_project_name(
        "סכם לי את הסטטוס של פרויקט מגדלי הצפון"
    )

    assert result == "מגדלי הצפון"