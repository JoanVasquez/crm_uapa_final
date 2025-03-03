# test_my_logger.py
import io
import json
import logging
import unittest

from pythonjsonlogger import jsonlogger

from app.utils.logger import get_logger


class TestLoggerConfiguration(unittest.TestCase):
    def test_logger_instance_and_level(self):
        """Test that get_logger returns a Logger instance with level INFO."""
        # Use a unique logger name for testing.
        logger = get_logger("unit_test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.level, logging.INFO)

    def test_handler_and_formatter_configuration(self):
        """Test that the logger has a StreamHandler with JsonFormatter."""
        logger = get_logger("handler_test_logger")
        # Ensure that at least one handler is attached.
        self.assertGreater(len(logger.handlers), 0)

        # Find at least one StreamHandler.
        stream_handlers = [
            handler
            for handler in logger.handlers
            if isinstance(handler, logging.StreamHandler)
        ]
        self.assertGreater(
            len(stream_handlers), 0, "No StreamHandler found in logger.handlers"
        )

        # Check that the formatter is an instance of jsonlogger.JsonFormatter.
        for handler in stream_handlers:
            self.assertIsNotNone(handler.formatter, "Handler has no formatter set")
            self.assertIsInstance(handler.formatter, jsonlogger.JsonFormatter)

    def test_logging_output_is_valid_json(self):
        """Test that logging an INFO message produces valid JSON output with
        the expected keys."""
        # Use a unique logger name for this test.
        logger = get_logger("json_output_test")
        # Remove any existing handlers to avoid duplicate output.
        logger.handlers = []

        # Create an in-memory stream to capture log output.
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log a test message.
        test_message = "Hello, JSON logger!"
        logger.info(test_message)
        handler.flush()

        # Get the logged output.
        log_output = stream.getvalue().strip()

        # Try parsing the output as JSON.
        try:
            log_record = json.loads(log_output)
        except json.JSONDecodeError as e:
            self.fail(f"Log output is not valid JSON: {e}")

        # Check that the JSON record contains expected fields.
        for field in ("asctime", "name", "levelname", "message"):
            self.assertIn(field, log_record, f"Missing '{field}' in log output")

        # Verify the content of some fields.
        self.assertEqual(log_record["message"], test_message)
        self.assertEqual(log_record["levelname"], "INFO")
        self.assertEqual(log_record["name"], "json_output_test")
