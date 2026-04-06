"""Headless game engine for Balatro Certamen simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .auction_manager import AuctionManager, AuctionOutcome
from .hand_evaluator import HandEvaluator
from .models import Card, GameResult, JokerType, PlayerState, Rank, Suit


@dataclass
class RoundResult:
    round_index: int
    winner_index: int
    round_delta: int
    p1_score: int
    p2_score: int
    hand_types: List[str] = field(default_factory=list)


class GameEngine:
    """Simulate one full match between two AI players."""

    def __init__(self, seed: Optional[int] = None):
        import random

        self.random = random.Random(seed)
        self.seed = seed
        self.player_one = PlayerState(name="AI-1")
        self.player_two = PlayerState(name="AI-2")
        self.momentum = 0
        self.current_round = 0
        self.round_history: List[RoundResult] = []
        self.auction_manager = AuctionManager(self.random)

        self.player_one.deck = self._create_deck()
        self.player_two.deck = self._create_deck()

    def play_game(self, game_index: int = 0, max_rounds: int = 250) -> GameResult:
        round_winner_index = 0
        while abs(self.momentum) < 10000 and self.current_round < max_rounds:
            self.current_round += 1
            round_result = self.play_round(self.current_round, round_winner_index)
            self.round_history.append(round_result)

            if abs(self.momentum) >= 10000:
                break

            round_winner_index = round_result.winner_index
            self.play_auction(round_winner_index)
            if abs(self.momentum) >= 10000:
                break

        winner_player = self._winner_player()
        return GameResult(
            game_index=game_index,
            winner=winner_player.name,
            rounds_played=self.current_round,
            final_momentum=self.momentum,
            winner_joker_ids=[joker.joker_id for joker in winner_player.jokers],
            winner_joker_types=[joker.joker_type.value for joker in winner_player.jokers],
            p1_joker_ids=[joker.joker_id for joker in self.player_one.jokers],
            p2_joker_ids=[joker.joker_id for joker in self.player_two.jokers],
            p1_joker_types=[joker.joker_type.value for joker in self.player_one.jokers],
            p2_joker_types=[joker.joker_type.value for joker in self.player_two.jokers],
            winner_hand_frequency=dict(winner_player.hand_frequency),
            p1_hand_frequency=dict(self.player_one.hand_frequency),
            p2_hand_frequency=dict(self.player_two.hand_frequency),
            round_winners=["AI-1" if result.winner_index == 0 else "AI-2" for result in self.round_history],
        )

    def play_round(self, round_index: int, previous_round_winner: int) -> RoundResult:
        self.player_one.reset_for_round()
        self.player_two.reset_for_round()
        self._apply_round_discard_modifiers()

        self._deal_to_8(self.player_one)
        self._deal_to_8(self.player_two)

        round_scores = [0, 0]
        hand_types: List[str] = []

        for _ in range(3):
            self._maybe_discard_for_best_rank(self.player_one, self.player_two)
            self._maybe_discard_for_best_rank(self.player_two, self.player_one)

            p1_result = HandEvaluator.best_scoring_hand(self.player_one.hand, self.player_one, self.player_two, track_contributions=True)
            p2_result = HandEvaluator.best_scoring_hand(self.player_two.hand, self.player_two, self.player_one, track_contributions=True)

            self._apply_set_result(self.player_one, self.player_two, p1_result, p2_result)
            round_scores[0] += p1_result.score
            round_scores[1] += p2_result.score

            hand_types.append(p1_result.hand_rank.name)
            hand_types.append(p2_result.hand_rank.name)

            self._remove_played_cards(self.player_one, p1_result.cards)
            self._remove_played_cards(self.player_two, p2_result.cards)
            self._deal_to_8(self.player_one)
            self._deal_to_8(self.player_two)

        round_delta = round_scores[0] - round_scores[1]
        self.player_one.round_score = round_scores[0]
        self.player_two.round_score = round_scores[1]

        if round_delta > 0:
            self.momentum += round_delta
            winner_index = 0
        elif round_delta < 0:
            self.momentum += round_delta
            winner_index = 1
        else:
            winner_index = previous_round_winner

        self.player_one.momentum = self.momentum
        self.player_two.momentum = -self.momentum

        return RoundResult(
            round_index=round_index,
            winner_index=winner_index,
            round_delta=round_delta,
            p1_score=round_scores[0],
            p2_score=round_scores[1],
            hand_types=hand_types,
        )

    def play_auction(self, round_winner_index: int) -> AuctionOutcome:
        outcome = self.auction_manager.run_auction(
            self.player_one,
            self.player_two,
            round_winner_index,
            self.momentum,
        )
        self.momentum = outcome.momentum_delta
        self.player_one.momentum = self.momentum
        self.player_two.momentum = -self.momentum
        return outcome

    def _deal_to_8(self, player: PlayerState) -> None:
        while len(player.hand) < 8:
            if not player.deck:
                player.deck = self._create_deck()
            player.hand.append(player.deck.pop(0))

    def _maybe_discard_for_best_rank(self, player: PlayerState, opponent: PlayerState) -> None:
        if player.discards_remaining <= 0 or len(player.hand) < 5:
            return

        discard_indices = self._select_discard_indices(player, opponent)
        if not discard_indices:
            return

        for index in sorted(discard_indices, reverse=True):
            del player.hand[index]

        player.discards_remaining -= 1
        self._deal_to_8(player)

    def _apply_round_discard_modifiers(self) -> None:
        p1_scrappy = sum(1 for joker in self.player_one.jokers if joker.joker_type == JokerType.SCRAPPY)
        p2_scrappy = sum(1 for joker in self.player_two.jokers if joker.joker_type == JokerType.SCRAPPY)
        p1_jacketed = sum(1 for joker in self.player_two.jokers if joker.joker_type == JokerType.STRAITJACKET)
        p2_jacketed = sum(1 for joker in self.player_one.jokers if joker.joker_type == JokerType.STRAITJACKET)

        self.player_one.discards_remaining = max(0, 2 + p1_scrappy - p1_jacketed)
        self.player_two.discards_remaining = max(0, 2 + p2_scrappy - p2_jacketed)

    def _select_discard_indices(self, player: PlayerState, opponent: PlayerState) -> List[int]:
        # Start from non-scoring cards and choose the discard count that maximizes expected score.
        best_now = HandEvaluator.best_scoring_hand(player.hand, player, opponent)
        base_score = best_now.score
        hand_size = len(player.hand)

        scoring_set = set(best_now.cards)
        fallback_candidates = [i for i, card in enumerate(player.hand) if card not in scoring_set]
        if not fallback_candidates:
            fallback_candidates = list(range(hand_size))

        ranked = sorted(
            range(hand_size),
            key=lambda i: (i not in fallback_candidates, player.hand[i].rank.order()),
        )

        options: List[List[int]] = [[]]
        max_discard = min(3, hand_size - 5)
        for count in range(1, max_discard + 1):
            options.append(ranked[:count])

        best_option: List[int] = []
        best_expected = float(base_score)

        for option in options[1:]:
            expected = self._expected_score_after_discard(player, opponent, option)
            if expected > best_expected + 6.0:
                best_expected = expected
                best_option = option

        return best_option

    def _expected_score_after_discard(self, player: PlayerState, opponent: PlayerState, discard_indices: Sequence[int]) -> float:
        discard_set = set(discard_indices)
        kept = [card for idx, card in enumerate(player.hand) if idx not in discard_set]
        draws_needed = len(discard_indices)
        if draws_needed <= 0:
            return float(HandEvaluator.best_scoring_hand(player.hand, player, opponent).score)

        pool = list(player.deck)
        if len(pool) < draws_needed:
            pool.extend(self._create_deck())

        samples = min(24, len(pool))
        if samples == 0:
            return float(HandEvaluator.best_scoring_hand(kept, player, opponent).score)

        total = 0.0
        for _ in range(samples):
            draw = self.random.sample(pool, draws_needed)
            hypothetical = kept + draw
            total += HandEvaluator.best_scoring_hand(hypothetical, player, opponent).score

        return total / float(samples)

    def _apply_set_result(self, player_one: PlayerState, player_two: PlayerState, p1_result, p2_result) -> None:
        player_one.total_points_scored += p1_result.score
        player_two.total_points_scored += p2_result.score
        player_one.hand_frequency[p1_result.hand_rank.name] += 1
        player_two.hand_frequency[p2_result.hand_rank.name] += 1

        if p1_result.score_result is not None:
            for joker_id, points in p1_result.score_result.joker_contributions_by_id.items():
                player_one.joker_points_generated[joker_id] += points
        if p2_result.score_result is not None:
            for joker_id, points in p2_result.score_result.joker_contributions_by_id.items():
                player_two.joker_points_generated[joker_id] += points

    def _remove_played_cards(self, player: PlayerState, played_cards: Sequence[Card]) -> None:
        played_set = set(played_cards)
        player.hand = [card for card in player.hand if card not in played_set]

    def _create_deck(self) -> List[Card]:
        deck = [Card(rank=rank, suit=suit) for suit in Suit for rank in Rank]
        self.random.shuffle(deck)
        return deck

    def _winner_name(self) -> str:
        return self._winner_player().name

    def _winner_player(self) -> PlayerState:
        if self.momentum > 0:
            return self.player_one
        if self.momentum < 0:
            return self.player_two
        return self.player_one if self.current_round % 2 == 1 else self.player_two

