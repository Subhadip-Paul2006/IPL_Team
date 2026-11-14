"""Adversarial Verification Probe Script reproducing Challenger 3's nested leak test.

Empirically proves:
1. Deeply nested dictionaries, lists of dictionaries, and primitive values containing secret patterns or keywords are masked.
2. Non-serializable objects (like Exception or custom classes) are handled gracefully (using default=str).
3. taskName is excluded if present.
4. No sensitive credentials leak into log output.
"""

import json
import logging
from typing import Any

from src.core.logging import JsonFormatter, SecretMaskingFilter, get_logger, setup_logging


class CustomDataClass:
    """Non-serializable custom object for probe."""

    def __init__(self, name: str, code: int) -> None:
        self.name = name
        self.code = code

    def __repr__(self) -> str:
        return f"<CustomDataClass(name={self.name}, code={self.code})>"


def test_adversarial_challenger_3_probe() -> None:
    """Execute complete adversarial probe verifying zero credential leaks."""
    exact_secret = "sbp_live_secret_oracle_987654321"
    setup_logging(log_level="INFO", additional_secrets=[exact_secret])

    filter_obj = SecretMaskingFilter(additional_secrets=[exact_secret])
    formatter = JsonFormatter(mask_filter=filter_obj)

    logger = get_logger("adversarial.probe")

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="adversarial_probe.py",
        lineno=50,
        msg="Processing adversarial payload with secrets",
        args=(),
        exc_info=None,
    )

    # 1. taskName attribute (should be excluded)
    record.taskName = "Task-Adversarial-Probe-123"

    # 2. Non-serializable objects (custom class, Exception)
    record.custom_obj = CustomDataClass(name="TestNode", code=42)
    record.unhandled_error = RuntimeError("Database connection timed out at 10.0.0.1")

    # 3. Challenger 3 scenario: extra with nested dict containing secret
    record.config = {
        "supabase": {
            "secret": exact_secret,
            "url": "https://xyzcompany.supabase.co",
            "api_key": "sbp_unregistered_api_key_88888",
        },
        "credentials": {
            "db_password": "super_secret_db_password_77777",
            "auth_tokens": ["token_secret_alpha_11111", "token_secret_beta_22222"],
        },
    }

    # 4. Deeply nested lists of dicts with mixed patterns
    record.deep_records = [
        {
            "player_id": "P-101",
            "player_name": "Sanju Samson",
            "private_metadata": {
                "auth": "Bearer secret_bearer_token_33333",
                "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc_xyz",
                "db_conn": "postgresql://postgres:db_pass_secret_44444@db.supabase.co:5432/postgres",
                "nested_passwords": [
                    {"password": "secret_in_list_55555"},
                    {"token": "secret_in_list_66666"},
                ],
            },
        }
    ]

    formatted_output = formatter.format(record)
    parsed: dict[str, Any] = json.loads(formatted_output)

    # ASSERTION 1: taskName is strictly excluded
    assert "taskName" not in parsed, "taskName was not excluded from JSON log!"

    # ASSERTION 2: Non-serializable objects handled gracefully via default=str
    assert "custom_obj" in parsed
    assert "<CustomDataClass(name=TestNode, code=42)>" in parsed["custom_obj"]
    assert "unhandled_error" in parsed
    assert "Database connection timed out" in parsed["unhandled_error"]

    # ASSERTION 3: Challenger 3 nested dict leak prevented 100%
    assert exact_secret not in formatted_output, "CRITICAL: exact_secret leaked into log output!"
    assert "sbp_unregistered_api_key_88888" not in formatted_output, "CRITICAL: api_key leaked!"
    assert "super_secret_db_password_77777" not in formatted_output, "CRITICAL: db_password leaked!"
    assert "token_secret_alpha_11111" not in formatted_output, "CRITICAL: auth_tokens leaked!"
    assert "token_secret_beta_22222" not in formatted_output, "CRITICAL: auth_tokens leaked!"

    assert parsed["config"]["supabase"]["secret"] == "[REDACTED]"
    assert parsed["config"]["supabase"]["api_key"] == "[REDACTED]"
    assert parsed["config"]["supabase"]["url"] == "https://xyzcompany.supabase.co"
    assert parsed["config"]["credentials"]["db_password"] == "[REDACTED]"
    assert parsed["config"]["credentials"]["auth_tokens"] == ["[REDACTED]", "[REDACTED]"]

    # ASSERTION 4: Pattern-based and list-of-dict nested redaction
    assert "secret_bearer_token_33333" not in formatted_output, "CRITICAL: Bearer token leaked!"
    assert "db_pass_secret_44444" not in formatted_output, "CRITICAL: postgres password leaked!"
    assert "secret_in_list_55555" not in formatted_output, "CRITICAL: nested password leaked!"
    assert "secret_in_list_66666" not in formatted_output, "CRITICAL: nested token leaked!"

    # ASSERTION 5: Preserves legitimate domain payload
    assert parsed["deep_records"][0]["player_id"] == "P-101"
    assert parsed["deep_records"][0]["player_name"] == "Sanju Samson"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "rr_platform.adversarial.probe"
