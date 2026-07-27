import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page

from flowpilot_browser_worker.config import WorkerLimits
from flowpilot_browser_worker.schemas import (
    AllowedElementAction,
    ElementState,
    InteractiveElement,
    LastAction,
    Observation,
    SemanticNode,
)

SEMANTIC_SELECTOR = "h1,h2,h3,h4,p,label,button,a,strong,span,em,article,li,td,th"
INTERACTIVE_SELECTOR = (
    "a,button,input,select,textarea,[role='button'],[role='link'],"
    "[role='checkbox'],[role='radio'],[role='combobox']"
)

_ELEMENT_METADATA_SCRIPT = """
(element) => {
  const tag = element.tagName.toLowerCase();
  const implicitRoles = {
    a: element.hasAttribute('href') ? 'link' : 'generic',
    button: 'button', h1: 'heading', h2: 'heading', h3: 'heading', h4: 'heading',
    input: ({checkbox: 'checkbox', radio: 'radio', submit: 'button', button: 'button'}
      [String(element.type || '').toLowerCase()] || 'textbox'),
    select: 'combobox', textarea: 'textbox', article: 'article', label: 'label',
    li: 'listitem', th: 'columnheader', td: 'cell', p: 'paragraph'
  };
  const labels = element.labels
    ? Array.from(element.labels).map((label) => label.innerText || '').join(' ')
    : '';
  const visibleText = String(element.innerText || '');
  const name = String(
    element.getAttribute('aria-label') || labels ||
    (tag === 'input' || tag === 'textarea' ? element.getAttribute('placeholder') : '') ||
    element.getAttribute('title') || visibleText || ''
  );
  const options = tag === 'select'
    ? Array.from(element.options).map((option) => ({
        label: String(option.label || option.textContent || option.value),
        value: String(option.value)
      }))
    : [];
  const nullableBoolean = (name) => {
    if (!element.hasAttribute(name)) return null;
    return element.getAttribute(name) !== 'false';
  };
  return {
    tag,
    role: String(element.getAttribute('role') || implicitRoles[tag] || 'generic'),
    name,
    text: visibleText,
    inputType: String(element.getAttribute('type') || ''),
    disabled: Boolean(element.disabled || element.getAttribute('aria-disabled') === 'true'),
    checked: typeof element.checked === 'boolean'
      ? Boolean(element.checked) : nullableBoolean('aria-checked'),
    selected: typeof element.selected === 'boolean'
      ? Boolean(element.selected) : nullableBoolean('aria-selected'),
    expanded: nullableBoolean('aria-expanded'),
    readonly: Boolean(element.readOnly || element.getAttribute('aria-readonly') === 'true'),
    required: Boolean(element.required || element.getAttribute('aria-required') === 'true'),
    options
  };
}
"""

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str, limit: int) -> str:
    return _WHITESPACE.sub(" ", value).strip()[:limit]


@dataclass(frozen=True, slots=True)
class ElementTarget:
    locator: Locator
    allowed_actions: tuple[AllowedElementAction, ...]
    input_type: str
    safe_name: str
    option_values: dict[str, str]


@dataclass(frozen=True, slots=True)
class ObservationBuild:
    observation: Observation
    references: dict[str, ElementTarget]


class ObservationBuilder:
    def __init__(
        self,
        limits: WorkerLimits,
        nonce_factory: Callable[[], str] | None = None,
    ) -> None:
        self._limits = limits
        self._nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(9))

    async def build(
        self,
        page: Page,
        session_id: str,
        last_action: LastAction | None = None,
        page_error: str | None = None,
    ) -> ObservationBuild:
        nonce = self._nonce_factory()
        observation_id = f"obs_{nonce}"
        semantic_nodes, semantic_truncated = await self._semantic_nodes(page)
        interactive, references, interactive_truncated = await self._interactive_elements(
            page, nonce
        )
        title = normalize_text(await page.title(), self._limits.max_page_title_chars)
        error = normalize_text(page_error, 300) if page_error else None
        truncated = semantic_truncated or interactive_truncated

        observation = Observation(
            session_id=session_id,
            observation_id=observation_id,
            current_url=page.url[:500],
            page_title=title,
            semantic_nodes=tuple(semantic_nodes),
            interactive_elements=tuple(interactive),
            last_action=last_action,
            page_error=error,
            truncated=truncated,
        )
        observation, references = self._fit_serialized_limit(observation, references)
        return ObservationBuild(observation=observation, references=references)

    async def _semantic_nodes(self, page: Page) -> tuple[list[SemanticNode], bool]:
        locator = page.locator(SEMANTIC_SELECTOR)
        count = await locator.count()
        truncated = count > self._limits.max_semantic_nodes
        nodes: list[SemanticNode] = []
        for index in range(min(count, self._limits.max_semantic_nodes)):
            item = locator.nth(index)
            try:
                if not await item.is_visible():
                    continue
                metadata = await item.evaluate(_ELEMENT_METADATA_SCRIPT)
                text = normalize_text(str(metadata["text"]), self._limits.max_node_text_chars)
                name = normalize_text(str(metadata["name"]), self._limits.max_node_text_chars)
                if not text and not name:
                    continue
                nodes.append(SemanticNode(role=str(metadata["role"])[:40], name=name, text=text))
            except PlaywrightError:
                continue
        return nodes, truncated

    async def _interactive_elements(
        self, page: Page, nonce: str
    ) -> tuple[list[InteractiveElement], dict[str, ElementTarget], bool]:
        locator = page.locator(INTERACTIVE_SELECTOR)
        count = await locator.count()
        truncated = count > self._limits.max_interactive_elements
        elements: list[InteractiveElement] = []
        references: dict[str, ElementTarget] = {}
        for index in range(min(count, self._limits.max_interactive_elements)):
            item = locator.nth(index)
            try:
                if not await item.is_visible():
                    continue
                metadata = await item.evaluate(_ELEMENT_METADATA_SCRIPT)
            except PlaywrightError:
                continue
            actions = self._allowed_actions(metadata)
            if not actions:
                continue
            element_ref = f"ref_{nonce}_{index + 1}"
            name = normalize_text(str(metadata["name"]), self._limits.max_node_text_chars)
            options = {
                normalize_text(str(option["label"]), 120): str(option["value"])
                for option in metadata["options"]
                if normalize_text(str(option["label"]), 120)
            }
            state = ElementState(
                disabled=bool(metadata["disabled"]),
                checked=metadata["checked"],
                selected=metadata["selected"],
                expanded=metadata["expanded"],
                readonly=bool(metadata["readonly"]),
                required=bool(metadata["required"]),
            )
            elements.append(
                InteractiveElement(
                    element_ref=element_ref,
                    role=str(metadata["role"])[:40],
                    name=name,
                    state=state,
                    allowed_actions=actions,
                    options=tuple(options),
                )
            )
            references[element_ref] = ElementTarget(
                locator=item,
                allowed_actions=actions,
                input_type=str(metadata["inputType"]),
                safe_name=name,
                option_values=options,
            )
        return elements, references, truncated

    @staticmethod
    def _allowed_actions(metadata: dict[str, object]) -> tuple[AllowedElementAction, ...]:
        if bool(metadata["disabled"]):
            return ()
        tag = str(metadata["tag"])
        role = str(metadata["role"])
        input_type = str(metadata["inputType"]).lower()
        if tag == "select" or role == "combobox":
            return ("select", "read", "scroll")
        if tag in {"input", "textarea"} and input_type not in {
            "button",
            "submit",
            "checkbox",
            "radio",
        }:
            return ("fill", "read", "scroll")
        if tag in {"a", "button"} or role in {"button", "link", "checkbox", "radio"}:
            return ("click", "read", "scroll")
        return ("read", "scroll")

    def _fit_serialized_limit(
        self, observation: Observation, references: dict[str, ElementTarget]
    ) -> tuple[Observation, dict[str, ElementTarget]]:
        semantic = list(observation.semantic_nodes)
        interactive = list(observation.interactive_elements)
        truncated = observation.truncated
        while (
            len(observation.model_dump_json().encode("utf-8")) > self._limits.max_observation_bytes
        ):
            truncated = True
            if semantic:
                semantic.pop()
            elif interactive:
                removed = interactive.pop()
                references.pop(removed.element_ref, None)
            else:
                break
            observation = observation.model_copy(
                update={
                    "semantic_nodes": tuple(semantic),
                    "interactive_elements": tuple(interactive),
                    "truncated": truncated,
                }
            )
        return observation, references
