"""Core game models: Card, Hand, Player, Jokers, Planets."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Set
from collections import Counter


class Suit(Enum):
    """Card suits."""
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"


class Rank(Enum):
    """Card ranks."""
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

    def numeric_value(self) -> int:
        """Get the numeric chip value of a rank."""
        if self in (Rank.JACK, Rank.QUEEN, Rank.KING):
            return 10
        elif self == Rank.ACE:
            return 11
        else:
            return int(self.value)

    def rank_order(self) -> int:
        """Get the rank for hand evaluation (Ace=14)."""
        order = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13,
            Rank.ACE: 14
        }
        return order[self]

    @staticmethod
    def from_string(s: str) -> 'Rank':
        """Convert string to Rank."""
        for rank in Rank:
            if rank.value == s:
                return rank
        raise ValueError(f"Unknown rank: {s}")


class HandRank(Enum):
    """Poker hand classifications."""
    HIGH_CARD = (0, 5, 1)  # (rank, combination_size, base_mult)
    PAIR = (1, 10, 2)
    TWO_PAIR = (2, 20, 2)
    THREE_OF_A_KIND = (3, 30, 3)
    STRAIGHT = (4, 40, 4)
    FLUSH = (5, 50, 4)
    FULL_HOUSE = (6, 75, 4)
    FOUR_OF_A_KIND = (7, 100, 6)
    STRAIGHT_FLUSH = (8, 125, 8)

    def base_chips(self) -> int:
        return self.value[1]

    def base_mult(self) -> int:
        return self.value[2]

    def rank_value(self) -> int:
        """For ranking hands."""
        return self.value[0]


class Planet(Enum):
    """Planet cards and their bonuses."""
    PLUTO = ("High Card", 5, 1)
    MERCURY = ("Pair", 10, 1)
    URANUS = ("Two Pair", 10, 1)
    VENUS = ("Three of a Kind", 15, 1)
    SATURN = ("Straight", 20, 2)
    JUPITER = ("Flush", 15, 1)
    EARTH = ("Full House", 20, 2)
    MARS = ("Four of a Kind", 25, 2)
    NEPTUNE = ("Straight Flush", 30, 3)

    def hand_type(self) -> str:
        return self.value[0]

    def chip_bonus(self) -> int:
        return self.value[1]

    def mult_bonus(self) -> int:
        return self.value[2]


class JokerType(Enum):
    """Joker types and rarity."""
    # Common
    BANNER = auto()
    ABSTRACT = auto()
    EVEN_STEVEN = auto()
    ODD_TODD = auto()
    BLACK_HOLE = auto()
    THE_DUO = auto()
    THE_GREEDY = auto()
    THE_LOVER = auto()
    THE_PROTECTOR = auto()
    THE_CHAIRMAN = auto()

    # Rare
    SCRAPPY = auto()
    STRAITJACKET = auto()
    COPYRIGHT = auto()
    TAX_MAN = auto()
    TRADE_INSIDER = auto()
    FOUR_FINGERS = auto()
    SHORTCUT = auto()
    THE_TRIBE = auto()
    THE_ORDER = auto()

    # Legendary
    FAMILY = auto()
    RAINBOW = auto()
    UNIFORM = auto()
    SMEAR = auto()
    COPYCAT = auto()

    @property
    def rarity(self) -> str:
        if self in {
            JokerType.BANNER,
            JokerType.ABSTRACT,
            JokerType.EVEN_STEVEN,
            JokerType.ODD_TODD,
            JokerType.BLACK_HOLE,
            JokerType.THE_DUO,
            JokerType.THE_GREEDY,
            JokerType.THE_LOVER,
            JokerType.THE_PROTECTOR,
            JokerType.THE_CHAIRMAN,
        }:
            return "Common"
        if self in {
            JokerType.SCRAPPY,
            JokerType.STRAITJACKET,
            JokerType.COPYRIGHT,
            JokerType.TAX_MAN,
            JokerType.TRADE_INSIDER,
            JokerType.FOUR_FINGERS,
            JokerType.SHORTCUT,
            JokerType.THE_TRIBE,
            JokerType.THE_ORDER,
        }:
            return "Rare"
        return "Legendary"


@dataclass
class Card:
    """A playing card."""
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()

    def chip_value(self) -> int:
        """Chip value of this card."""
        return self.rank.numeric_value()


@dataclass
class Joker:
    """A joker card."""
    type: JokerType

    def __str__(self) -> str:
        return self.type.name.replace("_", " ")

    def __repr__(self) -> str:
        return f"Joker({self.type.name})"


@dataclass
class PokerHand:
    """A 5-card poker hand with evaluation."""
    cards: List[Card]
    hand_rank: HandRank
    high_card: Rank  # For tiebreakers
    kicker_ranks: List[Rank] = field(default_factory=list)

    def __str__(self) -> str:
        cards_str = " ".join(str(c) for c in self.cards)
        return f"{self.hand_rank.name} [{cards_str}]"


@dataclass
class ScoreResult:
    """Result of a score calculation."""
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
    breakdown: dict = field(default_factory=dict)


@dataclass
class Player:
    """A player in the game."""
    name: str
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    discard_actions_used: int = 0
    discard_actions_max: int = 2
    jokers: List[Joker] = field(default_factory=list)
    planets: List[Planet] = field(default_factory=list)
    round_score: int = 0
    momentum: int = 0

    def discard_actions_remaining(self) -> int:
        return self.discard_actions_max - self.discard_actions_used

    def can_discard(self) -> bool:
        return self.discard_actions_remaining() > 0

    def joker_count(self) -> int:
        return len(self.jokers)

    def has_joker_type(self, jtype: JokerType) -> bool:
        return any(j.type == jtype for j in self.jokers)

    def planet_level(self, planet: Planet) -> int:
        """How many of a given planet does this player own."""
        return sum(1 for p in self.planets if p == planet)

    def reset_round(self):
        """Reset per-round state."""
        self.round_score = 0
        self.discard_actions_used = 0
        self.hand = []


@dataclass
class AuctionCard:
    """A card available in the auction."""
    id: int
    is_joker: bool
    is_planet: bool
    joker_type: JokerType = None
    planet_type: Planet = None
    minimum_bid: int = 0

    def __str__(self) -> str:
        if self.is_joker:
            return str(self.joker_type.name.replace("_", " "))
        elif self.is_planet:
            return self.planet_type.name
        return "Unknown"


@dataclass
class AuctionState:
    """Current state of an auction."""
    revealed_cards: List[AuctionCard] = field(default_factory=list)
    card_bids: List[int] = field(default_factory=list)
    card_leaders: List[int] = field(default_factory=list)
    card_player_bids: List[int] = field(default_factory=list)
    card_ai_bids: List[int] = field(default_factory=list)
    current_card_index: int = 0
    first_bidder: int = 0  # 0 for player, 1 for AI
    turn_index: int = 0  # 0..3 for winner/loser/winner/loser
    current_bid: int = 0
    current_leader: int = -1  # -1 means no bid yet
    last_bidder: int = -1
    player_spent: int = 0
    ai_spent: int = 0
    pending_human_joker_choice: bool = False
    is_active: bool = False
