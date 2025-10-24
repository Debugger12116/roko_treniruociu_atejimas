import os
from datetime import datetime
from collections import defaultdict
import calendar

# --- LT lokalizacija ir šriftai ---
LT_MONTHS = [
    "Sausis","Vasaris","Kovas","Balandis","Gegužė","Birželis",
    "Liepa","Rugpjūtis","Rugsėjis","Spalis","Lapkritis","Gruodis"
]
LT_WEEKDAYS = [
    "Pirmadienis","Antradienis","Trečiadienis",
    "Ketvirtadienis","Penktadienis","Šeštadienis","Sekmadienis"
]

def register_pdf_fonts():
    """Registruoja Unicode šriftus PDF’ui, kad neliktų juodų kvadratų."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    candidates = [
        # projektinėje aplinkoje
        ("DejaVuSans", "DejaVuSans.ttf"),
        ("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"),
        # tipinės Linux/Mac lokacijos
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ( "ArialUnicodeMS", "/Library/Fonts/Arial Unicode.ttf"),
        ( "ArialUnicodeMS-Bold", "/Library/Fonts/Arial Unicode Bold.ttf"),
    ]

    found = {}
    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                found[name] = True
            except Exception:
                pass

    # Pasirink šrifto vardus, kurie tikrai užsiregistravo
    base = "DejaVuSans" if "DejaVuSans" in found else ("ArialUnicodeMS" if "ArialUnicodeMS" in found else "Helvetica")
    bold = "DejaVuSans-Bold" if "DejaVuSans-Bold" in found else ("ArialUnicodeMS-Bold" if "ArialUnicodeMS-Bold" in found else "Helvetica-Bold")
    return base, bold


def load_attendance(filename="attendance.txt"):
    """Įkelia lankomumo įrašus iš failo."""
    attendance = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    date, status = line.split(',')
                    attendance[date] = status.lower() == 'taip'
    return attendance

def save_attendance(attendance, filename="attendance.txt"):
    """Išsaugo lankomumo įrašus į failą."""
    with open(filename, 'w') as f:
        for date, status in sorted(attendance.items()):
            f.write(f"{date},{'taip' if status else 'ne'}\n")

def add_record(attendance):
    """Prideda naują lankomumo įrašą."""
    date_str = input("Įveskite datą (YYYY-MM-DD): ").strip()
    
    # Patikrina datos formatą
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Neteisingas datos formatas! Naudokite YYYY-MM-DD")
        return
    
    status = input("Ar Rokas Šipkauskas buvo treniruotėje? (taip/ne): ").strip().lower()
    
    if status not in ['taip', 'ne']:
        print("Prašome įvesti 'taip' arba 'ne'")
        return
    
    attendance[date_str] = (status == 'taip')
    save_attendance(attendance)
    print(f"✓ Įrašas pridėtas {date_str}")

def generate_pdf_report(attendance):
    """Sugeneruoja PDF ataskaitą konkrečiam mėnesiui ir metams (su Calibri šriftu)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import matplotlib.pyplot as plt
        import matplotlib
        import io, os
    except ImportError:
        print("\n⚠ Trūksta reikalingų bibliotekų!")
        print("Įdiekite: pip install reportlab matplotlib")
        return

    # --- Šriftų registracija (Calibri + fallback į DejaVu Sans) ---
    calibri_paths = [
        "calibri.ttf", "calibrib.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Calibri.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/calibrib.ttf",
        "/Library/Fonts/Calibri.ttf",
        "/Library/Fonts/Calibri Bold.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf",
    ]

    found_font = None
    found_bold = None
    for path in calibri_paths:
        if os.path.exists(path):
            if "bold" in path.lower() or path.lower().endswith("b.ttf"):
                found_bold = path
            else:
                found_font = path

    if found_font and found_bold:
        pdfmetrics.registerFont(TTFont("Calibri", found_font))
        pdfmetrics.registerFont(TTFont("Calibri-Bold", found_bold))
        base_font, bold_font = "Calibri", "Calibri-Bold"
    else:
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
        base_font, bold_font = "DejaVuSans", "DejaVuSans-Bold"

    matplotlib.rcParams['font.family'] = base_font

    # --- Lietuviški pavadinimai ---
    LT_MONTHS = [
        "Sausis","Vasaris","Kovas","Balandis","Gegužė","Birželis",
        "Liepa","Rugpjūtis","Rugsėjis","Spalis","Lapkritis","Gruodis"
    ]
    LT_WEEKDAYS = [
        "Pirmadienis","Antradienis","Trečiadienis",
        "Ketvirtadienis","Penktadienis","Šeštadienis","Sekmadienis"
    ]

    # --- Įvedimas ---
    year = input("Įveskite metus (YYYY): ").strip()
    month = input("Įveskite mėnesį (MM): ").strip()

    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        print("Neteisingi metai arba mėnuo!")
        return

    # --- Filtruojame įrašus ---
    month_records = {}
    for date_str, status in attendance.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.year == year and date_obj.month == month:
            month_records[date_str] = status

    if not month_records:
        print(f"Nerasta įrašų {year}-{month:02d}")
        return

    total_trainings = len(month_records)
    attended = sum(1 for status in month_records.values() if status)
    attendance_rate = (attended / total_trainings * 100) if total_trainings > 0 else 0

    weekday_stats = defaultdict(lambda: {'attended': 0, 'total': 0})
    for date_str, status in month_records.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        wd_idx = date_obj.weekday()
        weekday_stats[wd_idx]['total'] += 1
        if status:
            weekday_stats[wd_idx]['attended'] += 1

    filename = f"lankomumo_ataskaita_{year}_{month:02d}.pdf"

    try:
        with open(filename, 'a'):
            pass
    except PermissionError:
        print(f"\n⚠ Klaida: {filename} šiuo metu atidarytas.")
        return

    # --- PDF kūrimas ---
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=bold_font
    )
    title = Paragraph(f"Treniruotės lankomumo ataskaita – {LT_MONTHS[month-1]} {year}", title_style)
    elements.append(title)

    name_style = ParagraphStyle(
        'RedName',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.red,
        alignment=TA_CENTER,
        fontName=bold_font,
        spaceAfter=20
    )
    elements.append(Paragraph("Rokas Šipkauskas", name_style))

    # --- Santrauka ---
    summary_data = [
        ['Rodiklis', 'Duomenys'],
        ['Viso treniruočių', str(total_trainings)],
        ['Dalyvauta', str(attended)],
        ['Praleista', str(total_trainings - attended)],
        ['Lankomumo procentas', f"{attendance_rate:.1f}%"]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cyan),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), base_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    weekday_heading_style = ParagraphStyle(
    'WeekdayHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.black,
    fontName=bold_font,
    spaceAfter=18,
    )

    # --- Pagal savaitės dienas ---
    weekday_data = [['Diena', 'Dalyvauta', 'Iš viso', 'Procentas']]
    for wd_idx in range(7):
        if wd_idx in weekday_stats:
            stats = weekday_stats[wd_idx]
            percentage = (stats['attended'] / stats['total'] * 100) if stats['total'] > 0 else 0
            weekday_data.append([LT_WEEKDAYS[wd_idx], str(stats['attended']), str(stats['total']), f"{percentage:.0f}%"])
    weekday_table = Table(weekday_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    weekday_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB366')),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), base_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(Paragraph("Lankomumas pagal savaitės dienas", weekday_heading_style))
    elements.append(Spacer(1, 0.15*inch))  # + ~11pt tarpas po antraštės
    elements.append(weekday_table)
    elements.append(Spacer(1, 0.3*inch))

    # --- Diagrama ---
    fig, ax = plt.subplots(figsize=(4, 4))
    labels = ['Dalyvauta', 'Praleista']
    sizes = [attended, total_trainings - attended]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
    img_buffer.seek(0)
    plt.close()
    pie_img = Image(img_buffer, width=2.5*inch, height=2.5*inch)

    layout_table = Table([[Paragraph("Išsamūs<br/>lankomumo įrašai",
                                     ParagraphStyle('h3', fontName=bold_font, fontSize=14)), pie_img]],
                         colWidths=[3*inch, 3*inch])
    layout_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(layout_table)
    elements.append(Spacer(1, 0.3*inch))

    # --- Išsamūs įrašai ---
    detail_data = [['Data', 'Diena', 'Būsena']]
    for date_str in sorted(month_records.keys()):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        wd_idx = date_obj.weekday()
        status = 'Buvo' if month_records[date_str] else 'Nebuvo'
        detail_data.append([date_str, LT_WEEKDAYS[wd_idx], status])
    detail_table = Table(detail_data, colWidths=[2*inch, 2*inch, 2*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), base_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    print(f"\n✓ PDF ataskaita sugeneruota: {filename}")


def view_records(attendance):
    """Parodo visus lankomumo įrašus."""
    if not attendance:
        print("\nĮrašų nerasta.")
        return
    
    print("\n=== Visi lankomumo įrašai ===")
    for date_str in sorted(attendance.keys()):
        status = "Buvo" if attendance[date_str] else "Nebuvo"
        print(f"{date_str}: {status}")
    print()

def main():
    """Pagrindinis programos ciklas."""
    print("=" * 50)
    print("Treniruotės lankomumo sekimo programa".center(50))
    print("Rokas Šipkauskas".center(50))
    print("=" * 50)
    
    attendance = load_attendance()
    
    while True:
        print("\n--- Meniu ---")
        print("1. Pridėti lankomumo įrašą")
        print("2. Peržiūrėti visus įrašus")
        print("3. Sugeneruoti PDF ataskaitą")
        print("4. Išeiti")
        
        choice = input("\nPasirinkite veiksmą (1-4): ").strip()
        
        if choice == '1':
            add_record(attendance)
        elif choice == '2':
            view_records(attendance)
        elif choice == '3':
            generate_pdf_report(attendance)
        elif choice == '4':
            print("\nViso gero!")
            break
        else:
            print("Neteisingas pasirinkimas. Bandykite dar kartą.")

if __name__ == "__main__":
    main()
