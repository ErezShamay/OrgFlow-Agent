import json
import logging

from app.exceptions.logger import JSONFormatter


def test_json_formatter_includes_extra_fields():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Structured log test",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    record.trace_id = "trace-456"
    record.user_id = "user-789"

    formatted = formatter.format(record)
    log_obj = json.loads(formatted)

    assert log_obj["message"] == "Structured log test"
    assert log_obj["level"] == "INFO"
    assert log_obj["logger"] == "app.test"
    assert log_obj["request_id"] == "req-123"
    assert log_obj["trace_id"] == "trace-456"
    assert log_obj["user_id"] == "user-789"
    assert log_obj["module"] == "test_structured_logging"
