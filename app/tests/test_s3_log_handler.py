import logging
import unittest
from unittest.mock import patch

from pythonjsonlogger import jsonlogger

from app.utils.s3_log_handler import S3LogHandler


class TestS3LogHandler(unittest.TestCase):
    @patch("app.utils.s3_bucket_util.upload_file")
    def test_flush_uploads_logs_and_clears_buffer(self, mock_upload_file):
        """
        Test that when the buffer reaches capacity and flush() is called,
        upload_file is called with the aggregated log content and the buffer is cleared.
        """
        # Set capacity to 3 for the test.
        s3_key = "logs/test.log"
        handler = S3LogHandler(s3_key=s3_key, capacity=3)
        formatter = jsonlogger.JsonFormatter(fmt="%(message)s")
        handler.setFormatter(formatter)

        # Create dummy log records.
        record1 = logging.LogRecord(
            "test", logging.INFO, "", 0, "Message 1", None, None
        )
        record2 = logging.LogRecord(
            "test", logging.INFO, "", 0, "Message 2", None, None
        )
        record3 = logging.LogRecord(
            "test", logging.INFO, "", 0, "Message 3", None, None
        )

        # Emit three records; flush() should be triggered on the third record.
        handler.emit(record1)
        handler.emit(record2)
        handler.emit(record3)

        # The expected log content using the JSON formatter with fmt="%(message)s"
        # would be:
        # '{"message": "Message 1"}\n{"message": "Message 2"}\n{"message": "Message 3"}'
        expected_content = (
            '{"message": "Message 1"}\n{"message": "Message 2"}\n{"message": "Message 3"}'
        ).encode("utf-8")

        # Verify that upload_file was called once with the expected parameters.
        mock_upload_file.assert_called_once_with(s3_key, expected_content, "text/plain")
        # Buffer should be cleared after flush.
        self.assertEqual(handler.buffer, [])

    @patch("app.utils.s3_bucket_util.upload_file")
    def test_emit_does_not_trigger_flush_until_capacity_reached(self, mock_upload_file):
        """
        Test that emit() does not automatically call flush() until the buffer reaches capacity.
        """
        s3_key = "logs/test.log"
        # Set capacity higher than the number of emitted records.
        handler = S3LogHandler(s3_key=s3_key, capacity=5)
        formatter = jsonlogger.JsonFormatter(fmt="%(message)s")
        handler.setFormatter(formatter)

        # Emit 3 records, which is below capacity.
        for i in range(3):
            record = logging.LogRecord(
                "test", logging.INFO, "", 0, f"Msg {i + 1}", None, None
            )
            handler.emit(record)

        # Check that the buffer length is 3 and flush was not triggered.
        self.assertEqual(len(handler.buffer), 3)
        mock_upload_file.assert_not_called()

        # Now manually call flush() and verify behavior.
        handler.flush()
        self.assertEqual(handler.buffer, [])
        self.assertEqual(mock_upload_file.call_count, 1)
