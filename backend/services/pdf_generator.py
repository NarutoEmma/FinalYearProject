from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
import os
from datetime import datetime

"""
    this generates a pdf report of patient symptoms containing:
        session_id
        patient_name
        list of symptoms
        and returns pdf file path
    """
def generate_summary_pdf(session_id: int, patient_name: str, symptoms: list, file_path: str):

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    #header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Patient Pre-Consultation Report")

    #patient details
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Session ID: {session_id}")
    c.drawString(50, height - 100, f"Patient Name: {patient_name}")
    c.drawString(50, height - 120, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.line(50, height - 140, width - 50, height - 140)

    #symptom section
    y_pos = height - 180
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "Reported Symptoms:")
    y_pos -= 30

    if not symptoms:
        c.setFont("Helvetica", 12)
        c.drawString(70, y_pos, "No symptoms reported.")
    else:
        for idx, s in enumerate(symptoms, 1):
            #extract symptom details with defaults
            name = s.get("symptom", "Unknown symptom").capitalize()
            severity = s.get("severity", "Not specified")
            duration = s.get("duration", "Not specified")
            freq = s.get("frequency", "Not specified")

            #check if we need a new page
            if y_pos < 150:
                c.showPage()
                y_pos = height - 50
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_pos, "Reported Symptoms (continued):")
                y_pos -= 30

            #symptom number and name
            c.setFont("Helvetica-Bold", 12)
            c.drawString(60, y_pos, f"{idx}. {name}")
            y_pos -= 20

            #symptom details
            c.setFont("Helvetica", 10)
            c.drawString(80, y_pos, f"Severity: {severity}")
            y_pos -= 15
            c.drawString(80, y_pos, f"Duration: {duration}")
            y_pos -= 15
            c.drawString(80, y_pos, f"Frequency: {freq}")
            y_pos -= 25  # Extra space between symptoms

            #separator line between symptoms
            c.setStrokeColor(colors.lightgrey)
            c.setLineWidth(0.5)
            c.line(70, y_pos + 5, width - 70, y_pos + 5)
            y_pos -= 10

    #footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    footer_text = "This report is generated automatically and should be reviewed by a healthcare professional."
    c.drawString(50, 30, footer_text)
    c.drawString(width - 150, 30, f"Page 1")

    #save the pdf
    c.save()
    print(f"✅ PDF generated successfully: {file_path}")
    return file_path


#pdf test
def test_pdf_generation():
    #test the pdf generator with sample data
    test_symptoms = [
        {
            "symptom": "headache",
            "severity": "severe",
            "duration": "3 days",
            "frequency": "constant"
        },
        {
            "symptom": "fever",
            "severity": "moderate",
            "duration": "2 days",
            "frequency": "intermittent"
        },
        {
            "symptom": "cough",
            "severity": "mild",
            "duration": "1 week",
            "frequency": "occasional"
        }
    ]

    #create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    #generate test pdf
    output_path = f"reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generate_summary_pdf(
        session_id=12345,
        patient_name="Test Patient",
        symptoms=test_symptoms,
        file_path=output_path
    )

    print(f"Test PDF saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    test_pdf_generation()