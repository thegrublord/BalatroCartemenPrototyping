"""Main game window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QGridLayout, QMessageBox, QScrollArea,
    QSpinBox, QInputDialog, QDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap
from typing import List, Optional
from pathlib import Path
from collections import Counter

from game import (
    GameState, GamePhase, PokerHandEvaluator, ScoringRules, AIPlayer, Card,
    JokerType, Planet, HandRank, PokerHand
)
from ui.card_widgets import CardWidget
from ui.panels import MomentumBar, PlayerInfoPanel, ActionLogPanel


class GameWindow(QMainWindow):
    """Main game window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Balatro Certamen")
        self.setGeometry(100, 100, 1600, 900)

        # Game state
        self.game_state = GameState()
        self.ai = AIPlayer(self.game_state.ai)

        # Exchange data - track played cards during a set
        self.player_played_cards: Optional[List[Card]] = None
        self.ai_played_cards: Optional[List[Card]] = None

        # Selected cards for playing hand
        self.selected_cards: List[Card] = []
        self.selected_card_widgets: List[CardWidget] = []

        # Current card widgets
        self.hand_widgets: List[CardWidget] = []
        self.hand_section_label: Optional[QLabel] = None
        self.hand_buttons_widget: Optional[QWidget] = None
        self.hand_preview_label: Optional[QLabel] = None
        self.played_frame: Optional[QFrame] = None
        self.auction_board_frame: Optional[QFrame] = None
        self.auction_board_grid: Optional[QGridLayout] = None
        self.auction_cards_container: Optional[QWidget] = None
        self.auction_turn_info_label: Optional[QLabel] = None
        self.auction_end_turn_btn: Optional[QPushButton] = None

        # Auction controls
        self.auction_card_label: Optional[QLabel] = None
        self.auction_bid_label: Optional[QLabel] = None
        self.auction_turn_label: Optional[QLabel] = None
        self.auction_spent_label: Optional[QLabel] = None
        self.auction_min_raise_btn: Optional[QPushButton] = None
        self.auction_custom_bid_btn: Optional[QPushButton] = None
        self.auction_pass_btn: Optional[QPushButton] = None
        self.auction_custom_bid_input: Optional[QSpinBox] = None
        self.auction_frame: Optional[QFrame] = None

        # Center status widgets
        self.title_label: Optional[QLabel] = None
        self.round_set_label: Optional[QLabel] = None
        self.player_points_value: Optional[QLabel] = None
        self.ai_points_value: Optional[QLabel] = None
        self.player_discards_value: Optional[QLabel] = None
        self.ai_discards_value: Optional[QLabel] = None

        # Left-panel auction preview
        self.auction_preview_image: Optional[QLabel] = None
        self.auction_preview_title: Optional[QLabel] = None
        self.auction_preview_description: Optional[QLabel] = None

        # Keep dialog refs so windows remain open.
        self.collection_windows: List[QDialog] = []

        # AI action timer
        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self._perform_ai_action)

        # Setup UI
        self._setup_ui()

        # Apply stylesheet
        self._apply_stylesheet()

    def _setup_ui(self):
        """Set up the user interface."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left sidebar
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # Center area
        center_widget = self._create_center_area()
        main_layout.addWidget(center_widget, 1)

        # Right sidebar
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel)

    def _create_left_panel(self) -> QWidget:
        """Create left sidebar with momentum and status."""
        panel = QFrame()
        panel.setFixedWidth(250)
        layout = QVBoxLayout(panel)

        # Momentum bar
        momentum_label = QLabel("MOMENTUM")
        momentum_label.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        momentum_label.setStyleSheet("color: #c9a66b;")
        layout.addWidget(momentum_label)

        self.momentum_bar = MomentumBar()
        layout.addWidget(self.momentum_bar)

        # Status
        status_label = QLabel("STATUS")
        status_label.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        status_label.setStyleSheet("color: #c9a66b;")
        layout.addWidget(status_label)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #64ff96;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Player info
        self.player_info = PlayerInfoPanel(self.game_state.player, is_opponent=False)
        self.player_info.collection_requested.connect(self._open_collection_from_panel)
        layout.addWidget(self.player_info)

        # Auction card preview (lower-left)
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)

        preview_header = QLabel("CURRENT AUCTION CARD")
        preview_header.setFont(QFont("Bahnschrift", 10, QFont.Bold))
        preview_header.setStyleSheet("color: #c9a66b;")
        preview_layout.addWidget(preview_header)

        self.auction_preview_image = QLabel("No Card")
        self.auction_preview_image.setAlignment(Qt.AlignCenter)
        self.auction_preview_image.setFixedHeight(140)
        self.auction_preview_image.setStyleSheet(
            "background-color: #141a2f; border: 1px solid #2f3c7e; border-radius: 6px; color: #8aa1d4;"
        )
        preview_layout.addWidget(self.auction_preview_image)

        self.auction_preview_title = QLabel("-")
        self.auction_preview_title.setAlignment(Qt.AlignCenter)
        self.auction_preview_title.setStyleSheet("color: #00d4ff; font-weight: bold;")
        preview_layout.addWidget(self.auction_preview_title)

        self.auction_preview_description = QLabel("Waiting for auction phase")
        self.auction_preview_description.setWordWrap(True)
        self.auction_preview_description.setStyleSheet("color: #cccccc;")
        preview_layout.addWidget(self.auction_preview_description)

        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #11182c;
                border: 1px solid #2f3c7e;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        layout.addWidget(preview_frame)

        layout.addStretch()

        # New Game button
        new_game_btn = QPushButton("NEW GAME")
        new_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        new_game_btn.clicked.connect(self.start_new_game)
        layout.addWidget(new_game_btn)

        panel.setStyleSheet("""
            QFrame {
                background-color: #0f1419;
                border: 2px solid #0f3460;
                border-radius: 8px;
            }
        """)
        panel.setLayout(layout)
        return panel

    def _create_center_area(self) -> QWidget:
        """Create center game area."""
        center_frame = QFrame()
        layout = QVBoxLayout(center_frame)

        # Game title
        self.title_label = QLabel("BALATRO CERTAMEN")
        self.title_label.setFont(QFont("Bahnschrift", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: #c9a66b;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(44)
        layout.addWidget(self.title_label)

        # Round and score header
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)

        self.round_set_label = QLabel("Round 1, Set 1")
        self.round_set_label.setAlignment(Qt.AlignCenter)
        self.round_set_label.setStyleSheet("color: #c9a66b; font-size: 18px; font-weight: bold;")
        status_layout.addWidget(self.round_set_label)

        points_row = QHBoxLayout()

        player_points_frame = QFrame()
        player_points_layout = QVBoxLayout(player_points_frame)
        self.player_points_value = QLabel("0")
        self.player_points_value.setAlignment(Qt.AlignCenter)
        self.player_points_value.setStyleSheet("color: #64ff96; font-size: 28px; font-weight: bold;")
        player_points_layout.addWidget(self.player_points_value)
        player_points_label = QLabel("PLAYER")
        player_points_label.setAlignment(Qt.AlignCenter)
        player_points_label.setStyleSheet("color: #9dd8b5; font-size: 10px; letter-spacing: 1px;")
        player_points_layout.addWidget(player_points_label)

        self.player_discards_value = QLabel("Discards Left: 2")
        self.player_discards_value.setAlignment(Qt.AlignCenter)
        self.player_discards_value.setStyleSheet(
            "color: #8fe8b7; font-size: 10px; font-weight: bold; "
            "background-color: rgba(0, 0, 0, 0.25); border-radius: 4px; padding: 2px 6px;"
        )
        player_points_layout.addWidget(self.player_discards_value)
        points_row.addWidget(player_points_frame)

        versus_label = QLabel("VS")
        versus_label.setAlignment(Qt.AlignCenter)
        versus_label.setStyleSheet("color: #c9a66b; font-size: 16px; font-weight: bold;")
        points_row.addWidget(versus_label)

        ai_points_frame = QFrame()
        ai_points_layout = QVBoxLayout(ai_points_frame)
        self.ai_points_value = QLabel("0")
        self.ai_points_value.setAlignment(Qt.AlignCenter)
        self.ai_points_value.setStyleSheet("color: #ff8f8f; font-size: 28px; font-weight: bold;")
        ai_points_layout.addWidget(self.ai_points_value)
        ai_points_label = QLabel("AI")
        ai_points_label.setAlignment(Qt.AlignCenter)
        ai_points_label.setStyleSheet("color: #ffb4b4; font-size: 10px; letter-spacing: 1px;")
        ai_points_layout.addWidget(ai_points_label)

        self.ai_discards_value = QLabel("Discards Left: 2")
        self.ai_discards_value.setAlignment(Qt.AlignCenter)
        self.ai_discards_value.setStyleSheet(
            "color: #ffc2c2; font-size: 10px; font-weight: bold; "
            "background-color: rgba(0, 0, 0, 0.25); border-radius: 4px; padding: 2px 6px;"
        )
        ai_points_layout.addWidget(self.ai_discards_value)
        points_row.addWidget(ai_points_frame)

        status_layout.addLayout(points_row)

        status_frame.setStyleSheet("""
            QFrame {
                background-color: #15172b;
                border: 1px solid #2f3c7e;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        player_points_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(100, 255, 150, 0.08);
                border: 1px solid #2d7a55;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        ai_points_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 120, 120, 0.10);
                border: 1px solid #7b3434;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout.addWidget(status_frame)

        # Played hands display
        self.played_frame = QFrame()
        played_layout = QVBoxLayout(self.played_frame)
        played_title = QLabel("PLAYED HANDS")
        played_title.setStyleSheet("color: #00d4ff; font-weight: bold;")
        played_layout.addWidget(played_title)

        self.played_display = QLabel("Waiting for player action...")
        self.played_display.setStyleSheet("color: #cccccc;")
        self.played_display.setWordWrap(True)
        self.played_display.setMinimumHeight(60)
        played_layout.addWidget(self.played_display)

        self.played_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.played_frame)

        # Auction board (shown during auction; replaces played-hands block)
        self.auction_board_frame = QFrame()
        auction_board_layout = QVBoxLayout(self.auction_board_frame)
        auction_board_layout.setContentsMargins(4, 4, 4, 4)
        auction_board_layout.setSpacing(4)
        auction_board_title = QLabel("AUCTION BOARD")
        auction_board_title.setStyleSheet(
            "color: #c9a66b; font-weight: bold; font-size: 10px; "
            "background-color: #11182d; border: 1px solid #2a3d66; border-radius: 4px; padding: 1px 4px;"
        )
        auction_board_layout.addWidget(auction_board_title)

        self.auction_turn_info_label = QLabel("Waiting for auction")
        self.auction_turn_info_label.setStyleSheet(
            "color: #d6deeb; font-size: 10px; "
            "background-color: #11182d; border: 1px solid #2a3d66; border-radius: 4px; padding: 1px 4px;"
        )
        self.auction_turn_info_label.setWordWrap(True)
        self.auction_turn_info_label.setFixedHeight(26)
        auction_board_layout.addWidget(self.auction_turn_info_label)

        self.auction_cards_container = QWidget()
        self.auction_cards_container.setStyleSheet(
            "background-color: #0f1419; border: 1px solid #2f3c7e; border-radius: 6px;"
        )
        self.auction_board_grid = QGridLayout(self.auction_cards_container)
        self.auction_board_grid.setSpacing(4)
        self.auction_board_grid.setContentsMargins(4, 4, 4, 4)
        auction_board_layout.addWidget(self.auction_cards_container)

        self.auction_end_turn_btn = QPushButton("END BIDDING TURN")
        self.auction_end_turn_btn.setStyleSheet(
            "QPushButton { background-color: #2d6a4f; color: #e9f5ee; font-weight: bold; padding: 4px; }"
            "QPushButton:hover { background-color: #3a8a67; }"
        )
        self.auction_end_turn_btn.setFixedHeight(28)
        self.auction_end_turn_btn.clicked.connect(self._handle_auction_end_turn)
        auction_board_layout.addWidget(self.auction_end_turn_btn)

        self.auction_board_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 3px;
            }
        """)
        self.auction_board_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.auction_board_frame.setMaximumHeight(420)
        self.auction_board_frame.setVisible(False)
        layout.addWidget(self.auction_board_frame)

        # Player's hand
        self.hand_section_label = QLabel("YOUR HAND")
        self.hand_section_label.setStyleSheet("color: #00d4ff; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.hand_section_label)

        self.hand_preview_label = QLabel("Select cards to preview projected hand value")
        self.hand_preview_label.setWordWrap(True)
        self.hand_preview_label.setStyleSheet(
            "color: #d6deeb; background-color: #121c33; border: 1px solid #2f3c7e; "
            "border-radius: 6px; padding: 6px;"
        )
        layout.addWidget(self.hand_preview_label)

        self.hand_scroll = QScrollArea()
        self.hand_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 5px;
            }
        """)
        self.hand_scroll.setMinimumHeight(180)

        self.hand_container = QWidget()
        self.hand_grid = QGridLayout(self.hand_container)
        self.hand_grid.setSpacing(5)
        self.hand_scroll.setWidget(self.hand_container)
        self.hand_scroll.setWidgetResizable(True)
        layout.addWidget(self.hand_scroll)

        # Action buttons
        self.hand_buttons_widget = QWidget()
        button_layout = QHBoxLayout(self.hand_buttons_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.play_btn = QPushButton("PLAY HAND (5 selected)")
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #64ff96;
                color: black;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
        """)
        self.play_btn.clicked.connect(self._handle_play_hand)
        button_layout.addWidget(self.play_btn)

        self.discard_btn = QPushButton("DISCARD SELECTED")
        self.discard_btn.setEnabled(False)
        self.discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9d3d;
                color: black;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
        """)
        self.discard_btn.clicked.connect(self._handle_discard)
        button_layout.addWidget(self.discard_btn)

        layout.addWidget(self.hand_buttons_widget)

        # Auction section
        self.auction_frame = QFrame()
        auction_layout = QVBoxLayout(self.auction_frame)
        auction_title = QLabel("AUCTION")
        auction_title.setStyleSheet("color: #c9a66b; font-weight: bold; margin-top: 8px;")
        auction_layout.addWidget(auction_title)

        self.auction_card_label = QLabel("No active auction")
        self.auction_card_label.setStyleSheet("color: #00d4ff;")
        self.auction_card_label.setWordWrap(True)
        auction_layout.addWidget(self.auction_card_label)

        self.auction_bid_label = QLabel("Bid: -")
        self.auction_bid_label.setStyleSheet("color: #64ff96;")
        auction_layout.addWidget(self.auction_bid_label)

        self.auction_turn_label = QLabel("Turn: -")
        self.auction_turn_label.setStyleSheet("color: #ff9d3d;")
        auction_layout.addWidget(self.auction_turn_label)

        auction_buttons = QHBoxLayout()

        self.auction_min_raise_btn = QPushButton("MIN RAISE")
        self.auction_min_raise_btn.clicked.connect(self._handle_auction_min_raise)
        auction_buttons.addWidget(self.auction_min_raise_btn)

        self.auction_custom_bid_input = QSpinBox()
        self.auction_custom_bid_input.setRange(0, 999999)
        self.auction_custom_bid_input.setValue(0)
        self.auction_custom_bid_input.setStyleSheet("padding: 6px;")
        auction_buttons.addWidget(self.auction_custom_bid_input)

        self.auction_custom_bid_btn = QPushButton("CUSTOM BID")
        self.auction_custom_bid_btn.clicked.connect(self._handle_auction_custom_bid)
        auction_buttons.addWidget(self.auction_custom_bid_btn)

        self.auction_pass_btn = QPushButton("PASS")
        self.auction_pass_btn.clicked.connect(self._handle_auction_pass)
        auction_buttons.addWidget(self.auction_pass_btn)

        auction_layout.addLayout(auction_buttons)

        self.auction_frame.setStyleSheet("""
            QFrame {
                background-color: #15172b;
                border: 1px solid #2f3c7e;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.auction_frame.setVisible(False)
        layout.addWidget(self.auction_frame)

        center_frame.setStyleSheet("""
            QFrame {
                background-color: #0f1419;
                border: 2px solid #0f3460;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        center_frame.setLayout(layout)
        return center_frame

    def _create_right_panel(self) -> QWidget:
        """Create right sidebar with AI info and action log."""
        panel = QFrame()
        panel.setFixedWidth(250)
        layout = QVBoxLayout(panel)

        # AI info
        self.ai_info = PlayerInfoPanel(self.game_state.ai, is_opponent=True)
        self.ai_info.collection_requested.connect(self._open_collection_from_panel)
        layout.addWidget(self.ai_info)

        # Action log
        self.action_log = ActionLogPanel()
        layout.addWidget(self.action_log, 1)

        panel.setStyleSheet("""
            QFrame {
                background-color: #0f1419;
                border: 2px solid #0f3460;
                border-radius: 8px;
            }
        """)
        panel.setLayout(layout)
        return panel

    def _apply_stylesheet(self):
        """Apply global stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0e27;
            }
            QLabel {
                color: #ffffff;
                font-family: "Segoe UI";
            }
            QPushButton {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 5px;
                font-family: "Segoe UI Semibold";
            }
            QPushButton:hover {
                background-color: #2a2a4e;
            }
        """)

    def start_new_game(self):
        """Start a new game."""
        self.game_state.new_game()
        self.selected_cards = []
        self.selected_card_widgets = []
        self.player_played_cards = None
        self.ai_played_cards = None
        self.game_state.start_set()
        self._update_display()
        self.action_log.add_log_entry("New game started! Set 1 of 3")

    def _update_display(self):
        """Update all UI displays."""
        # Update momentum bar
        self.momentum_bar.set_momentum(self.game_state.player.momentum)

        # Update status
        phase_name = self.game_state.current_phase.value.replace("_", " ").title()
        status_text = (
            f"Phase: {phase_name}\n"
            f"Round Score: You {self.game_state.player.round_score:,} | "
            f"AI {self.game_state.ai.round_score:,}\n"
            f"Momentum: {self.game_state.player.momentum:+,}"
        )
        self.status_label.setText(status_text)

        self.round_set_label.setText(
            f"Round {self.game_state.current_round}, Set {self.game_state.current_set}"
        )
        self.player_points_value.setText(f"{self.game_state.player.round_score:,}")
        self.ai_points_value.setText(f"{self.game_state.ai.round_score:,}")
        self.player_discards_value.setText(
            f"Discards Left: {self.game_state.player.discard_actions_remaining()}"
        )
        self.ai_discards_value.setText(
            f"Discards Left: {self.game_state.ai.discard_actions_remaining()}"
        )

        # Update player info
        self.player_info.update_display()
        self.ai_info.update_display()

        # Update hand display
        self._update_hand_display()
        self._update_hand_section_visibility()
        self._update_center_header_layout()

        # Update played hands display
        self._update_played_hands_display()

        # Update auction panel
        self._update_auction_panel()
        self._update_auction_board_ui()

        # Update auction preview
        self._update_auction_preview()

        # Update selected hand preview
        self._update_selected_hand_preview()

    def _update_played_hands_display(self):
        """Update the display of played hands."""
        if self.player_played_cards and self.ai_played_cards:
            player_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
                self.player_played_cards,
                self.game_state.player,
                self.game_state.round_disabled_jokers[0],
            )
            ai_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
                self.ai_played_cards,
                self.game_state.ai,
                self.game_state.round_disabled_jokers[1],
            )
            
            player_score = ScoringRules.calculate_score(
                player_hand,
                self.game_state.player,
                self.game_state.ai,
                disabled_jokers=self.game_state.round_disabled_jokers[0],
                opponent_disabled_jokers=self.game_state.round_disabled_jokers[1],
            )
            ai_score = ScoringRules.calculate_score(
                ai_hand,
                self.game_state.ai,
                self.game_state.player,
                disabled_jokers=self.game_state.round_disabled_jokers[1],
                opponent_disabled_jokers=self.game_state.round_disabled_jokers[0],
            )
            
            display_text = (
                f"Player: {player_hand.hand_rank.name} = {player_score.final_score} pts\n"
                f"AI: {ai_hand.hand_rank.name} = {ai_score.final_score} pts"
            )
            self.played_display.setText(display_text)
        elif self.player_played_cards:
            player_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
                self.player_played_cards,
                self.game_state.player,
                self.game_state.round_disabled_jokers[0],
            )
            self.played_display.setText(f"Player played: {player_hand.hand_rank.name}\nWaiting for AI...")
        else:
            self.played_display.setText("Waiting for player action...")

    def _update_hand_display(self):
        """Update the player's hand display."""
        # Clear old widgets
        for widget in self.hand_widgets:
            widget.deleteLater()
        self.hand_widgets = []
        self.selected_card_widgets = []
        self.selected_cards = []

        # Create new card widgets
        for i, card in enumerate(self.game_state.player.hand):
            card_widget = CardWidget(card)
            card_widget.clicked.connect(self._on_card_clicked)
            self.hand_grid.addWidget(card_widget, 0, i)
            self.hand_widgets.append(card_widget)

        # Update play button
        is_set_play = self.game_state.current_phase == GamePhase.SET_PLAY
        self.play_btn.setEnabled(is_set_play and len(self.selected_cards) == 5)
        self.discard_btn.setEnabled(is_set_play and len(self.selected_cards) > 0)
        self._update_selected_hand_preview()

    def _update_hand_section_visibility(self):
        """Hide hand UI during auction and show it otherwise."""
        show_hand_section = self.game_state.current_phase != GamePhase.AUCTION

        if self.hand_section_label is not None:
            self.hand_section_label.setVisible(show_hand_section)
        if self.hand_preview_label is not None:
            self.hand_preview_label.setVisible(show_hand_section)
        if hasattr(self, "hand_scroll") and self.hand_scroll is not None:
            self.hand_scroll.setVisible(show_hand_section)
        if self.hand_buttons_widget is not None:
            self.hand_buttons_widget.setVisible(show_hand_section)

    def _update_center_header_layout(self):
        """Compact top header during auction to free vertical space for cards."""
        if self.title_label is None or self.round_set_label is None:
            return

        in_auction = self.game_state.current_phase == GamePhase.AUCTION
        if in_auction:
            self.title_label.setFont(QFont("Bahnschrift", 14, QFont.Bold))
            self.title_label.setFixedHeight(28)
            self.round_set_label.setStyleSheet("color: #c9a66b; font-size: 14px; font-weight: bold;")
        else:
            self.title_label.setFont(QFont("Bahnschrift", 20, QFont.Bold))
            self.title_label.setFixedHeight(44)
            self.round_set_label.setStyleSheet("color: #c9a66b; font-size: 18px; font-weight: bold;")

    def _update_selected_hand_preview(self):
        """Show projected hand type/chips/mult/score for current card selections."""
        if self.hand_preview_label is None:
            return

        selected = list(self.selected_cards)
        if not selected:
            self.hand_preview_label.setText("Select cards to preview projected hand value")
            return

        player = self.game_state.player
        opponent = self.game_state.ai
        disabled = self.game_state.round_disabled_jokers[0]
        opponent_disabled = self.game_state.round_disabled_jokers[1]

        # Use only selected cards for preview; do not auto-fill to 5 cards.
        projected_hand = None
        try:
            if len(selected) > 5:
                projected_hand = PokerHandEvaluator.find_best_hand_with_modifiers(selected, player, disabled)
            elif len(selected) == 5:
                projected_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(selected, player, disabled)
            else:
                projected_hand = self._evaluate_partial_hand_with_modifiers(selected, player, disabled)
        except Exception:
            projected_hand = None

        if projected_hand is None:
            self.hand_preview_label.setText(
                f"Selected: {len(selected)} card(s) | Need more cards for a valid projection"
            )
            return

        projected_score = ScoringRules.calculate_score(
            projected_hand,
            player,
            opponent,
            disabled_jokers=disabled,
            opponent_disabled_jokers=opponent_disabled,
        )

        total_chips = (
            projected_score.base_chips
            + projected_score.planet_chips
            + projected_score.card_chips
            + projected_score.joker_chip_bonus
        )
        additive_mult = projected_score.base_mult + projected_score.planet_mult + projected_score.joker_mult_bonus
        hand_name = ScoringRules.get_hand_name(projected_hand.hand_rank)

        self.hand_preview_label.setText(
            f"Selected: {len(selected)}/5 | Hand: {hand_name}\n"
            f"Chips: {total_chips} | Mult: {additive_mult} x {projected_score.joker_x_mult:.2f}\n"
            f"Projected Score: {projected_score.final_score}"
        )

    def _evaluate_partial_hand_with_modifiers(
        self,
        cards: List[Card],
        player,
        disabled_jokers,
    ) -> PokerHand:
        """Evaluate selected cards as a variable-size hand (2-4 cards)."""
        if not cards:
            raise ValueError("No cards selected")

        sorted_cards = sorted(cards, key=lambda c: c.rank.rank_order(), reverse=True)
        active_jokers = [j for j in player.jokers if j not in disabled_jokers]

        normalized_suits = [PokerHandEvaluator._normalize_suit(c.suit, active_jokers) for c in sorted_cards]
        suit_counts = Counter(normalized_suits)

        n = len(sorted_cards)
        has_four_fingers = any(j.type == JokerType.FOUR_FINGERS for j in active_jokers)
        has_shortcut = any(j.type == JokerType.SHORTCUT for j in active_jokers)

        flush_required = 4 if has_four_fingers else 5
        is_flush = n >= flush_required and max(suit_counts.values()) >= flush_required

        ranks = [c.rank.rank_order() for c in sorted_cards]
        straight_required = 4 if has_shortcut else 5
        is_straight = self._is_partial_straight(ranks, has_shortcut, straight_required)

        rank_counts = Counter([c.rank for c in sorted_cards])
        count_values = sorted(rank_counts.values(), reverse=True)

        if is_straight and is_flush:
            hand_rank = HandRank.STRAIGHT_FLUSH
        elif n >= 4 and count_values[0] == 4:
            hand_rank = HandRank.FOUR_OF_A_KIND
        elif n >= 5 and count_values[0] == 3 and len(count_values) > 1 and count_values[1] >= 2:
            hand_rank = HandRank.FULL_HOUSE
        elif is_flush:
            hand_rank = HandRank.FLUSH
        elif is_straight:
            hand_rank = HandRank.STRAIGHT
        elif n >= 3 and count_values[0] == 3:
            hand_rank = HandRank.THREE_OF_A_KIND
        elif n >= 4 and count_values.count(2) >= 2:
            hand_rank = HandRank.TWO_PAIR
        elif n >= 2 and count_values[0] == 2:
            hand_rank = HandRank.PAIR
        else:
            hand_rank = HandRank.HIGH_CARD

        return PokerHand(cards=sorted_cards, hand_rank=hand_rank, high_card=sorted_cards[0].rank)

    @staticmethod
    def _is_partial_straight(ranks: List[int], has_shortcut: bool, required_cards: int) -> bool:
        """Evaluate straight for variable-size selected cards."""
        if len(ranks) < required_cards:
            return False

        unique = set(ranks)
        if len(unique) != len(ranks):
            return False

        if 14 in unique:
            unique.add(1)

        ordered = sorted(unique)
        n = len(ranks)
        if len(ordered) < required_cards:
            return False

        span = ordered[-1] - ordered[0]
        if not has_shortcut:
            return required_cards == 5 and span == 4

        # Shortcut allows one-rank gap but only at 4+ selected cards.
        return span <= required_cards

    def _update_auction_panel(self):
        """Legacy auction panel is hidden in favor of the auction board."""
        self.auction_frame.setVisible(False)

    def _update_auction_board_ui(self):
        """Render simultaneous 5-card auction board during auction phase."""
        in_auction = self.game_state.current_phase == GamePhase.AUCTION and self.game_state.auction_state.is_active

        self.auction_board_frame.setVisible(in_auction)
        self.played_frame.setVisible(not in_auction)
        # Keep auction board compact only during auction, while normal set-play uses full center space.
        self.auction_board_frame.setMaximumHeight(420 if in_auction else 16777215)

        if not in_auction:
            return

        next_bidder = self.game_state.get_next_auction_bidder()
        next_text = "Player" if next_bidder == 0 else ("AI" if next_bidder == 1 else "Resolving")
        self.auction_turn_info_label.setText(
            f"Turn {self.game_state.auction_state.turn_index + 1}/4 | Next: {next_text} | "
            f"Spent P:{self.game_state.auction_state.player_spent} AI:{self.game_state.auction_state.ai_spent}"
        )
        self.auction_end_turn_btn.setEnabled(next_bidder == 0)

        # Rebuild auction card widgets each refresh for correctness over complexity.
        while self.auction_board_grid.count():
            item = self.auction_board_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, card in enumerate(self.game_state.auction_state.revealed_cards):
            frame = QFrame()
            frame.setStyleSheet("background-color: #121c33; border: 1px solid #2a3d66; border-radius: 8px;")
            outer = QHBoxLayout(frame)
            outer.setContentsMargins(6, 6, 6, 6)
            outer.setSpacing(8)

            image = QLabel("Image Missing")
            image.setAlignment(Qt.AlignCenter)
            image.setFixedSize(96, 96)
            image.setStyleSheet("background-color: #0c1223; border: 1px solid #2f3c7e; border-radius: 6px;")
            image_path = self._get_auction_card_image_path(card)
            if image_path and image_path.exists():
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    image.setPixmap(pixmap.scaled(92, 92, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    image.setText("")
            outer.addWidget(image)

            details = QWidget()
            details_layout = QVBoxLayout(details)
            details_layout.setContentsMargins(0, 0, 0, 0)
            details_layout.setSpacing(4)

            name = QLabel(str(card))
            name.setWordWrap(True)
            name.setStyleSheet("color: #c9a66b; font-weight: bold; font-size: 11px;")
            details_layout.addWidget(name)

            desc = QLabel(self._get_auction_card_description(card))
            desc.setWordWrap(True)
            desc.setStyleSheet(
                "color: #c8d3e6; font-size: 10px; "
                "background-color: #172443; border: 1px solid #2d4270; border-radius: 6px; padding: 4px;"
            )
            details_layout.addWidget(desc)

            current_bid = self.game_state.auction_state.card_bids[idx]
            leader = self.game_state.auction_state.card_leaders[idx]
            leader_text = "None" if leader == -1 else ("Player" if leader == 0 else "AI")
            min_next = self.game_state.get_card_min_next_bid(idx)
            info = QLabel(
                f"Min: {card.minimum_bid} | Bid: {current_bid}\nLeader: {leader_text} | Next: {min_next}"
            )
            info.setWordWrap(True)
            info.setStyleSheet(
                "color: #9fd8ff; font-size: 10px; "
                "background-color: #172443; border: 1px solid #2d4270; border-radius: 6px; padding: 4px;"
            )
            details_layout.addWidget(info)

            button_row = QHBoxLayout()
            button_row.setSpacing(4)

            bid_btn = QPushButton("Bid +Min")
            bid_btn.setEnabled(next_bidder == 0)
            bid_btn.clicked.connect(lambda _, card_idx=idx: self._handle_auction_card_bid(card_idx))
            bid_btn.setStyleSheet("padding: 4px; font-size: 10px;")
            bid_btn.setFixedHeight(24)
            button_row.addWidget(bid_btn)

            reduce_btn = QPushButton("Bid -Min")
            reduce_btn.setEnabled(next_bidder == 0)
            reduce_btn.clicked.connect(lambda _, card_idx=idx: self._handle_auction_card_reduce(card_idx))
            reduce_btn.setStyleSheet(
                "padding: 4px; font-size: 10px; background-color: #40312a; border: 1px solid #6f5346;"
            )
            reduce_btn.setFixedHeight(24)
            button_row.addWidget(reduce_btn)

            details_layout.addLayout(button_row)
            outer.addWidget(details, 1)

            row = idx // 2
            col = idx % 2
            self.auction_board_grid.addWidget(frame, row, col)

    def _set_auction_controls_enabled(self, enabled: bool):
        """Enable/disable interactive auction controls."""
        self.auction_min_raise_btn.setEnabled(enabled)
        self.auction_custom_bid_btn.setEnabled(enabled)
        self.auction_custom_bid_input.setEnabled(enabled)
        self.auction_pass_btn.setEnabled(enabled)

    def _update_auction_preview(self):
        """Update lower-left preview with current auction card image and description."""
        card = self.game_state.get_current_auction_card()
        in_auction = self.game_state.current_phase == GamePhase.AUCTION and self.game_state.auction_state.is_active

        if not in_auction or card is None:
            self.auction_preview_title.setText("-")
            self.auction_preview_description.setText("Waiting for auction phase")
            self.auction_preview_image.setPixmap(QPixmap())
            self.auction_preview_image.setText("No Card")
            return

        self.auction_preview_title.setText(str(card))
        self.auction_preview_description.setText(self._get_auction_card_description(card))

        image_path = self._get_auction_card_image_path(card)
        if image_path and image_path.exists():
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.auction_preview_image.width() - 8,
                    self.auction_preview_image.height() - 8,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.auction_preview_image.setPixmap(scaled)
                self.auction_preview_image.setText("")
                return

        self.auction_preview_image.setPixmap(QPixmap())
        self.auction_preview_image.setText("Image Missing")

    @staticmethod
    def _get_auction_card_description(card) -> str:
        """Return a concise card description for the auction preview."""
        if card.is_planet and card.planet_type is not None:
            planet = card.planet_type
            return (
                f"Planet upgrade for {planet.hand_type()} | "
                f"+{planet.chip_bonus()} chips, +{planet.mult_bonus()} mult per level"
            )

        if card.is_joker and card.joker_type is not None:
            descriptions = {
                "BANNER": "+20 chips per remaining discard",
                "ABSTRACT": "+2 mult for each joker you own",
                "EVEN_STEVEN": "+2 mult for each even-ranked played card",
                "ODD_TODD": "+2 mult for each odd-ranked played card",
                "BLACK_HOLE": "Opponent aces score as 0 chips",
                "THE_DUO": "+20 chips if your hand contains a pair",
                "THE_GREEDY": "+10 chips for each diamond played",
                "THE_LOVER": "+10 chips for each heart played",
                "THE_PROTECTOR": "+10 chips for each spade played",
                "THE_CHAIRMAN": "+10 chips for each club played",
                "SCRAPPY": "+1 discard action per round",
                "STRAITJACKET": "Opponent gets -1 discard action per round",
                "COPYRIGHT": "If same hand type is played, disable an opponent joker",
                "TAX_MAN": "+10 chips per opponent face card played",
                "TRADE_INSIDER": "Future auction insight and bidding value",
                "FOUR_FINGERS": "Flush can be made with 4 matching suits",
                "SHORTCUT": "Straight can include one rank gap",
                "THE_TRIBE": "x2 mult if hand is a flush",
                "THE_ORDER": "x2 mult if hand is a straight",
                "FAMILY": "x4 mult if hand contains four of a kind",
                "RAINBOW": "x4 mult if hand contains all four suits",
                "UNIFORM": "Spades and clubs count as same suit",
                "SMEAR": "Hearts and diamonds count as same suit",
                "COPYCAT": "Copies strongest mirrorable joker effect",
            }
            return descriptions.get(card.joker_type.name, "Joker effect")

        return "Auction card"

    @staticmethod
    def _get_auction_card_image_path(card) -> Optional[Path]:
        """Resolve expected image path for the current auction card."""
        root = Path(__file__).resolve().parent.parent
        base = root / "assets" / "auction_cards"

        def to_capitalized_words(name: str) -> str:
            return "_".join(part.capitalize() for part in name.split("_"))

        if card.is_joker and card.joker_type is not None:
            capitalized_name = to_capitalized_words(card.joker_type.name)
            preferred = base / "jokers" / f"Joker_{capitalized_name}.webp"
            fallback = base / "jokers" / f"joker_{card.joker_type.name.lower()}.webp"
            return preferred if preferred.exists() else fallback

        if card.is_planet and card.planet_type is not None:
            capitalized_name = to_capitalized_words(card.planet_type.name)
            preferred = base / "planets" / f"Planet_{capitalized_name}.webp"
            fallback = base / "planets" / f"planet_{card.planet_type.name.lower()}.webp"
            return preferred if preferred.exists() else fallback

        return None

    def _open_collection_from_panel(self, collection_type: str, is_opponent: bool):
        """Open collection gallery window for a player's jokers or planets."""
        player = self.game_state.ai if is_opponent else self.game_state.player
        owner = "AI" if is_opponent else "Player"

        if collection_type == "jokers":
            if not player.jokers:
                QMessageBox.information(self, "No Jokers", f"{owner} has no jokers yet.")
                return
            entries = []
            counts = {}
            for joker in player.jokers:
                counts[joker.type] = counts.get(joker.type, 0) + 1
            for jtype, count in counts.items():
                entries.append((
                    jtype.name.replace("_", " ").title(),
                    self._get_joker_description(jtype),
                    self._get_joker_image_path(jtype),
                    count,
                ))
            title = f"{owner} Joker Collection"
        else:
            if not player.planets:
                QMessageBox.information(self, "No Planets", f"{owner} has no planets yet.")
                return
            entries = []
            counts = {}
            for planet in player.planets:
                counts[planet] = counts.get(planet, 0) + 1
            for planet, count in counts.items():
                entries.append((
                    planet.name.title(),
                    self._get_planet_description(planet),
                    self._get_planet_image_path(planet),
                    count,
                ))
            title = f"{owner} Planet Collection"

        self._show_collection_window(title, entries)

    def _show_collection_window(self, title: str, entries: List[tuple]):
        """Render a scrollable gallery window for collection entries."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(900, 640)
        dialog.setStyleSheet("background-color: #0e1428; color: #d6deeb;")

        outer = QVBoxLayout(dialog)
        header = QLabel(title)
        header.setStyleSheet("color: #c9a66b; font-size: 18px; font-weight: bold;")
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #0f1419; border: 1px solid #2f3c7e; border-radius: 8px; }
            QScrollBar:vertical { background-color: #1a1a2e; width: 10px; }
            QScrollBar::handle:vertical { background-color: #0f3460; }
        """)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(12)
        grid.setContentsMargins(12, 12, 12, 12)

        for idx, (name, description, image_path, count) in enumerate(entries):
            card_frame = QFrame()
            card_frame.setStyleSheet(
                "background-color: #121c33; border: 1px solid #2a3d66; border-radius: 8px;"
            )
            card_layout = QVBoxLayout(card_frame)

            image = QLabel("Image Missing")
            image.setAlignment(Qt.AlignCenter)
            image.setFixedHeight(170)
            image.setStyleSheet("background-color: #0c1223; border: 1px solid #2f3c7e; border-radius: 6px;")
            if image_path and image_path.exists():
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(190, 165, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image.setPixmap(scaled)
                    image.setText("")
            card_layout.addWidget(image)

            name_label = QLabel(f"{name} x{count}" if count > 1 else name)
            name_label.setStyleSheet("color: #c9a66b; font-size: 13px; font-weight: bold;")
            name_label.setWordWrap(True)
            card_layout.addWidget(name_label)

            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #c8d3e6; font-size: 11px;")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)

            row = idx // 3
            col = idx % 3
            grid.addWidget(card_frame, row, col)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.collection_windows.append(dialog)
        dialog.finished.connect(lambda _: self.collection_windows.remove(dialog) if dialog in self.collection_windows else None)
        dialog.show()

    @staticmethod
    def _get_joker_description(jtype: JokerType) -> str:
        descriptions = {
            JokerType.BANNER: "+20 chips per remaining discard",
            JokerType.ABSTRACT: "+2 mult for each joker you own",
            JokerType.EVEN_STEVEN: "+2 mult for each even-ranked played card",
            JokerType.ODD_TODD: "+2 mult for each odd-ranked played card",
            JokerType.BLACK_HOLE: "Opponent aces score as 0 chips",
            JokerType.THE_DUO: "+20 chips if your hand contains a pair",
            JokerType.THE_GREEDY: "+10 chips for each diamond played",
            JokerType.THE_LOVER: "+10 chips for each heart played",
            JokerType.THE_PROTECTOR: "+10 chips for each spade played",
            JokerType.THE_CHAIRMAN: "+10 chips for each club played",
            JokerType.SCRAPPY: "+1 discard action per round",
            JokerType.STRAITJACKET: "Opponent gets -1 discard action per round",
            JokerType.COPYRIGHT: "If same hand type is played, disable an opponent joker",
            JokerType.TAX_MAN: "+10 chips per opponent face card played",
            JokerType.TRADE_INSIDER: "Future auction insight and bidding value",
            JokerType.FOUR_FINGERS: "Flush can be made with 4 matching suits",
            JokerType.SHORTCUT: "Straight can include one rank gap",
            JokerType.THE_TRIBE: "x2 mult if hand is a flush",
            JokerType.THE_ORDER: "x2 mult if hand is a straight",
            JokerType.FAMILY: "x4 mult if hand contains four of a kind",
            JokerType.RAINBOW: "x4 mult if hand contains all four suits",
            JokerType.UNIFORM: "Spades and clubs count as same suit",
            JokerType.SMEAR: "Hearts and diamonds count as same suit",
            JokerType.COPYCAT: "Copies strongest mirrorable joker effect",
        }
        return descriptions.get(jtype, "Joker effect")

    @staticmethod
    def _get_planet_description(planet: Planet) -> str:
        return (
            f"Upgrades {planet.hand_type()} | "
            f"+{planet.chip_bonus()} chips, +{planet.mult_bonus()} mult per level"
        )

    @staticmethod
    def _get_joker_image_path(jtype: JokerType) -> Path:
        root = Path(__file__).resolve().parent.parent
        base = root / "assets" / "auction_cards" / "jokers"
        capitalized_name = "_".join(part.capitalize() for part in jtype.name.split("_"))
        preferred = base / f"Joker_{capitalized_name}.webp"
        fallback = base / f"joker_{jtype.name.lower()}.webp"
        return preferred if preferred.exists() else fallback

    @staticmethod
    def _get_planet_image_path(planet: Planet) -> Path:
        root = Path(__file__).resolve().parent.parent
        base = root / "assets" / "auction_cards" / "planets"
        capitalized_name = "_".join(part.capitalize() for part in planet.name.split("_"))
        preferred = base / f"Planet_{capitalized_name}.webp"
        fallback = base / f"planet_{planet.name.lower()}.webp"
        return preferred if preferred.exists() else fallback

    def _on_card_clicked(self, card_widget: CardWidget):
        """Handle card click."""
        if self.game_state.current_phase != GamePhase.SET_PLAY:
            return

        if card_widget not in self.hand_widgets:
            return

        # Track by widget identity so duplicate value cards can be selected independently.
        if card_widget in self.selected_card_widgets:
            idx = self.selected_card_widgets.index(card_widget)
            self.selected_card_widgets.pop(idx)
            self.selected_cards.pop(idx)
            card_widget.set_selected(False)
        else:
            self.selected_card_widgets.append(card_widget)
            self.selected_cards.append(card_widget.card)
            card_widget.set_selected(True)

        # Update buttons
        self.play_btn.setEnabled(len(self.selected_cards) == 5)
        self.discard_btn.setEnabled(len(self.selected_cards) > 0)
        self._update_selected_hand_preview()

    def _handle_play_hand(self):
        """Handle play hand button click."""
        if self.game_state.current_phase != GamePhase.SET_PLAY:
            return

        if len(self.selected_cards) != 5:
            QMessageBox.warning(self, "Invalid", "Select exactly 5 cards!")
            return

        # Validate it's a legal hand
        try:
            hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
                self.selected_cards,
                self.game_state.player,
                self.game_state.round_disabled_jokers[0],
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid hand: {e}")
            return

        # Store player's played cards
        self.player_played_cards = self.selected_cards.copy()

        # Remove played cards from hand
        for card in self.selected_cards:
            self.game_state.player.hand.remove(card)

        hand_score = ScoringRules.calculate_score(
            hand,
            self.game_state.player,
            self.game_state.ai,
            disabled_jokers=self.game_state.round_disabled_jokers[0],
            opponent_disabled_jokers=self.game_state.round_disabled_jokers[1],
        )
        self.action_log.add_log_entry(f"Player played {hand.hand_rank.name}: {hand_score.final_score} pts")

        # Clear selection
        self.selected_cards = []
        self.selected_card_widgets = []
        self._update_hand_display()
        self._update_played_hands_display()

        # Disable buttons temporarily
        self.play_btn.setEnabled(False)
        self.discard_btn.setEnabled(False)

        # Schedule AI action
        self.ai_timer.start(1000)

    def _handle_discard(self):
        """Handle discard button click."""
        if self.game_state.current_phase != GamePhase.SET_PLAY:
            return

        if not self.game_state.player.can_discard():
            QMessageBox.warning(self, "No Discards", "No discard actions remaining!")
            return

        if len(self.selected_cards) == 0:
            QMessageBox.warning(self, "Invalid", "Select at least 1 card to discard!")
            return

        # Remove discarded cards
        for card in self.selected_cards:
            self.game_state.player.hand.remove(card)

        self.game_state.player.discard_actions_used += 1
        cards_discarded = len(self.selected_cards)

        # Redraw
        self.game_state.draw_cards(self.game_state.player, cards_discarded)

        self.action_log.add_log_entry(f"Player discarded {cards_discarded} cards")

        self.selected_cards = []
        self.selected_card_widgets = []
        self._update_hand_display()

    def _handle_auction_min_raise(self):
        """Place the minimum legal raise for the human bidder."""
        # Legacy single-card control hidden in current auction UX.
        return

    def _handle_auction_custom_bid(self):
        """Place a custom legal bid for the human bidder."""
        # Legacy single-card control hidden in current auction UX.
        return

    def _handle_auction_pass(self):
        """Pass on current auction turn for the human bidder."""
        # Legacy single-card control hidden in current auction UX.
        return

    def _handle_auction_card_bid(self, card_index: int):
        """Bid minimum raise on a specific auction card during player's turn."""
        if self.game_state.get_next_auction_bidder() != 0:
            return

        min_bid = self.game_state.get_card_min_next_bid(card_index)
        if self.game_state.place_auction_bid_for_card(0, card_index, min_bid):
            card_name = str(self.game_state.auction_state.revealed_cards[card_index])
            self.action_log.add_log_entry(f"Player bids {min_bid} on {card_name}")
            self._update_display()

    def _handle_auction_card_reduce(self, card_index: int):
        """Reduce player's bid by card minimum on a specific auction card."""
        if self.game_state.get_next_auction_bidder() != 0:
            return

        if self.game_state.reduce_auction_bid_for_card(0, card_index):
            card_name = str(self.game_state.auction_state.revealed_cards[card_index])
            reduced_to = self.game_state.auction_state.card_player_bids[card_index]
            self.action_log.add_log_entry(f"Player reduces bid to {reduced_to} on {card_name}")
            self._update_display()

    def _handle_auction_end_turn(self):
        """End player's auction turn and pass bidding control to AI."""
        if self.game_state.get_next_auction_bidder() != 0:
            return

        if self.game_state.end_auction_turn(0):
            self.action_log.add_log_entry("Player ends bidding turn")
            self._after_auction_action()

    def _handle_human_joker_overflow(self):
        """Prompt human to discard one joker when over 5."""
        if not self.game_state.auction_state.pending_human_joker_choice:
            return

        options = [str(joker) for joker in self.game_state.player.jokers]
        choice, ok = QInputDialog.getItem(
            self,
            "Joker Limit Reached",
            "Choose a joker to discard (max 5 jokers):",
            options,
            0,
            False,
        )

        if not ok:
            return

        discard_index = options.index(choice)
        if self.game_state.discard_human_joker(discard_index):
            self.action_log.add_log_entry(f"Player discards joker: {choice}")

    def _after_auction_action(self):
        """Refresh UI and continue auction flow after any auction action."""
        self._handle_human_joker_overflow()
        self._update_display()

        if self.game_state.current_phase == GamePhase.GAME_OVER:
            self._show_game_over()
            return

        if self.game_state.current_phase == GamePhase.AUCTION:
            next_bidder = self.game_state.get_next_auction_bidder()
            if next_bidder == 1:
                self.ai_timer.start(800)
        else:
            self.player_played_cards = None
            self.ai_played_cards = None
            self.action_log.add_log_entry(f"Set {self.game_state.current_set} started")

    def _perform_ai_action(self):
        """Perform the AI's action."""
        self.ai_timer.stop()

        if self.game_state.current_phase == GamePhase.AUCTION:
            self._perform_ai_auction_action()
            return

        # If both players have played, score the set
        if self.player_played_cards and self.ai_played_cards:
            self.game_state.score_set(self.player_played_cards, self.ai_played_cards)
            self.game_state.end_set()
            self._update_display()

            if self.game_state.current_phase == GamePhase.GAME_OVER:
                self._show_game_over()
                return

            if self.game_state.current_phase == GamePhase.AUCTION:
                self.action_log.add_log_entry("Auction phase started")
                if self.game_state.get_next_auction_bidder() == 1:
                    self.ai_timer.start(1000)
                return

            self.player_played_cards = None
            self.ai_played_cards = None
            self.action_log.add_log_entry(f"Set {self.game_state.current_set} started")
            return

        # If only player has played, AI plays
        if self.player_played_cards and not self.ai_played_cards:
            # AI decides
            should_play, cards_to_discard = self.ai.decide_play_or_discard(self.game_state.player)

            if should_play:
                # AI plays
                ai_hand_cards = self.ai.select_playing_hand()
                self.ai_played_cards = ai_hand_cards.copy()

                for card in ai_hand_cards:
                    self.game_state.ai.hand.remove(card)

                ai_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
                    ai_hand_cards,
                    self.game_state.ai,
                    self.game_state.round_disabled_jokers[1],
                )
                ai_score = ScoringRules.calculate_score(
                    ai_hand,
                    self.game_state.ai,
                    self.game_state.player,
                    disabled_jokers=self.game_state.round_disabled_jokers[1],
                    opponent_disabled_jokers=self.game_state.round_disabled_jokers[0],
                )
                self.action_log.add_log_entry(f"AI played {ai_hand.hand_rank.name}: {ai_score.final_score} pts")

                self._update_played_hands_display()
                self.ai_timer.start(1000)
            else:
                # AI discards
                for card in cards_to_discard:
                    self.game_state.ai.hand.remove(card)
                self.game_state.ai.discard_actions_used += 1
                self.game_state.draw_cards(self.game_state.ai, len(cards_to_discard))
                self.action_log.add_log_entry(f"AI discarded {len(cards_to_discard)} cards")
                self._update_display()
                self.ai_timer.start(1000)

    def _perform_ai_auction_action(self):
        """Perform AI action during auction phase."""
        if self.game_state.current_phase != GamePhase.AUCTION:
            return

        if self.game_state.get_next_auction_bidder() != 1:
            return

        bids = self.ai.decide_auction_turn_bids(self.game_state, self.game_state.player)
        for card_index, bid_amount in bids:
            if self.game_state.place_auction_bid_for_card(1, card_index, bid_amount):
                card_name = str(self.game_state.auction_state.revealed_cards[card_index])
                self.action_log.add_log_entry(f"AI bids {bid_amount} on {card_name}")

        self.game_state.end_auction_turn(1)
        self.action_log.add_log_entry("AI ends bidding turn")

        self._after_auction_action()

    def _show_game_over(self):
        """Show game over message."""
        winner = "Player" if self.game_state.player.momentum >= 10000 else "AI"
        momentum_final = abs(self.game_state.player.momentum)
        msg = f"GAME OVER!\n\n{winner} Wins!\n\nFinal Momentum: {momentum_final}"
        QMessageBox.information(self, "Game Over", msg)
