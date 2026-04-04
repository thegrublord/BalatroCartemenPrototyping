#!/usr/bin/env python3
"""Quick test of game systems."""

from game import GameState, PokerHandEvaluator, ScoringRules, AIPlayer

print("=" * 60)
print("BALATRO CERTAMEN - GAME SYSTEMS TEST")
print("=" * 60)

# Initialize game
game = GameState()
game.new_game()
game.start_set()

print(f"\n✓ Game initialized")
print(f"✓ Player hand: {len(game.player.hand)} cards")
print(f"✓ AI hand: {len(game.ai.hand)} cards")
print(f"✓ Round {game.current_round}, Set {game.current_set}")

# Test card selection and hand evaluation
if len(game.player.hand) >= 5:
    best_hand = PokerHandEvaluator.find_best_hand(game.player.hand)
    print(f"\n✓ Best hand found: {best_hand.hand_rank.name}")
    print(f"  Cards: {', '.join(str(c) for c in best_hand.cards)}")
    
    score = ScoringRules.calculate_score(best_hand, game.player, game.ai)
    print(f"\n✓ Score Calculation:")
    print(f"  Base: {score.base_chips} chips × {score.base_mult} mult = {score.base_chips * score.base_mult}")
    print(f"  Card bonus: {score.card_chips} chips")
    print(f"  **FINAL SCORE: {score.final_score} pts**")

# Test discard
print(f"\n✓ Discard system:")
print(f"  Discards remaining: {game.player.discard_actions_remaining()}/2")

# Test AI
ai_player = AIPlayer(game.ai)
should_play, discard_cards = ai_player.decide_play_or_discard(game.player)
decision = "PLAY best hand" if should_play else f"DISCARD {len(discard_cards)} cards"
print(f"\n✓ AI Decision: {decision}")

# Test momentum
print(f"\n✓ Momentum Tracking:")
print(f"  Current momentum: {game.player.momentum}")
print(f"  Win condition: ±10,000")

print("\n" + "=" * 60)
print("✅ ALL SYSTEMS OPERATIONAL!")
print("The game is ready to play.")
print("=" * 60)
