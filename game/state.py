"""Main game state and flow manager."""

import random
from typing import List, Optional, Tuple
from enum import Enum
from game.models import (
    Card, Rank, Suit, Player, Joker, JokerType, Planet, AuctionCard,
    AuctionState, PokerHand
)
from game.rules import PokerHandEvaluator, ScoringRules


class GamePhase(Enum):
    """Current phase of the game."""
    SETUP = "setup"
    ROUND_START = "round_start"
    SET_PLAY = "set_play"  # During a set
    SET_SCORING = "set_scoring"
    ROUND_END = "round_end"
    AUCTION = "auction"
    GAME_OVER = "game_over"


class GameState:
    """Main game state manager."""

    def __init__(self):
        self.player = Player(name="Human")
        self.ai = Player(name="AI")

        self.current_phase = GamePhase.SETUP
        self.current_round = 0
        self.current_set = 0

        # Auction state
        self.auction_state = AuctionState()
        self.auction_deck: List[AuctionCard] = []

        # Round tracking
        self.round_winner = None  # 0 for player, 1 for AI
        self.last_auction_first_bidder = 0

        # Action log
        self.action_log: List[str] = []

    def new_game(self):
        """Initialize a new game."""
        # Create decks
        self.player.deck = self._create_deck()
        self.ai.deck = self._create_deck()

        # Initialize auctions deck
        self._init_auction_deck()

        self.current_round = 1
        self.current_set = 1
        self.current_phase = GamePhase.ROUND_START

        self.add_action("Game started!")

    def _create_deck(self) -> List[Card]:
        """Create a shuffled 52-card deck."""
        deck = []
        for suit in Suit:
            for rank in Rank:
                deck.append(Card(rank=rank, suit=suit))
        random.shuffle(deck)
        return deck

    def _init_auction_deck(self):
        """Initialize the auction deck with all possible jokers and planets."""
        self.auction_deck = []
        card_id = 0

        # Add all jokers (5 copies each for strategy)
        for jtype in JokerType:
            for _ in range(2):  # 2 copies of each joker
                self.auction_deck.append(AuctionCard(
                    id=card_id,
                    is_joker=True,
                    is_planet=False,
                    joker_type=jtype,
                    minimum_bid=5 if jtype.value == "Common" else (10 if jtype.value == "Rare" else 20)
                ))
                card_id += 1

        # Add planets (multiple copies)
        for planet in Planet:
            for _ in range(3):  # 3 copies of each planet
                self.auction_deck.append(AuctionCard(
                    id=card_id,
                    is_joker=False,
                    is_planet=True,
                    planet_type=planet,
                    minimum_bid=8
                ))
                card_id += 1

        random.shuffle(self.auction_deck)

    def draw_cards(self, player: Player, count: int):
        """Draw cards from a player's deck, reshuffling if needed."""
        for _ in range(count):
            if not player.deck:
                # Reshuffle
                player.deck = self._create_deck()

            if player.deck:
                card = player.deck.pop(0)
                player.hand.append(card)

    def start_set(self):
        """Start a new set within a round."""
        # Reset hands if starting a new round
        if self.current_set == 1:
            self.player.reset_round()
            self.ai.reset_round()

        # Draw to 8 cards
        self.player.hand = []
        self.ai.hand = []

        while len(self.player.hand) < 8:
            self.draw_cards(self.player, 1)
        while len(self.ai.hand) < 8:
            self.draw_cards(self.ai, 1)

        self.current_phase = GamePhase.SET_PLAY
        self.add_action(f"Round {self.current_round}, Set {self.current_set} started")

    def score_set(self, player_cards: List[Card], ai_cards: List[Card]):
        """Score a set based on played hands."""
        player_hand = PokerHandEvaluator.evaluate_hand(player_cards)
        ai_hand = PokerHandEvaluator.evaluate_hand(ai_cards)

        player_score = ScoringRules.calculate_score(player_hand, self.player, self.ai)
        ai_score = ScoringRules.calculate_score(ai_hand, self.ai, self.player)

        self.player.round_score += player_score.final_score
        self.ai.round_score += ai_score.final_score

        set_winner = "Player" if player_score.final_score > ai_score.final_score else "AI"
        self.add_action(
            f"{set_winner} wins set {self.current_set}: "
            f"Player {player_score.final_score} vs AI {ai_score.final_score}"
        )

        return player_score, ai_score

    def end_set(self):
        """End the current set and check if round is over."""
        if self.current_set >= 3:
            self.end_round()
        else:
            self.current_set += 1
            self.start_set()

    def end_round(self):
        """End the round and update momentum, then go to auction."""
        round_delta = self.player.round_score - self.ai.round_score
        self.player.momentum += round_delta
        self.ai.momentum -= round_delta

        if self.player.round_score > self.ai.round_score:
            self.round_winner = 0
        elif self.ai.round_score > self.player.round_score:
            self.round_winner = 1
        else:
            # Ties keep first-bid priority from previous auction.
            self.round_winner = self.last_auction_first_bidder

        self.add_action(
            f"Round {self.current_round} ends. "
            f"Player: {self.player.round_score} vs AI: {self.ai.round_score}"
        )
        self.add_action(f"Momentum: Player {self.player.momentum}")

        # Check win condition
        if abs(self.player.momentum) >= 10000:
            self.current_phase = GamePhase.GAME_OVER
            winner = "Player" if self.player.momentum >= 10000 else "AI"
            self.add_action(f"GAME OVER! {winner} wins!")
        else:
            self.current_phase = GamePhase.AUCTION
            self.start_auction()

    def start_auction(self):
        """Start the auction phase."""
        # Reveal 5 cards
        self.auction_state.revealed_cards = []
        for _ in range(5):
            if self.auction_deck:
                self.auction_state.revealed_cards.append(self.auction_deck.pop(0))

        self.auction_state.current_card_index = 0
        self.auction_state.first_bidder = self.round_winner if self.round_winner is not None else 0
        self.last_auction_first_bidder = self.auction_state.first_bidder
        self.auction_state.turn_index = 0
        self.auction_state.current_bid = 0
        self.auction_state.current_leader = -1
        self.auction_state.last_bidder = -1
        self.auction_state.player_spent = 0
        self.auction_state.ai_spent = 0
        self.auction_state.pending_human_joker_choice = False
        self.auction_state.is_active = True

        self.add_action(
            f"Auction phase started. {len(self.auction_state.revealed_cards)} cards revealed. "
            f"First bidder: {'Player' if self.auction_state.first_bidder == 0 else 'AI'}."
        )

    def get_current_auction_card(self) -> Optional[AuctionCard]:
        """Get the card currently being auctioned."""
        if not self.auction_state.is_active:
            return None
        idx = self.auction_state.current_card_index
        if idx < 0 or idx >= len(self.auction_state.revealed_cards):
            return None
        return self.auction_state.revealed_cards[idx]

    def get_min_next_bid(self) -> int:
        """Get the minimum legal next bid for the current auction card."""
        card = self.get_current_auction_card()
        if card is None:
            return 0
        if self.auction_state.current_bid == 0:
            return card.minimum_bid
        return self.auction_state.current_bid + card.minimum_bid

    def get_next_auction_bidder(self) -> int:
        """Get the next player who should bid (0=player, 1=ai)."""
        if not self.auction_state.is_active or self.auction_state.pending_human_joker_choice:
            return -1

        if self.auction_state.turn_index >= 4:
            return -1

        # Bid order per card: winner, loser, winner, loser
        first = self.auction_state.first_bidder
        order = [first, 1 - first, first, 1 - first]
        return order[self.auction_state.turn_index]

    def place_auction_bid(self, player_index: int, bid_amount: int) -> bool:
        """Place a bid in the auction."""
        if not self.auction_state.is_active:
            return False

        if player_index != self.get_next_auction_bidder():
            return False

        card = self.get_current_auction_card()
        if card is None:
            return False

        # Check if bid is legal.
        min_next_bid = self.get_min_next_bid()

        if bid_amount < min_next_bid:
            return False

        # Place the bid
        self.auction_state.current_bid = bid_amount
        self.auction_state.current_leader = player_index
        self.auction_state.last_bidder = player_index
        self.auction_state.turn_index += 1

        bidder_name = "Player" if player_index == 0 else "AI"
        self.add_action(f"{bidder_name} bids {bid_amount} on {card}")

        if self.auction_state.turn_index >= 4:
            self._resolve_current_auction_card()

        return True

    def pass_auction_bid(self, player_index: int) -> bool:
        """Pass on the current auction bid."""
        if not self.auction_state.is_active:
            return False

        if player_index != self.get_next_auction_bidder():
            return False

        bidder_name = "Player" if player_index == 0 else "AI"
        card = self.get_current_auction_card()
        self.add_action(f"{bidder_name} passes on {card}")

        self.auction_state.turn_index += 1

        # If a bidder exists and the opponent passes, award immediately.
        if self.auction_state.current_leader != -1 and player_index != self.auction_state.current_leader:
            self._resolve_current_auction_card()
        elif self.auction_state.turn_index >= 4:
            self._resolve_current_auction_card()

        return True

    def _resolve_current_auction_card(self):
        """Resolve the current auction card after 4 turns."""
        card = self.get_current_auction_card()
        if card is None:
            self._finish_auction()
            return

        if self.auction_state.current_leader == -1:
            self.add_action(f"{card} is unsold.")
        else:
            winner_index = self.auction_state.current_leader
            winner = self.player if winner_index == 0 else self.ai
            winning_bid = self.auction_state.current_bid
            self._apply_auction_card(winner_index, card)

            if winner_index == 0:
                self.auction_state.player_spent += winning_bid
            else:
                self.auction_state.ai_spent += winning_bid

            self.add_action(f"{winner.name} won {card} for {winning_bid} momentum")

        self.auction_state.current_card_index += 1

        if self.auction_state.current_card_index >= len(self.auction_state.revealed_cards):
            self._finish_auction()
            return

        self.auction_state.current_bid = 0
        self.auction_state.current_leader = -1
        self.auction_state.last_bidder = -1
        self.auction_state.turn_index = 0

    def _apply_auction_card(self, winner_index: int, card: AuctionCard):
        """Apply a won auction card to the winner's inventory."""
        player = self.player if winner_index == 0 else self.ai

        if card.is_joker and card.joker_type is not None:
            player.jokers.append(Joker(type=card.joker_type))

            if winner_index == 1 and len(player.jokers) > 5:
                # AI auto-removes lowest value joker when over cap.
                self._auto_trim_ai_jokers()

            if winner_index == 0 and len(player.jokers) > 5:
                self.auction_state.pending_human_joker_choice = True

        elif card.is_planet and card.planet_type is not None:
            player.planets.append(card.planet_type)

    def _auto_trim_ai_jokers(self):
        """Auto-discard AI's lowest value joker when over cap."""
        while len(self.ai.jokers) > 5:
            lowest = min(self.ai.jokers, key=lambda j: self._ai_joker_value(j.type))
            self.ai.jokers.remove(lowest)
            self.add_action(f"AI discards joker {lowest} to stay at 5 jokers")

    @staticmethod
    def _ai_joker_value(jtype: JokerType) -> int:
        """Rough value ordering for AI joker inventory trimming."""
        value_map = {
            JokerType.FAMILY: 60,
            JokerType.RAINBOW: 55,
            JokerType.COPYCAT: 50,
            JokerType.THE_TRIBE: 45,
            JokerType.THE_ORDER: 45,
            JokerType.ABSTRACT: 40,
            JokerType.BANNER: 35,
            JokerType.EVEN_STEVEN: 35,
            JokerType.ODD_TODD: 35,
            JokerType.THE_DUO: 30,
            JokerType.THE_GREEDY: 25,
            JokerType.THE_LOVER: 25,
            JokerType.THE_PROTECTOR: 25,
            JokerType.THE_CHAIRMAN: 25,
            JokerType.SCRAPPY: 20,
            JokerType.STRAITJACKET: 20,
            JokerType.BLACK_HOLE: 18,
            JokerType.TAX_MAN: 18,
            JokerType.TRADE_INSIDER: 18,
            JokerType.COPYRIGHT: 18,
            JokerType.SHORTCUT: 16,
            JokerType.FOUR_FINGERS: 16,
            JokerType.UNIFORM: 15,
            JokerType.SMEAR: 15,
        }
        return value_map.get(jtype, 10)

    def discard_human_joker(self, joker_index: int) -> bool:
        """Discard one human joker after exceeding the joker cap."""
        if not self.auction_state.pending_human_joker_choice:
            return False

        if joker_index < 0 or joker_index >= len(self.player.jokers):
            return False

        removed = self.player.jokers.pop(joker_index)
        self.auction_state.pending_human_joker_choice = False
        self.add_action(f"Player discards joker {removed} to stay at 5 jokers")
        return True

    def _finish_auction(self):
        """Finish the auction, settle momentum, and start next round."""
        if self.auction_state.pending_human_joker_choice:
            return

        # Human spending lowers momentum, AI spending raises momentum.
        self.player.momentum = (
            self.player.momentum
            - self.auction_state.player_spent
            + self.auction_state.ai_spent
        )
        self.ai.momentum = -self.player.momentum

        self.add_action(
            f"Auction settles: Player spent {self.auction_state.player_spent}, "
            f"AI spent {self.auction_state.ai_spent}. Momentum now {self.player.momentum}."
        )

        if abs(self.player.momentum) >= 10000:
            self.current_phase = GamePhase.GAME_OVER
            winner = "Player" if self.player.momentum >= 10000 else "AI"
            self.add_action(f"GAME OVER! {winner} wins!")
            self.auction_state.is_active = False
            return

        self.auction_state.is_active = False

        self.current_round += 1
        self.current_set = 1
        self.current_phase = GamePhase.ROUND_START
        self.start_set()

    def add_action(self, action: str):
        """Add an action to the log."""
        self.action_log.append(action)

    def get_game_status(self) -> str:
        """Get human-readable game status."""
        return (
            f"Round {self.current_round}, Set {self.current_set} | "
            f"Player {self.player.round_score} vs AI {self.ai.round_score} | "
            f"Momentum: {self.player.momentum}"
        )

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.current_phase == GamePhase.GAME_OVER
