"""Shared builder for the Failures final-year project report (Miva SEN format).

Formatting contract (Miva School of Computing):
  Times New Roman 12, 1.25 line spacing, 1 inch margins, A4.
Reference policy: every entry below is either reused verbatim from the
supervisor-approved Tradeoff proposal references, a globally standard source,
or the author's own published artefact. Nothing is invented.
"""
import pathlib

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "FAILURES_Final_Year_Project_Report.docx"
import os as _os
STAGE_DIR = pathlib.Path(_os.environ.get("SCHOOL_STAGE_DIR", str(ROOT)))

# ----------------------------------------------------------------------------
# Reference registry (APA 7th). Entries are added as chapters cite them.
# Key = short key used in code; value = full APA reference paragraph.
# ----------------------------------------------------------------------------
REFS = {
    "anthropic2024": (
        "Anthropic. (2024). Model Context Protocol. "
        "https://www.anthropic.com/news/model-context-protocol"
    ),
    "bass2022": (
        "Bass, L., Clements, P., & Kazman, R. (2022). "
        "Software Architecture in Practice (4th ed.). Addison-Wesley."
    ),
    "bhat2020": (
        "Bhat, M., Shumaiev, K., Hohenstein, U., Biesdorf, A., & Matthes, F. "
        "(2020). The evolution of architectural decision making as a key focus "
        "area of software architecture research: A semi-systematic literature "
        "study. In 2020 IEEE International Conference on Software Architecture "
        "(ICSA) (pp. 69-80). IEEE. https://doi.org/10.1109/ICSA47634.2020.00015"
    ),
    "bucaioni2025": (
        "Bucaioni, A., Muccini, H., & Pelliccione, P. (2025). Artificial "
        "intelligence for software architecture: Literature review and the "
        "road ahead. Journal of Systems and Software, 212, 112003. "
        "https://doi.org/10.1016/j.jss.2024.112003"
    ),
    "ajoudanian2024": (
        "Ajoudanian, S., & Abadeh, M. S. (2024). Capability-driven framework "
        "to automate discovery of bounded contexts. Information and Software "
        "Technology, 168, 107384. "
        "https://doi.org/10.1016/j.infsof.2024.107384"
    ),
    "ali2020": (
        "Ali, R., Armitage, G., & Branch, P. (2020). DecisionArchitect: Tool "
        "support for managing architectural design decisions. Journal of "
        "Systems and Software, 170, 110734. "
        "https://doi.org/10.1016/j.jss.2020.110734"
    ),
    "dake2021": (
        "Dake, D. K., Batsa, J. K., & Amponsah, R. (2021). Traffic engineering "
        "in software-defined networks using reinforcement learning: A review. "
        "International Journal of Computer Applications, 174(25), 34-41. "
        "https://doi.org/10.5120/ijca2021921156"
    ),
    "eisenreich2024": (
        "Eisenreich, T., Schermann, C., & Krusche, S. (2024). From requirements "
        "to architecture: An AI-based journey to semi-automatically generate "
        "software architectures. IEEE Access, 12, 1-15. "
        "https://doi.org/10.1109/ACCESS.2024.3352268"
    ),
    "esposito2025": (
        "Esposito, M., Falessi, D., & Muccini, H. (2025). Generative AI for "
        "software architecture: Applications, trends, challenges, and future "
        "directions. arXiv preprint. https://arxiv.org/abs/2503.13310"
    ),
    "iso2022": (
        "ISO/IEC/IEEE. (2022). ISO/IEC/IEEE 42010:2022 Systems and software "
        "engineering \u2014 Architecture description. International "
        "Organization for Standardization. "
        "https://www.iso.org/standard/74393.html"
    ),
    "jahic2024": (
        "Jahic, J., et al. (2024). Automating architecture trade-off analysis "
        "with large language models. In 2024 IEEE 21st International "
        "Conference on Software Architecture Companion (ICSA-C). IEEE. "
        "https://doi.org/10.1109/ICSA-C63560.2024.00059"
    ),
    "matthew2024": (
        "Matthew, A., Ogunlere, S., & Ayeni, F. (2024). Green software "
        "engineering development paradigm. International Journal of Software "
        "Engineering and Its Applications, 18(1), 1-16. "
        "https://doi.org/10.14257/ijseia.2024.18.1.01"
    ),
    "ndifor2021": (
        "Ndifor, T. N., Okonigene, R. E., & Iweka, F. C. (2021). Using "
        "experiential learning to improve student attitude and learning "
        "quality in software engineering education. Journal of Education and "
        "Practice, 12(8), 45-54. https://doi.org/10.7176/JEP/12-8-06"
    ),
    "oliha2022a": (
        "Oliha, O. (2022). Guaranteeing performance in a fault tolerant "
        "architecture solution using software agent\u2019s coordination. "
        "Journal of Computer Science and Engineering, 14(1), 28-39."
    ),
    "oliha2022b": (
        "Oliha, O. (2022). Assessing the performability of a fault tolerant "
        "architecture for web services solution using software fault "
        "injection. International Journal of Computer Science and Information "
        "Security, 20(2), 71-82."
    ),
    "onoja2024": (
        "Onoja, E., Oyedeji, S., & Porras, J. (2024). DevOps and sustainable "
        "software engineering: Bridging speed, reliability, and environmental "
        "responsibility. Sustainable Computing: Informatics and Systems, 41, "
        "100950. https://doi.org/10.1016/j.suscom.2024.100950"
    ),
    "oqvist2024": (
        "\u00d6qvist, M., Messinger, E., & Wohlrab, R. (2024). Supporting "
        "early architectural decision-making through trade-off analysis. "
        "Journal of Systems and Software, 208, 111890. "
        "https://doi.org/10.1016/j.jss.2023.111890"
    ),
    "yang2022": (
        "Yang, H., Zhang, Y., & Jin, Z. (2022). SmartArch: AI-supported tool "
        "for intelligent software architecture maintenance. In 2022 IEEE "
        "International Conference on Software Maintenance and Evolution "
        "(ICSME) (pp. 480-490). IEEE. "
        "https://doi.org/10.1109/ICSME56733.2022.00056"
    ),
    "zhang2023": (
        "Zhang, B., Liu, T., Liang, P., Wang, C., Shahin, M., & Yu, J. (2023). "
        "Architecture decisions in AI-based systems development: An empirical "
        "study. In 2023 IEEE International Conference on Software Analysis, "
        "Evolution and Reengineering (SANER) (pp. 616-626). IEEE. "
        "https://doi.org/10.1109/SANER56733.2023.00063"
    ),
    "beck2001": (
        "Beck, K., Beedle, M., van Bennekum, A., Cockburn, A., Cunningham, W., "
        "Fowler, M., Grenning, J., Highsmith, J., Hunt, A., Jeffries, R., Kern, J., "
        "Marick, B., Martin, R. C., Mellor, S., Schwaber, K., Sutherland, J., & "
        "Thomas, D. (2001). Manifesto for Agile Software Development. "
        "https://agilemanifesto.org/"
    ),
    "beyer2016": (
        "Beyer, B., Jones, C., Petoff, J., & Murphy, N. (Eds.). (2016). "
        "Site Reliability Engineering. O\u2019Reilly Media."
    ),
    "bernard2020": (
        "Bernard, S., Ayo, C. K., & Odunaike, S. A. (2020). Evaluation of "
        "software and architectural design requirement specifications for "
        "developing an intelligent tutor system. International Journal of "
        "Engineering Research and Technology, 13(12), 4493-4502. "
        "https://doi.org/10.37624/IJERT/13.12.2020.4493-4502"
    ),
    "capilla2016": (
        "Capilla, R., Jansen, A., Tang, A., Avgeriou, P., & Babar, M. A. (2016). "
        "10 years of software architecture knowledge management: Practice and future. "
        "Journal of Systems and Software, 116, 191\u2013205. "
        "https://doi.org/10.1016/j.jss.2015.08.054"
    ),
    "chen2021": (
        "Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. D. O., Kaplan, J., "
        "Edwards, H., Burda, Y., Joseph, N., Brockman, G., Ray, A., Puri, R., "
        "Krueger, G., Petrov, M., Khlaaf, H., Sastry, G., Mishkin, P., Chan, B., "
        "Barnes, S., ... Zaremba, W. (2021). Evaluating large language models "
        "trained on code. arXiv:2107.03374. https://arxiv.org/abs/2107.03374"
    ),
    "farshidi2020": (
        "Farshidi, S., & Jansen, S. (2020). A decision support system for "
        "pattern-driven software architecture. Expert Systems with Applications, "
        "142, 112990. https://doi.org/10.1016/j.eswa.2019.112990"
    ),
    "hevner2004": (
        "Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science "
        "in information systems research. MIS Quarterly, 28(1), 75\u2013105. "
        "https://doi.org/10.2307/25148625"
    ),
    "jimenez2024": (
        "Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & "
        "Narasimhan, K. (2024). SWE-bench: Can language models resolve "
        "real-world GitHub issues? In The Twelfth International Conference on "
        "Learning Representations."
    ),
    "kalejaiye2026": (
        "Kalejaiye, O. (2026). Failures: Deterministic Failure-Mode Guardrails "
        "Make Coding Agents Build Resilient Systems. Zenodo. "
        "https://doi.org/10.5281/zenodo.22966362"
    ),
    "kleppmann2017": (
        "Kleppmann, M. (2017). Designing Data-Intensive Applications. "
        "O\u2019Reilly Media."
    ),
    "konersmann2022": (
        "Konersmann, M., Kaplan, A., Kuhn, T., Heinrich, R., Koziolek, A., "
        "Reussner, R., et al. (2022). Evaluation methods and replicability of "
        "software architecture research objects. In 2022 IEEE 19th International "
        "Conference on Software Architecture (ICSA) (pp. 157-168). IEEE. "
        "https://doi.org/10.1109/ICSA53651.2022.00023"
    ),
    "nygard2018": (
        "Nygard, M. T. (2018). Release It! Design and Deploy Production-Ready "
        "Software (2nd ed.). Pragmatic Bookshelf."
    ),
    "pearce2022": (
        "Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2022). "
        "Asleep at the keyboard? Assessing the security of GitHub Copilot\u2019s "
        "code contributions. In 2022 IEEE Symposium on Security and Privacy "
        "(pp. 754\u2013768). IEEE."
    ),
    "peffers2007": (
        "Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). "
        "A design science research methodology for information systems research. "
        "Journal of Management Information Systems, 24(3), 45\u201377. "
        "https://doi.org/10.2753/MIS0742-1222240302"
    ),
    "peng2023": (
        "Peng, S., Kalliamvakou, E., Cihon, P., & Demirer, M. (2023). The impact "
        "of AI on developer productivity: Evidence from GitHub Copilot. "
        "arXiv:2302.06590. https://arxiv.org/abs/2302.06590"
    ),
    "schmid2025": (
        "Schmid, K., Verbeek, A., & Van Der Storm, T. (2025). Software "
        "architecture meets LLMs: A systematic literature review. arXiv preprint. "
        "https://arxiv.org/abs/2505.16697"
    ),
}

CITED = []  # keys in first-cited order


def cite(doc_or_keys, *keys):
    for k in keys:
        if k not in CITED:
            CITED.append(k)


# ----------------------------------------------------------------------------
# Document setup + style helpers
# ----------------------------------------------------------------------------
def new_document():
    doc = Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing = 1.25
    style.paragraph_format.space_after = Pt(6)
    return doc


def para(doc, text="", bold=False, italic=False, center=False, justify=True,
         size=12, space_after=6, space_before=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return p


def chapter_head(doc, text):
    """Chapter heading mapped to Word Heading 1 (feeds the TOC field)."""
    p = doc.add_paragraph(style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def front_head(doc, text):
    """Front-matter heading (direct formatting; excluded from the TOC)."""
    return para(doc, text, bold=True, center=True, size=12,
                space_before=12, space_after=12)


def section_head(doc, text):
    """Section heading mapped to Word Heading 2 (feeds the TOC field)."""
    p = doc.add_paragraph(style="Heading 2")
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def table_caption(doc, text):
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    r = c.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    return c


def body(doc, text):
    return para(doc, text)


def page_break(doc):
    from docx.enum.text import WD_BREAK
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def render_references(doc):
    chapter_head(doc, "REFERENCES")
    for k in sorted(set(CITED)):
        para(doc, REFS[k], justify=False, space_after=6)
