from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os


def generate_sample_pdf(path: str = "sample_syllabus.pdf"):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Page 1
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 80, "UPSC General Studies Paper 1")
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 120, "Section: Indian History & Geography")
    c.drawString(72, height - 150, "Overview: Ancient, Medieval, and Modern Indian History; Physical and Human Geography of India.")
    c.drawString(72, height - 180, "Topics:")
    y = height - 210
    topics = [
        "Ancient India: Indus Valley, Vedic Age, Maurya, Gupta",
        "Medieval India: Delhi Sultanate, Mughal Empire",
        "Modern India: 1757-1947 - key movements and leaders",
        "Physical Geography: Indian Monsoon, Rivers, Himalayan orogeny",
    ]
    for t in topics:
        c.drawString(90, y, f"- {t}")
        y -= 20
    c.showPage()

    # Page 2
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 80, "Detailed Syllabus: Indian History")
    c.setFont("Helvetica", 11)
    y = height - 120
    for i in range(1, 12):
        c.drawString(72, y, f"{i}. Topic {i}: Key concepts and timeline summaries.")
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 80
    c.showPage()

    # Page 3
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 80, "Detailed Syllabus: Indian Geography")
    c.setFont("Helvetica", 11)
    y = height - 120
    for i in range(1, 12):
        c.drawString(72, y, f"G{i}. Subtopic {i}: maps, rivers, climate notes.")
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 80

    c.save()
    print(f"Sample PDF generated: {os.path.abspath(path)}")


if __name__ == "__main__":
    generate_sample_pdf()
