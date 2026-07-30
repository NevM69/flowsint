from tools.social.hikerapi import HikerAPITool

tool = HikerAPITool(access_key="dummy-token")


def test_name():
    assert tool.name() == "hikerapi"


def test_description():
    assert (
        tool.description()
        == "HikerAPI provides read access to public Instagram profile data (used by Osintgram)."
    )


def test_category():
    assert tool.category() == "Social intelligence"
