import logging


class S3LogHandler(logging.Handler):
    """
    A logging handler that buffers log records and, when flushed,
    uploads the aggregated logs to an S3 bucket.
    """

    def __init__(self, s3_key: str, capacity: int = 10, *args, **kwargs):
        """
        Args:
            s3_key (str): The S3 key (path/filename) for the log file.
            capacity (int): Number of log messages to buffer before auto-flushing.
        """
        super().__init__(*args, **kwargs)
        self.s3_key = s3_key
        self.capacity = capacity
        self.buffer = []

    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            if len(self.buffer) >= self.capacity:
                self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        from app.utils.s3_bucket_util import upload_file

        if self.buffer:
            try:
                log_content = "\n".join(self.buffer).encode("utf-8")
                upload_file(self.s3_key, log_content, "text/plain")
                self.buffer.clear()
            except Exception as e:
                self.handleError(e)
