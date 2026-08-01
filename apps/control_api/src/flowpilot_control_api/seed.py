"""Deterministic local-only W10 synthetic identity seed."""

import hashlib

from sqlalchemy.orm import Session

from flowpilot_control_api.config import OidcPolicy
from flowpilot_control_api.models import (
    ApprovalAuthority,
    AuditChainHead,
    Membership,
    OidcIdentity,
    Organization,
    User,
)

SYNTHETIC_IDENTITIES: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_admin_0001",
        "idn_syn_alpha_admin_0001",
        "mbr_syn_alpha_admin_0001",
        "10000000-0000-0000-0000-000000000001",
        "organization_admin",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_operator_0001",
        "idn_syn_alpha_operator_0001",
        "mbr_syn_alpha_operator_0001",
        "10000000-0000-0000-0000-000000000002",
        "operator",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_auditor_0001",
        "idn_syn_alpha_auditor_0001",
        "mbr_syn_alpha_auditor_0001",
        "10000000-0000-0000-0000-000000000003",
        "auditor",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_admin_0001",
        "idn_syn_beta_admin_0001",
        "mbr_syn_beta_admin_0001",
        "20000000-0000-0000-0000-000000000001",
        "organization_admin",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_operator_0001",
        "idn_syn_beta_operator_0001",
        "mbr_syn_beta_operator_0001",
        "20000000-0000-0000-0000-000000000002",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_auditor_0001",
        "idn_syn_beta_auditor_0001",
        "mbr_syn_beta_auditor_0001",
        "20000000-0000-0000-0000-000000000003",
        "auditor",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_manager_0001",
        "idn_syn_alpha_manager_0001",
        "mbr_syn_alpha_manager_0001",
        "10000000-0000-0000-0000-000000000004",
        "operator",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_security_0001",
        "idn_syn_alpha_security_0001",
        "mbr_syn_alpha_security_0001",
        "10000000-0000-0000-0000-000000000005",
        "operator",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_disabled_manager_0001",
        "idn_syn_alpha_disabled_manager_0001",
        "mbr_syn_alpha_disabled_manager_0001",
        "10000000-0000-0000-0000-000000000006",
        "operator",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_disabled_security_0001",
        "idn_syn_alpha_disabled_security_0001",
        "mbr_syn_alpha_disabled_security_0001",
        "10000000-0000-0000-0000-000000000007",
        "operator",
    ),
    (
        "org_syn_alpha_0001",
        "usr_syn_alpha_noauthority_0001",
        "idn_syn_alpha_noauthority_0001",
        "mbr_syn_alpha_noauthority_0001",
        "10000000-0000-0000-0000-000000000008",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_manager_0001",
        "idn_syn_beta_manager_0001",
        "mbr_syn_beta_manager_0001",
        "20000000-0000-0000-0000-000000000004",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_security_0001",
        "idn_syn_beta_security_0001",
        "mbr_syn_beta_security_0001",
        "20000000-0000-0000-0000-000000000005",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_disabled_manager_0001",
        "idn_syn_beta_disabled_manager_0001",
        "mbr_syn_beta_disabled_manager_0001",
        "20000000-0000-0000-0000-000000000006",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_disabled_security_0001",
        "idn_syn_beta_disabled_security_0001",
        "mbr_syn_beta_disabled_security_0001",
        "20000000-0000-0000-0000-000000000007",
        "operator",
    ),
    (
        "org_syn_beta_0001",
        "usr_syn_beta_noauthority_0001",
        "idn_syn_beta_noauthority_0001",
        "mbr_syn_beta_noauthority_0001",
        "20000000-0000-0000-0000-000000000008",
        "operator",
    ),
)

SYNTHETIC_AUTHORITIES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "aut_syn_alpha_manager_0001",
        "org_syn_alpha_0001",
        "usr_syn_alpha_manager_0001",
        "manager",
        "active",
    ),
    (
        "aut_syn_alpha_security_0001",
        "org_syn_alpha_0001",
        "usr_syn_alpha_security_0001",
        "security",
        "active",
    ),
    (
        "aut_syn_alpha_disabled_manager_0001",
        "org_syn_alpha_0001",
        "usr_syn_alpha_disabled_manager_0001",
        "manager",
        "active",
    ),
    (
        "aut_syn_alpha_disabled_security_0001",
        "org_syn_alpha_0001",
        "usr_syn_alpha_disabled_security_0001",
        "security",
        "disabled",
    ),
    (
        "aut_syn_beta_manager_0001",
        "org_syn_beta_0001",
        "usr_syn_beta_manager_0001",
        "manager",
        "active",
    ),
    (
        "aut_syn_beta_security_0001",
        "org_syn_beta_0001",
        "usr_syn_beta_security_0001",
        "security",
        "active",
    ),
    (
        "aut_syn_beta_disabled_manager_0001",
        "org_syn_beta_0001",
        "usr_syn_beta_disabled_manager_0001",
        "manager",
        "active",
    ),
    (
        "aut_syn_beta_disabled_security_0001",
        "org_syn_beta_0001",
        "usr_syn_beta_disabled_security_0001",
        "security",
        "disabled",
    ),
)


def seed_synthetic_identities(session: Session, policy: OidcPolicy) -> None:
    policy.validate()
    organizations = (
        ("org_syn_alpha_0001", "synthetic_alpha"),
        ("org_syn_beta_0001", "synthetic_beta"),
    )
    for organization_id, profile_code in organizations:
        if session.get(Organization, organization_id) is None:
            session.add(
                Organization(
                    organization_id=organization_id,
                    profile_code=profile_code,
                    status="active",
                    version=1,
                    memory_version=1,
                )
            )
        if session.get(AuditChainHead, organization_id) is None:
            session.add(
                AuditChainHead(
                    organization_id=organization_id,
                    head_sequence=0,
                    head_hash="0" * 64,
                    version=1,
                )
            )
    session.flush()

    issuer_hash = hashlib.sha256(policy.issuer.encode()).hexdigest()
    for organization_id, user_id, identity_id, membership_id, subject, role in SYNTHETIC_IDENTITIES:
        if session.get(User, user_id) is None:
            user_status = "disabled" if "disabled_manager" in user_id else "active"
            session.add(
                User(
                    user_id=user_id,
                    organization_id=organization_id,
                    profile_code=f"synthetic_{role}",
                    status=user_status,
                    version=1,
                )
            )
        session.flush()
        if session.get(OidcIdentity, identity_id) is None:
            session.add(
                OidcIdentity(
                    identity_id=identity_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    issuer_id=policy.issuer_id,
                    issuer_hash=issuer_hash,
                    subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
                    status="active",
                    version=1,
                )
            )
        if session.get(Membership, membership_id) is None:
            session.add(
                Membership(
                    membership_id=membership_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    role=role,
                    status="active",
                    version=1,
                )
            )
    session.flush()
    for authority_id, organization_id, user_id, role, authority_status in SYNTHETIC_AUTHORITIES:
        if session.get(ApprovalAuthority, authority_id) is None:
            session.add(
                ApprovalAuthority(
                    authority_id=authority_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    role=role,
                    status=authority_status,
                    version=1,
                )
            )
    session.commit()
