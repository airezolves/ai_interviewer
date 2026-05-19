"""PDF Generator service business logic."""

import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from shared.utils.logger import get_logger
from services.pdf_generator.config.settings import get_pdf_generator_settings

logger = get_logger(__name__)
settings = get_pdf_generator_settings()


class PDFGeneratorService:
    """Generates PDF interview kits from structured data."""

    def __init__(self):
        template_dir = Path(settings.TEMPLATE_DIR)
        template_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_pdf(self, kit_data: dict, title: str, candidate_name: str | None = None) -> str:
        """Generate a PDF from kit data. Returns the file path."""
        job_id = str(uuid.uuid4())
        output_path = self.output_dir / f"{job_id}.pdf"

        try:
            # Render HTML from template
            template = self.env.get_template("kit_template.html")
            html_content = template.render(
                title=title,
                candidate_name=candidate_name or "Candidate",
                kit=kit_data,
            )

            # Generate PDF
            HTML(string=html_content).write_pdf(str(output_path))
            logger.info("pdf_generated", job_id=job_id, path=str(output_path))

            return job_id

        except Exception as e:
            logger.error("pdf_generation_failed", error=str(e))
            raise

    def get_pdf_path(self, job_id: str) -> Path | None:
        """Get the path to a generated PDF."""
        path = self.output_dir / f"{job_id}.pdf"
        return path if path.exists() else None
