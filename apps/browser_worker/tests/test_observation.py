from typing import Any

from flowpilot_browser_worker.config import WorkerLimits
from flowpilot_browser_worker.observation import (
    INTERACTIVE_SELECTOR,
    SEMANTIC_SELECTOR,
    ObservationBuilder,
)


def metadata(
    tag: str,
    role: str,
    name: str,
    text: str,
    *,
    visible: bool = True,
    input_type: str = "",
    options: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "tag": tag,
        "role": role,
        "name": name,
        "text": text,
        "inputType": input_type,
        "disabled": False,
        "checked": None,
        "selected": None,
        "expanded": None,
        "readonly": False,
        "required": False,
        "options": options or [],
        "visible": visible,
        "value": "SECRET-FORM-VALUE",
    }


class FakeItem:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    async def is_visible(self) -> bool:
        return bool(self.value["visible"])

    async def evaluate(self, _: str) -> dict[str, Any]:
        return self.value


class FakeCollection:
    def __init__(self, values: list[dict[str, Any]]) -> None:
        self.values = values

    async def count(self) -> int:
        return len(self.values)

    def nth(self, index: int) -> FakeItem:
        return FakeItem(self.values[index])


class FakePage:
    url = "http://sandbox-web/hris"

    def __init__(self, semantic: list[dict[str, Any]], interactive: list[dict[str, Any]]) -> None:
        self.semantic = semantic
        self.interactive = interactive

    def locator(self, selector: str) -> FakeCollection:
        if selector == SEMANTIC_SELECTOR:
            return FakeCollection(self.semantic)
        assert selector == INTERACTIVE_SELECTOR
        return FakeCollection(self.interactive)

    async def title(self) -> str:
        return "  Synthetic   HRIS  "


async def test_observation_is_stable_filtered_and_never_returns_form_values() -> None:
    semantic = [
        metadata("h1", "heading", "Employees", " Employees "),
        metadata("p", "paragraph", "", "hidden text", visible=False),
        metadata("p", "paragraph", "", "x" * 400),
    ]
    interactive = [
        metadata("input", "textbox", "Work email", "", input_type="email"),
        metadata(
            "select",
            "combobox",
            "Device",
            "",
            options=[{"label": "Laptop", "value": "internal-laptop-value"}],
        ),
    ]
    limits = WorkerLimits(max_node_text_chars=20)
    page = FakePage(semantic, interactive)
    first = await ObservationBuilder(limits, lambda: "stable123").build(page, "bw_abcdefghijklmnop")
    second = await ObservationBuilder(limits, lambda: "stable123").build(
        page, "bw_abcdefghijklmnop"
    )

    assert first.observation.model_dump_json() == second.observation.model_dump_json()
    assert [node.text for node in first.observation.semantic_nodes] == ["Employees", "x" * 20]
    assert first.observation.page_title == "Synthetic HRIS"
    assert first.observation.interactive_elements[1].options == ("Laptop",)
    serialized = first.observation.model_dump_json()
    assert "SECRET-FORM-VALUE" not in serialized
    assert "internal-laptop-value" not in serialized


async def test_observation_enforces_node_element_and_serialized_limits() -> None:
    semantic = [metadata("p", "paragraph", "", f"node-{index}-" + "x" * 100) for index in range(8)]
    interactive = [metadata("button", "button", f"Button {index}", "") for index in range(8)]
    limits = WorkerLimits(
        max_semantic_nodes=3,
        max_interactive_elements=2,
        max_node_text_chars=40,
        max_observation_bytes=1_400,
    )
    built = await ObservationBuilder(limits, lambda: "limited12").build(
        FakePage(semantic, interactive), "bw_abcdefghijklmnop"
    )
    assert built.observation.truncated is True
    assert len(built.observation.semantic_nodes) <= 3
    assert len(built.observation.interactive_elements) <= 2
    assert len(built.observation.model_dump_json().encode("utf-8")) <= 1_400
    assert set(built.references) == {
        item.element_ref for item in built.observation.interactive_elements
    }
