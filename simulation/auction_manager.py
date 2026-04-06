"""Auction logic for the standalone simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .models import (
    AuctionCard,
    JOKER_MIN_BID,
    JOKER_RARITY,
    PLANET_MIN_BID,
    JokerCard,
    JokerType,
    Planet,
    PlayerState,
)


@dataclass
class AuctionOutcome:
    purchases: List[Tuple[str, AuctionCard, int]] = field(default_factory=list)
    momentum_delta: int = 0
    first_bidder: int = 0
    revealed_cards: List[AuctionCard] = field(default_factory=list)


class AuctionManager:
    """Builds auction pools, estimates card value, and executes bidding."""

    def __init__(self, rng):
        self.rng = rng
        self._auction_cards: List[AuctionCard] = []
        self._next_auction_id = 0
        self._build_auction_pool()

    def _build_auction_pool(self) -> None:
        self._auction_cards = []
        self._next_auction_id = 0

        for joker_type in JokerType:
            for _ in range(2):
                rarity = JOKER_RARITY[joker_type]
                self._auction_cards.append(
                    AuctionCard(
                        auction_id=self._next_auction_id,
                        is_joker=True,
                        is_planet=False,
                        joker_type=joker_type,
                        minimum_bid=JOKER_MIN_BID[rarity],
                    )
                )
                self._next_auction_id += 1

        for planet in Planet:
            for _ in range(3):
                self._auction_cards.append(
                    AuctionCard(
                        auction_id=self._next_auction_id,
                        is_joker=False,
                        is_planet=True,
                        planet_type=planet,
                        minimum_bid=PLANET_MIN_BID[planet],
                    )
                )
                self._next_auction_id += 1

        self.rng.shuffle(self._auction_cards)

    def reveal_cards(self, count: int = 5) -> List[AuctionCard]:
        if len(self._auction_cards) < count:
            self._build_auction_pool()

        revealed: List[AuctionCard] = []
        seen_types: set[Tuple[str, str]] = set()
        index = 0
        while len(revealed) < count and index < len(self._auction_cards):
            card = self._auction_cards[index]
            key = self._card_key(card)
            if key not in seen_types:
                seen_types.add(key)
                revealed.append(card)
                self._auction_cards.pop(index)
                continue
            index += 1

        return revealed

    def run_auction(
        self,
        player_one: PlayerState,
        player_two: PlayerState,
        round_winner: int,
        current_momentum: int,
    ) -> AuctionOutcome:
        revealed_cards = self.reveal_cards(5)
        first_bidder = round_winner
        order = [first_bidder, 1 - first_bidder, first_bidder, 1 - first_bidder]

        outcome = AuctionOutcome(revealed_cards=revealed_cards, first_bidder=first_bidder)

        for bidder_index in order:
            bidder = player_one if bidder_index == 0 else player_two
            opponent = player_two if bidder_index == 0 else player_one

            card, bid_amount = self._choose_bid_for_turn(
                bidder=bidder,
                opponent=opponent,
                revealed_cards=revealed_cards,
                current_momentum=current_momentum,
            )
            if card is None or bid_amount <= 0:
                continue

            if bidder_index == 0:
                current_momentum -= bid_amount
            else:
                current_momentum += bid_amount

            self._apply_purchase(bidder, card, bid_amount)
            outcome.purchases.append((bidder.name, card, bid_amount))
            outcome.momentum_delta = current_momentum
            revealed_cards.remove(card)

            if abs(current_momentum) >= 10000:
                break

        return outcome

    def _choose_bid_for_turn(
        self,
        bidder: PlayerState,
        opponent: PlayerState,
        revealed_cards: Sequence[AuctionCard],
        current_momentum: int,
    ) -> Tuple[Optional[AuctionCard], int]:
        best_card: Optional[AuctionCard] = None
        best_value = 0.0
        best_bid = 0

        lead = abs(current_momentum)
        threshold = max(1.0, lead * 0.10)

        for card in revealed_cards:
            value = self.estimate_score_boost(card, bidder, opponent, current_momentum)
            if value <= threshold:
                continue
            bid_cap = 1500
            minimum = card.minimum_bid
            bid = min(bid_cap, max(minimum, int(value)))
            if value > best_value:
                best_card = card
                best_value = value
                best_bid = bid

        return best_card, best_bid

    def estimate_score_boost(
        self,
        card: AuctionCard,
        bidder: PlayerState,
        opponent: PlayerState,
        current_momentum: int,
    ) -> float:
        if card.is_planet and card.planet_type is not None:
            return self._estimate_planet_value(card.planet_type, bidder)

        if card.is_joker and card.joker_type is not None:
            return self._estimate_joker_value(card.joker_type, bidder, opponent, current_momentum)

        return 0.0

    def _estimate_planet_value(self, planet: Planet, bidder: PlayerState) -> float:
        hand_focus = 0
        for joker in bidder.jokers:
            if joker.joker_type in {JokerType.THE_TRIBE, JokerType.RAINBOW}:
                hand_focus += 1
            if joker.joker_type in {JokerType.THE_ORDER, JokerType.SHORTCUT}:
                hand_focus += 1
            if joker.joker_type == JokerType.FAMILY:
                hand_focus += 1

        total_hand_uses = max(1, sum(bidder.hand_frequency.values()))
        hand_key = planet.hand_type.upper().replace(" ", "_")
        hand_usage_share = bidder.hand_frequency.get(hand_key, 0) / total_hand_uses

        base = 100.0
        if planet.hand_type == "Straight Flush":
            base = 450.0
        elif planet.hand_type == "Four of a Kind":
            base = 320.0
        elif planet.hand_type in {"Full House", "Flush", "Straight"}:
            base = 220.0
        elif planet.hand_type in {"Three of a Kind", "Two Pair", "Pair"}:
            base = 160.0

        return base * (0.85 + hand_usage_share) + 25.0 * hand_focus + planet.chip_bonus * 4 + planet.mult_bonus * 40

    def _estimate_joker_value(
        self,
        joker_type: JokerType,
        bidder: PlayerState,
        opponent: PlayerState,
        current_momentum: int,
    ) -> float:
        total_hand_uses = max(1, sum(bidder.hand_frequency.values()))
        pair_share = bidder.hand_frequency.get("PAIR", 0) / total_hand_uses
        two_pair_share = bidder.hand_frequency.get("TWO_PAIR", 0) / total_hand_uses
        straight_share = bidder.hand_frequency.get("STRAIGHT", 0) / total_hand_uses
        flush_share = bidder.hand_frequency.get("FLUSH", 0) / total_hand_uses
        full_house_share = bidder.hand_frequency.get("FULL_HOUSE", 0) / total_hand_uses
        quads_share = bidder.hand_frequency.get("FOUR_OF_A_KIND", 0) / total_hand_uses
        base_discards = max(
            0,
            2
            + sum(1 for joker in bidder.jokers if joker.joker_type == JokerType.SCRAPPY)
            - sum(1 for joker in opponent.jokers if joker.joker_type == JokerType.STRAITJACKET),
        )
        opponent_discards = max(
            0,
            2
            + sum(1 for joker in opponent.jokers if joker.joker_type == JokerType.SCRAPPY)
            - sum(1 for joker in bidder.jokers if joker.joker_type == JokerType.STRAITJACKET),
        )
        existing_same = sum(1 for joker in bidder.jokers if joker.joker_type == joker_type)

        base_values = {
            JokerType.BANNER: 140.0,
            JokerType.ABSTRACT: 170.0,
            JokerType.EVEN_STEVEN: 120.0,
            JokerType.ODD_TODD: 120.0,
            JokerType.BLACK_HOLE: 110.0,
            JokerType.THE_DUO: 150.0,
            JokerType.THE_GREEDY: 130.0,
            JokerType.THE_LOVER: 130.0,
            JokerType.THE_PROTECTOR: 130.0,
            JokerType.THE_CHAIRMAN: 130.0,
            JokerType.SCRAPPY: 210.0,
            JokerType.STRAITJACKET: 190.0,
            JokerType.COPYRIGHT: 240.0,
            JokerType.TAX_MAN: 120.0,
            JokerType.TRADE_INSIDER: 170.0,
            JokerType.FOUR_FINGERS: 220.0,
            JokerType.SHORTCUT: 220.0,
            JokerType.THE_TRIBE: 260.0,
            JokerType.THE_ORDER: 260.0,
            JokerType.FAMILY: 420.0,
            JokerType.RAINBOW: 420.0,
            JokerType.UNIFORM: 280.0,
            JokerType.SMEAR: 280.0,
            JokerType.COPYCAT: 320.0,
        }

        value = base_values.get(joker_type, 120.0)

        if joker_type == JokerType.ABSTRACT:
            value += 28.0 * (len(bidder.jokers) + 1)
            if existing_same > 0:
                value *= max(0.55, 0.82 ** existing_same)
        elif joker_type == JokerType.BANNER:
            expected_discards = base_discards
            value = 20.0 * expected_discards
        elif joker_type == JokerType.SCRAPPY:
            banner_count = sum(1 for joker in bidder.jokers if joker.joker_type == JokerType.BANNER)
            shaping_synergy = 120.0 * (straight_share + flush_share + full_house_share + quads_share)
            value += 80.0 + shaping_synergy + 45.0 * banner_count
            if base_discards == 0:
                value += 90.0
        elif joker_type == JokerType.STRAITJACKET:
            opponent_banner = sum(1 for joker in opponent.jokers if joker.joker_type == JokerType.BANNER)
            denial_pressure = 70.0 * (straight_share + flush_share)
            value += 70.0 + 90.0 * opponent_discards + 55.0 * opponent_banner + denial_pressure
        elif joker_type in {JokerType.THE_TRIBE, JokerType.THE_ORDER, JokerType.FAMILY, JokerType.RAINBOW}:
            value += 60.0 * (len(bidder.jokers) + 1)
        elif joker_type in {JokerType.UNIFORM, JokerType.SMEAR}:
            value += 20.0 * (len(bidder.jokers) + 1)
        elif joker_type == JokerType.COPYCAT and bidder.jokers:
            value += 25.0 * len(bidder.jokers)
        elif joker_type == JokerType.THE_DUO:
            value += 220.0 * (pair_share + two_pair_share)
        elif joker_type == JokerType.THE_GREEDY:
            value += 180.0 * max(pair_share, two_pair_share)
        elif joker_type == JokerType.THE_LOVER:
            value += 180.0 * flush_share
        elif joker_type == JokerType.THE_PROTECTOR:
            value += 180.0 * straight_share
        elif joker_type == JokerType.THE_CHAIRMAN:
            value += 180.0 * full_house_share
        elif joker_type == JokerType.FAMILY:
            value += 260.0 * quads_share
        elif joker_type == JokerType.RAINBOW:
            value += 260.0 * flush_share
        elif joker_type == JokerType.FOUR_FINGERS:
            value += 240.0 * flush_share
        elif joker_type == JokerType.SHORTCUT:
            value += 240.0 * straight_share

        if existing_same > 0 and joker_type not in {JokerType.BANNER, JokerType.COPYCAT, JokerType.SCRAPPY, JokerType.STRAITJACKET}:
            value *= max(0.6, 1.0 - 0.18 * existing_same)

        if any(joker.joker_type == JokerType.COPYRIGHT for joker in opponent.jokers):
            value *= 0.82

        if any(joker.joker_type == JokerType.TRADE_INSIDER for joker in bidder.jokers):
            value *= 1.10

        if joker_type == JokerType.TAX_MAN:
            value += 120.0 * sum(1 for joker in opponent.jokers if joker.joker_type in {JokerType.EVEN_STEVEN, JokerType.ODD_TODD})

        lead = max(1.0, abs(current_momentum))
        if value > 0.25 * lead:
            value *= 1.05

        return value

    def _apply_purchase(self, bidder: PlayerState, card: AuctionCard, bid_amount: int) -> None:
        if card.is_joker and card.joker_type is not None:
            bidder.add_joker(JokerCard(joker_id=card.auction_id, joker_type=card.joker_type), bid_amount)
        elif card.is_planet and card.planet_type is not None:
            bidder.add_planet(card.planet_type, bid_amount)

    @staticmethod
    def _card_key(card: AuctionCard) -> Tuple[str, str]:
        if card.is_joker and card.joker_type is not None:
            return ("joker", card.joker_type.value)
        if card.is_planet and card.planet_type is not None:
            return ("planet", card.planet_type.name)
        return ("unknown", str(card.auction_id))

