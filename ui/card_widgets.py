"""Card widget for displaying playing cards."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QSize, QRectF
from PySide6.QtGui import QFont, QColor, QPalette, QBrush, QPainter, QPen
from game.models import Card, Suit


class CardWidget(QWidget):
    """A single card display widget."""
    
    clicked = Signal(object)  # Emits the CardWidget instance
    
    def __init__(self, card: Card, parent=None):
        super().__init__(parent)
        self.card = card
        self.is_selected = False
        self.is_hovering = False
        
        self.setFixedSize(QSize(100, 140))
        self.setCursor(Qt.PointingHandCursor)
        
    def set_selected(self, selected: bool):
        """Set whether this card is selected."""
        self.is_selected = selected
        self.update()
        
    def mousePressEvent(self, event):
        """Handle click."""
        self.clicked.emit(self)
        
    def enterEvent(self, event):
        """Handle mouse enter."""
        self.is_hovering = True
        self.update()
        
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.is_hovering = False
        self.update()
        
    def paintEvent(self, event):
        """Paint the card."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw card background
        card_rect = QRectF(0, 0, self.width(), self.height())
        
        # Background color
        if self.is_selected:
            bg_color = QColor(100, 200, 255)  # Cyan for selected
        elif self.is_hovering:
            bg_color = QColor(50, 50, 80)  # Dark blue highlight
        else:
            bg_color = QColor(30, 30, 40)  # Dark background
            
        painter.fillRect(card_rect, bg_color)
        
        # Border
        border_color = QColor(200, 150, 50) if self.is_selected else QColor(100, 100, 120)
        border_width = 3 if self.is_selected else 1
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(card_rect, 8, 8)
        
        # Draw suit color indicator
        suit_color = self._get_suit_color()
        
        # Draw rank and suit
        painter.setFont(QFont("Bahnschrift", 14, QFont.Bold))
        painter.setPen(suit_color)
        
        # Rank in top-left
        painter.drawText(5, 5, 90, 30, Qt.AlignTop | Qt.AlignLeft, self.card.rank.value)
        
        # Suit symbol
        suit_symbol = self._get_suit_symbol()
        painter.setFont(QFont("Segoe UI Symbol", 20))
        painter.drawText(5, 110, 90, 30, Qt.AlignBottom | Qt.AlignLeft, suit_symbol)
        
        # Center display
        painter.setFont(QFont("Segoe UI Symbol", 32, QFont.Bold))
        painter.drawText(10, 40, 80, 60, Qt.AlignCenter, suit_symbol)
        
        painter.end()
        
    def _get_suit_color(self) -> QColor:
        """Get the color for this card's suit."""
        if self.card.suit in (Suit.HEARTS, Suit.DIAMONDS):
            return QColor(255, 100, 150)  # Rose/Red
        else:
            return QColor(100, 150, 255)  # Dark/Cyan
            
    def _get_suit_symbol(self) -> str:
        """Get the suit symbol."""
        symbols = {
            Suit.HEARTS: "♥",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
            Suit.SPADES: "♠"
        }
        return symbols.get(self.card.suit, "?")
