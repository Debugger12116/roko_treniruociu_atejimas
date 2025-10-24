import os
from datetime import datetime
from collections import defaultdict
import calendar

def load_attendance(filename="attendance.txt"):
    """Load attendance records from file."""
    attendance = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    date, status = line.split(',')
                    attendance[date] = status.lower() == 'yes'
    return attendance

def save_attendance(attendance, filename="attendance.txt"):
    """Save attendance records to file."""
    with open(filename, 'w') as f:
        for date, status in sorted(attendance.items()):
            f.write(f"{date},{'yes' if status else 'no'}\n")

def add_record(attendance):
    """Add a new attendance record."""
    date_str = input("Enter date (YYYY-MM-DD): ").strip()
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format! Please use YYYY-MM-DD")
        return
    
    status = input("Was Rokas Šipkauskas present? (yes/no): ").strip().lower()
    
    if status not in ['yes', 'no']:
        print("Please enter 'yes' or 'no'")
        return
    
    attendance[date_str] = (status == 'yes')
    save_attendance(attendance)
    print(f"✓ Record added for {date_str}")

def generate_pdf_report(attendance):
    """Generate a PDF report for a specific month and year."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        import matplotlib.pyplot as plt
        import io
    except ImportError:
        print("\n⚠ Missing required libraries!")
        print("Please install: pip install reportlab matplotlib")
        return
    
    year = input("Enter year (YYYY): ").strip()
    month = input("Enter month (MM): ").strip()
    
    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        print("Invalid year or month!")
        return
    
    # Filter records for the selected month
    month_records = {}
    for date_str, status in attendance.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.year == year and date_obj.month == month:
            month_records[date_str] = status
    
    if not month_records:
        print(f"No records found for {year}-{month:02d}")
        return
    
    # Calculate statistics
    total_trainings = len(month_records)
    attended = sum(1 for status in month_records.values() if status)
    attendance_rate = (attended / total_trainings * 100) if total_trainings > 0 else 0
    
    # Calculate weekday statistics
    weekday_stats = defaultdict(lambda: {'attended': 0, 'total': 0})
    for date_str, status in month_records.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = calendar.day_name[date_obj.weekday()]
        weekday_stats[weekday]['total'] += 1
        if status:
            weekday_stats[weekday]['attended'] += 1
    
    # Create PDF
    filename = f"attendance_report_{year}_{month:02d}.pdf"
    
    # Check if file is open
    try:
        with open(filename, 'a'):
            pass
    except PermissionError:
        print(f"\n⚠ Error: {filename} is currently open in another program.")
        print("Please close the file and try again.")
        return
    
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    title = Paragraph(f"Training Attendance Report – {calendar.month_name[month]} {year}", title_style)
    elements.append(title)
    
    # Person name in red
    name_style = ParagraphStyle(
        'RedName',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.red,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=20
    )
    name = Paragraph("Rokas Šipkauskas", name_style)
    elements.append(name)
    
    # Summary statistics table - cyan header
    summary_data = [
        ['Metric', 'Data'],
        ['Total Trainings', str(total_trainings)],
        ['Attended', str(attended)],
        ['Missed', str(total_trainings - attended)],
        ['Attendance Rate', f"{attendance_rate:.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cyan),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Attendance by Weekday heading
    weekday_heading_style = ParagraphStyle(
        'WeekdayHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        spaceAfter=10
    )
    elements.append(Paragraph("Attendance by Weekday", weekday_heading_style))
    
    # Weekday statistics table - orange header
    weekday_data = [['Weekday', 'Attended', 'Total', 'Rate']]
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        if day in weekday_stats:
            stats = weekday_stats[day]
            percentage = (stats['attended'] / stats['total'] * 100) if stats['total'] > 0 else 0
            weekday_data.append([day, str(stats['attended']), str(stats['total']), f"{percentage:.0f}%"])
    
    if len(weekday_data) > 1:
        weekday_table = Table(weekday_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        weekday_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB366')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(weekday_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Create two-column layout for "Detailed Attendance Records" heading and pie chart
    from reportlab.platypus import KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    
    # Detailed heading
    detail_heading_style = ParagraphStyle(
        'DetailHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        spaceAfter=10
    )
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(4, 4))
    labels = ['Attended', 'Missed']
    sizes = [attended, total_trainings - attended]
    colors_pie = ['#4A90A4', '#E74C3C']
    
    ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
           shadow=False, startangle=90, textprops={'fontsize': 10})
    ax.axis('equal')
    
    # Save chart to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
    img_buffer.seek(0)
    plt.close()
    
    # Create a table to place heading and pie chart side by side
    pie_img = Image(img_buffer, width=2.5*inch, height=2.5*inch)
    
    heading_cell = Paragraph("Detailed Attendance<br/>Records", detail_heading_style)
    
    layout_table = Table([[heading_cell, pie_img]], colWidths=[3*inch, 3*inch])
    layout_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(layout_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed Attendance Records heading
    elements.append(Paragraph("Detailed Attendance Records", detail_heading_style))
    
    # Detailed attendance list - green header
    detail_data = [['Date', 'Day', 'Status']]
    for date_str in sorted(month_records.keys()):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = calendar.day_name[date_obj.weekday()]
        status = 'Present' if month_records[date_str] else 'Absent'
        detail_data.append([date_str, weekday, status])
    
    detail_table = Table(detail_data, colWidths=[2*inch, 2*inch, 2*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(detail_table)
    
    # Build PDF
    doc.build(elements)
    print(f"\n✓ PDF report generated: {filename}")

def view_records(attendance):
    """View all attendance records."""
    if not attendance:
        print("\nNo records found.")
        return
    
    print("\n=== All Attendance Records ===")
    for date_str in sorted(attendance.keys()):
        status = "Present" if attendance[date_str] else "Absent"
        print(f"{date_str}: {status}")
    print()

def main():
    """Main application loop."""
    print("=" * 50)
    print("Training Attendance Tracker".center(50))
    print("Rokas Šipkauskas".center(50))
    print("=" * 50)
    
    attendance = load_attendance()
    
    while True:
        print("\n--- Menu ---")
        print("1. Add attendance record")
        print("2. View all records")
        print("3. Generate PDF report")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            add_record(attendance)
        elif choice == '2':
            view_records(attendance)
        elif choice == '3':
            generate_pdf_report(attendance)
        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()