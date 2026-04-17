import sys
import os
import re
import csv
import PyPDF2
from fpdf import FPDF
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                             QFileDialog, QSlider, QMessageBox, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor
from PyQt6.QtCharts import QChart, QChartView, QPieSeries

class ATSFriendlyPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(44, 62, 80)
        self.cell(0, 10, 'AI-OPTIMIZED CANDIDATE PROFILE', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(127, 140, 141)
        self.cell(0, 5, 'Auto-generated ATS-Friendly Format', 0, 1, 'C')
        self.line(10, 28, 200, 28)
        self.ln(10)

class ResumeScreeningApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Resume Screening Pro - Enterprise Dashboard")
        self.setGeometry(50, 50, 1300, 800)
        self.uploaded_files = []
        self.processed_results = []
        self.stats = {"Passed": 0, "Modified": 0}
        
        self.init_ui()
        self.apply_dark_gradient_theme()

    def apply_dark_gradient_theme(self):
        self.setStyleSheet("""
            QWidget#CentralWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #0B0F19, stop:1 #1A2639);
            }
            QLabel { color: #E2E8F0; }
            QTextEdit { 
                background-color: rgba(15, 23, 42, 0.7); 
                border: 1px solid #38BDF8; 
                border-radius: 8px; 
                padding: 12px;
                color: #F8FAFC;
                font-size: 13px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: white; border-radius: 6px; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #1D4ED8; border: 1px solid #60A5FA; }
            QPushButton#ActionBtn { background: #10B981; }
            QPushButton#ActionBtn:hover { background: #059669; }
            QPushButton:disabled { background: #334155; color: #94A3B8; }
            QProgressBar {
                border: 1px solid #475569; border-radius: 6px; text-align: center;
                background-color: #1E293B; color: #F8FAFC; font-weight: bold;
            }
            QProgressBar::chunk { background: #38BDF8; border-radius: 5px; }
            QTableWidget {
                background-color: rgba(15, 23, 42, 0.8); border: 1px solid #334155;
                gridline-color: #334155; color: #E2E8F0; border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #0F172A; padding: 6px; border: 1px solid #334155;
                font-weight: bold; color: #38BDF8;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # === LEFT PANEL ===
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)
        
        title = QLabel("⚙️ Enterprise Screening Engine")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #38BDF8;")
        left_panel.addWidget(title)

        left_panel.addWidget(QLabel("📝 Target Job Description (JD):"))
        self.jd_input = QTextEdit()
        self.jd_input.setPlaceholderText("Enter required skills, tools, and qualifications...")
        left_panel.addWidget(self.jd_input)

        self.threshold_label = QLabel("🎚️ Minimum Match Threshold: 50%")
        left_panel.addWidget(self.threshold_label)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.update_slider_label)
        left_panel.addWidget(self.slider)

        self.upload_btn = QPushButton("📁 Upload Resumes (PDF)")
        self.upload_btn.clicked.connect(self.upload_files)
        left_panel.addWidget(self.upload_btn)

        self.file_count_label = QLabel("0 files loaded ready for processing.")
        self.file_count_label.setStyleSheet("color: #94A3B8; font-style: italic;")
        left_panel.addWidget(self.file_count_label)

        self.analyze_btn = QPushButton("🚀 Run AI Analysis & Auto-Fix")
        self.analyze_btn.setObjectName("ActionBtn")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False) 
        left_panel.addWidget(self.analyze_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        left_panel.addWidget(self.progress_bar)

        self.status_label = QLabel("System Idle.")
        left_panel.addWidget(self.status_label)

        # === RIGHT PANEL (Dashboard) ===
        self.right_panel = QFrame()
        right_layout = QVBoxLayout(self.right_panel)
        
        # Dashboard Header with Buttons
        header_layout = QHBoxLayout()
        results_title = QLabel("📊 Visual Analytics & Reports")
        results_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(results_title)

        self.export_csv_btn = QPushButton("💾 Export CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(self.export_csv_btn)

        self.export_pdf_btn = QPushButton("📄 Download Full Report")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        self.export_pdf_btn.setObjectName("ActionBtn")
        header_layout.addWidget(self.export_pdf_btn)
        
        right_layout.addLayout(header_layout)

        # Chart Area
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(250)
        self.chart_view.setStyleSheet("background: transparent;")
        right_layout.addWidget(self.chart_view)

        # Data Table
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(["Candidate File", "Match %", "Status", "System Action"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.results_table)

        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.right_panel, 2)

        # Animations
        self.right_panel.setMaximumWidth(0)
        self.opacity_effect = QGraphicsOpacityEffect()
        self.right_panel.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.slide_anim = QPropertyAnimation(self.right_panel, b"maximumWidth")
        self.slide_anim.setDuration(1000)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutElastic) 

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(1200)

    def update_slider_label(self, value):
        self.threshold_label.setText(f"🎚️ Minimum Match Threshold: {value}%")

    def upload_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Select Resumes", "", "PDF Files (*.pdf)")
        if filenames:
            self.uploaded_files = filenames
            self.file_count_label.setText(f"{len(self.uploaded_files)} PDF(s) loaded.")
            self.analyze_btn.setEnabled(True)

    def start_analysis(self):
        if not self.jd_input.toPlainText().strip():
            QMessageBox.warning(self, "Input Error", "Please enter a Job Description.")
            return

        self.analyze_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        self.right_panel.setMaximumWidth(0) 
        self.opacity_effect.setOpacity(0.0)
        self.progress_bar.setValue(0)
        self.stats = {"Passed": 0, "Modified": 0}
        self.processed_results.clear()
        self.current_file_idx = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_next_resume)
        self.timer.start(250) 

    def extract_text(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except: pass
        return text

    def calculate_match(self, resume_text, jd_text):
        jd_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', jd_text.lower()))
        res_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', resume_text.lower()))
        if not jd_words: return 0, set()
        
        matches = jd_words.intersection(res_words)
        missing = jd_words - res_words 
        score = (len(matches) / len(jd_words)) * 100
        return min(int(score * 1.5), 99), missing 

    def create_ats_resume(self, filename, original_text, missing_words):
        output_dir = "Optimized_Resumes"
        os.makedirs(output_dir, exist_ok=True)
        
        # Strictly encode text to prevent FPDF crashes
        clean_text = original_text.encode('latin-1', 'replace').decode('latin-1')
        
        pdf = ATSFriendlyPDF()
        pdf.add_page()
        
        # --- SECTION: INJECTED SKILLS ---
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(41, 128, 185) # Blue
        pdf.cell(0, 10, "CORE COMPETENCIES & AI-INJECTED SKILLS", 0, 1)
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        
        # REPLACED unicode bullet "•" with standard ASCII hyphen "-"
        skills_list = list(missing_words)[:20]
        skills_str = " - ".join(skills_list).title()
        
        pdf.multi_cell(0, 6, txt=f"System added missing JD keywords to pass ATS filters:\n{skills_str}")
        pdf.ln(5)

        # --- SECTION: ORIGINAL CONTENT ---
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 10, "PROFESSIONAL EXPERIENCE & EDUCATION", 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        
        pdf.multi_cell(0, 5, txt=clean_text)
        
        save_path = os.path.join(output_dir, f"ATS_Optimized_{filename}")
        pdf.output(save_path)
        return f"Added {len(skills_list)} skills & Reformatted"

    def process_next_resume(self):
        if self.current_file_idx < len(self.uploaded_files):
            file_path = self.uploaded_files[self.current_file_idx]
            filename = os.path.basename(file_path)
            
            self.status_label.setText(f"Analyzing & Modifying: {filename}...")
            
            jd_text = self.jd_input.toPlainText()
            resume_text = self.extract_text(file_path)
            score, missing_words = self.calculate_match(resume_text, jd_text)
            
            if score >= self.slider.value():
                status = "🟢 Passed"
                action = "None needed"
                self.stats["Passed"] += 1
            else:
                status = "🟡 AI Modified"
                action = self.create_ats_resume(filename, resume_text, missing_words)
                self.stats["Modified"] += 1

            self.processed_results.append((filename, f"{score}%", status, action))
            
            self.current_file_idx += 1
            self.progress_bar.setValue(int((self.current_file_idx / len(self.uploaded_files)) * 100))
        else:
            self.timer.stop()
            self.status_label.setText("Done! Check 'Optimized_Resumes' folder.")
            self.update_chart()
            self.show_results()

    def update_chart(self):
        series = QPieSeries()
        
        slice_pass = series.append("Passed", self.stats["Passed"])
        slice_pass.setBrush(QColor("#10B981")) # Green
        
        slice_mod = series.append("AI Modified", self.stats["Modified"])
        slice_mod.setBrush(QColor("#F59E0B")) # Orange
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Screening Outcomes")
        chart.setTitleFont(QFont("Arial", 14, QFont.Weight.Bold))
        chart.setTitleBrush(QColor("#E2E8F0"))
        chart.setBackgroundBrush(QColor("transparent"))
        chart.legend().setLabelBrush(QColor("#E2E8F0"))
        
        self.chart_view.setChart(chart)

    def show_results(self):
        self.processed_results.sort(key=lambda x: int(x[1].replace('%', '')), reverse=True)
        self.results_table.setRowCount(len(self.processed_results))
        for r_idx, row in enumerate(self.processed_results):
            for c_idx, item in enumerate(row):
                table_item = QTableWidgetItem(item)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(r_idx, c_idx, table_item)

        self.slide_anim.setStartValue(0)
        self.slide_anim.setEndValue(800)
        self.slide_anim.start()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        self.analyze_btn.setEnabled(True)

    def export_to_csv(self):
        if not self.processed_results: return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "HR_Report.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Candidate", "Match", "Status", "Action"])
                writer.writerows(self.processed_results)
            QMessageBox.information(self, "Success", "CSV Exported!")

    def export_to_pdf(self):
        if not self.processed_results: return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "Batch_Report.pdf", "PDF (*.pdf)")
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "HR Batch Screening Report", 0, 1, 'C')
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(60, 10, "Candidate", 1)
            pdf.cell(30, 10, "Match %", 1)
            pdf.cell(40, 10, "Status", 1)
            pdf.cell(60, 10, "Action Taken", 1, 1)
            
            pdf.set_font("Arial", '', 10)
            for row in self.processed_results:
                # Replace unsupported characters for the batch report as well
                clean_filename = row[0][:20].encode('latin-1', 'replace').decode('latin-1')
                clean_action = row[3][:30].encode('latin-1', 'replace').decode('latin-1')
                
                pdf.cell(60, 10, clean_filename, 1)
                pdf.cell(30, 10, row[1], 1)
                pdf.cell(40, 10, row[2], 1)
                pdf.cell(60, 10, clean_action, 1, 1)
            pdf.output(path)
            QMessageBox.information(self, "Success", "PDF Report Exported!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = ResumeScreeningApp()
    window.show()
    sys.exit(app.exec())