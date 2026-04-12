"""Hand ranking and score calculation for the standalone simulator."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .models import (
    Card,
    HandRank,
    HandResult,
    JokerCard,
    JokerType,
    Planet,
    PlayerState,
    Rank,
    ScoreResult,
    Suit,
)


@dataclass(frozen=True)
class JokerEffect:
    chips: int = 0
    mult: int = 0
    x_mult: float = 1.0


class HandEvaluator:
    """Evaluate poker hands, including the custom joker modifiers."""

    @staticmethod
    def best_rank_hand(
        cards: Sequence[Card],
        player: Optional[PlayerState] = None,
        disabled_joker_ids: Optional[Iterable[int]] = None,
    ) -> HandResult:
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards")

        disabled_set = set(disabled_joker_ids or [])
        best_result: Optional[HandResult] = None
        best_key: Tuple[int, int, int] = (-1, -1, -1)

        for combo in combinations(cards, 5):
            result = HandEvaluator.evaluate_five_card_hand(list(combo), player, None, disabled_set)
            key = (
                result.hand_rank.rank_value(),
                result.high_card.order(),
                result.score,
            )
            if key > best_key:
                best_key = key
                best_result = result

        if best_result is None:
            raise RuntimeError("Failed to evaluate hand")
        return best_result

    @staticmethod
    def best_scoring_hand(
        cards: Sequence[Card],
        player: PlayerState,
        opponent: Optional[PlayerState] = None,
        disabled_joker_ids: Optional[Iterable[int]] = None,
        track_contributions: bool = False,
    ) -> HandResult:
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards")

        disabled_set = set(disabled_joker_ids or [])
        best_result: Optional[HandResult] = None
        best_score = -1
        best_key: Tuple[int, int] = (-1, -1)

        for combo in combinations(cards, 5):
            result = HandEvaluator.evaluate_five_card_hand(
                list(combo),
                player,
                opponent,
                disabled_set,
                track_contributions=False,
            )
            key = (result.score, result.hand_rank.rank_value())
            if key > best_key:
                best_key = key
                best_score = result.score
                best_result = result

        if best_result is None:
            raise RuntimeError("Failed to evaluate scoring hand")

        if track_contributions:
            best_result = HandEvaluator.evaluate_five_card_hand(
                list(best_result.cards),
                player,
                opponent,
                disabled_set,
                track_contributions=True,
            )

        return best_result

    @staticmethod
    def evaluate_five_card_hand(
        cards: List[Card],
        player: Optional[PlayerState] = None,
        opponent: Optional[PlayerState] = None,
        disabled_joker_ids: Optional[Iterable[int]] = None,
        track_contributions: bool = False,
    ) -> HandResult:
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")

        disabled_set = set(disabled_joker_ids or [])
        sorted_cards = sorted(cards, key=lambda card: card.rank.order(), reverse=True)
        rank_counts = Counter(card.rank for card in sorted_cards)
        ordered_counts = sorted(rank_counts.items(), key=lambda item: (item[1], item[0].order()), reverse=True)

        active_jokers = HandEvaluator._active_jokers(player, disabled_set) if player else []
        normalized_suits = [HandEvaluator._normalize_suit(card.suit, active_jokers) for card in sorted_cards]
        is_flush = len(set(normalized_suits)) == 1
        if not is_flush and any(joker.joker_type == JokerType.FOUR_FINGERS for joker in active_jokers):
            is_flush = max(Counter(normalized_suits).values()) >= 4

        ranks = [card.rank.order() for card in sorted_cards]
        is_straight = HandEvaluator._is_straight(ranks)
        if not is_straight and any(joker.joker_type == JokerType.SHORTCUT for joker in active_jokers):
            is_straight = HandEvaluator._is_shortcut_straight(ranks)

        if is_straight and is_flush:
            hand_rank = HandRank.STRAIGHT_FLUSH
            high_card = sorted_cards[0].rank
        elif ordered_counts[0][1] == 4:
            hand_rank = HandRank.FOUR_OF_A_KIND
            high_card = ordered_counts[0][0]
        elif ordered_counts[0][1] == 3 and ordered_counts[1][1] == 2:
            hand_rank = HandRank.FULL_HOUSE
            high_card = ordered_counts[0][0]
        elif is_flush:
            hand_rank = HandRank.FLUSH
            high_card = sorted_cards[0].rank
        elif is_straight:
            hand_rank = HandRank.STRAIGHT
            high_card = sorted_cards[0].rank
        elif ordered_counts[0][1] == 3:
            hand_rank = HandRank.THREE_OF_A_KIND
            high_card = ordered_counts[0][0]
        elif ordered_counts[0][1] == 2 and ordered_counts[1][1] == 2:
            hand_rank = HandRank.TWO_PAIR
            high_card = ordered_counts[0][0]
        elif ordered_counts[0][1] == 2:
            hand_rank = HandRank.PAIR
            high_card = ordered_counts[0][0]
        else:
            hand_rank = HandRank.HIGH_CARD
            high_card = sorted_cards[0].rank

        score_result = None
        final_score = 0
        if player is not None:
            score_result = ScoreCalculator.calculate_score(
                hand_cards=sorted_cards,
                hand_rank=hand_rank,
                player=player,
                opponent=opponent,
                disabled_joker_ids=disabled_set,
                track_contributions=track_contributions,
            )
            final_score = score_result.final_score

        return HandResult(
            cards=sorted_cards,
            hand_rank=hand_rank,
            high_card=high_card,
            kicker_ranks=[rank for rank, count in ordered_counts[1:]],
            score=final_score,
            score_result=score_result,
        )

    @staticmethod
    def _active_jokers(player: Optional[PlayerState], disabled_set: set[int]) -> List[JokerCard]:
        if player is None:
            return []
        return [joker for joker in player.jokers if joker.joker_id not in disabled_set]

    @staticmethod
    def _normalize_suit(suit: Suit, active_jokers: Sequence[JokerCard]) -> Suit:
        has_uniform = any(joker.joker_type == JokerType.UNIFORM for joker in active_jokers)
        has_smear = any(joker.joker_type == JokerType.SMEAR for joker in active_jokers)

        normalized = suit
        if has_uniform and normalized in (Suit.SPADES, Suit.CLUBS):
            normalized = Suit.CLUBS
        if has_smear and normalized in (Suit.HEARTS, Suit.DIAMONDS):
            normalized = Suit.HEARTS
        return normalized

    @staticmethod
    def _is_straight(ranks: Sequence[int]) -> bool:
        unique = sorted(set(ranks))
        if len(unique) != 5:
            return False
        if unique[-1] - unique[0] == 4:
            return True
        return unique == [2, 3, 4, 5, 14]

    @staticmethod
    def _is_shortcut_straight(ranks: Sequence[int]) -> bool:
        unique = sorted(set(ranks))
        if len(unique) != 5:
            return False
        if HandEvaluator._is_straight(unique):
            return True
        return unique[-1] - unique[0] <= 5


class ScoreCalculator:
    """Implement the game scoring formula and joker attribution."""

    @staticmethod
    def _planet_applies_to_hand(planet: Planet, hand_rank: HandRank) -> bool:
        planet_name = planet.hand_type
        if hand_rank == HandRank.STRAIGHT_FLUSH:
            return planet_name in {"Straight Flush", "Straight", "Flush"}
        return planet_name == ScoreCalculator._hand_label(hand_rank)

    @staticmethod
    def calculate_score(
        hand_cards: Sequence[Card],
        hand_rank: HandRank,
        player: PlayerState,
        opponent: Optional[PlayerState] = None,
        disabled_joker_ids: Optional[Iterable[int]] = None,
        track_contributions: bool = False,
    ) -> ScoreResult:
        disabled_set = set(disabled_joker_ids or [])
        active_jokers = [joker for joker in player.jokers if joker.joker_id not in disabled_set]
        active_opponent_jokers = []
        if opponent is not None:
            active_opponent_jokers = [joker for joker in opponent.jokers if joker.joker_id not in disabled_set]

        base_chips = hand_rank.base_chips()
        base_mult = hand_rank.base_mult()

        opponent_has_black_hole = any(joker.joker_type == JokerType.BLACK_HOLE for joker in active_opponent_jokers)
        card_chips = 0
        for card in hand_cards:
            if opponent_has_black_hole and card.rank == Rank.ACE:
                continue
            card_chips += card.chip_value()

        planet_chips = 0
        planet_mult = 0
        hand_label = ScoreCalculator._hand_label(hand_rank)
        for planet, level in player.planets.items():
            if ScoreCalculator._planet_applies_to_hand(planet, hand_rank):
                planet_chips += level * planet.chip_bonus
                planet_mult += level * planet.mult_bonus

        joker_effects = ScoreCalculator._resolve_joker_effects(
            hand_cards=hand_cards,
            hand_rank=hand_rank,
            player=player,
            opponent=opponent,
            active_jokers=active_jokers,
        )

        joker_chip_bonus = sum(effect.chips for effect in joker_effects)
        joker_mult_bonus = sum(effect.mult for effect in joker_effects)
        joker_x_mult = 1.0
        for effect in joker_effects:
            joker_x_mult *= effect.x_mult

        total_chips = base_chips + planet_chips + card_chips + joker_chip_bonus
        total_mult = base_mult + planet_mult + joker_mult_bonus
        final_score = int(total_chips * total_mult * joker_x_mult)

        contributions_by_id: Dict[int, int] = {}
        types_by_id: Dict[int, str] = {}
        if track_contributions and active_jokers:
            for joker in active_jokers:
                reduced_disabled = set(disabled_set)
                reduced_disabled.add(joker.joker_id)
                reduced_score = ScoreCalculator.calculate_score(
                    hand_cards=hand_cards,
                    hand_rank=hand_rank,
                    player=player,
                    opponent=opponent,
                    disabled_joker_ids=reduced_disabled,
                    track_contributions=False,
                ).final_score
                contributions_by_id[joker.joker_id] = final_score - reduced_score
                types_by_id[joker.joker_id] = joker.joker_type.value

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
            hand_rank=hand_rank,
            breakdown={
                "base": base_chips,
                "planets": planet_chips,
                "cards": card_chips,
                "joker_chips": joker_chip_bonus,
                "joker_mult": joker_mult_bonus,
            },
            joker_contributions_by_id=contributions_by_id,
            joker_types_by_id=types_by_id,
        )

    @staticmethod
    def _hand_label(hand_rank: HandRank) -> str:
        return {
            HandRank.HIGH_CARD: "High Card",
            HandRank.PAIR: "Pair",
            HandRank.TWO_PAIR: "Two Pair",
            HandRank.THREE_OF_A_KIND: "Three of a Kind",
            HandRank.STRAIGHT: "Straight",
            HandRank.FLUSH: "Flush",
            HandRank.FULL_HOUSE: "Full House",
            HandRank.FOUR_OF_A_KIND: "Four of a Kind",
            HandRank.STRAIGHT_FLUSH: "Straight Flush",
        }[hand_rank]

    @staticmethod
    def _resolve_joker_effects(
        hand_cards: Sequence[Card],
        hand_rank: HandRank,
        player: PlayerState,
        opponent: Optional[PlayerState],
        active_jokers: Sequence[JokerCard],
    ) -> List[JokerEffect]:
        resolved_by_index: List[JokerEffect] = []

        for index in range(len(active_jokers) - 1, -1, -1):
            joker = active_jokers[index]
            if joker.joker_type == JokerType.COPYCAT and resolved_by_index:
                effect = resolved_by_index[-1]
            else:
                effect = ScoreCalculator._joker_effect_for_type(
                    joker_type=joker.joker_type,
                    hand_cards=hand_cards,
                    hand_rank=hand_rank,
                    player=player,
                    opponent=opponent,
                    active_jokers=active_jokers,
                )
            resolved_by_index.append(effect)

        return list(reversed(resolved_by_index))

    @staticmethod
    def _joker_effect_for_type(
        joker_type: JokerType,
        hand_cards: Sequence[Card],
        hand_rank: HandRank,
        player: PlayerState,
        opponent: Optional[PlayerState],
        active_jokers: Sequence[JokerCard],
    ) -> JokerEffect:
        normalized_suits = [HandEvaluator._normalize_suit(card.suit, active_jokers) for card in hand_cards]

        if joker_type == JokerType.BANNER:
            return JokerEffect(chips=20 * max(0, player.discards_remaining))
        if joker_type == JokerType.ABSTRACT:
            return JokerEffect(mult=1 * len(player.jokers))
        if joker_type == JokerType.EVEN_STEVEN:
            even_cards = sum(1 for card in hand_cards if card.rank.order() % 2 == 0)
            return JokerEffect(mult=2 * even_cards)
        if joker_type == JokerType.ODD_TODD:
            odd_cards = sum(1 for card in hand_cards if card.rank.order() % 2 == 1)
            return JokerEffect(mult=2 * odd_cards)
        if joker_type == JokerType.THE_DUO:
            if hand_rank in (HandRank.PAIR, HandRank.TWO_PAIR):
                return JokerEffect(chips=20)
            return JokerEffect()
        if joker_type == JokerType.THE_GREEDY:
            diamonds = sum(1 for suit in normalized_suits if suit == Suit.DIAMONDS)
            return JokerEffect(chips=10 * diamonds)
        if joker_type == JokerType.THE_LOVER:
            hearts = sum(1 for suit in normalized_suits if suit == Suit.HEARTS)
            return JokerEffect(chips=10 * hearts)
        if joker_type == JokerType.THE_PROTECTOR:
            spades = sum(1 for suit in normalized_suits if suit == Suit.SPADES)
            return JokerEffect(chips=10 * spades)
        if joker_type == JokerType.THE_CHAIRMAN:
            clubs = sum(1 for suit in normalized_suits if suit == Suit.CLUBS)
            return JokerEffect(chips=10 * clubs)
        if joker_type == JokerType.TAX_MAN and opponent is not None:
            opponent_face_cards = sum(
                1
                for card in opponent.hand
                if card.rank in {Rank.JACK, Rank.QUEEN, Rank.KING}
            )
            return JokerEffect(chips=10 * opponent_face_cards)
        if joker_type == JokerType.THE_TRIBE and hand_rank == HandRank.FLUSH:
            return JokerEffect(x_mult=2.0)
        if joker_type == JokerType.THE_ORDER and hand_rank == HandRank.STRAIGHT:
            return JokerEffect(x_mult=2.0)
        if joker_type == JokerType.FAMILY and hand_rank == HandRank.FOUR_OF_A_KIND:
            return JokerEffect(x_mult=4.0)
        if joker_type == JokerType.RAINBOW:
            if len({card.suit for card in hand_cards}) == 4:
                return JokerEffect(x_mult=2.0)
            return JokerEffect()
        return JokerEffect()

