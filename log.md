# Change Log

## 2026-04-04 - Prompt 1 (Auction Phase + Momentum)
- Implemented full auction flow in game state with 5 revealed cards auctioned one-by-one.
- Enforced 4-turn bidding order per card: Winner -> Loser -> Winner -> Loser.
- Added minimum-raise rules for bids and pass handling per turn.
- Implemented unsold-card behavior (permanently discarded).
- Added tie handling for first bidder: ties inherit the previous auction's first bidder.
- Added auction settlement momentum logic after all 5 cards resolve.
- Integrated auction inventory rewards (jokers/planets) and persistence into players.
- Added joker overflow handling:
  - Human: prompted to choose a joker to discard when over 5.
  - AI: auto-discards lowest-value joker when over 5.
- Added auction UI block in the main window with:
  - Current card info
  - Bid/leader/next legal bid info
  - Min Raise button
  - Numeric custom bid input + Custom Bid button
  - Pass button
- Replaced previous "auction not yet implemented" set-flow stub with live auction phase transitions.

## 2026-04-04 - Prompt 2 (Resume / Verification)
- Resumed implementation after interruption and verified auction-related files compile cleanly in editor diagnostics.
- Confirmed no current type/syntax errors in:
  - game/state.py
  - ui/main_window.py
  - game/ai.py
  - game/models.py
- Continued using log.md as the running historical record per prompt.

## 2026-04-04 - Prompt 3 (Auction Auto-Collect + Status UI Upgrade)
- Implemented immediate auction resolution when a bidder exists and the opponent passes.
  - Example: player bids, AI immediately passes, card is awarded without waiting for remaining turns.
- Updated auction momentum settlement formula to:
  - momentum = momentum - player_spent + ai_spent
  - AI momentum mirrors as negative of player momentum.
- Added a polished center status header with:
  - Round/Set banner (e.g., "Round 3, Set 1")
  - Player vs AI points tiles with centered score values and labels beneath.
- Upgraded left status text to include phase, remaining discards, and signed momentum formatting.
- Verified no editor diagnostics errors after changes in modified files.

## 2026-04-04 - Prompt 4 (Lower-Left Auction Card Preview)
- Added a new lower-left panel under player stats showing:
  - Current auction card image
  - Card title
  - Card description/effect summary
- Wired preview updates to the active auction card; includes fallback text when not in auction.
- Added WebP image loading for auction cards from the assets folder with predictable naming.
  - Jokers: assets/auction_cards/jokers/joker_<joker_name_lower>.webp
  - Planets: assets/auction_cards/planets/planet_<planet_name_lower>.webp
- Added graceful fallback state "Image Missing" if expected art file is not present.
- Verified no editor diagnostics errors in updated UI module.

## 2026-04-04 - Prompt 5 (Capitalized Image Naming Convention)
- Updated image path resolution to prefer capitalized-word filenames:
  - Jokers: Joker_<Capitalized_Words>.webp
  - Planets: Planet_<Capitalized_Words>.webp
- Added fallback support for previous lowercase filenames so existing assets still work.

## 2026-04-04 - Prompt 6 (Auction Spend + Discard Counters)
- Added auction spend tracking display to the auction panel:
  - "Spent This Auction: Player X | AI Y"
  - Updates live after each resolved card bid outcome using existing auction_state totals.
- Added compact discard counters into both score boxes in the center header:
  - Player tile shows "Discards Left: N"
  - AI tile shows "Discards Left: N"
- Kept left-side status text cleaner by replacing discard line with round score summary.
- Verified updated UI module has no editor diagnostics errors.

## 2026-04-04 - Prompt 7 (Auction Detail Line Condense)
- Condensed auction phase visibility by combining detail lines.
- Removed dedicated auction spend line and merged spend totals into the turn line.
- Auction details now use fewer rows while preserving current bid, leader, next legal bid, turn order, and spend totals.
- Verified updated UI module has no editor diagnostics errors.

## 2026-04-04 - Prompt 8 (Yellow Accent Tone Refinement)
- Replaced bright yellow accent text with a more muted premium gold tone for a more professional look.
- Updated accent color in main window headers/labels and shared side panels.
- New accent color used: #c9a66b.
- Verified updated UI files have no editor diagnostics errors.

## 2026-04-04 - Prompt 9 (Professional Game-Like Font System)
- Replaced Arial usage in key UI headers and panels with Bahnschrift for a cleaner game-facing style.
- Applied global UI fallback styling:
  - QLabel uses Segoe UI
  - QPushButton uses Segoe UI Semibold
- Updated card rank typography to Bahnschrift and suit glyphs to Segoe UI Symbol for crisp card readability.
- Verified updated UI files have no editor diagnostics errors.

## 2026-04-04 - Prompt 10 (Action Log Readability Upgrade)
- Improved action log readability with larger, cleaner text styling and padded entry cards.
- Added numbered log entries (e.g., 001, 002, 003) to show event sequence clearly.
- Constrained visible log viewport to about six events while keeping deep scrollable history.
- Increased retained history capacity (up to 300 entries) to support scrolling through older actions.
- Verified updated UI panel module has no editor diagnostics errors.

## 2026-04-04 - Prompt 11 (Live Action Log Header)
- Updated the top Action Log header block to be event-driven instead of static text.
- Header now displays: "Latest Event: <number>. <event text>" and updates with each new log entry.
- Keeps numbered scrollable entries while making the top block part of the live event feed.
- Verified updated UI panel module has no editor diagnostics errors.

## 2026-04-04 - Prompt 12 (Latest Event Header Sizing)
- Reworked Action Log internal layout to a proportional split.
- Latest Event header area now uses roughly one-third of the Action Log panel.
- Scrollable event history now uses roughly two-thirds of the Action Log panel.
- Verified updated UI panel module has no editor diagnostics errors.

## 2026-04-04 - Prompt 13 (Collection Bubble Windows)
- Added clickable Joker and Planet bubble buttons in both player info panels (human and AI).
- Clicking a bubble now opens a new collection window for that owner and category.
- New collection window shows card image, card name, count, and description in a scrollable gallery grid.
- Supports both naming conventions for image files:
  - Preferred capitalized format (e.g., Joker_The_Tribe.webp, Planet_Pluto.webp)
  - Lowercase fallback format.
- Added empty-collection feedback dialogs when no cards are owned yet.
- Verified updated UI files have no editor diagnostics errors.
