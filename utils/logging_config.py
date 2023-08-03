import json
import logging

# Adapted from https://github.com/codecov/codecov-cli/blob/master/codecov_cli/helpers/logging_utils.py

LOGGER_NAME = "ats-data"


class JsonEncoder(json.JSONEncoder):
    """
    A custom encoder extending the default JSONEncoder
    """

    def default(self, obj):
        try:
            return super(JsonEncoder, self).default(obj)
        except TypeError:
            try:
                return str(obj)
            except Exception:
                return None


class ColorFormatter(logging.Formatter):
    def format(self, record):
        if not record.exc_info:
            level = record.levelname.lower()
            asctime = self.formatTime(record, self.datefmt)
            msg = record.getMessage()
            msg = "\n".join(f"{level} - {asctime} -- {x}" for x in msg.splitlines())
            if hasattr(record, "extra_log_attributes"):
                msg += " --- " + json.dumps(
                    record.extra_log_attributes, cls=JsonEncoder
                )
            return msg
        return super().format(record)


def configure_logger(logger: logging.Logger, log_level=logging.INFO):
    # This if exists to avoid an issue where extra handlers would be added by tests that use runner.invoke()
    # Which would cause subsequent tests to failed due to repeated log lines
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setFormatter(ColorFormatter())
        logger.addHandler(ch)
    logger.setLevel(log_level)
