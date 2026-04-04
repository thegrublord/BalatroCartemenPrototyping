"""UI panels for game information display."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette
from game.models import Player, Joker, Planet


class MomentumBar(QWidget):
    """Visual momentum bar showing game progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_momentum = 0
        self.max_momentum = 10000
        self.setFixedHeight(40)
        
    def set_momentum(self, value: int):
        """Set the momentum value."""
        self.player_momentum = value
        self.update()
        
    def paintEvent(self, event):
        """Paint the momentum bar."""
        from PySide6.QtGui import QPainter, QBrush
        from PySide6.QtCore import QRect
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(20, 20, 30))
        
        # Calculate bar width
        center_x = self.width() / 2
        max_width = (self.width() / 2) - 5
        
        # Normalize momentum (-10000 to +10000)
        normalized = max(-1.0, min(1.0, self.player_momentum / self.max_momentum))
        
        # Draw player side (right)
        if normalized > 0:
            player_width = max_width * normalized
            painter.fillRect(
                int(center_x),
                0,
                int(player_width),
                self.height(),
                QColor(100, 255, 150)  # Green for player
            )
        
        # Draw AI side (left)
        if normalized < 0:
            ai_width = max_width * abs(normalized)
            painter.fillRect(
                int(center_x - ai_width),
                0,
                int(ai_width),
                self.height(),
                QColor(255, 100, 100)  # Red for AI
            )
        
        # Center line
        painter.setPen(QColor(150, 150, 150))
        painter.drawLine(int(center_x), 0, int(center_x), self.height())
        
        # Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        text = f"{self.player_momentum:+,}"
        painter.drawText(self.rect(), Qt.AlignCenter, text)
        
        painter.end()


class PlayerInfoPanel(QFrame):
    """Panel showing player information."""
    collection_requested = Signal(str, bool)  # ("jokers"|"planets", is_opponent)
    
    def __init__(self, player: Player, is_opponent: bool = False, parent=None):
        super().__init__(parent)
        self.player = player
        self.is_opponent = is_opponent
        
        # Style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            PlayerInfoPanel {
                background-color: #1a1a2e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel(player.name)
        title.setFont(QFont("Bahnschrift", 12, QFont.Bold))
        title.setStyleSheet("color: #c9a66b;")
        layout.addWidget(title)
        
        # Round score
        self.round_score_label = QLabel("Round: 0")
        self.round_score_label.setStyleSheet("color: #64ff96;")
        layout.addWidget(self.round_score_label)
        
        # Discard actions
        self.discard_label = QLabel("Discards: 0/2")
        self.discard_label.setStyleSheet("color: #00bfff;")
        layout.addWidget(self.discard_label)
        
        # Jokers section
        joker_header = QHBoxLayout()
        joker_title = QLabel("Jokers:")
        joker_title.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        joker_title.setStyleSheet("color: #ff6b6b;")
        joker_header.addWidget(joker_title)
        joker_header.addStretch()
        joker_btn = QPushButton("○")
        joker_btn.setFixedSize(22, 22)
        joker_btn.setToolTip("Open joker collection")
        joker_btn.setStyleSheet(
            "QPushButton {"
            "background-color: #2a1630; color: #ff9fb0; border: 1px solid #8c4a5e;"
            "border-radius: 11px; font-weight: bold; padding: 0px;"
            "}"
            "QPushButton:hover { background-color: #3a2044; }"
        )
        joker_btn.clicked.connect(lambda: self.collection_requested.emit("jokers", self.is_opponent))
        joker_header.addWidget(joker_btn)
        layout.addLayout(joker_header)
        
        self.joker_label = QLabel("(None)")
        self.joker_label.setStyleSheet("color: #cccccc; padding-left: 10px;")
        self.joker_label.setWordWrap(True)
        layout.addWidget(self.joker_label)
        
        # Planets section
        planet_header = QHBoxLayout()
        planet_title = QLabel("Planets:")
        planet_title.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        planet_title.setStyleSheet("color: #00d4ff;")
        planet_header.addWidget(planet_title)
        planet_header.addStretch()
        planet_btn = QPushButton("○")
        planet_btn.setFixedSize(22, 22)
        planet_btn.setToolTip("Open planet collection")
        planet_btn.setStyleSheet(
            "QPushButton {"
            "background-color: #14263f; color: #7ec7ff; border: 1px solid #2f5b89;"
            "border-radius: 11px; font-weight: bold; padding: 0px;"
            "}"
            "QPushButton:hover { background-color: #1d3559; }"
        )
        planet_btn.clicked.connect(lambda: self.collection_requested.emit("planets", self.is_opponent))
        planet_header.addWidget(planet_btn)
        layout.addLayout(planet_header)
        
        self.planet_label = QLabel("(None)")
        self.planet_label.setStyleSheet("color: #cccccc; padding-left: 10px;")
        self.planet_label.setWordWrap(True)
        layout.addWidget(self.planet_label)
        
        layout.addStretch()
        
    def update_display(self):
        """Update all information displays."""
        self.round_score_label.setText(f"Round: {self.player.round_score}")
        self.discard_label.setText(
            f"Discards: {self.player.discard_actions_used}/{self.player.discard_actions_max}"
        )
        
        # Jokers
        if self.player.jokers:
            joker_names = [str(j) for j in self.player.jokers]
            self.joker_label.setText(", ".join(joker_names))
        else:
            self.joker_label.setText("(None)")
        
        # Planets
        if self.player.planets:
            planet_counts = {}
            for p in self.player.planets:
                planet_counts[p.name] = planet_counts.get(p.name, 0) + 1
            planet_strs = [f"{name} x{count}" for name, count in planet_counts.items()]
            self.planet_label.setText(", ".join(planet_strs))
        else:
            self.planet_label.setText("(None)")


class ActionLogPanel(QFrame):
    """Panel for displaying game action log."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entry_count = 0
        self.max_history = 300
        self.header_label = None
        
        # Style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ActionLogPanel {
                background-color: #1a1a2e;
                border: 2px solid #0f3460;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Live header (shows latest event)
        header_frame = QFrame()
        header_frame.setStyleSheet(
            "background-color: #121c33; border: 1px solid #24365f; border-radius: 6px;"
        )
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)

        self.header_label = QLabel("Action Log | waiting for events")
        self.header_label.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        self.header_label.setStyleSheet("color: #c9a66b;")
        self.header_label.setWordWrap(True)
        header_layout.addWidget(self.header_label)

        # Keep this area to roughly one-third of the total panel.
        layout.addWidget(header_frame, 1)
        
        # Scroll area for log
        self.scroll = QScrollArea()
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0f1419;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #0f3460;
            }
        """)
        
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(2)
        
        self.scroll.setWidget(self.log_widget)
        self.scroll.setWidgetResizable(True)
        # Keep history area at roughly two-thirds of the total panel.
        layout.addWidget(self.scroll, 2)
        
    def add_log_entry(self, text: str):
        """Add an entry to the action log."""
        self.entry_count += 1
        label = QLabel(f"{self.entry_count:03d}. {text}")
        label.setStyleSheet(
            "color: #d6deeb; "
            "font-family: 'Segoe UI'; "
            "font-size: 10px; "
            "font-weight: 600; "
            "background-color: #121c33; "
            "border: 1px solid #24365f; "
            "border-radius: 4px; "
            "padding: 4px 6px;"
        )
        label.setWordWrap(True)
        self.log_layout.insertWidget(0, label)

        # Keep the top header informative and event-driven.
        self.header_label.setText(f"Latest Event: {self.entry_count:03d}. {text}")
        
        # Keep deep history available through scrolling.
        while self.log_layout.count() > self.max_history:
            item = self.log_layout.takeAt(self.log_layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()
