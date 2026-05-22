"""PDF Renderer — generates branded PDF from kit data."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from shared.database.models import Kit


# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


async def render_kit_pdf(kit: Kit, output_path: Path) -> None:
    """Render a kit to PDF using WeasyPrint + Jinja2 templates."""
    # Load Jinja2 template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("kit_pdf.html")

    # Render HTML
    html_content = template.render(
        title=kit.title or "Interview Kit",
        role_type=kit.role_type,
        match_analysis=kit.match_analysis or {},
        questions=kit.questions or [],
        practical_test=kit.practical_test or {},
        rubric=kit.rubric or {},
        red_flags=kit.red_flags or [],
        flow_guide=kit.flow_guide or [],
    )

    # Generate PDF
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(str(output_path))
    except ImportError:
        # Fallback: save as HTML if WeasyPrint not installed
        html_path = output_path.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        # Create a simple text PDF as placeholder
        output_path.write_text(f"PDF generation requires WeasyPrint. HTML saved at: {html_path}")
