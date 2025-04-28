from reportlab.pdfgen import canvas

c = canvas.Canvas('prueba.pdf', pagesize=(595.44, 297.72))
c.drawString(200, 100, 'Juan Perez')
c.showPage()
c.save()