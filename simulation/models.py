"""Core data models for the standalone Balatro Certamen simulator."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Suit(Enum):
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

    def chip_value(self) -> int:
        if self in (Rank.JACK, Rank.QUEEN, Rank.KING):
            return 10
        if self == Rank.ACE:
            return 11
        return int(self.value)

    def order(self) -> int:
        return {
            Rank.TWO: 2,
            Rank.THREE: 3,
            Rank.FOUR: 4,
            Rank.FIVE: 5,
            Rank.SIX: 6,
            Rank.SEVEN: 7,
            Rank.EIGHT: 8,
            Rank.NINE: 9,
            Rank.TEN: 10,
            Rank.JACK: 11,
            Rank.QUEEN: 12,
            Rank.KING: 13,
            Rank.ACE: 14,
        }[self]


class HandRank(Enum):
    HIGH_CARD = (0, 5, 1)
    PAIR = (1, 10, 2)
    TWO_PAIR = (2, 20, 2)
    THREE_OF_A_KIND = (3, 30, 3)
    STRAIGHT = (4, 40, 4)
    FLUSH = (5, 50, 4)
    FULL_HOUSE = (6, 75, 4)
    FOUR_OF_A_KIND = (7, 100, 6)
    STRAIGHT_FLUSH = (8, 125, 8)

    def rank_value(self) -> int:
        return self.value[0]

    def base_chips(self) -> int:
        return self.value[1]

    def base_mult(self) -> int:
        return self.value[2]


class Planet(Enum):
    PLUTO = ("High Card", 5, 1)
    MERCURY = ("Pair", 10, 1)
    URANUS = ("Two Pair", 10, 1)
    VENUS = ("Three of a Kind", 15, 1)
    SATURN = ("Straight", 20, 2)
    JUPITER = ("Flush", 15, 1)
    EARTH = ("Full House", 20, 2)
    MARS = ("Four of a Kind", 25, 2)
    NEPTUNE = ("Straight Flush", 30, 3)

    @property
    def hand_type(self) -> str:
        return self.value[0]

    @property
    def chip_bonus(self) -> int:
        return self.value[1]

    @property
    def mult_bonus(self) -> int:
        return self.value[2]


class JokerType(Enum):
    BANNER = "Banner"
    ABSTRACT = "Abstract"
    EVEN_STEVEN = "Even Steven"
    ODD_TODD = "Odd Todd"
    BLACK_HOLE = "Black Hole"
    THE_DUO = "The Duo"
    THE_GREEDY = "The Greedy"
    THE_LOVER = "The Lover"
    THE_PROTECTOR = "The Protector"
    THE_CHAIRMAN = "The Chairman"
    SCRAPPY = "Scrappy"
    STRAITJACKET = "Straitjacket"
    COPYRIGHT = "Copyright"
    TAX_MAN = "Tax Man"
    TRADE_INSIDER = "Trade Insider"
    FOUR_FINGERS = "Four Fingers"
    SHORTCUT = "Shortcut"
    THE_TRIBE = "The Tribe"
    THE_ORDER = "The Order"
    FAMILY = "Family"
    RAINBOW = "Rainbow"
    UNIFORM = "Uniform"
    SMEAR = "Smear"
    COPYCAT = "Copycat"


JOKER_RARITY: Dict[JokerType, str] = {
    JokerType.BANNER: "Common",
    JokerType.ABSTRACT: "Common",
    JokerType.EVEN_STEVEN: "Common",
    JokerType.ODD_TODD: "Common",
    JokerType.BLACK_HOLE: "Common",
    JokerType.THE_DUO: "Common",
    JokerType.THE_GREEDY: "Common",
    JokerType.THE_LOVER: "Common",
    JokerType.THE_PROTECTOR: "Common",
    JokerType.THE_CHAIRMAN: "Common",
    JokerType.SCRAPPY: "Rare",
    JokerType.STRAITJACKET: "Rare",
    JokerType.COPYRIGHT: "Rare",
    JokerType.TAX_MAN: "Rare",
    JokerType.TRADE_INSIDER: "Rare",
    JokerType.FOUR_FINGERS: "Rare",
    JokerType.SHORTCUT: "Rare",
    JokerType.THE_TRIBE: "Rare",
    JokerType.THE_ORDER: "Rare",
    JokerType.FAMILY: "Legendary",
    JokerType.RAINBOW: "Legendary",
    JokerType.UNIFORM: "Legendary",
    JokerType.SMEAR: "Legendary",
    JokerType.COPYCAT: "Legendary",
}


JOKER_MIN_BID: Dict[str, int] = {
    "Common": 100,
    "Rare": 250,
    "Legendary": 500,
}


PLANET_MIN_BID: Dict[Planet, int] = {
    Planet.PLUTO: 100,
    Planet.MERCURY: 100,
    Planet.URANUS: 100,
    Planet.VENUS: 150,
    Planet.SATURN: 250,
    Planet.JUPITER: 150,
    Planet.EARTH: 250,
    Planet.MARS: 250,
    Planet.NEPTUNE: 300,
}


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def chip_value(self) -> int:
        return self.rank.chip_value()

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"


@dataclass(frozen=True)
class JokerCard:
    joker_id: int
    joker_type: JokerType
    purchase_cost: int = 0


@dataclass(frozen=True)
class PlanetCard:
    planet_type: Planet
    purchase_cost: int = 0


@dataclass(frozen=True)
class AuctionCard:
    auction_id: int
    is_joker: bool
    is_planet: bool
    joker_type: Optional[JokerType] = None
    planet_type: Optional[Planet] = None
    minimum_bid: int = 0

    def display_name(self) -> str:
        if self.is_joker and self.joker_type is not None:
            return self.joker_type.value
        if self.is_planet and self.planet_type is not None:
            return self.planet_type.name.title()
        return f"AuctionCard#{self.auction_id}"


@dataclass
class ScoreResult:
    base_chips: int
    base_mult: int
    card_chips: int
    planet_chips: int
    planet_mult: int
    joker_chip_bonus: int
    joker_mult_bonus: int
    joker_x_mult: float
    final_score: int
    hand_rank: HandRank
    breakdown: Dict[str, int] = field(default_factory=dict)
    joker_contributions_by_id: Dict[int, int] = field(default_factory=dict)
    joker_types_by_id: Dict[int, str] = field(default_factory=dict)


@dataclass
class HandResult:
    cards: List[Card]
    hand_rank: HandRank
    high_card: Rank
    kicker_ranks: List[Rank] = field(default_factory=list)
    score: int = 0
    score_result: Optional[ScoreResult] = None


@dataclass
class PlayerState:
    name: str
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    jokers: List[JokerCard] = field(default_factory=list)
    planets: Dict[Planet, int] = field(default_factory=lambda: Counter())
    discards_remaining: int = 2
    round_score: int = 0
    momentum: int = 0
    hand_frequency: Counter = field(default_factory=Counter)
    joker_points_generated: Counter = field(default_factory=Counter)
    joker_momentum_spent: Counter = field(default_factory=Counter)
    total_points_scored: int = 0

    def reset_for_round(self) -> None:
        self.hand = []
        self.discards_remaining = 2
        self.round_score = 0

    def add_joker(self, joker: JokerCard, cost: int) -> None:
        self.jokers.append(JokerCard(joker_id=joker.joker_id, joker_type=joker.joker_type, purchase_cost=cost))
        self.joker_momentum_spent[joker.joker_type.value] += cost

    def add_planet(self, planet: Planet, cost: int) -> None:
        self.planets[planet] = self.planets.get(planet, 0) + 1

    def active_joker_ids(self) -> List[int]:
        return [joker.joker_id for joker in self.jokers]


@dataclass
class GameResult:
    game_index: int
    winner: str
    rounds_played: int
    final_momentum: int
    winner_joker_ids: List[int]
    winner_joker_types: List[str]
    p1_joker_ids: List[int]
    p2_joker_ids: List[int]
    p1_joker_types: List[str]
    p2_joker_types: List[str]
    winner_hand_frequency: Dict[str, int]
    p1_hand_frequency: Dict[str, int]
    p2_hand_frequency: Dict[str, int]
    round_winners: List[str] = field(default_factory=list)
