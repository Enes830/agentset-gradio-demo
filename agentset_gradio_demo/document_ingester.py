"""
Document Ingester - Handles document ingestion into Agentset namespace
Supports multiple ingestion types: TEXT, FILE, and MANAGED_FILE
"""

import logging
import time
import requests
from agentset import Agentset

logger = logging.getLogger(__name__)


class DocumentIngester:
    """
    Handles document ingestion into Agentset namespace.
    Supports ingesting documents from URLs, text content, and local files.
    """

    def __init__(self, agentset_namespace_id: str, agentset_api_token: str):
        """
        Initialize the Document Ingester.

        Args:
            agentset_namespace_id: Agentset namespace ID
            agentset_api_token: Agentset API token
        """
        logger.info("Initializing Document Ingester")

        self.agentset_namespace_id = agentset_namespace_id
        self.agentset_api_token = agentset_api_token

        # Initialize Agentset client
        self.client = Agentset(
            namespace_id=agentset_namespace_id,
            token=agentset_api_token,
        )
        logger.debug("Agentset client initialized for ingestion")

    def ingest_text(
        self, text_content: str, file_name: str = None, metadata: dict = None
    ) -> dict:
        """
        Ingest text content into the namespace.

        Args:
            text_content: The text content to ingest
            file_name: Optional file name for the content
            metadata: Optional metadata dictionary

        Returns:
            Dictionary containing the job ID and status
        """
        logger.info(
            f"Ingesting text content" + (f" as '{file_name}'" if file_name else "")
        )

        try:
            payload = {
                "type": "TEXT",
                "text": text_content,
            }

            if file_name:
                payload["fileName"] = file_name

            config = {}
            if metadata:
                config["metadata"] = metadata

            job = self.client.ingest_jobs.create(
                payload=payload, config=config if config else None
            )

            logger.info(f"Text ingestion job created: {job.data.id}")

            return {
                "success": True,
                "job_id": job.data.id,
                "document_name": file_name or "text-content",
                "message": f"Successfully initiated ingestion of text content",
            }
        except Exception as e:
            logger.error(f"Error ingesting text: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error ingesting text: {str(e)}",
            }

    def ingest_file_from_url(
        self, document_name: str, file_url: str, metadata: dict = None
    ) -> dict:
        """
        Ingest a document from a URL into the namespace.

        Args:
            document_name: Name for the document
            file_url: URL of the document to ingest
            metadata: Optional metadata dictionary

        Returns:
            Dictionary containing the job ID and status
        """
        logger.info(f"Ingesting document: '{document_name}' from URL: {file_url}")

        try:
            payload = {
                "type": "FILE",
                "fileUrl": file_url,
            }

            config = {}
            if metadata:
                config["metadata"] = metadata

            job = self.client.ingest_jobs.create(
                name=document_name, payload=payload, config=config if config else None
            )

            logger.info(f"Document ingestion job created: {job.data.id}")

            return {
                "success": True,
                "job_id": job.data.id,
                "document_name": document_name,
                "message": f"Successfully initiated ingestion of '{document_name}'",
            }
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error ingesting document: {str(e)}",
            }

    def ingest_local_file(
        self, file_path: str, file_name: str = None, metadata: dict = None
    ) -> dict:
        """
        Upload and ingest a local file.

        Args:
            file_path: Path to the local file
            file_name: Optional custom file name (uses original if not provided)
            metadata: Optional metadata dictionary

        Returns:
            Dictionary containing the job ID and status
        """
        logger.info(f"Ingesting local file: {file_path}")

        try:
            # Read the file
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Use provided file_name or extract from path
            if not file_name:
                file_name = file_path.split("/")[-1]

            file_size = len(file_data)
            # Determine content type from the actual file name being used
            content_type = self._get_content_type(file_name)

            logger.info(
                f"File: {file_name}, Size: {file_size} bytes, Content-Type: {content_type}"
            )

            # Get a presigned upload URL
            logger.info(f"Requesting presigned upload URL for {file_name}")
            upload = self.client.uploads.create(
                file_name=file_name,
                file_size=file_size,
                content_type=content_type,
            )

            # Upload the file
            logger.info(
                f"Uploading file to presigned URL with Content-Type: {content_type}"
            )
            response = requests.put(
                upload.data.url,
                data=file_data,
                headers={"Content-Type": content_type},
            )

            if response.status_code not in [200, 204]:
                logger.error(
                    f"Upload failed with status {response.status_code}: {response.text}"
                )
                raise Exception(
                    f"File upload failed: {response.status_code} - {response.text}"
                )

            # Create an ingest job for the uploaded file
            logger.info(f"Creating ingest job for {file_name}")
            payload = {
                "type": "MANAGED_FILE",
                "key": upload.data.key,
                "fileName": file_name,
            }

            config = {}
            if metadata:
                config["metadata"] = metadata

            job = self.client.ingest_jobs.create(
                payload=payload, config=config if config else None
            )

            logger.info(f"Local file ingestion job created: {job.data.id}")

            return {
                "success": True,
                "job_id": job.data.id,
                "document_name": file_name,
                "message": f"Successfully uploaded and initiated ingestion of '{file_name}'",
            }
        except Exception as e:
            logger.error(f"Error ingesting local file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error ingesting file: {str(e)}",
            }

    def get_job_status(self, job_id: str) -> dict:
        """
        Get the status of an ingestion job.

        Args:
            job_id: The job ID to check

        Returns:
            Dictionary containing job status information
        """
        logger.info(f"Checking status of job: {job_id}")

        try:
            job = self.client.ingest_jobs.get(job_id=job_id)

            return {
                "success": True,
                "job_id": job_id,
                "status": job.data.status,
                "message": f"Job status: {job.data.status}",
            }
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error checking job status: {str(e)}",
            }

    def wait_for_job_completion(
        self, job_id: str, max_wait_seconds: int = 3600, poll_interval: int = 10
    ) -> dict:
        """
        Wait for an ingestion job to complete.

        Args:
            job_id: The job ID to wait for
            max_wait_seconds: Maximum time to wait (default 1 hour)
            poll_interval: How often to check status in seconds

        Returns:
            Dictionary containing final job status
        """
        logger.info(f"Waiting for job completion: {job_id}")

        start_time = time.time()

        try:
            while time.time() - start_time < max_wait_seconds:
                job = self.client.ingest_jobs.get(job_id=job_id)
                status = job.data.status

                logger.debug(f"Job status: {status}")

                if status in ["COMPLETED", "FAILED"]:
                    logger.info(f"Job {job_id} finished with status: {status}")
                    return {
                        "success": status == "COMPLETED",
                        "job_id": job_id,
                        "status": status,
                        "message": f"Job completed successfully!"
                        if status == "COMPLETED"
                        else "Job failed",
                    }

                time.sleep(poll_interval)

            logger.error(
                f"Job {job_id} did not complete within {max_wait_seconds} seconds"
            )
            return {
                "success": False,
                "job_id": job_id,
                "status": "TIMEOUT",
                "message": f"Job did not complete within {max_wait_seconds} seconds",
            }
        except Exception as e:
            logger.error(f"Error waiting for job completion: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error waiting for job: {str(e)}",
            }

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """
        Determine content type based on file extension.
        Uses mimetypes module as fallback for more comprehensive coverage.

        Args:
            file_path: The file path or file name

        Returns:
            The content type string
        """
        import mimetypes

        # Manual mapping for common document types
        extension = file_path.lower().split(".")[-1] if "." in file_path else ""

        content_types = {
            # Documents
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "odt": "application/vnd.oasis.opendocument.text",
            "rtf": "application/rtf",
            # Spreadsheets
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            "csv": "text/csv",
            # Presentations
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "odp": "application/vnd.oasis.opendocument.presentation",
            # Images
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "bmp": "image/bmp",
            "svg": "image/svg+xml",
            "webp": "image/webp",
            # Text
            "txt": "text/plain",
            "md": "text/markdown",
            "html": "text/html",
            "xml": "application/xml",
            "json": "application/json",
            # Archives
            "zip": "application/zip",
            "tar": "application/x-tar",
            "gz": "application/gzip",
        }

        # Check manual mapping first
        if extension in content_types:
            mime_type = content_types[extension]
            logger.debug(f"Using manual mapping for .{extension}: {mime_type}")
            return mime_type

        # Try mimetypes module as fallback
        guessed_type, _ = mimetypes.guess_type(file_path)
        if guessed_type:
            logger.debug(f"Using mimetypes for {file_path}: {guessed_type}")
            return guessed_type

        # Default fallback
        logger.warning(
            f"Could not determine MIME type for {file_path}, defaulting to application/octet-stream"
        )
        return "application/octet-stream"
