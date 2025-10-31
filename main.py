import os
import subprocess
from datetime import datetime
from collections import defaultdict

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
    """Įkelia lankomumo įrašus."""
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
    """Sugeneruoja paprastą PDF ataskaitą (testinė versija)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    base_font, bold_font = register_pdf_fonts()
    filename = f"lankomumo_ataskaita_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                 alignment=TA_CENTER, fontName=bold_font)
    elements.append(Paragraph("Treniruočių lankomumo ataskaita", title_style))
    elements.append(Spacer(1, 0.3*inch))
    data = [['Data', 'Tipas', 'Būsena']]
    for d, rec in sorted(attendance.items()):
        data.append([d, rec['type'], 'Buvo' if rec['present'] else 'Nebuvo'])
    tbl = Table(data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
    ]))
    elements.append(tbl)
    doc.build(elements)
    print(f"✓ PDF ataskaita sugeneruota: {filename}")
    return filename


# ==== GIT UPLOAD ====

def git_push():
    """Automatiškai atlieka git add, commit ir push."""
    try:
        # Patikrinam, ar esame git repozitorijoje
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("\n➡️  Vykdomas automatinis commit ir push į GitHub...")

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Automatinis įkėlimas"], check=False)
        subprocess.run(["git", "push"], check=True)

        print("✅ Failai sėkmingai įkelti į GitHub!")
    except subprocess.CalledProcessError as e:
        print("❌ Nepavyko įkelti į GitHub.")
        print("Patikrink, ar esi prisijungęs ir ar sukonfigūruotas remote 'origin'.")
    except FileNotFoundError:
        print("❌ Git neįdiegtas arba neprieinamas PATH.")


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
    last_pdf = None  # kad prisimintume paskutinį PDF failą

    while True:
        print("\n--- Meniu ---")
        print("1. Pridėti lankomumo įrašą")
        print("2. Peržiūrėti visus įrašus")
        print("3. Sugeneruoti PDF ataskaitą")
        print("4. Išeiti")
        print("5. Įkelti projektą į GitHub (commit + push)")

        choice = input("\nPasirinkite veiksmą (1-5): ").strip()

        if choice == '1':
            add_record(attendance)
        elif choice == '2':
            view_records(attendance)
        elif choice == '3':
            last_pdf = generate_pdf_report(attendance)
        elif choice == '4':
            print("\nViso gero!")
            break
        elif choice == '5':
            git_push()
        else:
            print("Neteisingas pasirinkimas. Bandykite dar kartą.")


if __name__ == "__main__":
    main()
