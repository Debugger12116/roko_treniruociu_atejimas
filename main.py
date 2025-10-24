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
    
    status = input("Was Vardenis Pavardenis present? (yes/no): ").strip().lower()
    
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
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    title = Paragraph(f"Training Attendance Report<br/>{calendar.month_name[month]} {year}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Person name
    name_style = ParagraphStyle('CustomName', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#34495E'), alignment=TA_CENTER)
    name = Paragraph("Vardenis Pavardenis", name_style)
    elements.append(name)
    elements.append(Spacer(1, 0.4*inch))
    
    # Summary statistics
    summary_data = [
        ['Metric', 'Value'],
        ['Total Trainings', str(total_trainings)],
        ['Attended', str(attended)],
        ['Missed', str(total_trainings - attended)],
        ['Attendance Rate', f"{attendance_rate:.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Weekday statistics
    elements.append(Paragraph("Attendance by Weekday", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    weekday_data = [['Weekday', 'Attended', 'Total', 'Percentage']]
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        if day in weekday_stats:
            stats = weekday_stats[day]
            percentage = (stats['attended'] / stats['total'] * 100) if stats['total'] > 0 else 0
            weekday_data.append([day, str(stats['attended']), str(stats['total']), f"{percentage:.1f}%"])
    
    if len(weekday_data) > 1:
        weekday_table = Table(weekday_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        weekday_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(weekday_table)
        elements.append(Spacer(1, 0.4*inch))
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ['Attended', 'Missed']
    sizes = [attended, total_trainings - attended]
    colors_pie = ['#2ECC71', '#E74C3C']
    explode = (0.1, 0)
    
    ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='%1.1f%%',
           shadow=True, startangle=90)
    ax.axis('equal')
    plt.title('Attendance Distribution', fontsize=14, fontweight='bold')
    
    # Save chart to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
    img_buffer.seek(0)
    plt.close()
    
    # Add chart to PDF
    img = Image(img_buffer, width=4*inch, height=2.67*inch)
    elements.append(img)
    elements.append(Spacer(1, 0.4*inch))
    
    # Detailed attendance list
    elements.append(Paragraph("Detailed Attendance Records", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    detail_data = [['Date', 'Day', 'Status']]
    for date_str in sorted(month_records.keys()):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = calendar.day_name[date_obj.weekday()]
        status = '✓ Present' if month_records[date_str] else '✗ Absent'
        detail_data.append([date_str, weekday, status])
    
    detail_table = Table(detail_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
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
    print("Vardenis Pavardenis".center(50))
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