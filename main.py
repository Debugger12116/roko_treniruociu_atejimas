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
    """Registruoja PDF šriftus (Calibri -> DejaVuSans -> Helvetica)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        ("Calibri", "calibri.ttf"),
        ("Calibri-Bold", "calibrib.ttf"),
        ("Calibri", "C:\\Windows\\Fonts\\calibri.ttf"),
        ("Calibri-Bold", "C:\\Windows\\Fonts\\calibrib.ttf"),
        ("Calibri", "/Library/Fonts/Calibri.ttf"),
        ("Calibri-Bold", "/Library/Fonts/Calibri Bold.ttf"),
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    found = {}
    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                found[name] = True
            except Exception:
                pass

    base = "Calibri" if "Calibri" in found else ("DejaVuSans" if "DejaVuSans" in found else "Helvetica")
    bold = "Calibri-Bold" if "Calibri-Bold" in found else ("DejaVuSans-Bold" if "DejaVuSans-Bold" in found else "Helvetica-Bold")
    return base, bold


# ==== DUOMENYS ====

def load_attendance(filename="attendance.txt"):
    """Įkelia lankomumo įrašus.
       Formatai:
       - YYYY-MM-DD,taip|ne
       - YYYY-MM-DD,tipas,taip|ne
       (senas 'varzybos' → konvertuojamas į 'rungtynes')
    """
    attendance = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                try:
                    if len(parts) == 2:
                        date, status = parts
                        typ = 'treniruote'
                    else:
                        date, typ, status = parts
                        typ = typ.lower()
                        if typ in ('varzybos', 'varžybos'):
                            typ = 'rungtynes'
                        if typ not in ('treniruote', 'rungtynes'):
                            typ = 'treniruote'
                    attendance[date] = {'present': status.lower() == 'taip', 'type': typ}
                except Exception:
                    continue
    return attendance


def save_attendance(attendance, filename="attendance.txt"):
    """Išsaugo nauju formatu: data,tipas,taip|ne."""
    with open(filename, 'w', encoding='utf-8') as f:
        for date, rec in sorted(attendance.items()):
            status = 'taip' if rec['present'] else 'ne'
            typ = rec.get('type', 'treniruote')
            f.write(f"{date},{typ},{status}\n")


def add_record(attendance):
    """Prideda naują lankomumo įrašą."""
    date_str = input("Įveskite datą (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Neteisingas datos formatas! Naudokite YYYY-MM-DD")
        return

    typ = input("Koks tipas? (t=treniruotė, r=rungtynės): ").strip().lower()
    if typ in ('t', 'treniruote', 'treniruotė'):
        typ = 'treniruote'
    elif typ in ('r', 'rungtynes', 'rungtynės', 'varzybos', 'varžybos'):
        typ = 'rungtynes'
    else:
        print("Neteisingas tipas. Įveskite 't' arba 'r'.")
        return

    status = input("Ar Rokas Šipkauskas dalyvavo? (taip/ne): ").strip().lower()
    if status not in ['taip', 'ne']:
        print("Prašome įvesti 'taip' arba 'ne'")
        return

    attendance[date_str] = {'present': (status == 'taip'), 'type': typ}
    save_attendance(attendance)
    print(f"✓ Įrašas pridėtas {date_str} ({'Treniruotė' if typ=='treniruote' else 'Rungtynės'})")


# ==== PDF ====

def generate_pdf_report(attendance):
    """Sugeneruoja PDF ataskaitą konkrečiam mėnesiui ir metams (atskirai treniruotėms ir rungtynėms)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        import matplotlib.pyplot as plt
        import matplotlib
        import io
    except ImportError:
        print("\n⚠ Trūksta reikalingų bibliotekų!")
        print("Įdiekite: pip install reportlab matplotlib")
        return

    base_font, bold_font = register_pdf_fonts()
    matplotlib.rcParams['font.family'] = base_font

    # Įvedimas
    year = input("Įveskite metus (YYYY): ").strip()
    month = input("Įveskite mėnesį (MM): ").strip()
    try:
        year = int(year)
        month = int(month)
        if not 1 <= month <= 12:
            raise ValueError
    except ValueError:
        print("Neteisingi metai arba mėnuo!")
        return

    # Filtruojame įrašus pasirinktai datai
    month_records = {}
    for date_str, rec in attendance.items():
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if date_obj.year == year and date_obj.month == month:
            month_records[date_str] = rec

    if not month_records:
        print(f"Nerasta įrašų {year}-{month:02d}")
        return

    # Skirstom į tipus
    def filter_by_type(t):
        return {d: r for d, r in month_records.items() if r.get('type') == t}

    rec_train = filter_by_type('treniruote')
    rec_match = filter_by_type('rungtynes')

    def compute_stats(records):
        total = len(records)
        attended = sum(1 for r in records.values() if r['present'])
        rate = (attended / total * 100) if total else 0
        wd = defaultdict(lambda: {'attended': 0, 'total': 0})
        for date_str, r in records.items():
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            idx = dt.weekday()
            wd[idx]['total'] += 1
            if r['present']:
                wd[idx]['attended'] += 1
        return total, attended, rate, wd

    t_total, t_att, t_rate, t_wd = compute_stats(rec_train)
    m_total, m_att, m_rate, m_wd = compute_stats(rec_match)

    # PDF paruošimas
    filename = f"lankomumo_ataskaita_{year}_{month:02d}.pdf"
    try:
        with open(filename, 'a'):
            pass
    except PermissionError:
        print(f"\n⚠ Klaida: {filename} šiuo metu atidarytas.")
        return

    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()

    # Pavadinimas ir informacija po vardu
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                 alignment=TA_CENTER, fontName=bold_font, spaceAfter=8)
    elements.append(Paragraph(f"Treniruotės lankomumo ataskaita – {LT_MONTHS[month-1]} {year}", title_style))
    elements.append(Paragraph("Rokas Šipkauskas",
                              ParagraphStyle('name', parent=styles['Heading2'], fontName=bold_font,
                                             fontSize=14, textColor=colors.red, alignment=TA_CENTER, spaceAfter=4)))
    elements.append(Paragraph(
        "*lankomumas pradėtas skaičiuoti nuo spalio 6 dienos",
        ParagraphStyle('note', fontName=base_font, fontSize=10, alignment=TA_CENTER, spaceAfter=16, textColor=colors.black)
    ))

    # --- Treniruotės ir Rungtynės (be žodžio „Santrauka“) ---
    def summary_table(title_text, total, att, rate):
        data = [
            ['Rodiklis', 'Duomenys'],
            ['Įvykių skaičius', str(total)],
            ['Dalyvauta', str(att)],
            ['Praleista', str(max(0, total - att))],
            ['Lankomumo procentas', f"{rate:.1f}%"]
        ]
        tbl = Table(data, colWidths=[3*inch, 2.5*inch])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.cyan),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), base_font),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(Paragraph(title_text, ParagraphStyle('h2', fontName=bold_font, fontSize=15, spaceAfter=8)))
        elements.append(tbl)
        elements.append(Spacer(1, 0.25*inch))

    summary_table("Treniruotės", t_total, t_att, t_rate)
    summary_table("Rungtynės",   m_total, m_att, m_rate)

    # --- Lentelės pagal savaitės dienas ---
    def weekday_table(title_text, wd_stats):
        elements.append(Paragraph(title_text,
            ParagraphStyle('WeekdayHeading', parent=styles['Heading2'],
                           fontSize=14, fontName=bold_font, spaceAfter=10)))
        data = [['Diena', 'Dalyvauta', 'Iš viso', 'Procentas']]
        for i in range(7):
            stats = wd_stats.get(i, {'attended': 0, 'total': 0})
            pct = (stats['attended'] / stats['total'] * 100) if stats['total'] else 0
            data.append([LT_WEEKDAYS[i], str(stats['attended']), str(stats['total']), f"{pct:.0f}%"])
        tbl = Table(data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB366')),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), base_font),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(tbl)
        elements.append(Spacer(1, 0.3*inch))

    weekday_table("Lankomumas pagal savaitės dienas – Treniruotės", t_wd)
    weekday_table("Lankomumas pagal savaitės dienas – Rungtynės",   m_wd)

    # --- Diagramos ---
    def pie(attended, total):
        fig, ax = plt.subplots(figsize=(3.5, 3.5))
        labels = ['Dalyvauta', 'Praleista']
        sizes = [attended, max(0, total - attended)]
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=110)
        buf.seek(0)
        plt.close()
        return Image(buf, width=2.6*inch, height=2.6*inch)

    caption_style = ParagraphStyle('cap', alignment=TA_CENTER, fontName=bold_font, fontSize=12, spaceAfter=6)
    headers_row = [Paragraph("Treniruotės", caption_style), Paragraph("Rungtynės", caption_style)]
    images_row = [pie(t_att, t_total), pie(m_att, m_total)]
    elements.append(Paragraph("Diagramos", ParagraphStyle('h2b', fontName=bold_font, fontSize=15, spaceAfter=10)))
    elements.append(Table([headers_row, images_row], colWidths=[3*inch, 3*inch],
                          style=TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')])))

    elements.append(Spacer(1, 0.35*inch))

    # --- Išsamūs įrašai ---
    elements.append(Paragraph("Išsamūs lankomumo įrašai",
                              ParagraphStyle('DetailHeading', parent=styles['Heading2'],
                                             fontSize=14, fontName=bold_font, spaceAfter=8)))
    detail_data = [['Data', 'Diena', 'Tipas', 'Būsena']]
    for date_str in sorted(month_records.keys()):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        wd = LT_WEEKDAYS[dt.weekday()]
        typ = month_records[date_str].get('type', 'treniruote')
        typ_lt = 'Treniruotė' if typ == 'treniruote' else 'Rungtynės'
        status = 'Buvo' if month_records[date_str]['present'] else 'Nebuvo'
        detail_data.append([date_str, wd, typ_lt, status])

    detail_table = Table(detail_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), base_font),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    print(f"\n✓ PDF ataskaita sugeneruota: {filename}")


# ==== PERŽIŪRA & UI ====

def view_records(attendance):
    """Parodo visus lankomumo įrašus."""
    if not attendance:
        print("\nĮrašų nerasta.")
        return

    print("\n=== Visi lankomumo įrašai ===")
    for date_str in sorted(attendance.keys()):
        rec = attendance[date_str]
        status = "Buvo" if rec['present'] else "Nebuvo"
        typ = "Treniruotė" if rec.get('type') == 'treniruote' else "Rungtynės"
        print(f"{date_str}: {typ} – {status}")
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
