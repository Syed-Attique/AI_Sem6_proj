from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "AI_Phishing_Detector_Report.pdf"
METRICS = ROOT / "model" / "metrics.txt"

BLUE = colors.HexColor("#2E74B5")
DARK_BLUE = colors.HexColor("#1F4D78")
MUTED = colors.HexColor("#555555")
BORDER = colors.HexColor("#DADCE0")
LIGHT_GRAY = colors.HexColor("#F2F4F7")
CALLOUT = colors.HexColor("#F4F6F9")
RISK_RED = colors.HexColor("#9B1C1C")
GREEN = colors.HexColor("#166534")


def styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=DARK_BLUE,
            spaceAfter=8,
        )
    )
    base.add(
        ParagraphStyle(
            name="Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceAfter=6,
        )
    )
    base.add(
        ParagraphStyle(
            name="Meta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceAfter=18,
        )
    )
    base.add(
        ParagraphStyle(
            name="Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=7,
        )
    )
    base.add(
        ParagraphStyle(
            name="H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=BLUE,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    base.add(
        ParagraphStyle(
            name="H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    base.add(
        ParagraphStyle(
            name="H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=DARK_BLUE,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    base.add(
        ParagraphStyle(
            name="Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=MUTED,
        )
    )
    base.add(
        ParagraphStyle(
            name="TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=11,
            spaceAfter=0,
        )
    )
    base.add(
        ParagraphStyle(
            name="TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.7,
            leading=11,
            textColor=DARK_BLUE,
            spaceAfter=0,
        )
    )
    return base


S = styles()


def p(text, style="Body"):
    return Paragraph(text, S[style])


def bullet_list(items):
    return ListFlowable(
        [ListItem(p(item), leftIndent=12) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
        bulletFontSize=7,
    )


def numbered_list(items):
    return ListFlowable(
        [ListItem(p(item), leftIndent=14) for item in items],
        bulletType="1",
        leftIndent=20,
    )


def table(data, widths):
    wrapped = []
    for row_idx, row in enumerate(data):
        style = "TableHead" if row_idx == 0 else "TableCell"
        wrapped.append([p(str(cell), style) for cell in row])
    tbl = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="CENTER")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tbl


def callout(title, body):
    content = [[p(f"<b>{title}</b> {body}", "Body")]]
    tbl = Table(content, colWidths=[6.3 * inch], hAlign="CENTER")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CALLOUT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return tbl


def metrics_summary():
    if not METRICS.exists():
        return "Metrics file not found. Run python -m backend.train_model to regenerate metrics."
    text = METRICS.read_text(encoding="utf-8", errors="ignore")
    lines = []
    capture = False
    for line in text.splitlines():
        if line.startswith("Best model:"):
            lines.append(line)
        if line.startswith("Model: Random Forest"):
            capture = True
        if capture:
            lines.append(line)
            if line.strip().startswith("phishing"):
                break
    return " | ".join(lines[:14])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(
        letter[0] - inch,
        0.55 * inch,
        f"AI Phishing Detector Report | Page {doc.page}",
    )
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title="AI Browser Extension for Phishing Detection",
        author="S M Attique Ur Rehman, Anfas Ali, Asher Ahmed",
    )

    story = []
    story.append(p("AI Browser Extension for Phishing Detection", "ReportTitle"))
    story.append(p("Final Project Report", "Subtitle"))
    story.append(
        p(
            "23K-0714 S M Attique Ur Rehman | 23K-0574 Anfas Ali | 23K-0511 Asher Ahmed",
            "Meta",
        )
    )
    story.append(
        callout(
            "Executive summary.",
            "This project implements a Chrome/Edge browser extension that detects phishing URLs in real time using a Flask backend and a machine learning classifier. It warns users before they enter sensitive information and includes user feedback to reduce false positives.",
        )
    )
    story.append(Spacer(1, 10))

    story.append(p("1. Introduction", "H1"))
    story.append(
        p(
            "Phishing websites imitate trusted services to steal credentials, card details, and personal information. The goal of this project is to demonstrate how artificial intelligence can support safer browsing by classifying URLs as legitimate or suspicious while the user browses the web."
        )
    )
    story.append(
        p(
            "The solution combines machine learning, URL feature engineering, a Flask prediction API, and a Manifest V3 browser extension. The extension performs real-time checks, displays a popup status, and shows a full-page warning when a phishing risk is detected."
        )
    )

    story.append(p("2. Objectives", "H1"))
    story.append(
        bullet_list(
            [
                "Detect phishing websites in real time from the browser.",
                "Train and evaluate machine learning models for URL classification.",
                "Warn users clearly before they enter sensitive information.",
                "Reduce false positives through trusted domains and user feedback.",
                "Demonstrate a practical AI application in cybersecurity.",
            ]
        )
    )

    story.append(p("3. System Architecture", "H1"))
    story.append(
        p(
            "The system is divided into five main parts. The extension captures the current tab URL, the backend predicts risk, the model performs classification, and feedback files allow user corrections to improve future scans."
        )
    )
    story.append(
        table(
            [
                ["Component", "Main Files", "Purpose"],
                ["Browser Extension", "extension/manifest.json, background.js, popup.js, content.js", "Captures visited URLs, displays scan status, and shows phishing warnings."],
                ["Flask Backend", "backend/app.py", "Provides /predict and /mark-legitimate APIs for scanning and user feedback."],
                ["Feature Extraction", "backend/features.py", "Converts URLs into numeric ML features such as entropy, suspicious keywords, IP address flags, and query structure."],
                ["Model Training", "backend/train_model.py", "Trains and compares ML models, then saves the best classifier as phishing_model.pkl."],
                ["Datasets", "dataset/*.csv, real_phishdataset_balanced.xlsx", "Stores real phishing data, trusted legitimate domains, and user feedback."],
            ],
            [1.35 * inch, 2.2 * inch, 2.75 * inch],
        )
    )

    story.append(p("4. Dataset and Feature Engineering", "H1"))
    story.append(
        p(
            "The project uses the public ESDAUNG/PhishDataset balanced dataset, based on PhishTank phishing URLs and legitimate URL sources. It is normalized into url,label format. The project also includes trusted legitimate domains and user feedback data to reduce false positives for well-known services."
        )
    )
    story.append(p("Key URL Features", "H2"))
    story.append(
        bullet_list(
            [
                "Length-based features: URL length, domain length, path length, query length, and longest token length.",
                "Character-based features: dot count, hyphen count, digit count, special character ratio, and entropy.",
                "Security indicators: HTTPS usage, IP address in hostname, suspicious TLD, URL shortener, and encoded characters.",
                "Phishing patterns: suspicious keywords, brand keywords in subdomains, executable file extensions, and redirect-like paths.",
            ]
        )
    )

    story.append(p("5. Machine Learning Model", "H1"))
    story.append(
        p(
            "The training script evaluates Logistic Regression, Decision Tree, Random Forest, and Naive Bayes. The selected model is chosen using phishing recall first and F1-score second because missing a phishing website is more dangerous than marking an extra site as suspicious."
        )
    )
    story.append(callout("Current model result.", metrics_summary()))
    story.append(Spacer(1, 8))
    story.append(
        table(
            [
                ["Evaluation Item", "Result", "Interpretation", "Status"],
                ["Selected model", "Random Forest", "Best model according to phishing recall and F1-score.", "Passed"],
                ["Accuracy", "Approx. 94.5%", "Correctly classifies most URLs in the held-out split.", "Passed"],
                ["Phishing recall", "Approx. 94.9%", "Prioritizes catching phishing URLs, reducing missed attacks.", "Passed"],
                ["Backend tests", "8 passed", "API, trusted domains, and feedback endpoint verified.", "Passed"],
                ["Extension checks", "JS syntax passed", "Popup, background, and content scripts parse correctly.", "Passed"],
            ],
            [1.45 * inch, 1.15 * inch, 2.85 * inch, 0.85 * inch],
        )
    )

    story.append(PageBreak())
    story.append(p("6. Backend API", "H1"))
    story.append(
        p(
            "The Flask backend exposes two main endpoints. The /predict endpoint receives a URL, checks trusted domains, extracts features, loads the saved model, and returns a prediction with risk score. The /mark-legitimate endpoint lets the user correct false positives."
        )
    )
    story.append(
        numbered_list(
            [
                "Extension sends the current URL to /predict.",
                "Backend checks trusted legitimate domains before calling the model.",
                "If not trusted, features are extracted and passed to the trained model.",
                "Backend returns prediction, risk score, URL, and source where applicable.",
                "If the user marks a false positive as legitimate, the URL and domain are saved for future scans.",
            ]
        )
    )

    story.append(p("7. Browser Extension", "H1"))
    story.append(
        p(
            "The extension uses Chrome Manifest V3. Its background script monitors tab updates, calls the Flask backend, stores results, and notifies content scripts. The popup displays the scan result, risk score, and actions. The content script renders a full-page warning overlay for suspicious websites."
        )
    )
    story.append(p("User Interface Behavior", "H2"))
    story.append(
        bullet_list(
            [
                "Safe sites show a green safe status and low risk score.",
                "Suspicious sites show a red danger status and warning text.",
                "The warning overlay includes Go Back, Mark as Legit, and Continue Anyway.",
                "Mark as Legit records user feedback and immediately trusts the corrected domain.",
                "Rescan Current Page sends the current URL to the backend again without retraining the model.",
            ]
        )
    )

    story.append(p("8. Testing", "H1"))
    story.append(
        p(
            "Testing covered feature extraction, backend endpoints, trusted-domain handling, user feedback, JavaScript syntax, and manual browser behavior."
        )
    )
    story.append(
        bullet_list(
            [
                "Feature tests verify URL normalization and suspicious signal extraction.",
                "Backend tests verify /health, /predict, trusted domains, and /mark-legitimate.",
                "JavaScript syntax checks verify background.js, popup.js, and content.js.",
                "Manual tests verify safe websites, suspicious phishing-like URLs, warning overlay actions, and user feedback.",
            ]
        )
    )

    story.append(p("9. Limitations", "H1"))
    story.append(
        bullet_list(
            [
                "The model uses URL-based features only and does not inspect full webpage HTML or screenshots.",
                "The extension depends on a locally running Flask backend.",
                "Trusted-domain overrides reduce false positives but must be maintained carefully to avoid over-trusting broad domains.",
                "The model is suitable for academic demonstration and should not be treated as production security software without further validation.",
            ]
        )
    )

    story.append(p("10. Future Improvements", "H1"))
    story.append(
        bullet_list(
            [
                "Add webpage content features such as forms, password fields, hidden inputs, and suspicious scripts.",
                "Use domain age, certificate information, WHOIS data, and reputation services.",
                "Add automated retraining after enough user feedback is collected.",
                "Package the model inside the extension using ONNX or TensorFlow.js to remove the Flask dependency.",
                "Add a dashboard showing scan history, blocked sites, and false-positive corrections.",
            ]
        )
    )

    story.append(p("11. Conclusion", "H1"))
    story.append(
        p(
            "The project demonstrates a complete AI-assisted phishing detection workflow. It combines a browser extension, Flask API, machine learning model, real phishing dataset, trusted-domain handling, user feedback, and clear warning actions. The result is an interactive cybersecurity tool that can identify risky URLs and help users avoid phishing attacks."
        )
    )

    story.append(p("References", "H1"))
    story.append(
        bullet_list(
            [
                "ESDAUNG/PhishDataset public dataset: https://github.com/ESDAUNG/PhishDataset",
                "PhishTank phishing URL source referenced by the dataset: https://phishtank.org",
                "Scikit-learn machine learning library: https://scikit-learn.org",
                "Chrome Extensions Manifest V3 documentation: https://developer.chrome.com/docs/extensions",
                "Flask web framework documentation: https://flask.palletsprojects.com",
            ]
        )
    )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
