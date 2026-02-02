from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
from datetime import datetime

def generate_summary_pdf(session_id:int, patient_name:str, symptoms:list, file_path:str):

    c=canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    #header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-80, f"Session ID: {session_id}")
    c.drawString(50, height-100, f"Patient Name: {patient_name}")
    c.drawString(50, height-120, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    #divider line

    c.setStrokeColor(colors.gray)
    c.line(50, height-140, width-50, height-140)

    #symptom section
    y_pos = height-180
    c.setFont("Helvetica", 16)
    c.drawString(50, y_pos, "Reported Symptoms:")
    y_pos -= 30

    c.setFont("Helvetica-Bold", 12)

    if not symptoms:
        c.drawString(50, y_pos, "No symptoms reported.")
    else:
        for s in symptoms:
            name = s.get("symptom", "unknown").capitalize()
            severity = s.get("severity", "N/A")
            duration = s.get("duration", "N/A")
            freq = s.get("frequency", "N/A")

            #bullet
            c.setFont("Helvetica", 12)
            c.drawString(60, y_pos, "-")
            y_pos -= 20

            #details
            c.setFont("Helvetica-Bold", 10)
            c.drawString(80, y_pos, f"Severity: {severity}")
            c.drawString(70, y_pos, f"Duration: {duration}")
            c.drawString(50, y_pos, f"Frequency: {freq}")
            c.setFillColor(colors.black)
            y_pos -= 30

            #break
            if y_pos < 100:
                c.showPage()
                y_pos = height-50
    c.save()
    return file_path
