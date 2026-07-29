import base64
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from flowpilot_recovery_worker.schemas import (
    OpaqueEnvelope,
    PlainRunInput,
    WorkflowStart,
    canonical_json_bytes,
    sha256_hex,
)


def _b64encode(value: bytes) -> str:
    # Standard Base64 keeps opaque envelope text free of URL-safe '-' tokens.
    # The history scanner must reject plaintext sentinels without treating a
    # random ciphertext occurrence of the short ``SYN-`` sentinel as a match.
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)


def decode_runtime_key(encoded_key: str) -> bytes:
    key = _b64decode(encoded_key)
    if len(key) != 32:
        raise ValueError("RECOVERY_ENVELOPE_KEY must decode to exactly 32 bytes")
    return key


def associated_data(workflow_id: str, run_id: str, task_id: str) -> bytes:
    return canonical_json_bytes(
        {
            "schema_version": "w8-opaque-envelope/1.0",
            "key_id": "w8-local-runtime-key/1",
            "workflow_id": workflow_id,
            "run_id": run_id,
            "task_id": task_id,
        }
    )


def encrypt_plain_input(plain: PlainRunInput, key: bytes, *, nonce: bytes) -> OpaqueEnvelope:
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError("AES-GCM requires a 32-byte key and 12-byte nonce")
    aad = associated_data(plain.workflow_id, plain.run_id, plain.task_id)
    ciphertext = AESGCM(key).encrypt(nonce, canonical_json_bytes(plain), aad)
    return OpaqueEnvelope(
        nonce=_b64encode(nonce),
        ciphertext=_b64encode(ciphertext),
        associated_data_hash=sha256_hex(aad),
    )


def decrypt_plain_input(start: WorkflowStart, key: bytes) -> PlainRunInput:
    if len(key) != 32:
        raise ValueError("invalid AES-GCM key length")
    aad = associated_data(start.workflow_id, start.run_id, start.task_id)
    if sha256_hex(aad) != start.envelope.associated_data_hash:
        raise ValueError("opaque envelope associated-data hash mismatch")
    plaintext = AESGCM(key).decrypt(
        _b64decode(start.envelope.nonce),
        _b64decode(start.envelope.ciphertext),
        aad,
    )
    plain = PlainRunInput.model_validate(json.loads(plaintext))
    if (
        plain.workflow_id != start.workflow_id
        or plain.run_id != start.run_id
        or plain.task_id != start.task_id
    ):
        raise ValueError("opaque envelope identity mismatch")
    return plain
