import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime
from functools import lru_cache
from importlib import resources

from flowpilot_sandbox_api.arena.jml.schemas import (
    AccountFact,
    AssetFact,
    CatalogDocument,
    CatalogEntry,
    CatalogSummary,
    EmployeeFact,
    FactBundle,
    JmlInstance,
    JmlTemplate,
    JoinerValues,
    LeaverValues,
    MailboxFact,
    MoverValues,
    Process,
    SuppliedValues,
    TicketFact,
    Variant,
)

PROCESS_OFFSET: dict[Process, int] = {"joiner": 0, "mover": 12, "leaver": 20}
VARIANTS: tuple[Variant, ...] = ("v1", "v2", "v3")


def canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def catalog_checksum(document: CatalogDocument) -> str:
    payload = document.model_dump(mode="json", exclude={"catalog_checksum"})
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def instance_checksum(instance: JmlInstance) -> str:
    payload = instance.model_dump(mode="json", exclude={"canonical_checksum"})
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def _employee(
    *,
    employee_id: int,
    process: Process,
    local_number: int,
    variant_number: int,
    decoy: bool,
    department: str,
    job_title: str,
    location: str,
    status: str,
) -> EmployeeFact:
    kind = "decoy" if decoy else "target"
    return EmployeeFact.model_validate(
        {
            "id": employee_id,
            "first_name": f"Synthetic{kind.title()}",
            "last_name": f"{process.title()}{local_number:03d}V{variant_number}",
            "work_email": (
                f"w7-{process}-{local_number:03d}-v{variant_number}-{kind}@flowpilot.invalid"
            ),
            "department": department,
            "job_title": job_title,
            "location": location,
            "start_date": date(
                2027,
                ((local_number - 1) % 12) + 1,
                variant_number + 9,
            ),
            "status": status,
            "created_at": datetime(2027, 1, variant_number, tzinfo=UTC),
        }
    )


def generate_instance(template: JmlTemplate, variant: Variant) -> JmlInstance:
    local_number = int(template.template_id.rsplit("-", maxsplit=1)[1])
    variant_number = int(variant[1])
    ordinal = PROCESS_OFFSET[template.process] + local_number
    target_id = 41_000 + ordinal * 10 + variant_number
    decoy_id = target_id + 5_000
    record_base = 700_000 + ordinal * 100 + variant_number * 10
    old_department = f"Synthetic Department {(ordinal % 5) + 1}"
    old_job = f"Synthetic Specialist {(ordinal % 4) + 1}"
    old_location = f"Synthetic Location {(variant_number % 3) + 1}"
    new_department = f"Synthetic Transfer Department {(ordinal % 4) + 1}"
    new_job = f"Synthetic Transfer Lead {(local_number % 3) + 1}"
    new_location = f"Synthetic Transfer Location {variant_number}"

    initial_target = _employee(
        employee_id=target_id,
        process=template.process,
        local_number=local_number,
        variant_number=variant_number,
        decoy=False,
        department=old_department,
        job_title=old_job,
        location=old_location,
        status="confirmed",
    )
    decoy = _employee(
        employee_id=decoy_id,
        process=template.process,
        local_number=local_number,
        variant_number=variant_number,
        decoy=True,
        department="Synthetic Decoy Department",
        job_title="Synthetic Decoy Role",
        location="Synthetic Decoy Location",
        status="confirmed",
    )
    expected_target = initial_target
    if template.process == "mover":
        expected_target = initial_target.model_copy(
            update={
                "department": new_department,
                "job_title": new_job,
                "location": new_location,
                "status": "transferred",
            }
        )
    elif template.process == "leaver":
        expected_target = initial_target.model_copy(update={"status": "disabled"})

    ticket = TicketFact(
        id=record_base + 1,
        employee_id=target_id,
        title=f"W7 {template.process.title()} {local_number:03d} Variant {variant_number}",
        status="open",
    )
    account = AccountFact(
        id=record_base + 2,
        employee_id=target_id,
        username=f"w7.{template.process}{local_number:03d}v{variant_number}",
        role="employee",
        status="active",
    )
    asset = AssetFact(
        id=record_base + 3,
        employee_id=target_id,
        asset_tag=f"SYN-W7-{template.process.upper()}-{local_number:03d}-V{variant_number}",
        device_type="laptop",
        model=f"Synthetic Laptop {((ordinal + variant_number) % 4) + 1}",
        status="assigned",
    )
    mailbox = MailboxFact(
        id=record_base + 4,
        employee_id=target_id,
        address=f"w7.{template.process}{local_number:03d}v{variant_number}@flowpilot.invalid",
        status="active",
    )

    initial_bundle = FactBundle(
        target=initial_target,
        decoy=decoy,
        ticket=None if template.process == "joiner" else ticket,
        account=None if template.process == "joiner" else account,
        asset=None if template.process == "joiner" else asset,
        mailbox=None if template.process == "joiner" else mailbox,
    )
    expected_bundle = FactBundle(
        target=expected_target,
        decoy=decoy,
        ticket=ticket.model_copy(update={"status": "closed"})
        if template.process != "joiner"
        else ticket,
        account=account.model_copy(update={"status": "revoked"})
        if template.process == "leaver"
        else account,
        asset=asset.model_copy(update={"status": "released"})
        if template.process == "leaver"
        else asset,
        mailbox=mailbox.model_copy(update={"status": "disabled"})
        if template.process == "leaver"
        else mailbox,
    )

    supplied: SuppliedValues
    if template.process == "joiner":
        supplied = JoinerValues(
            employee_id=target_id,
            ticket_title=ticket.title,
            username=account.username,
            asset_tag=asset.asset_tag,
            laptop_model=asset.model,
            mailbox=mailbox.address,
        )
    elif template.process == "mover":
        supplied = MoverValues(
            employee_id=target_id,
            new_department=new_department,
            new_job_title=new_job,
            new_location=new_location,
        )
    else:
        supplied = LeaverValues(employee_id=target_id)

    instance = JmlInstance(
        schema_version="w7-jml-instance/1.0",
        task_id=f"{template.template_id}-{variant}",
        template_id=template.template_id,
        variant=variant,
        process=template.process,
        category=template.category,
        split=template.split,
        fixture_version="w7-jml-fixture/1.0",
        generator_version="w7-jml-variant-generator/1.0",
        human_brief=(
            f"Perform the bounded standard synthetic {template.process} process using only "
            "the supplied synthetic values. Independent grading remains external."
        ),
        supplied_values=supplied,
        initial_state=initial_bundle,
        expected_state=expected_bundle,
        canonical_checksum="0" * 64,
    )
    return instance.model_copy(update={"canonical_checksum": instance_checksum(instance)})


class JmlCatalog:
    def __init__(self, document: CatalogDocument) -> None:
        actual_checksum = catalog_checksum(document)
        if actual_checksum != document.catalog_checksum:
            raise ValueError(
                f"W7 catalog checksum mismatch: declared {document.catalog_checksum}, "
                f"calculated {actual_checksum}"
            )
        templates = tuple(sorted(document.templates, key=lambda item: item.template_id))
        self._validate_templates(templates)
        instances = tuple(
            generate_instance(template, variant) for template in templates for variant in VARIANTS
        )
        self.document = document
        self.templates = templates
        self.instances = instances
        self._by_id = {instance.task_id: instance for instance in instances}

    @classmethod
    def from_package(cls) -> "JmlCatalog":
        data = resources.files("flowpilot_sandbox_api.arena.jml").joinpath(
            "data", "catalog-v1.json"
        )
        return cls(CatalogDocument.model_validate_json(data.read_text(encoding="utf-8")))

    @staticmethod
    def _validate_templates(templates: tuple[JmlTemplate, ...]) -> None:
        expected = tuple(
            [f"w7-jml-joiner-{number:03d}" for number in range(1, 13)]
            + [f"w7-jml-mover-{number:03d}" for number in range(1, 9)]
            + [f"w7-jml-leaver-{number:03d}" for number in range(1, 11)]
        )
        if tuple(template.template_id for template in templates) != tuple(sorted(expected)):
            raise ValueError("W7 catalog must contain the exact 30 frozen template IDs")
        process_counts = Counter(template.process for template in templates)
        split_counts = Counter(template.split for template in templates)
        if process_counts != {"joiner": 12, "mover": 8, "leaver": 10}:
            raise ValueError("W7 process distribution must be 12/8/10")
        if split_counts != {"development": 18, "validation": 6, "reporting": 6}:
            raise ValueError("W7 split distribution must be 18/6/6")
        expected_process_split = {
            ("joiner", "development"): 8,
            ("joiner", "validation"): 2,
            ("joiner", "reporting"): 2,
            ("mover", "development"): 4,
            ("mover", "validation"): 2,
            ("mover", "reporting"): 2,
            ("leaver", "development"): 6,
            ("leaver", "validation"): 2,
            ("leaver", "reporting"): 2,
        }
        if Counter((item.process, item.split) for item in templates) != expected_process_split:
            raise ValueError("W7 process-specific split distribution is invalid")

    def get(self, task_id: str) -> JmlInstance:
        try:
            return self._by_id[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown W7 JML task: {task_id}") from exc

    def entries(self) -> tuple[CatalogEntry, ...]:
        return tuple(
            CatalogEntry(
                task_id=item.task_id,
                template_id=item.template_id,
                variant=item.variant,
                process=item.process,
                split=item.split,
                fixture_version=item.fixture_version,
                canonical_checksum=item.canonical_checksum,
            )
            for item in self.instances
        )

    @property
    def split_manifest_checksum(self) -> str:
        rows = [
            {
                "task_id": item.task_id,
                "template_id": item.template_id,
                "split": item.split,
                "checksum": item.canonical_checksum,
            }
            for item in self.instances
        ]
        return hashlib.sha256(canonical_bytes(rows)).hexdigest()

    @property
    def reporting_manifest_checksum(self) -> str:
        rows = [
            {"task_id": item.task_id, "checksum": item.canonical_checksum}
            for item in self.instances
            if item.split == "reporting"
        ]
        return hashlib.sha256(canonical_bytes(rows)).hexdigest()

    def summary(self) -> CatalogSummary:
        return CatalogSummary(
            template_count=30,
            instance_count=90,
            joiner_templates=12,
            mover_templates=8,
            leaver_templates=10,
            development_templates=18,
            validation_templates=6,
            reporting_templates=6,
            catalog_checksum=self.document.catalog_checksum,
            split_manifest_checksum=self.split_manifest_checksum,
            reporting_manifest_checksum=self.reporting_manifest_checksum,
        )


@lru_cache
def get_catalog() -> JmlCatalog:
    return JmlCatalog.from_package()
