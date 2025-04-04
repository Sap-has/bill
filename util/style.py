class StyleSheet:
    def apply_styles(self):
        """Apply stylesheet to the application for consistent styling."""
        self.setStyleSheet("""
            QWidget {
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QMainWindow {
                background-color: #f5f7fa;
            }
            
            /* Tab styling */
            QTabWidget::pane {
                border: none;
                background-color: transparent;
                border-radius: 0;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #718096;
                padding: 10px 18px;
                margin-right: 2px;
                margin-bottom: -1px;
                font-weight: bold;
                border-bottom: 3px solid transparent;
            }
            
            QTabBar::tab:selected {
                color: #3b82f6;
                border-bottom: 3px solid #3b82f6;
            }
            
            QTabBar::tab:hover:!selected {
                color: #4b5563;
                border-bottom: 3px solid #cbd5e1;
            }
            
            /* Card styling */
            #card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
            
            #photo-card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 8px;
                margin: 5px;
            }
            
            #stat-card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 15px;
                margin: 5px;
                min-height: 80px;
            }
            
            /* Form elements */
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #3b82f6;
                min-height: 25px;
            }
            
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                outline: 0;
            }
            
            #form-group {
                background-color: transparent;
                margin-bottom: 10px;
                max-width: 400px;
            }
            
            #form-label {
                color: #4b5563;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            /* Dashboard stats */
            #stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #3b82f6;
            }
            
            #card-title {
                font-size: 18px;
                font-weight: bold;
                color: #1e293b;
                margin-bottom: 15px;
            }
            
            /* Buttons styling */
            QPushButton {
                background-color: #e2e8f0;
                color: #4b5563;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #cbd5e1;
                color: #1e293b;
            }
            
            QPushButton:pressed {
                background-color: #94a3b8;
            }
            
            #primary-action {
                background-color: #3b82f6;
                color: white;
            }
            
            #primary-action:hover {
                background-color: #2563eb;
                color: white;
            }
            
            #primary-action:pressed {
                background-color: #1d4ed8;
            }
            
            #danger-button {
                background-color: #f87171;
                color: white;
            }
            
            #danger-button:hover {
                background-color: #ef4444;
            }
            
            #text-button {
                background-color: transparent;
                color: #3b82f6;
                font-weight: normal;
                border: none;
                text-decoration: underline;
                padding: 0;
                min-height: 20px;
            }
            
            #text-button:hover {
                color: #2563eb;
                background-color: transparent;
            }
            
            /* Category chips */
            #category-chip {
                background-color: #e2e8f0;
                color: #4b5563;
                border-radius: 15px;
                padding: 5px 10px;
                font-size: 12px;
                text-align: center;
                min-width: 80px;
            }
            
            #category-chip:checked {
                background-color: #3b82f6;
                color: white;
            }
            
            /* Photo preview */
            #photo-preview {
                background-color: #f1f5f9;
                border: 1px dashed #cbd5e1;
                border-radius: 4px;
            }
            
            /* Currency symbol */
            #currency-symbol {
                color: #64748b;
                font-weight: bold;
                margin-right: 0;
                padding-top: 8px;
            }
            
            /* Table styling */
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                gridline-color: #e2e8f0;
            }
            
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QTableWidget::item:selected {
                background-color: #bfdbfe;
                color: #1e293b;
            }
            
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #475569;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                font-weight: bold;
            }
            
            /* Calendar widget */
            QCalendarWidget {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            
            QCalendarWidget QToolButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px;
            }
            
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: #1e293b;
                selection-background-color: #3b82f6;
                selection-color: white;
            }
            
            /* Dropdown styling */
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                min-height: 25px;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #cbd5e1;
            }
            
            QComboBox QAbstractItemView {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                selection-background-color: #3b82f6;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f1f5f9;
                height: 8px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                min-width: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* List widget */
            QListWidget {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #bfdbfe;
                selection-color: #1e293b;
                outline: none;
            }
            
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QListWidget::item:selected {
                background-color: #bfdbfe;
                color: #1e293b;
            }
            
            QListWidget::item:hover {
                background-color: #f1f5f9;
            }
            
            /* Notification area */
            #notification-area {
                font-weight: bold;
                padding: 10px;
                margin: 0px;
            }
            
            /* Checkbox styling */
            QCheckBox {
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            
            /* Mobile responsiveness - base styles */
            @media (max-width: 800px) {
                QLineEdit, QComboBox, QPushButton {
                    min-height: 40px;  /* Larger touch targets */
                }
                
                QTableWidget::item {
                    padding: 8px;  /* More spacing for touch */
                }
            }
        """)