from tools.organizations.pappers import PappersTool

tool = PappersTool(api_token="dummy-token")


def test_name():
    assert tool.name() == "pappers"


def test_description():
    assert (
        tool.description()
        == "The Pappers API provides legal, financial, and beneficial ownership data for French companies."
    )


def test_category():
    assert tool.category() == "Business intelligence"
