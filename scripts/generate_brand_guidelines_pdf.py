from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


OUTPUT_PATH = "D:/dev/agents/meal-prep-workflow/major-meal-prep-brand-guidelines.pdf"


def build_pdf(output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Major Meal Prep Brand Guidelines",
        author="Major Meal Prep",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=10,
            textColor=colors.HexColor("#1A1A1A"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=6,
            textColor=colors.HexColor("#1A1A1A"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1A1A1A"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#333333"),
            spaceAfter=3,
        )
    )

    story = []
    story.append(Paragraph("Major Meal Prep Brand Guidelines (v1)", styles["TitleCustom"]))
    story.append(
        Paragraph(
            "Purpose: Provide a complete branding foundation for logo creation, visual identity, and supporting assets.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    sections = [
        (
            "1) Brand Essence",
            [
                "<b>Brand Name:</b> Major Meal Prep",
                "<b>Positioning:</b> Practical AI tool that turns any recipe into a macro-aligned meal prep plan quickly.",
                "<b>Personality:</b> Utilitarian, disciplined, direct, no fluff, performance-focused.",
                "<b>Tone of Voice:</b> Clear, confident, concise, results-oriented.",
            ],
        ),
        (
            "2) Core Messaging",
            [
                "<b>Primary Promise:</b> Turn any recipe into a macro-perfect meal prep plan in seconds.",
                "<b>Value Pillars:</b> Speed, Precision, Consistency.",
                "<b>Primary CTAs:</b> Start Free Trial, Create Your Free Account.",
                "<b>Secondary CTA:</b> Sign In.",
                "<b>Support Copy:</b> No credit card required. Cancel anytime.",
            ],
        ),
        (
            "3) Visual Style Direction",
            [
                "<b>Style Name:</b> Utilitarian Punk.",
                "<b>Look &amp; Feel:</b> Bold, functional, high-contrast, blocky components, stamped/shadowed edges, uppercase typography.",
                "<b>Principles:</b> Clarity over decoration, hard structure, modular layout, practical hierarchy.",
            ],
        ),
        (
            "4) Typography",
            [
                "<b>Heading Font:</b> Bebas Neue (fallback: Impact, sans-serif).",
                "<b>Body Font:</b> Inter (fallback: Arial/Helvetica, sans-serif).",
                "<b>Heading Rules:</b> Uppercase, bold, tight line-height, slight letter spacing.",
                "<b>UI Labels/Buttons:</b> Uppercase and heavy weight.",
            ],
        ),
        (
            "5) UI Shape Language",
            [
                "<b>Borders:</b> 3px solid black (#000000).",
                "<b>Card Surface:</b> Muted olive surface.",
                "<b>Shadow:</b> Hard stamp shadow (2px x 2px black).",
                "<b>Buttons:</b> Rectangular, heavy border, uppercase labels.",
                "<b>Interaction Feel:</b> Tactile pressed-state behavior.",
            ],
        ),
        (
            "6) Logo Direction",
            [
                "<b>Objective:</b> Functional and memorable, not ornate.",
                "<b>Preferred Concepts:</b> Wordmark-first, MMP monogram mark, or hard-edged badge lockup.",
                "<b>Constraints:</b> No gradients, no script fonts, no soft rounded style.",
                "<b>Coloring:</b> Prioritize monochrome + limited accent variant.",
            ],
        ),
        (
            "7) Imagery and Iconography",
            [
                "<b>Imagery:</b> Practical meal prep scenes, ingredients, prep containers, workflow context.",
                "<b>Avoid:</b> Glossy lifestyle stock look, abstract SaaS gradients, whimsical visuals.",
                "<b>Icons:</b> Simple, geometric, bold, high legibility.",
            ],
        ),
        (
            "8) Do / Don't",
            [
                "<b>Do:</b> Use uppercase headings and clear CTA hierarchy.",
                "<b>Do:</b> Keep strong contrast and visible borders.",
                "<b>Don't:</b> Introduce pastel palettes or delicate type hierarchy.",
                "<b>Don't:</b> Add decorative effects that reduce clarity.",
            ],
        ),
    ]

    for heading, bullets in sections:
        story.append(Paragraph(heading, styles["SectionHeading"]))
        for bullet in bullets:
            story.append(Paragraph(f"- {bullet}", styles["Body"]))
        story.append(Spacer(1, 4))

    story.append(Paragraph("Color System (Exact Hex)", styles["SectionHeading"]))
    color_rows = [
        ["Token", "Hex", "Usage"],
        ["Background", "#6B705C", "Primary page background"],
        ["Surface", "#8D927D", "Cards, panels, surface blocks"],
        ["Primary Text", "#1A1A1A", "Core text and headings"],
        ["Accent", "#FF5722", "Primary CTA buttons and highlights"],
        ["Accent Hover", "#FF6D40", "Primary CTA hover state"],
        ["Secondary CTA BG", "#3A3A3A", "Secondary button background"],
        ["Secondary CTA Hover", "#4A4A4A", "Secondary button hover"],
        ["Secondary CTA Text", "#F5F5F5", "Secondary button text"],
        ["Input/Dark Utility", "#2B2B2B", "Input and dark utility surfaces"],
        ["Error", "#EF4444", "Error and warning feedback"],
        ["Border/Shadow", "#000000", "Borders and stamped shadows"],
    ]
    color_table = Table(color_rows, colWidths=[1.8 * inch, 1.2 * inch, 3.4 * inch])
    color_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#000000")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(color_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Brand Kit Upload Checklist", styles["SectionHeading"]))
    checklist = [
        "Logo files: primary, inverse, and icon-only versions (SVG/PNG).",
        "Color palette: include all exact hex values from this guide.",
        "Typography: Bebas Neue and Inter.",
        "Button samples: primary and secondary variants.",
        "Card and layout samples with 3px border + hard shadow.",
        "Hero/supporting imagery aligned to practical performance vibe.",
    ]
    for item in checklist:
        story.append(Paragraph(f"- {item}", styles["Body"]))

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Reference website style tokens: background #6B705C, surface #8D927D, primary text #1A1A1A, accent #FF5722, border/shadow #000000.",
            styles["Small"],
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build_pdf(OUTPUT_PATH)
    print(f"Created: {OUTPUT_PATH}")
