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
        self.set_first_player = 0  # 0 for player, 1 for AI
        self.previous_set_winner: Optional[int] = None
        self.last_set_start_event: str = ""
        self.last_auction_first_bidder = 0
        self.round_disabled_jokers = {
            0: [],  # Human jokers disabled for current round
            1: [],  # AI jokers disabled for current round
        }

        # Action log
        self.action_log: List[str] = []

    def new_game(self):
        """Initialize a new game."""
        # Reset persistent player state while keeping the same objects referenced by the UI.
        self.player.deck = []
        self.player.hand = []
        self.player.discard_actions_used = 0
        self.player.discard_actions_max = 2
        self.player.jokers = []
        self.player.planets = []
        self.player.round_score = 0
        self.player.momentum = 0

        self.ai.deck = []
        self.ai.hand = []
        self.ai.discard_actions_used = 0
        self.ai.discard_actions_max = 2
        self.ai.jokers = []
        self.ai.planets = []
        self.ai.round_score = 0
        self.ai.momentum = 0

        # Create decks
        self.player.deck = self._create_deck()
        self.ai.deck = self._create_deck()

        # Initialize auctions deck
        self._init_auction_deck()

        self.auction_state = AuctionState()
        self.round_winner = None
        self.set_first_player = 0
        self.previous_set_winner = None
        self.last_set_start_event = ""
        self.last_auction_first_bidder = 0
        self.round_disabled_jokers = {0: [], 1: []}

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

        joker_min_bid_by_rarity = {
            "Common": 100,
            "Rare": 250,
            "Legendary": 500,
        }

        planet_min_bid = {
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

        joker_copy_counts = {
            JokerType.BANNER: 3,
            JokerType.ABSTRACT: 3,
            JokerType.EVEN_STEVEN: 3,
            JokerType.ODD_TODD: 3,
            JokerType.BLACK_HOLE: 3,
            JokerType.THE_DUO: 3,
            JokerType.THE_GREEDY: 2,
            JokerType.THE_LOVER: 2,
            JokerType.THE_PROTECTOR: 2,
            JokerType.THE_CHAIRMAN: 2,
            JokerType.SCRAPPY: 2,
            JokerType.STRAITJACKET: 2,
            JokerType.COPYRIGHT: 2,
            JokerType.TAX_MAN: 2,
            JokerType.TRADE_INSIDER: 2,
            JokerType.FOUR_FINGERS: 2,
            JokerType.SHORTCUT: 2,
            JokerType.THE_TRIBE: 2,
            JokerType.THE_ORDER: 2,
            JokerType.FAMILY: 1,
            JokerType.RAINBOW: 1,
            JokerType.UNIFORM: 1,
            JokerType.SMEAR: 1,
            JokerType.COPYCAT: 1,
        }

        for jtype in JokerType:
            for _ in range(joker_copy_counts.get(jtype, 1)):
                self.auction_deck.append(AuctionCard(
                    id=card_id,
                    is_joker=True,
                    is_planet=False,
                    joker_type=jtype,
                    minimum_bid=joker_min_bid_by_rarity.get(jtype.rarity, 100)
                ))
                card_id += 1

        planet_copy_count = 5
        for planet in Planet:
            for _ in range(planet_copy_count):
                self.auction_deck.append(AuctionCard(
                    id=card_id,
                    is_joker=False,
                    is_planet=True,
                    planet_type=planet,
                    minimum_bid=planet_min_bid.get(planet, 100)
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
        # Reset round state and deal fresh hands at round start.
        if self.current_set == 1:
            self.player.reset_round()
            self.ai.reset_round()
            self._apply_round_discard_modifiers()
            self.round_disabled_jokers = {0: [], 1: []}

            self.player.hand = []
            self.ai.hand = []

        self._resolve_set_first_player()

        # Between sets in the same round, keep remaining cards and refill to 8.

        while len(self.player.hand) < 8:
            self.draw_cards(self.player, 1)
        while len(self.ai.hand) < 8:
            self.draw_cards(self.ai, 1)

        self.current_phase = GamePhase.SET_PLAY
        self.add_action(f"Round {self.current_round}, Set {self.current_set} started")

    def _resolve_set_first_player(self):
        """Determine who acts first for this set."""
        if self.current_round == 1 and self.current_set == 1 and self.previous_set_winner is None:
            player_draw = self._draw_and_shuffle_back(self.player)
            ai_draw = self._draw_and_shuffle_back(self.ai)

            player_strength = self._initiative_card_strength(player_draw)
            ai_strength = self._initiative_card_strength(ai_draw)

            tie_break_note = ""
            if player_strength > ai_strength:
                self.set_first_player = 0
            elif ai_strength > player_strength:
                self.set_first_player = 1
            else:
                self.set_first_player = random.choice([0, 1])
                tie_break_note = " (exact tie, random tiebreak)"

            first_name = self.player.name if self.set_first_player == 0 else self.ai.name
            self.last_set_start_event = (
                f"Opening draw for first set: {self.player.name} drew {player_draw}, "
                f"{self.ai.name} drew {ai_draw}. {first_name} goes first{tie_break_note}."
            )
            self.add_action(self.last_set_start_event)
            return

        if self.previous_set_winner in (0, 1):
            self.set_first_player = self.previous_set_winner

        first_name = self.player.name if self.set_first_player == 0 else self.ai.name
        self.last_set_start_event = f"{first_name} goes first this set (won previous set)."
        self.add_action(self.last_set_start_event)

    @staticmethod
    def _initiative_card_strength(card: Card) -> Tuple[int, int]:
        """Return comparable strength tuple for initiative draw cards."""
        suit_strength = {
            Suit.CLUBS: 1,
            Suit.DIAMONDS: 2,
            Suit.HEARTS: 3,
            Suit.SPADES: 4,
        }
        return (card.rank.rank_order(), suit_strength[card.suit])

    def _draw_and_shuffle_back(self, player: Player) -> Card:
        """Draw one card for initiative and shuffle it back into deck."""
        if not player.deck:
            player.deck = self._create_deck()

        card = player.deck.pop(0)
        player.deck.append(card)
        random.shuffle(player.deck)
        return card

    def score_set(
        self,
        player_cards: List[Card],
        ai_cards: List[Card],
        player_copyright_target: Optional[Joker] = None,
        ai_copyright_target: Optional[Joker] = None,
    ):
        """Score a set based on played hands."""
        player_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
            player_cards, self.player, self.round_disabled_jokers[0]
        )
        ai_hand = PokerHandEvaluator.evaluate_hand_with_modifiers(
            ai_cards, self.ai, self.round_disabled_jokers[1]
        )

        # Copyright: same hand type disables one opponent joker for the round.
        if player_hand.hand_rank == ai_hand.hand_rank:
            self._apply_copyright_round_disable(
                player_target=player_copyright_target,
                ai_target=ai_copyright_target,
            )

        player_score = ScoringRules.calculate_score(
            player_hand,
            self.player,
            self.ai,
            opponent_hand_cards=ai_hand.cards,
            disabled_jokers=self.round_disabled_jokers[0],
            opponent_disabled_jokers=self.round_disabled_jokers[1],
        )
        ai_score = ScoringRules.calculate_score(
            ai_hand,
            self.ai,
            self.player,
            opponent_hand_cards=player_hand.cards,
            disabled_jokers=self.round_disabled_jokers[1],
            opponent_disabled_jokers=self.round_disabled_jokers[0],
        )

        self.player.round_score += player_score.final_score
        self.ai.round_score += ai_score.final_score

        if player_score.final_score > ai_score.final_score:
            self.previous_set_winner = 0
            set_winner = self.player.name
            self.add_action(
                f"{set_winner} wins set {self.current_set}: "
                f"{self.player.name} {player_score.final_score} vs {self.ai.name} {ai_score.final_score}"
            )
        elif ai_score.final_score > player_score.final_score:
            self.previous_set_winner = 1
            set_winner = self.ai.name
            self.add_action(
                f"{set_winner} wins set {self.current_set}: "
                f"{self.player.name} {player_score.final_score} vs {self.ai.name} {ai_score.final_score}"
            )
        else:
            # No winner on tied sets; keep existing first-player side for the next set.
            self.previous_set_winner = self.set_first_player
            retained = self.player.name if self.set_first_player == 0 else self.ai.name
            self.add_action(
                f"Set {self.current_set} tied: "
                f"{self.player.name} {player_score.final_score} vs {self.ai.name} {ai_score.final_score}. "
                f"{retained} keeps first move next set."
            )

        return player_score, ai_score

    def _apply_round_discard_modifiers(self):
        """Apply SCRAPPY/STRAITJACKET effects for the whole round."""
        player_scrappy = sum(1 for j in self.player.jokers if j.type == JokerType.SCRAPPY)
        ai_scrappy = sum(1 for j in self.ai.jokers if j.type == JokerType.SCRAPPY)
        player_jacketed = sum(1 for j in self.ai.jokers if j.type == JokerType.STRAITJACKET)
        ai_jacketed = sum(1 for j in self.player.jokers if j.type == JokerType.STRAITJACKET)

        self.player.discard_actions_max = max(0, 2 + player_scrappy - player_jacketed)
        self.ai.discard_actions_max = max(0, 2 + ai_scrappy - ai_jacketed)

    def _apply_copyright_round_disable(
        self,
        player_target: Optional[Joker] = None,
        ai_target: Optional[Joker] = None,
    ):
        """Disable one opponent joker for the entire round when COPYRIGHT triggers."""
        if self._player_has_active_joker(self.player, JokerType.COPYRIGHT, 0):
            target = player_target if self._is_active_copyright_target(player_target, self.ai, 1) else self._pick_highest_value_active_joker(self.ai, 1)
            if target is not None:
                self.round_disabled_jokers[1].append(target)
                self.add_action(f"COPYRIGHT: Player disables AI joker {target}")

        if self._player_has_active_joker(self.ai, JokerType.COPYRIGHT, 1):
            target = ai_target if self._is_active_copyright_target(ai_target, self.player, 0) else self._pick_highest_value_active_joker(self.player, 0)
            if target is not None:
                self.round_disabled_jokers[0].append(target)
                self.add_action(f"COPYRIGHT: AI disables Player joker {target}")

    def has_active_copyright(self, player_index: int) -> bool:
        """Public helper to check whether a side can trigger COPYRIGHT now."""
        player = self.player if player_index == 0 else self.ai
        return self._player_has_active_joker(player, JokerType.COPYRIGHT, player_index)

    def get_active_copyright_targets(self, target_index: int) -> List[Joker]:
        """Public helper to list valid COPYRIGHT targets for a side."""
        target_player = self.player if target_index == 0 else self.ai
        return self._get_active_copyright_targets(target_player, target_index)

    def _is_active_copyright_target(self, target: Optional[Joker], target_player: Player, target_index: int) -> bool:
        """Check if target joker is currently valid for COPYRIGHT disable."""
        if target is None:
            return False
        return target in self._get_active_copyright_targets(target_player, target_index)

    def _get_active_copyright_targets(self, target: Player, target_index: int) -> List[Joker]:
        """List active target jokers that can be disabled by COPYRIGHT."""
        disabled = self.round_disabled_jokers[target_index]
        return [
            j for j in target.jokers
            if j not in disabled and j.type != JokerType.COPYRIGHT
        ]

    def _player_has_active_joker(self, player: Player, jtype: JokerType, player_index: int) -> bool:
        """Check if player has at least one active (non-disabled) joker type."""
        disabled = self.round_disabled_jokers[player_index]
        for joker in player.jokers:
            if joker.type == jtype and joker not in disabled:
                return True
        return False

    def _pick_highest_value_active_joker(self, target: Player, target_index: int) -> Optional[Joker]:
        """Pick strongest active target joker for automatic COPYRIGHT behavior."""
        active = self._get_active_copyright_targets(target, target_index)
        if not active:
            return None
        return max(active, key=lambda j: self._ai_joker_value(j.type))

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
        # Round hand leftovers are not shown/used during auction.
        self.player.hand = []
        self.ai.hand = []

        # Reveal up to 5 unique card types from remaining supply without consuming
        # cards until they are actually won.
        self.auction_state.revealed_cards = self._build_unique_auction_reveal(self.auction_deck, limit=5)

        self.auction_state.current_card_index = 0
        self.auction_state.card_bids = [0 for _ in self.auction_state.revealed_cards]
        self.auction_state.card_leaders = [-1 for _ in self.auction_state.revealed_cards]
        self.auction_state.card_player_bids = [0 for _ in self.auction_state.revealed_cards]
        self.auction_state.card_ai_bids = [0 for _ in self.auction_state.revealed_cards]
        self.auction_state.card_player_last_raise_turn = [-1 for _ in self.auction_state.revealed_cards]
        self.auction_state.card_ai_last_raise_turn = [-1 for _ in self.auction_state.revealed_cards]
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

    def _build_unique_auction_reveal(self, source_cards: List[AuctionCard], limit: int = 5) -> List[AuctionCard]:
        """Build a reveal list with unique card types from source order."""
        revealed_cards: List[AuctionCard] = []
        revealed_keys = set()

        for card in source_cards:
            if len(revealed_cards) >= limit:
                break
            key = self._auction_card_key(card)
            if key not in revealed_keys:
                revealed_keys.add(key)
                revealed_cards.append(card)

        return revealed_cards

    def get_next_auction_jokers(self, limit: int = 2) -> List[JokerType]:
        """Peek up to N joker types that will appear in the next auction reveal."""
        revealed_cards = self._build_unique_auction_reveal(self.auction_deck, limit=5)
        joker_types: List[JokerType] = []
        for card in revealed_cards:
            if card.is_joker and card.joker_type is not None:
                joker_types.append(card.joker_type)
                if len(joker_types) >= limit:
                    break
        return joker_types

    @staticmethod
    def _auction_card_key(card: AuctionCard):
        """Unique key for duplicate prevention within a single reveal."""
        if card.is_joker and card.joker_type is not None:
            return ("joker", card.joker_type)
        if card.is_planet and card.planet_type is not None:
            return ("planet", card.planet_type)
        return ("unknown", card.id)

    def get_current_auction_card(self) -> Optional[AuctionCard]:
        """Get a representative auction card for preview panes."""
        if not self.auction_state.is_active:
            return None
        if not self.auction_state.revealed_cards:
            return None
        return self.auction_state.revealed_cards[0]

    def get_card_min_next_bid(self, card_index: int) -> int:
        """Get next legal bid for a specific revealed auction card."""
        if card_index < 0 or card_index >= len(self.auction_state.revealed_cards):
            return 0

        current_bid = self.auction_state.card_bids[card_index]
        minimum = self.auction_state.revealed_cards[card_index].minimum_bid
        if current_bid == 0:
            return minimum
        return current_bid + minimum

    def get_min_next_bid(self) -> int:
        """Get the minimum legal next bid for the current auction card."""
        if not self.auction_state.revealed_cards:
            return 0
        return self.get_card_min_next_bid(0)

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
        return self.place_auction_bid_for_card(player_index, 0, bid_amount)

    def place_auction_bid_for_card(self, player_index: int, card_index: int, bid_amount: int) -> bool:
        """Place a bid on a specific revealed card during the current turn."""
        if not self.auction_state.is_active:
            return False

        if player_index != self.get_next_auction_bidder():
            return False

        if card_index < 0 or card_index >= len(self.auction_state.revealed_cards):
            return False

        card = self.auction_state.revealed_cards[card_index]

        # Check if bid is legal.
        min_next_bid = self.get_card_min_next_bid(card_index)

        if bid_amount < min_next_bid:
            return False

        # Place the bid
        if player_index == 0:
            previous_bid = self.auction_state.card_player_bids[card_index]
            self.auction_state.card_player_bids[card_index] = bid_amount
            if bid_amount > previous_bid:
                self.auction_state.card_player_last_raise_turn[card_index] = self.auction_state.turn_index
        else:
            previous_bid = self.auction_state.card_ai_bids[card_index]
            self.auction_state.card_ai_bids[card_index] = bid_amount
            if bid_amount > previous_bid:
                self.auction_state.card_ai_last_raise_turn[card_index] = self.auction_state.turn_index

        self._sync_card_leader_and_bid(card_index)
        # Legacy fields kept synced for any preview logic.
        self.auction_state.current_bid = self.auction_state.card_bids[card_index]
        self.auction_state.current_leader = self.auction_state.card_leaders[card_index]
        self.auction_state.last_bidder = player_index

        bidder_name = "Player" if player_index == 0 else "AI"
        self.add_action(f"{bidder_name} bids {bid_amount} on {card}")

        return True

    def reduce_auction_bid_for_card(self, player_index: int, card_index: int) -> bool:
        """Reduce a bidder's current offer on a revealed card by the card minimum (floor 0)."""
        if not self.auction_state.is_active:
            return False

        if player_index != self.get_next_auction_bidder():
            return False

        if card_index < 0 or card_index >= len(self.auction_state.revealed_cards):
            return False

        if not self.can_reduce_auction_bid_for_card(player_index, card_index):
            return False

        minimum_step = self.auction_state.revealed_cards[card_index].minimum_bid
        if player_index == 0:
            current = self.auction_state.card_player_bids[card_index]
            if current <= 0:
                return False
            self.auction_state.card_player_bids[card_index] = max(0, current - minimum_step)
        else:
            current = self.auction_state.card_ai_bids[card_index]
            if current <= 0:
                return False
            self.auction_state.card_ai_bids[card_index] = max(0, current - minimum_step)

        self._sync_card_leader_and_bid(card_index)
        self.auction_state.current_bid = self.auction_state.card_bids[card_index]
        self.auction_state.current_leader = self.auction_state.card_leaders[card_index]
        self.auction_state.last_bidder = player_index

        bidder_name = "Player" if player_index == 0 else "AI"
        card = self.auction_state.revealed_cards[card_index]
        reduced_to = self.auction_state.card_player_bids[card_index] if player_index == 0 else self.auction_state.card_ai_bids[card_index]
        self.add_action(f"{bidder_name} reduces bid to {reduced_to} on {card}")
        return True

    def can_reduce_auction_bid_for_card(self, player_index: int, card_index: int) -> bool:
        """Return whether a bidder can reduce a card bid this turn."""
        if not self.auction_state.is_active:
            return False
        if player_index != self.get_next_auction_bidder():
            return False
        if card_index < 0 or card_index >= len(self.auction_state.revealed_cards):
            return False

        if player_index == 0:
            return self.auction_state.card_player_last_raise_turn[card_index] == self.auction_state.turn_index
        return self.auction_state.card_ai_last_raise_turn[card_index] == self.auction_state.turn_index

    def _sync_card_leader_and_bid(self, card_index: int):
        """Sync aggregate bid/leader from per-player card bids."""
        player_bid = self.auction_state.card_player_bids[card_index]
        ai_bid = self.auction_state.card_ai_bids[card_index]
        previous_leader = self.auction_state.card_leaders[card_index]

        if player_bid == 0 and ai_bid == 0:
            self.auction_state.card_bids[card_index] = 0
            self.auction_state.card_leaders[card_index] = -1
            return

        if player_bid > ai_bid:
            self.auction_state.card_bids[card_index] = player_bid
            self.auction_state.card_leaders[card_index] = 0
            return

        if ai_bid > player_bid:
            self.auction_state.card_bids[card_index] = ai_bid
            self.auction_state.card_leaders[card_index] = 1
            return

        # Tie: preserve current leader when possible, otherwise use auction first bidder.
        self.auction_state.card_bids[card_index] = player_bid
        if previous_leader in (0, 1):
            self.auction_state.card_leaders[card_index] = previous_leader
        else:
            self.auction_state.card_leaders[card_index] = self.auction_state.first_bidder

    def pass_auction_bid(self, player_index: int) -> bool:
        """Pass and end turn in auction."""
        return self.end_auction_turn(player_index)

    def end_auction_turn(self, player_index: int) -> bool:
        """End bidder's turn (pass priority to the other side)."""
        if not self.auction_state.is_active:
            return False

        if player_index != self.get_next_auction_bidder():
            return False

        bidder_name = "Player" if player_index == 0 else "AI"
        self.add_action(f"{bidder_name} ends bidding turn")

        self.auction_state.turn_index += 1

        if self.auction_state.turn_index >= 4:
            self._resolve_all_auction_cards()

        return True

    def _resolve_all_auction_cards(self):
        """Resolve all revealed cards after all bidding turns complete."""
        for idx, card in enumerate(self.auction_state.revealed_cards):
            leader = self.auction_state.card_leaders[idx]
            winning_bid = self.auction_state.card_bids[idx]

            if leader == -1 or winning_bid <= 0:
                self.add_action(f"{card} is unsold.")
                continue

            winner = self.player if leader == 0 else self.ai
            self._apply_auction_card(leader, card)
            if leader == 0:
                self.auction_state.player_spent += winning_bid
            else:
                self.auction_state.ai_spent += winning_bid
            self.add_action(f"{winner.name} won {card} for {winning_bid} momentum")

        self._cycle_revealed_cards_to_back(self.auction_state.revealed_cards)

        self._finish_auction()

    def _cycle_revealed_cards_to_back(self, revealed_cards: List[AuctionCard]):
        """Move revealed unsold cards to the back so next auction cycles to fresh cards."""
        carry_to_back = [card for card in revealed_cards if card in self.auction_deck]
        if not carry_to_back:
            return

        remaining = [card for card in self.auction_deck if card not in carry_to_back]
        self.auction_deck = remaining + carry_to_back

        self.add_action(
            f"{len(carry_to_back)} revealed unsold card(s) cycled to back of auction deck."
        )

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
            if card in self.auction_deck:
                self.auction_deck.remove(card)

            if winner_index == 1 and len(player.jokers) > 5:
                # AI auto-removes lowest value joker when over cap.
                self._auto_trim_ai_jokers()

            if winner_index == 0 and len(player.jokers) > 5:
                self.auction_state.pending_human_joker_choice = True

        elif card.is_planet and card.planet_type is not None:
            player.planets.append(card.planet_type)
            if card in self.auction_deck:
                self.auction_deck.remove(card)

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

        # Resume auction settlement now that overflow choice is resolved.
        if self.auction_state.is_active:
            self._finish_auction()

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
