import pytest

from pitt_save import catalog, model


def test_catalog_milestones_are_unique_and_not_actions():
    assert len(catalog.MILESTONES) == 135
    assert len(set(catalog.MILESTONES)) == 135
    assert "unlock_sprint" in catalog.MILESTONES
    assert "unlock_tool_level" not in catalog.MILESTONES


@pytest.mark.parametrize("old, text, expected", [
    (True, "false", False), (False, " TRUE ", True), (False, "1", True),
    (3, " 12 ", 12), (0.0, "2.5", 2.5), (1.0, "7", 7.0),
    ("abc", " keeps spaces ", " keeps spaces "), (None, "null", None),
])
def test_coerce_like(old, text, expected):
    result = model.coerce_like(old, text)
    assert result == expected and type(result) is type(expected)


@pytest.mark.parametrize("old, text", [
    (True, "maybe"), (3, "1.5"), (0.0, "abc"), (0.0, "inf"), (None, "0"), ({}, "{}"), ([], "[]"),
])
def test_coerce_like_rejects(old, text):
    with pytest.raises(ValueError):
        model.coerce_like(old, text)


def test_parse_bigint():
    assert model.parse_bigint(" 6000 ") == "6000"
    assert model.parse_bigint("007") == "7"
    assert model.parse_bigint("123456789012345678901234567890") == "123456789012345678901234567890"
    for bad in ("", "1e9", "-5", "12a", "1 000"):
        with pytest.raises(ValueError):
            model.parse_bigint(bad)


def test_parse_count_and_resource():
    assert model.parse_count(1, "3") == 3
    with pytest.raises(ValueError):
        model.parse_count(1, "-1")
    assert model.parse_resource("6", "6000") == "6000"
    assert model.parse_resource(0.0, "5000") == 5000.0
    assert model.parse_resource(0, "12") == 12
    with pytest.raises(ValueError):
        model.parse_resource(0.0, "-1")


def test_format_and_preview():
    assert model.format_value(True) == "true"
    assert model.format_value(None) == "null"
    assert model.format_value(2.5) == "2.5"
    assert model.format_value("x y") == "x y"
    assert model.preview("6") == '"6"'
    assert model.preview({"a": 1, "b": 2}) == "{2 keys}"
    assert model.preview([1]) == "[1 item]"
    assert model.type_name(1.0) == "number"


def test_get_in():
    data = {"a": {"b": [10, {"c": 3}]}}
    assert model.get_in(data, ()) is data
    assert model.get_in(data, ("a", "b", 1, "c")) == 3


def test_level_nodes_with_products():
    game_state = {
        "tools": {"box": {"enabled": True, "level": 0}},
        "products": {"duck": {"auto_machine": {"level": 0}, "craft_speed": {"level": 1}, "enabled": True}},
    }
    assert model.level_nodes(game_state, "tools") == [model.LevelNode(("tools", "box"), [])]
    assert model.level_nodes(game_state, "products") == [model.LevelNode(
        ("products", "duck"), [("products", "duck", "auto_machine"), ("products", "duck", "craft_speed")])]
    assert model.level_nodes(game_state, "toys") == []


def test_milestone_rows_and_set_milestone():
    data = {"unlocked_milestones": ["unlock_jump", "custom_event", "unlock_jump"]}
    rows = model.milestone_rows(data)
    assert rows[0] == ("unlock_sprint", False)
    assert ("unlock_jump", True) in rows
    assert rows[-1] == ("custom_event", True)
    assert len(rows) == 136

    model.set_milestone(data, "unlock_sprint", True)
    model.set_milestone(data, "unlock_sprint", True)
    assert data["unlocked_milestones"] == ["unlock_jump", "custom_event", "unlock_jump", "unlock_sprint"]
    model.set_milestone(data, "unlock_jump", False)
    assert data["unlocked_milestones"] == ["custom_event", "unlock_sprint"]

    empty = {}
    model.set_milestone(empty, "unlock_box", True)
    assert empty == {"unlocked_milestones": ["unlock_box"]}
