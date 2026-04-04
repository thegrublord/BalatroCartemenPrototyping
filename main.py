#!/usr/bin/env python3
"""Balatro Certamen - Desktop Card Game Application."""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import GameWindow


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = GameWindow()
    window.show()
    
    # Start a new game
    window.start_new_game()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
