"""Game rules and scoring system."""

from typing import List, Tuple
from collections import Counter
from game.models import (
    Card, Rank, Suit, HandRank, PokerHand, Player, Joker, JokerType,
    Planet, ScoreResult
)


class PokerHandEvaluator:
    """Evaluates 5-card poker hands."""

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> PokerHand:
        """Evaluate a 5-card hand and return PokerHand with rank."""
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")

        # Sort by rank for easier evaluation
        sorted_cards = sorted(cards, key=lambda c: c.rank.rank_order(), reverse=True)

        # Check for flush
        suits = [c.suit for c in sorted_cards]
        is_flush = len(set(suits)) == 1

        # Check for straight
        ranks = sorted([c.rank.rank_order() for c in sorted_cards], reverse=True)
        is_straight = PokerHandEvaluator._is_straight(ranks)

        # Count rank frequencies
        rank_counts = Counter([c.rank for c in sorted_cards])
        counts_list = sorted(rank_counts.items(), key=lambda x: (x[1], x[0].rank_order()), reverse=True)

        # Determine hand rank
        if is_straight and is_flush:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.STRAIGHT_FLUSH,
                high_card=sorted_cards[0].rank
            )
        elif counts_list[0][1] == 4:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.FOUR_OF_A_KIND,
                high_card=counts_list[0][0]
            )
        elif counts_list[0][1] == 3 and counts_list[1][1] == 2:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.FULL_HOUSE,
                high_card=counts_list[0][0]
            )
        elif is_flush:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.FLUSH,
                high_card=sorted_cards[0].rank
            )
        elif is_straight:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.STRAIGHT,
                high_card=sorted_cards[0].rank
            )
        elif counts_list[0][1] == 3:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.THREE_OF_A_KIND,
                high_card=counts_list[0][0]
            )
        elif counts_list[0][1] == 2 and counts_list[1][1] == 2:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.TWO_PAIR,
                high_card=counts_list[0][0]
            )
        elif counts_list[0][1] == 2:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.PAIR,
                high_card=counts_list[0][0]
            )
        else:
            return PokerHand(
                cards=sorted_cards,
                hand_rank=HandRank.HIGH_CARD,
                high_card=sorted_cards[0].rank
            )

    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if 5 ranks form a straight."""
        sorted_ranks = sorted(ranks, reverse=True)
        # Normal straight
        if sorted_ranks[0] - sorted_ranks[4] == 4 and len(set(sorted_ranks)) == 5:
            return True
        # Ace-low straight (A,2,3,4,5)
        if sorted_ranks == [14, 5, 4, 3, 2]:
            return True
        return False

    @staticmethod
    def find_best_hand(cards: List[Card]) -> PokerHand:
        """Find the best 5-card hand from 6+ cards."""
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards")

        # Generate all 5-card combinations
        best_hand = None
        best_rank = -1

        from itertools import combinations
        for combo in combinations(cards, 5):
            hand = PokerHandEvaluator.evaluate_hand(list(combo))
            rank_value = hand.hand_rank.rank_value()

            if rank_value > best_rank:
                best_rank = rank_value
                best_hand = hand

        return best_hand


class ScoringRules:
    """Implements game scoring with jokers and planets."""

    @staticmethod
    def calculate_score(
        hand: PokerHand,
        player: Player,
        opponent: Player = None,
        disabled_jokers: List[JokerType] = None
    ) -> ScoreResult:
        """Calculate final score for a played hand."""
        if disabled_jokers is None:
            disabled_jokers = []

        # Base chips and mult from hand rank
        base_chips = hand.hand_rank.base_chips()
        base_mult = hand.hand_rank.base_mult()

        # Card chips
        card_chips = sum(c.chip_value() for c in hand.cards)

        # planets modify hand type scores
        planet_name = hand.hand_rank.value[0]
        planet_chips = 0
        planet_mult = 0
        for planet_enum in Planet:
            if planet_enum.hand_type() == hand.hand_rank.name.replace("_", " "):
                level = player.planet_level(planet_enum)
                planet_chips += level * planet_enum.chip_bonus()
                planet_mult += level * planet_enum.mult_bonus()

        # Calculate joker bonuses
        joker_chip_bonus = 0
        joker_mult_bonus = 0
        joker_x_mult = 1.0

        available_jokers = [j for j in player.jokers if j.type not in disabled_jokers]

        for joker in available_jokers:
            jtype = joker.type

            # Common jokers
            if jtype == JokerType.BANNER:
                joker_chip_bonus += 20 * player.discard_actions_remaining()

            elif jtype == JokerType.ABSTRACT:
                joker_mult_bonus += 2 * len(player.jokers)

            elif jtype == JokerType.EVEN_STEVEN:
                even_cards = sum(1 for c in hand.cards if c.rank.rank_order() % 2 == 0)
                joker_mult_bonus += 2 * even_cards

            elif jtype == JokerType.ODD_TODD:
                odd_cards = sum(1 for c in hand.cards if c.rank.rank_order() % 2 == 1)
                joker_mult_bonus += 2 * odd_cards

            elif jtype == JokerType.THE_DUO:
                if hand.hand_rank == HandRank.PAIR or hand.hand_rank == HandRank.TWO_PAIR:
                    joker_chip_bonus += 20

            elif jtype == JokerType.THE_GREEDY:
                diamonds = sum(1 for c in hand.cards if c.suit == Suit.DIAMONDS)
                joker_chip_bonus += 10 * diamonds

            elif jtype == JokerType.THE_LOVER:
                hearts = sum(1 for c in hand.cards if c.suit == Suit.HEARTS)
                joker_chip_bonus += 10 * hearts

            elif jtype == JokerType.THE_PROTECTOR:
                spades = sum(1 for c in hand.cards if c.suit == Suit.SPADES)
                joker_chip_bonus += 10 * spades

            elif jtype == JokerType.THE_CHAIRMAN:
                clubs = sum(1 for c in hand.cards if c.suit == Suit.CLUBS)
                joker_chip_bonus += 10 * clubs

            # Rare jokers
            elif jtype == JokerType.TAX_MAN and opponent:
                # Need to track opponent's played hand - simplify for now
                pass

            elif jtype == JokerType.THE_TRIBE:
                if hand.hand_rank == HandRank.FLUSH:
                    joker_x_mult *= 2

            elif jtype == JokerType.THE_ORDER:
                if hand.hand_rank == HandRank.STRAIGHT:
                    joker_x_mult *= 2

            # Legendary jokers
            elif jtype == JokerType.FAMILY:
                if hand.hand_rank == HandRank.FOUR_OF_A_KIND:
                    joker_x_mult *= 4

            elif jtype == JokerType.RAINBOW:
                suits = set(c.suit for c in hand.cards)
                if len(suits) == 4:
                    joker_x_mult *= 4

        # Final calculation
        total_chips = base_chips + planet_chips + card_chips + joker_chip_bonus
        total_mult = base_mult + planet_mult + joker_mult_bonus
        final_score = int(total_chips * total_mult * joker_x_mult)

        return ScoreResult(
            base_chips=base_chips,
            base_mult=base_mult,
            card_chips=card_chips,
            planet_chips=planet_chips,
            planet_mult=planet_mult,
            joker_chip_bonus=joker_chip_bonus,
            joker_mult_bonus=joker_mult_bonus,
            joker_x_mult=joker_x_mult,
            final_score=final_score,
            hand_rank=hand.hand_rank,
            breakdown={
                "base": base_chips,
                "planets": planet_chips,
                "cards": card_chips,
                "joker_chips": joker_chip_bonus
            }
        )

    @staticmethod
    def get_hand_name(hand_rank: HandRank) -> str:
        """Get human-readable hand name."""
        names = {
            HandRank.HIGH_CARD: "High Card",
            HandRank.PAIR: "Pair",
            HandRank.TWO_PAIR: "Two Pair",
            HandRank.THREE_OF_A_KIND: "Three of a Kind",
            HandRank.STRAIGHT: "Straight",
            HandRank.FLUSH: "Flush",
            HandRank.FULL_HOUSE: "Full House",
            HandRank.FOUR_OF_A_KIND: "Four of a Kind",
            HandRank.STRAIGHT_FLUSH: "Straight Flush"
        }
        return names.get(hand_rank, str(hand_rank))
