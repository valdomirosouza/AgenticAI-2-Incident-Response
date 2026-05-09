import logging
import sys

try:
    from pythonjsonlogger.json import JsonFormatter  # python-json-logger >= 3.x
except ImportError:
    from pythonjsonlogger.jsonlogger import JsonFormatter  # python-json-logger 2.x


def configure_logging(log_level: str = "info", log_format: str = "json") -> None:
    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        formatter = JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )
        handler.setFormatter(formatter)

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(log_level.upper())
