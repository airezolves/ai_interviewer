"""PDF Renderer — generates branded PDF from kit data."""

import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from shared.database.models import Kit

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Try to import WeasyPrint (requires system libraries)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
    logger.info("WeasyPrint available for PDF generation")
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    logger.warning(f"WeasyPrint not available: {e}. Will use ReportLab fallback.")


async def render_kit_pdf(kit: Kit, output_path: Path) -> None:
    """Render a kit to PDF.
    
    Tries WeasyPrint first (better formatting, requires system libs).
    Falls back to ReportLab (pure Python, simpler formatting).
    """
    if WEASYPRINT_AVAILABLE:
        try:
            await _render_with_weasyprint(kit, output_path)
            logger.info(f"PDF generated with WeasyPrint: {output_path}")
            return
        except Exception as e:
            logger.error(f"WeasyPrint rendering failed: {e}. Falling back to ReportLab.")
    
    # Fallback to ReportLab
    await _render_with_reportlab(kit, output_path)
    logger.info(f"PDF generated with ReportLab: {output_path}")


async def _render_with_weasyprint(kit: Kit, output_path: Path) -> None:
    """Render PDF using WeasyPrint + Jinja2 templates (best quality)."""
    from weasyprint import HTML
    
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("kit_pdf.html")

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

    HTML(string=html_content).write_pdf(str(output_path))


async def _render_with_reportlab(kit: Kit, output_path: Path) -> None:
    """Render PDF using ReportLab (pure Python fallback)."""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    
    # Create PDF
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Paragraph(kit.title or "Interview Kit", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Match Analysis
    if kit.match_analysis:
        story.append(Paragraph("Match Analysis", heading_style))
        match = kit.match_analysis
        
        # Score
        score_text = f"<b>Overall Match Score:</b> {match.get('overall_match_score', 0):.1f}%"
        story.append(Paragraph(score_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Strengths
        if match.get('skill_matches'):
            story.append(Paragraph("<b>Strengths:</b>", subheading_style))
            for skill in match['skill_matches'][:8]:
                story.append(Paragraph(f"• {skill}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Gaps
        if match.get('skill_gaps'):
            story.append(Paragraph("<b>Skill Gaps:</b>", subheading_style))
            for gap in match['skill_gaps'][:8]:
                story.append(Paragraph(f"• {gap}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Experience Fit
        if match.get('experience_fit'):
            story.append(Paragraph("<b>Experience Assessment:</b>", subheading_style))
            story.append(Paragraph(match['experience_fit'], styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Questions
    if kit.questions:
        story.append(PageBreak())
        story.append(Paragraph(f"Interview Questions ({len(kit.questions)})", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, q in enumerate(kit.questions[:20], 1):  # Limit to 20 for PDF size
            question_text = f"<b>{idx}. {q.get('question', '')}</b>"
            story.append(Paragraph(question_text, styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
            
            # Category and difficulty
            meta = f"Category: {q.get('category', 'N/A')} | Difficulty: {q.get('difficulty', 'N/A')}"
            story.append(Paragraph(f"<i>{meta}</i>", styles['Normal']))
            
            # What it tests
            if q.get('what_it_tests'):
                story.append(Paragraph(f"<b>Tests:</b> {q['what_it_tests']}", styles['Normal']))
            
            # Model answer
            if q.get('model_answer'):
                story.append(Paragraph(f"<b>Expected Answer:</b> {q['model_answer'][:300]}...", styles['Normal']))
            
            story.append(Spacer(1, 0.15*inch))
    
    # Practical Test
    if kit.practical_test:
        story.append(PageBreak())
        test = kit.practical_test
        story.append(Paragraph("Practical Technical Assessment", heading_style))
        
        if test.get('overview'):
            story.append(Paragraph(test['overview'][:500], styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Variants
        for variant in test.get('variants', [])[:3]:
            story.append(Paragraph(f"<b>{variant.get('difficulty', '').title()} Level</b> ({variant.get('time_limit', 'N/A')})", subheading_style))
            
            # Task description (truncate if too long)
            task_desc = variant.get('task_description', '')[:1000]
            # Replace newlines with <br/> for ReportLab
            task_desc = task_desc.replace('\n', '<br/>')
            story.append(Paragraph(task_desc, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    # Rubric
    if kit.rubric and kit.rubric.get('criteria'):
        story.append(PageBreak())
        story.append(Paragraph("Scoring Rubric", heading_style))
        
        for criterion in kit.rubric['criteria'][:8]:
            story.append(Paragraph(f"<b>{criterion.get('name', 'N/A')}</b> (Weight: {criterion.get('weight_pct', 0)}%)", subheading_style))
            story.append(Paragraph(criterion.get('description', ''), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    # Red Flags
    if kit.red_flags:
        story.append(PageBreak())
        story.append(Paragraph(f"Red Flags to Watch ({len(kit.red_flags)})", heading_style))
        
        for flag in kit.red_flags[:10]:
            severity_color = {
                'high': colors.red,
                'medium': colors.orange,
                'low': colors.yellow
            }.get(flag.get('severity', 'low'), colors.grey)
            
            concern_text = f"<b>[{flag.get('severity', 'N/A').upper()}]</b> {flag.get('concern', '')}"
            story.append(Paragraph(concern_text, styles['Normal']))
            
            if flag.get('probe_question'):
                story.append(Paragraph(f"<i>Probe: {flag['probe_question']}</i>", styles['Normal']))
            
            story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)

