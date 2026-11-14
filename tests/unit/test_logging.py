"""Unit tests for structured logging and automated secret masking."""

import json
import logging
from typing import Any

from src.core.logging import JsonFormatter, SecretMaskingFilter, get_logger, setup_logging


def test_secret_masking_filter_explicit_secrets() -> None:
    """Verify that exact secrets provided in additional_secrets are redacted."""
    secret = "my_super_confidential_token_12345"
    filter_obj = SecretMaskingFilter(additional_secrets=[secret])

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg=f"Connected using secret: {secret} successfully.",
        args=(),
        exc_info=None,
    )
    filter_obj.filter(record)
    assert secret not in record.msg
    assert "[REDACTED]" in record.msg


def test_secret_masking_filter_patterns() -> None:
    """Verify that regex patterns for passwords, JWTs, and bearer tokens are redacted."""
    filter_obj = SecretMaskingFilter()

    # Pattern: Bearer token
    msg_bearer = "Authorization: Bearer secret_jwt_payload_here"
    masked_bearer = filter_obj.mask_text(msg_bearer)
    assert "secret_jwt_payload_here" not in masked_bearer
    assert "[REDACTED]" in masked_bearer

    # Pattern: key=... / password=...
    msg_pwd = "db_connect(password='super_secret_db_pass')"
    masked_pwd = filter_obj.mask_text(msg_pwd)
    assert "super_secret_db_pass" not in masked_pwd
    assert "[REDACTED]" in masked_pwd

    # Pattern: postgres url with password
    msg_url = "Connecting to postgresql://admin:mysecretpassword@localhost:5432/rr_db"
    masked_url = filter_obj.mask_text(msg_url)
    assert "mysecretpassword" not in masked_url
    assert "[REDACTED]" in masked_url


def test_json_formatter_valid_json() -> None:
    """Verify that JsonFormatter produces valid JSON output with required schema fields."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.test",
        level=logging.WARNING,
        pathname="worker.py",
        lineno=42,
        msg="Sample log event: %s",
        args=("operational",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "WARNING"
    assert parsed["logger"] == "rr_platform.test"
    assert parsed["message"] == "Sample log event: operational"
    assert parsed["line"] == 42
    assert "timestamp" in parsed


def test_get_logger_prefix() -> None:
    """Verify that get_logger names child loggers under the rr_platform namespace."""
    logger = get_logger("pire")
    assert logger.name == "rr_platform.pire"


def test_setup_logging_idempotence() -> None:
    """Verify that setup_logging configures root logger without duplicating handlers."""
    setup_logging(log_level="DEBUG")
    setup_logging(log_level="DEBUG")
    root = logging.getLogger()
    stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) >= 1


def test_jwt_redaction_without_index_error() -> None:
    """Verify that raw JWT tokens are redacted without raising IndexError."""
    filter_obj = SecretMaskingFilter()
    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc_xyz"
    msg = f"User authenticated with token {raw_jwt}"
    masked = filter_obj.mask_text(msg)
    assert raw_jwt not in masked
    assert "[REDACTED]" in masked
    assert masked == "User authenticated with token [REDACTED]"


def test_bearer_token_case_insensitivity() -> None:
    """Verify that Bearer tokens are redacted across different casings."""
    filter_obj = SecretMaskingFilter()
    for prefix in ["Bearer", "bearer", "BEARER"]:
        msg = f"Auth header: {prefix} token_abc_12345"
        masked = filter_obj.mask_text(msg)
        assert "token_abc_12345" not in masked
        assert "[REDACTED]" in masked


def test_json_formatter_extra_attribute_redaction() -> None:
    """Verify that sensitive values in extra attributes are scrubbed in JsonFormatter."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.auth",
        level=logging.INFO,
        pathname="auth.py",
        lineno=15,
        msg="Authentication attempt",
        args=(),
        exc_info=None,
    )
    record.api_key = "key=super_secret_api_key_value"
    record.auth_header = "bearer jwt_token_12345"
    record.raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc_xyz"
    record.db_pass = "postgres://admin:secretpassword@localhost:5432/db"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "super_secret_api_key_value" not in formatted
    assert "jwt_token_12345" not in formatted
    assert "eyJhbGci" not in formatted
    assert "secretpassword" not in formatted
    assert "[REDACTED]" in parsed["api_key"]
    assert "[REDACTED]" in parsed["auth_header"]
    assert "[REDACTED]" in parsed["raw_jwt"]
    assert "[REDACTED]" in parsed["db_pass"]


def test_json_formatter_traceback_redaction() -> None:
    """Verify that exception tracebacks containing sensitive tokens are redacted."""
    import sys

    formatter = JsonFormatter()
    try:
        raise ValueError(
            "Failed connecting to postgresql://user:mypassword@localhost:5432/db "
            "with token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.xyz"
        )
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="rr_platform.db",
        level=logging.ERROR,
        pathname="db.py",
        lineno=30,
        msg="Database error occurred",
        args=(),
        exc_info=exc_info,
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "exception" in parsed
    assert "mypassword" not in parsed["exception"]
    assert "eyJhbGci" not in parsed["exception"]
    assert "[REDACTED]" in parsed["exception"]


def test_json_formatter_deeply_nested_sanitization() -> None:
    """Verify that multi-level nested dicts, lists of dicts, and nested lists are sanitized."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.nested",
        level=logging.INFO,
        pathname="nested.py",
        lineno=10,
        msg="Processing nested payload",
        args=(),
        exc_info=None,
    )
    record.nested_dict = {"l1": {"l2": "Bearer secret123"}}
    record.list_of_dicts = [{"token": "Bearer secret456"}]
    record.nested_list = [["Bearer secret789"]]
    record.nested_tuple = ({"auth": "Bearer secretabc"},)

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "secret123" not in formatted
    assert "secret456" not in formatted
    assert "secret789" not in formatted
    assert "secretabc" not in formatted

    assert parsed["nested_dict"]["l1"]["l2"] == "Bearer [REDACTED]"
    assert parsed["list_of_dicts"][0]["token"] == "Bearer [REDACTED]"
    assert parsed["nested_list"][0][0] == "Bearer [REDACTED]"
    assert parsed["nested_tuple"][0]["auth"] == "Bearer [REDACTED]"


def test_json_formatter_non_serializable_objects() -> None:
    """Verify that non-serializable objects in extra serialize safely with default=str."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.error",
        level=logging.ERROR,
        pathname="error.py",
        lineno=25,
        msg="Error encountered",
        args=(),
        exc_info=None,
    )
    record.error = ValueError("boom")
    record.custom_set = {"item1", "item2"}

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "boom" in parsed["error"]
    assert isinstance(parsed["custom_set"], list)


def test_json_formatter_task_name_excluded() -> None:
    """Verify that taskName is excluded from the formatted JSON output."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.async",
        level=logging.INFO,
        pathname="async.py",
        lineno=5,
        msg="Async event",
        args=(),
        exc_info=None,
    )
    record.taskName = "Task-1"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "taskName" not in parsed


def test_json_formatter_challenger_3_nested_secret_reproduction() -> None:
    """Verify challenger_3 reproduction: extra={"config": {"secret": "sbp_live_secret_999"}} is redacted."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.config",
        level=logging.INFO,
        pathname="config.py",
        lineno=42,
        msg="Config loaded",
        args=(),
        exc_info=None,
    )
    record.config = {"secret": "sbp_live_secret_999", "public_id": "pub_123"}

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "sbp_live_secret_999" not in formatted
    assert parsed["config"]["secret"] == "[REDACTED]"
    assert parsed["config"]["public_id"] == "pub_123"


def test_json_formatter_adversarial_nested_and_non_serializable() -> None:
    """Verify adversarial probe: deeply nested lists/dicts, passwords, custom objects, and primitives."""
    class CustomObject:
        def __str__(self) -> str:
            return "CustomObject(status=ok)"

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.adversarial",
        level=logging.INFO,
        pathname="adv.py",
        lineno=99,
        msg="Adversarial probe event",
        args=(),
        exc_info=None,
    )
    record.taskName = "ShouldBeExcluded"
    record.exception_obj = RuntimeError("Database timeout error")
    record.custom_entity = CustomObject()
    record.deep_hierarchy = {
        "level1": {
            "level2": {
                "secrets": ["raw_secret_token_1", "raw_secret_token_2"],
                "credentials": {"db_password": "my_super_secret_db_pass"},
            }
        },
        "records": [
            {"api_key": "raw_api_key_abc", "player_name": "Sanju Samson"},
            {"auth_token": "raw_auth_jwt_999", "runs": 450},
        ],
    }

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    # 1. taskName excluded
    assert "taskName" not in parsed

    # 2. Non-serializable handled gracefully
    assert "Database timeout error" in parsed["exception_obj"]
    assert "CustomObject(status=ok)" in parsed["custom_entity"]

    # 3. Deeply nested secrets masked
    assert "raw_secret_token_1" not in formatted
    assert "raw_secret_token_2" not in formatted
    assert "my_super_secret_db_pass" not in formatted
    assert "raw_api_key_abc" not in formatted
    assert "raw_auth_jwt_999" not in formatted

    assert parsed["deep_hierarchy"]["level1"]["level2"]["secrets"] == [
        "[REDACTED]",
        "[REDACTED]",
    ]
    assert (
        parsed["deep_hierarchy"]["level1"]["level2"]["credentials"]["db_password"]
        == "[REDACTED]"
    )
    assert parsed["deep_hierarchy"]["records"][0]["api_key"] == "[REDACTED]"
    assert parsed["deep_hierarchy"]["records"][1]["auth_token"] == "[REDACTED]"

    # 4. Domain data preserved
    assert parsed["deep_hierarchy"]["records"][0]["player_name"] == "Sanju Samson"
    assert parsed["deep_hierarchy"]["records"][1]["runs"] == 450


def test_bearer_token_collision_variants() -> None:
    """Verify that Bearer tokens prefixed with Auth, Token, key, or auth= are redacted."""
    filter_obj = SecretMaskingFilter()
    cases = [
        ("Auth: Bearer my_secret_token_456", "my_secret_token_456"),
        ("Token: Bearer secret123", "secret123"),
        ("key: Bearer tok456", "tok456"),
        ("auth=Bearer tok789", "tok789"),
        ("Authorization: Bearer my_auth_token_999", "my_auth_token_999"),
    ]
    for msg, secret in cases:
        masked = filter_obj.mask_text(msg)
        assert secret not in masked, f"Secret leaked in: {masked}"
        assert "[REDACTED]" in masked


def test_supabase_sbp_token_redaction() -> None:
    """Verify that modern Supabase sbp_ tokens in raw message strings are redacted."""
    filter_obj = SecretMaskingFilter()
    formatter = JsonFormatter(mask_filter=filter_obj)

    # 1. Raw message string without labels
    msg = "Connecting to Supabase with sbp_live_servicerole_abcdef1234567890"
    masked = filter_obj.mask_text(msg)
    assert "sbp_live_servicerole_abcdef1234567890" not in masked
    assert masked == "Connecting to Supabase with [REDACTED]"

    # 2. CLI token in message
    msg_cli = "Using CLI token sbp_cli_9876543210zyxwvutsrq for deployment"
    masked_cli = filter_obj.mask_text(msg_cli)
    assert "sbp_cli_9876543210zyxwvutsrq" not in masked_cli
    assert "[REDACTED]" in masked_cli

    # 3. In extra attribute of a log record
    record = logging.LogRecord(
        name="rr_platform.supabase",
        level=logging.INFO,
        pathname="supabase.py",
        lineno=10,
        msg="Supabase event",
        args=(),
        exc_info=None,
    )
    record.supabase_key = "sbp_live_servicerole_xyz123"
    formatted = formatter.format(record)
    assert "sbp_live_servicerole_xyz123" not in formatted
    parsed = json.loads(formatted)
    assert parsed["supabase_key"] == "[REDACTED]"


def test_camelcase_and_hyphenated_sensitive_keys() -> None:
    """Verify that camelCase and hyphenated sensitive keys are redacted while non-sensitive fields are preserved."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rr_platform.keys",
        level=logging.INFO,
        pathname="keys.py",
        lineno=12,
        msg="API credential verification",
        args=(),
        exc_info=None,
    )
    # Sensitive keys (camelCase, hyphenated, standard)
    record.dbPassword = "super_secret_db_password"
    record.authToken = "super_secret_auth_token"
    record.jwtToken = "super_secret_jwt_token"
    record.clientSecret = "super_secret_client_secret"
    record.privateKey = "super_secret_private_key"
    record.accessToken = "super_secret_access_token"
    record.refreshToken = "super_secret_refresh_token"
    record.authHeader = "super_secret_auth_header"
    record.authorization = "CustomToken_789"
    setattr(record, "x-api-key", "secret_x_api_key_123")
    setattr(record, "x-auth-token", "secret_x_auth_token_456")

    # Non-sensitive keys (subword tests and domain attributes)
    record.player_name = "Sanju Samson"
    record.team = "RR"
    record.runs_scored = 55
    record.boundary_hits = 6
    record.monkey = "chimpanzee"
    record.keyboard = "mechanical"
    record.author = "George Orwell"
    record.authentic = True
    record.hockey = "sport"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    # Sensitive values must all be redacted
    sensitive_keys = [
        "dbPassword",
        "authToken",
        "jwtToken",
        "clientSecret",
        "privateKey",
        "accessToken",
        "refreshToken",
        "authHeader",
        "authorization",
        "x-api-key",
        "x-auth-token",
    ]
    for key in sensitive_keys:
        assert parsed[key] == "[REDACTED]", f"Key {key} was not redacted: {parsed[key]}"

    # Non-sensitive domain values must be preserved verbatim
    assert parsed["player_name"] == "Sanju Samson"
    assert parsed["team"] == "RR"
    assert parsed["runs_scored"] == 55
    assert parsed["boundary_hits"] == 6
    assert parsed["monkey"] == "chimpanzee"
    assert parsed["keyboard"] == "mechanical"
    assert parsed["author"] == "George Orwell"
    assert parsed["authentic"] is True
    assert parsed["hockey"] == "sport"


def test_json_formatter_circular_reference_handling() -> None:
    """Verify that JsonFormatter handles circular references in dicts and lists without crashing."""
    formatter = JsonFormatter()

    # 1. Self-referencing dict
    record_dict = logging.LogRecord(
        name="rr_platform.cycle",
        level=logging.WARNING,
        pathname="cycle.py",
        lineno=1,
        msg="Cycle dict test",
        args=(),
        exc_info=None,
    )
    c_dict: dict[str, Any] = {"status": "ok"}
    c_dict["self"] = c_dict
    record_dict.cycle = c_dict
    out_dict = formatter.format(record_dict)
    parsed_dict = json.loads(out_dict)
    assert parsed_dict["cycle"]["self"] == "[CIRCULAR]"

    # 2. Mutually referencing dicts
    record_mutual = logging.LogRecord(
        name="rr_platform.mutual",
        level=logging.WARNING,
        pathname="cycle.py",
        lineno=2,
        msg="Mutual cycle test",
        args=(),
        exc_info=None,
    )
    d1: dict[str, Any] = {"name": "d1"}
    d2: dict[str, Any] = {"name": "d2"}
    d1["d2"] = d2
    d2["d1"] = d1
    record_mutual.mutual = d1
    out_mutual = formatter.format(record_mutual)
    parsed_mutual = json.loads(out_mutual)
    assert parsed_mutual["mutual"]["name"] == "d1"
    assert parsed_mutual["mutual"]["d2"]["name"] == "d2"
    assert parsed_mutual["mutual"]["d2"]["d1"] == "[CIRCULAR]"

    # 3. Self-referencing list
    record_list = logging.LogRecord(
        name="rr_platform.cycle_list",
        level=logging.WARNING,
        pathname="cycle.py",
        lineno=3,
        msg="Cycle list test",
        args=(),
        exc_info=None,
    )
    c_list: list[Any] = ["item1"]
    c_list.append(c_list)
    record_list.cycle_list = c_list
    out_list = formatter.format(record_list)
    parsed_list = json.loads(out_list)
    assert parsed_list["cycle_list"][0] == "item1"
    assert parsed_list["cycle_list"][1] == "[CIRCULAR]"



