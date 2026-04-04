"""AI decision logic for game play."""

import random
from typing import List, Tuple
from game.models import Card, Player, Joker, JokerType, PokerHand
from game.rules import PokerHandEvaluator, ScoringRules


class AIPlayer:
    """AI opponent logic."""

    def __init__(self, player: Player):
        self.player = player

    def decide_play_or_discard(self, opponent: Player) -> Tuple[bool, List[Card]]:
        """
        Decide whether to play the current hand or discard.
        Returns (play, cards_to_discard)
        If play=True, should play best hand.
        If play=False, cards_to_discard contains cards to discard.
        """
        if not self.player.can_discard():
            # Must play
            return (True, [])

        # Evaluate current best hand
        best_hand = PokerHandEvaluator.find_best_hand(self.player.hand)
        current_score = ScoringRules.calculate_score(best_hand, self.player, opponent)

        # Simple heuristic: if can improve by discarding, do it
        if len(self.player.hand) > 5:
            # Try discarding each non-contributing card
            unused_cards = [c for c in self.player.hand if c not in best_hand.cards]

            if unused_cards and random.random() < 0.6:  # 60% chance to discard
                # Discard the weakest cards
                return (False, unused_cards[:2])

        return (True, [])

    def select_playing_hand(self) -> List[Card]:
        """Select 5 cards to play from the 8-card hand."""
        best_hand = PokerHandEvaluator.find_best_hand(self.player.hand)
        return best_hand.cards

    def place_auction_bid(self, game_state, opponent: Player) -> Tuple[bool, int]:
        """
        Decide whether to bid in auction and how much.
        Returns (should_bid, bid_amount)
        """
        card = game_state.get_current_auction_card()
        if card is None:
            return (False, 0)

        min_raise = game_state.get_min_next_bid()

        # Evaluate card value
        card_value = self._evaluate_auction_card(card, opponent)

        # No hard cap by momentum in this rule set. Bid only if value supports it.
        if card_value >= min_raise:
            extra_raise = 0
            if card_value > min_raise and random.random() < 0.45:
                extra_raise = min(card.minimum_bid, card_value - min_raise)
            bid_amount = min_raise + extra_raise
            return (True, bid_amount)

        return (False, 0)

    def _evaluate_auction_card(self, card, opponent: Player) -> int:
        """Evaluate how valuable a card is to the AI."""
        value = 0

        if card.is_joker:
            jtype = card.joker_type

            # Basic value scoring
            if jtype == JokerType.BANNER:
                value = 20  # Discard economy
            elif jtype == JokerType.ABSTRACT:
                value = 15 * len(self.player.jokers)  # Scale with joker count
            elif jtype == JokerType.EVEN_STEVEN:
                value = 25  # Good multiplier
            elif jtype == JokerType.ODD_TODD:
                value = 25
            elif jtype == JokerType.THE_TRIBE:
                value = 30  # Strong if playing flushes
            elif jtype == JokerType.THE_ORDER:
                value = 30  # Strong if playing straights
            elif jtype == JokerType.FAMILY:
                value = 40  # Legendary is strong
            elif jtype == JokerType.RAINBOW:
                value = 40
            else:
                value = 15

        elif card.is_planet:
            # Planets are valuable for continuous scoring
            value = 30

        # Apply opponent disruption consideration
        if opponent.has_joker_type(JokerType.COPYRIGHT):
            value *= 0.8  # Reduce value if opponent can disable us

        return value
