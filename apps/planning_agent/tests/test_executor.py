from flowpilot_planning_agent.budget import TotalBudgetLedger
from flowpilot_planning_agent.executor import PlanningExecutor
from flowpilot_planning_agent.schemas import JoinerSuppliedValues, PlanningRunRequest
from flowpilot_planning_agent.worker_schemas import (
    DomObservation,
    ElementState,
    HybridActionResult,
    HybridDomObservation,
    HybridRouteSignals,
    HybridSessionCreated,
    InteractiveElement,
)


class FakeBrowser:
    def __init__(self) -> None:
        self.session_id = "bw_1234567890abcdef"
        self.page = "/hris"
        self.generation = 0
        self.closed = 0

    def observation(self) -> HybridDomObservation:
        self.generation += 1
        names = {
            "/hris": (
                ("Show transitions", ("click", "read")),
                ("Synthetic record", ("read",)),
                ("Transfer employee ID", ("fill", "read")),
                ("New department", ("fill", "read")),
                ("New job title", ("fill", "read")),
                ("New location", ("fill", "read")),
                ("Transfer employee", ("click", "read")),
                ("Disable employee ID", ("fill", "read")),
                ("Disable employee", ("click", "read")),
            ),
            "/itsm": (
                ("Show transitions", ("click", "read")),
                ("Synthetic record", ("read",)),
                ("Employee ID", ("fill", "read")),
                ("Ticket title", ("fill", "read")),
                ("Create ticket", ("click", "read")),
                ("Close ticket employee ID", ("fill", "read")),
                ("Close ticket", ("click", "read")),
            ),
            "/iam": (
                ("Show transitions", ("click", "read")),
                ("Synthetic record", ("read",)),
                ("Employee ID", ("fill", "read")),
                ("Username", ("fill", "read")),
                ("Create account", ("click", "read")),
                ("Revoke account employee ID", ("fill", "read")),
                ("Revoke account", ("click", "read")),
            ),
            "/assets": (
                ("Show transitions", ("click", "read")),
                ("Synthetic record", ("read",)),
                ("Employee ID", ("fill", "read")),
                ("Asset tag", ("fill", "read")),
                ("Model", ("fill", "read")),
                ("Assign laptop", ("click", "read")),
                ("Release asset employee ID", ("fill", "read")),
                ("Release asset", ("click", "read")),
            ),
            "/mail": (
                ("Show transitions", ("click", "read")),
                ("Synthetic record", ("read",)),
                ("Employee ID", ("fill", "read")),
                ("Mailbox address", ("fill", "read")),
                ("Create mailbox", ("click", "read")),
                ("Disable mailbox employee ID", ("fill", "read")),
                ("Disable mailbox", ("click", "read")),
            ),
        }[self.page]
        elements = tuple(
            InteractiveElement(
                element_ref=f"ref_{self.generation:08d}_{index:02d}",
                role="button" if "click" in actions else "textbox",
                name=name,
                state=ElementState(),
                allowed_actions=actions,
            )
            for index, (name, actions) in enumerate(names, start=1)
        )
        observation = DomObservation(
            schema_version="w4-dom-observation/1.0",
            session_id=self.session_id,
            observation_id=f"obs_{self.generation:08d}",
            current_url=f"http://sandbox-web{self.page}",
            page_title="Synthetic page",
            semantic_nodes=(),
            interactive_elements=elements,
            truncated=False,
        )
        return HybridDomObservation(
            schema_version="w6-hybrid-observation/1.0",
            session_id=self.session_id,
            generation=self.generation,
            modality="dom",
            observation=observation,
            route_signals=HybridRouteSignals(
                dom_structure="usable",
                dom_interactive_count=len(elements),
                dom_observation_bytes=1_000,
            ),
        )

    async def create_session(self) -> HybridSessionCreated:
        return HybridSessionCreated(
            schema_version="w6-hybrid-session/1.0",
            session_id=self.session_id,
            observation=self.observation(),
        )

    async def request_dom_observation(self, session_id: str) -> HybridDomObservation:
        assert session_id == self.session_id
        return self.observation()

    async def execute_action(self, session_id: str, envelope) -> HybridActionResult:
        assert session_id == self.session_id
        action = envelope.action
        if action.type == "navigate":
            self.page = action.url
        terminal = action.type == "finish"
        return HybridActionResult(
            schema_version="w6-hybrid-action-result/1.0",
            session_id=self.session_id,
            action_id=action.action_id,
            modality="dom",
            action_type=action.type,
            success=True,
            terminal=terminal,
            message="bounded fake action",
            observation=None if terminal else self.observation(),
        )

    async def close_session(self, session_id: str) -> None:
        assert session_id == self.session_id
        self.closed += 1


def request(scenario: str = "complete_with_rejection_probe") -> PlanningRunRequest:
    return PlanningRunRequest(
        run_id="run_12345678",
        task_id="w3-joiner-001",
        process="joiner",
        category="standard_joiner",
        human_brief="Bounded synthetic joiner brief.",
        supplied_values=JoinerSuppliedValues(
            employee_id=31001,
            ticket_title="Provision synthetic joiner",
            username="synthetic.joiner",
            asset_tag="SYN-W7-JOINER",
            laptop_model="Synthetic Laptop",
            mailbox="synthetic.joiner@flowpilot.invalid",
        ),
        fake_scenario=scenario,
    )


async def test_executor_runs_multi_dependency_dag_and_cleans_up() -> None:
    browser = FakeBrowser()
    payload = request()
    ledger = TotalBudgetLedger(payload.budget)
    ledger.charge_context_assembly()
    ledger.charge_context_item(canonical_bytes=100, estimated_tokens=25)
    result = await PlanningExecutor(browser).run(payload, ledger=ledger)  # type: ignore[arg-type]
    assert result.status == "finished_ungraded"
    assert len(result.step_results) == 6
    assert all(item.state == "verified" for item in result.step_results)
    assert result.tool_rejection_reasons == ("unknown_tool",)
    assert result.usage.verifier_calls == 6
    assert result.usage.verifier_probes == 1
    assert result.usage.worker_actions == 22
    assert result.usage.cost_microusd == 0
    assert result.usage.context_assemblies == 1
    assert result.usage.context_items == 1
    assert browser.closed == 1


async def test_inconclusive_verifier_is_not_success_and_cleans_up() -> None:
    browser = FakeBrowser()
    result = await PlanningExecutor(browser).run(request("verifier_inconclusive"))  # type: ignore[arg-type]
    assert result.status == "verification_inconclusive"
    assert result.step_results[0].state == "failed"
    assert result.step_results[0].verifier is not None
    assert result.step_results[0].verifier.status == "inconclusive"
    assert browser.closed == 1


async def test_immediate_finish_remains_ungraded() -> None:
    browser = FakeBrowser()
    result = await PlanningExecutor(browser).run(request("finish_immediately"))  # type: ignore[arg-type]
    assert result.status == "finished_ungraded"
    assert result.step_results == ()
    assert browser.closed == 1


async def test_out_of_order_probe_is_blocked_and_cleaned_up() -> None:
    browser = FakeBrowser()
    result = await PlanningExecutor(browser).run(request("out_of_order_probe"))  # type: ignore[arg-type]
    assert result.status == "dependency_blocked"
    assert result.step_results[0].state == "blocked"
    assert result.usage.worker_actions == 0
    assert browser.closed == 1
