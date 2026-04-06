"""Simulation runner and CSV export for Balatro Certamen."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .game_engine import GameEngine
from .models import GameResult


@dataclass
class JokerSummaryStats:
    owned_games: int = 0
    win_games: int = 0
    total_points_generated: float = 0.0
    total_momentum_spent: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.owned_games == 0:
            return 0.0
        return self.win_games / self.owned_games

    @property
    def roi(self) -> float:
        if self.total_momentum_spent == 0:
            return 0.0
        return self.total_points_generated / self.total_momentum_spent


@dataclass
class HandSummaryStats:
    seen_games: int = 0
    winner_games: int = 0
    total_player_uses: int = 0
    total_winner_uses: int = 0

    @property
    def winner_game_rate(self) -> float:
        if self.seen_games == 0:
            return 0.0
        return self.winner_games / self.seen_games


class SimulationRunner:
    """Run many games and export game-level and joker-level summaries."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def run(
        self,
        games: int = 1000,
        output_path: str = "simulation_results.csv",
        summary_path: str = "simulation_summary.csv",
        hand_summary_path: str = "simulation_hand_summary.csv",
    ) -> List[GameResult]:
        results: List[GameResult] = []
        joker_stats: Dict[str, JokerSummaryStats] = defaultdict(JokerSummaryStats)
        hand_stats: Dict[str, HandSummaryStats] = defaultdict(HandSummaryStats)

        for game_index in range(games):
            engine_seed = None if self.seed is None else self.seed + game_index
            engine = GameEngine(seed=engine_seed)
            result = engine.play_game(game_index=game_index)
            results.append(result)
            self._update_joker_stats(joker_stats, result, engine)
            self._update_hand_stats(hand_stats, result)

        self._write_results_csv(Path(output_path), results)
        self._write_summary_csv(Path(summary_path), joker_stats)
        self._write_hand_summary_csv(Path(hand_summary_path), hand_stats)
        return results

    def _update_joker_stats(self, joker_stats: Dict[str, JokerSummaryStats], result: GameResult, engine: GameEngine) -> None:
        winner_name = result.winner
        winner_player = engine.player_one if winner_name == engine.player_one.name else engine.player_two
        loser_player = engine.player_two if winner_player is engine.player_one else engine.player_one

        owned_types = set(joker.joker_type.value for joker in winner_player.jokers + loser_player.jokers)
        winner_owned_types = set(joker.joker_type.value for joker in winner_player.jokers)

        for joker_type in owned_types:
            stats = joker_stats[joker_type]
            stats.owned_games += 1
            if joker_type in winner_owned_types:
                stats.win_games += 1

        for player in (winner_player, loser_player):
            for joker in player.jokers:
                stats = joker_stats[joker.joker_type.value]
                stats.total_momentum_spent += max(0, joker.purchase_cost)
                points = player.joker_points_generated.get(joker.joker_id, 0)
                stats.total_points_generated += points

    def _update_hand_stats(self, hand_stats: Dict[str, HandSummaryStats], result: GameResult) -> None:
        all_hand_types = set(result.p1_hand_frequency) | set(result.p2_hand_frequency)
        for hand_type in all_hand_types:
            stats = hand_stats[hand_type]
            stats.seen_games += 1

            p1_uses = result.p1_hand_frequency.get(hand_type, 0)
            p2_uses = result.p2_hand_frequency.get(hand_type, 0)
            stats.total_player_uses += p1_uses + p2_uses

            winner_uses = result.winner_hand_frequency.get(hand_type, 0)
            stats.total_winner_uses += winner_uses
            if winner_uses > 0:
                stats.winner_games += 1

    def _write_results_csv(self, path: Path, results: List[GameResult]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "game_index",
                    "winner",
                    "rounds_played",
                    "final_momentum",
                    "winner_joker_ids",
                    "winner_joker_types",
                    "p1_joker_ids",
                    "p2_joker_ids",
                    "winner_most_used_hand",
                    "winner_hand_frequency",
                    "p1_hand_frequency",
                    "p2_hand_frequency",
                    "round_winners",
                ],
            )
            writer.writeheader()
            for result in results:
                winner_most_used_hand = self._most_used_hand(result.winner_hand_frequency)
                writer.writerow(
                    {
                        "game_index": result.game_index,
                        "winner": result.winner,
                        "rounds_played": result.rounds_played,
                        "final_momentum": result.final_momentum,
                        "winner_joker_ids": json.dumps(result.winner_joker_ids),
                        "winner_joker_types": json.dumps(result.winner_joker_types),
                        "p1_joker_ids": json.dumps(result.p1_joker_ids),
                        "p2_joker_ids": json.dumps(result.p2_joker_ids),
                        "winner_most_used_hand": winner_most_used_hand,
                        "winner_hand_frequency": json.dumps(result.winner_hand_frequency, sort_keys=True),
                        "p1_hand_frequency": json.dumps(result.p1_hand_frequency, sort_keys=True),
                        "p2_hand_frequency": json.dumps(result.p2_hand_frequency, sort_keys=True),
                        "round_winners": json.dumps(result.round_winners),
                    }
                )

    def _write_summary_csv(self, path: Path, joker_stats: Dict[str, JokerSummaryStats]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "joker_type",
                    "owned_games",
                    "win_games",
                    "win_rate",
                    "total_points_generated",
                    "total_momentum_spent",
                    "roi",
                ],
            )
            writer.writeheader()
            for joker_type in sorted(joker_stats.keys()):
                stats = joker_stats[joker_type]
                writer.writerow(
                    {
                        "joker_type": joker_type,
                        "owned_games": stats.owned_games,
                        "win_games": stats.win_games,
                        "win_rate": round(stats.win_rate, 6),
                        "total_points_generated": round(stats.total_points_generated, 2),
                        "total_momentum_spent": round(stats.total_momentum_spent, 2),
                        "roi": round(stats.roi, 6),
                    }
                )

    def _write_hand_summary_csv(self, path: Path, hand_stats: Dict[str, HandSummaryStats]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "hand_type",
                    "seen_games",
                    "winner_games",
                    "winner_game_rate",
                    "total_player_uses",
                    "total_winner_uses",
                ],
            )
            writer.writeheader()
            for hand_type in sorted(hand_stats.keys()):
                stats = hand_stats[hand_type]
                writer.writerow(
                    {
                        "hand_type": hand_type,
                        "seen_games": stats.seen_games,
                        "winner_games": stats.winner_games,
                        "winner_game_rate": round(stats.winner_game_rate, 6),
                        "total_player_uses": stats.total_player_uses,
                        "total_winner_uses": stats.total_winner_uses,
                    }
                )

    @staticmethod
    def _most_used_hand(hand_frequency: Dict[str, int]) -> str:
        if not hand_frequency:
            return ""
        return max(hand_frequency.items(), key=lambda item: (item[1], item[0]))[0]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run Balatro Certamen simulations.")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default="simulation_results.csv")
    parser.add_argument("--summary", type=str, default="simulation_summary.csv")
    parser.add_argument("--hand-summary", type=str, default="simulation_hand_summary.csv")
    args = parser.parse_args()

    runner = SimulationRunner(seed=args.seed)
    runner.run(games=args.games, output_path=args.output, summary_path=args.summary, hand_summary_path=args.hand_summary)


if __name__ == "__main__":
    main()
