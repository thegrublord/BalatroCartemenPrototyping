"""Game rules and scoring system."""

from typing import List, Tuple
from collections import Counter
from itertools import combinations
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
    def evaluate_hand_with_modifiers(
        cards: List[Card],
        player: Player,
        disabled_jokers: List[Joker] = None,
    ) -> PokerHand:
        """Evaluate a 5-card hand with joker rule modifiers."""
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")

        if disabled_jokers is None:
            disabled_jokers = []

        effective_joker_types = PokerHandEvaluator._resolve_effective_joker_types(player, disabled_jokers)
        has_uniform = JokerType.UNIFORM in effective_joker_types
        has_smear = JokerType.SMEAR in effective_joker_types

        # Sort by rank for easier evaluation
        sorted_cards = sorted(cards, key=lambda c: c.rank.rank_order(), reverse=True)

        # Check for flush with suit-normalization jokers
        normalized_suits = [
            PokerHandEvaluator._normalize_suit_with_effects(c.suit, has_uniform, has_smear) for c in sorted_cards
        ]
        suit_counts = Counter(normalized_suits)
        is_flush = len(suit_counts) == 1

        has_four_fingers = JokerType.FOUR_FINGERS in effective_joker_types
        if not is_flush and has_four_fingers and suit_counts:
            is_flush = max(suit_counts.values()) >= 4

        # Check for straight with shortcut joker support
        ranks = sorted([c.rank.rank_order() for c in sorted_cards], reverse=True)
        is_straight = PokerHandEvaluator._is_straight(ranks)

        has_shortcut = JokerType.SHORTCUT in effective_joker_types
        if not is_straight and has_shortcut:
            is_straight = PokerHandEvaluator._is_shortcut_straight(ranks)

        # Count rank frequencies
        rank_counts = Counter([c.rank for c in sorted_cards])
        counts_list = sorted(rank_counts.items(), key=lambda x: (x[1], x[0].rank_order()), reverse=True)

        # Determine hand rank
        if is_straight and is_flush:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.STRAIGHT_FLUSH, high_card=sorted_cards[0].rank)
        elif counts_list[0][1] == 4:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.FOUR_OF_A_KIND, high_card=counts_list[0][0])
        elif counts_list[0][1] == 3 and counts_list[1][1] == 2:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.FULL_HOUSE, high_card=counts_list[0][0])
        elif is_flush:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.FLUSH, high_card=sorted_cards[0].rank)
        elif is_straight:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.STRAIGHT, high_card=sorted_cards[0].rank)
        elif counts_list[0][1] == 3:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.THREE_OF_A_KIND, high_card=counts_list[0][0])
        elif counts_list[0][1] == 2 and counts_list[1][1] == 2:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.TWO_PAIR, high_card=counts_list[0][0])
        elif counts_list[0][1] == 2:
            return PokerHand(cards=sorted_cards, hand_rank=HandRank.PAIR, high_card=counts_list[0][0])
        return PokerHand(cards=sorted_cards, hand_rank=HandRank.HIGH_CARD, high_card=sorted_cards[0].rank)

    @staticmethod
    def _is_shortcut_straight(ranks: List[int]) -> bool:
        """Shortcut straight: any 4 cards can form a sequence with one optional gap."""
        unique_ranks = set(ranks)
        if 14 in unique_ranks:
            unique_ranks.add(1)  # Ace-low compatibility

        ordered = sorted(unique_ranks)
        if len(ordered) < 4:
            return False

        for combo in combinations(ordered, 4):
            if combo[-1] - combo[0] <= 4:
                return True
        return False

    @staticmethod
    def _normalize_suit(suit: Suit, active_jokers: List[Joker]) -> Suit:
        """Normalize suit for Uniform/Smear rules."""
        has_uniform = any(j.type == JokerType.UNIFORM for j in active_jokers)
        has_smear = any(j.type == JokerType.SMEAR for j in active_jokers)

        return PokerHandEvaluator._normalize_suit_with_effects(suit, has_uniform, has_smear)

    @staticmethod
    def _normalize_suit_with_effects(suit: Suit, has_uniform: bool, has_smear: bool) -> Suit:
        """Normalize suit using pre-resolved effect flags."""

        normalized = suit
        if has_uniform and normalized in (Suit.SPADES, Suit.CLUBS):
            normalized = Suit.CLUBS
        if has_smear and normalized in (Suit.HEARTS, Suit.DIAMONDS):
            normalized = Suit.HEARTS
        return normalized

    @staticmethod
    def _resolve_effective_joker_types(player: Player, disabled_jokers: List[Joker]) -> List[JokerType]:
        """Resolve effective joker types in player order, including COPYCAT right-neighbor copying."""
        disabled_list = disabled_jokers or []
        ordered = player.jokers
        cache = {}

        def resolve_index(index: int, visiting: set) -> JokerType:
            if index in cache:
                return cache[index]
            if index < 0 or index >= len(ordered):
                return None

            joker = ordered[index]
            if joker in disabled_list:
                cache[index] = None
                return None

            if index in visiting:
                return None

            if joker.type != JokerType.COPYCAT:
                cache[index] = joker.type
                return cache[index]

            copied = resolve_index(index + 1, visiting | {index})
            cache[index] = copied
            return copied

        resolved: List[JokerType] = []
        for idx, joker in enumerate(ordered):
            if joker in disabled_list:
                continue
            effective = resolve_index(idx, set())
            if effective is not None:
                resolved.append(effective)

        return resolved

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

    @staticmethod
    def find_best_hand_with_modifiers(
        cards: List[Card],
        player: Player,
        disabled_jokers: List[Joker] = None,
    ) -> PokerHand:
        """Find best 5-card hand while applying joker rule modifiers."""
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards")

        if disabled_jokers is None:
            disabled_jokers = []

        best_hand = None
        best_rank = -1
        for combo in combinations(cards, 5):
            hand = PokerHandEvaluator.evaluate_hand_with_modifiers(list(combo), player, disabled_jokers)
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
        opponent_hand_cards: List[Card] = None,
        disabled_jokers: List[Joker] = None,
        opponent_disabled_jokers: List[Joker] = None,
    ) -> ScoreResult:
        """Calculate final score for a played hand."""
        if disabled_jokers is None:
            disabled_jokers = []
        if opponent_disabled_jokers is None:
            opponent_disabled_jokers = []

        # Base chips and mult from hand rank
        base_chips = hand.hand_rank.base_chips()
        base_mult = hand.hand_rank.base_mult()

        # Card chips (Black Hole modifies opponent aces)
        opponent_active = []
        if opponent:
            opponent_active = [j for j in opponent.jokers if j not in opponent_disabled_jokers]
        opponent_has_black_hole = any(j.type == JokerType.BLACK_HOLE for j in opponent_active)

        card_chips = 0
        for c in hand.cards:
            if opponent_has_black_hole and c.rank == Rank.ACE:
                continue
            card_chips += c.chip_value()

        # planets modify hand type scores
        planet_chips = 0
        planet_mult = 0
        hand_type_name = hand.hand_rank.name.replace("_", " ").lower()
        for planet_enum in Planet:
            if planet_enum.hand_type().lower() == hand_type_name:
                level = player.planet_level(planet_enum)
                planet_chips += level * planet_enum.chip_bonus()
                planet_mult += level * planet_enum.mult_bonus()

        # Calculate joker bonuses
        joker_chip_bonus = 0
        joker_mult_bonus = 0
        joker_x_mult = 1.0

        available_joker_types = PokerHandEvaluator._resolve_effective_joker_types(player, disabled_jokers)
        has_uniform = JokerType.UNIFORM in available_joker_types
        has_smear = JokerType.SMEAR in available_joker_types

        def normalize_suit_for_player(suit: Suit) -> Suit:
            return PokerHandEvaluator._normalize_suit_with_effects(suit, has_uniform, has_smear)

        for jtype in available_joker_types:

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
                diamonds = sum(1 for c in hand.cards if normalize_suit_for_player(c.suit) == Suit.DIAMONDS)
                joker_chip_bonus += 10 * diamonds

            elif jtype == JokerType.THE_LOVER:
                hearts = sum(1 for c in hand.cards if normalize_suit_for_player(c.suit) == Suit.HEARTS)
                joker_chip_bonus += 10 * hearts

            elif jtype == JokerType.THE_PROTECTOR:
                spades = sum(1 for c in hand.cards if normalize_suit_for_player(c.suit) == Suit.SPADES)
                joker_chip_bonus += 10 * spades

            elif jtype == JokerType.THE_CHAIRMAN:
                clubs = sum(1 for c in hand.cards if normalize_suit_for_player(c.suit) == Suit.CLUBS)
                joker_chip_bonus += 10 * clubs

            # Rare jokers
            elif jtype == JokerType.TAX_MAN and opponent:
                if opponent_hand_cards:
                    opponent_face_cards = sum(
                        1 for c in opponent_hand_cards if c.rank in (Rank.JACK, Rank.QUEEN, Rank.KING)
                    )
                    joker_chip_bonus += 10 * opponent_face_cards

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
