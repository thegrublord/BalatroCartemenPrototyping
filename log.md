# Change Log

## 2026-04-06 - Prompt 35 (Panel Spacer Placement Fix)
- Repositioned left panel stretch spacer to below the NEW GAME button so the button no longer gets pushed downward by extra column space.
- Updated right panel layout to remove stretch weighting from Action Log and place a bottom spacer after both sections.
- This keeps extra black space at the bottom of side columns rather than between Human/Latest Event sections.

## 2026-04-06 - Prompt 34 (Side Panel Height Restore)
- Extended the first-round layout snapshot to include left/right panel section heights.
- Restored fixed heights for:
  - Human details panel
  - AI details panel
  - Action Log panel (including Latest Event region)
- This keeps side columns from stretching vertically after auction transitions.

## 2026-04-06 - Prompt 33 (Top-Aligned Center Column)
- Anchored the center column to the top of the main layout in fullscreen so it no longer floats vertically after auction.
- Changed the center frame from fixed-height to preferred-height sizing, then forced a layout/size refresh after restoring the first-round state.
- This should keep the round UI in the same vertical position as the first round without requiring a fullscreen toggle.

## 2026-04-06 - Prompt 32 (Center Column Height Policy Fix)
- Set the center play column and its key child panels to height-fixed sizing so later rounds cannot inherit the taller auction layout.
- Constrained the hand scroll and action button area to fixed vertical sizing, while keeping the center column width flexible.
- This should prevent the next round from being pushed downward in fullscreen after an auction round.

## 2026-04-06 - Prompt 31 (Fullscreen Layout Reflow)
- Added an explicit top-level layout reflow after restoring the first-round UI so fullscreen mode recalculates the center and side panel positions immediately.
- This avoids relying on a manual fullscreen toggle to make the next round render correctly.
- The fix keeps the window size unchanged and only refreshes widget layout state.

## 2026-04-06 - Prompt 30 (Fullscreen-Safe Round Layout Restore)
- Removed the geometry resize from the round layout restore path so fullscreen and maximized windows stay in their current size.
- The game now only restores widget visibility and spacing between rounds, which should keep fullscreen mode active while preserving the first-round UI positions.
- Also removed the forced resize on new game and after auction so the window state remains unchanged.

## 2026-04-06 - Prompt 29 (Restore First-Round Layout Snapshot)
- Replaced the ad hoc auction reset behavior with a first-round layout snapshot that is captured during normal play and restored after auction.
- Stopped forcing the hidden auction board to zero height, which was leaving the later rounds visually stretched.
- This should make the later rounds reuse the same layout state and widget spacing as the first round.

## 2026-04-06 - Prompt 28 (End-of-Refresh Layout Restore)
- Moved the normal-layout restore to the end of the UI refresh cycle so it runs after all auction-to-play widget updates settle.
- This is meant to prevent the next round from re-expanding the screen after the auction board is hidden.
- Keeps the center, side panels, and bottom buttons aligned the same way they are in the first round.

## 2026-04-06 - Prompt 27 (Auction Collapse on Round Transition)
- Fixed the auction board so it fully collapses when auction ends instead of leaving behind extra vertical space.
- Deferred restoring the normal window size until the layout settles, which keeps the next round's play screen from shifting downward.
- This should keep the card/play section and buttons in their normal position after auction transitions.

## 2026-04-06 - Prompt 26 (Auction Window Size Reset)
- Fixed the auction-to-play transition so the game window is resized back to the normal play layout after auction growth.
- Also restore the normal window size when starting a new game from auction so New Game and Play Hand stay accessible on-screen.
- This addresses the visible downward shift caused by the auction board enlarging the overall window.

## 2026-04-06 - Prompt 25 (New Game Momentum Reset)
- Fixed the New Game path so player and AI momentum reset to 0 visibly and in game state.
- Also reset round score, discard counters, decks, jokers, planets, auction state, and round tracking on a fresh game.
- This keeps the UI attached to the same player objects while still restoring a true clean start.

## 2026-04-06 - Prompt 24 (New Game Auction UI Reset)
- Fixed the new-game path so starting over from auction restores the normal play layout instead of leaving auction UI state behind.
- Added an explicit UI reset when New Game is pressed:
  - Stops any pending AI timer action
  - Hides and clears the auction board
  - Restores the normal title/header sizing
  - Forces the played-hands area back into its normal visible state
- Logged this change immediately as requested.

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

## 2026-04-04 - Prompt 14 (Special Joker Rules - Group 1)
- Implemented modifier-aware hand evaluation engine and integrated it into gameplay/UI scoring paths.
- Implemented round-start discard modifier application:
  - SCRAPPY grants +1 discard per copy
  - STRAITJACKET applies -1 discard per copy to opponent
  - Effects are applied at the start of each round (after auction acquisitions).
- Implemented COPYRIGHT as a round-long disable mechanic:
  - Triggers when both players play the same hand type in a set.
  - Disables one active opponent joker for the rest of the round.
  - Current behavior auto-selects highest-value active opponent joker.
- Implemented BLACK HOLE scoring impact:
  - Opponent aces in played hand count as 0 card chips.
- Implemented FOUR FINGERS flush logic:
  - Any 4 cards of same (normalized) suit count as Flush with any fifth card.
- Implemented SHORTCUT straight logic:
  - Any 4 cards that fit a straight window with up to one missing rank count as Straight with any fifth card.
- Implemented UNIFORM/SMEAR suit normalization effects:
  - Affects flush detection and suit-based joker chip bonuses (Greedy/Lover/Protector/Chairman).
- Updated AI hand decision/selection and window scoring previews to use modifier-aware evaluation/scoring.
- Verified all modified files report no editor diagnostics errors.

## 2026-04-04 - Prompt 15 (COPYRIGHT Target Exclusion)
- Added rule: COPYRIGHT cannot disable an opponent COPYRIGHT.
- Kept sequential COPYRIGHT resolution order unchanged.
- Auto-target selector now excludes opponent jokers of type COPYRIGHT from disable candidates.
- Verified updated game state module has no editor diagnostics errors.

## 2026-04-04 - Prompt 16 (Set-to-Set Hand Persistence Fix)
- Fixed set transition hand behavior within rounds.
- At round start (Set 1), both players receive a fresh random 8-card hand.
- Between sets in the same round, remaining cards are now preserved and each player only draws up to 8.
- This ensures a played 5-card hand leaves 3 cards to carry into the next set, then refills with 5 new cards.
- Verified updated game state module has no editor diagnostics errors.

## 2026-04-04 - Prompt 17 (Auction Minimum Bid Alignment)
- Updated auction minimum bids to match spreadsheet rules.
- Jokers now use rarity-wide defaults:
  - Common: 100
  - Rare: 250
  - Legendary: 500
- Planets now use per-card minimum bids:
  - Pluto 100, Mercury 100, Uranus 100, Venus 150
  - Saturn 250, Jupiter 150, Earth 250, Mars 250, Neptune 300
- Verified updated game state module has no editor diagnostics errors.

## 2026-04-04 - Prompt 18 (Live Selected-Hand Projection)
- Added a live preview section directly under "YOUR HAND".
- On every card click, preview now updates immediately (without requiring exactly 5 selected cards).
- Preview shows:
  - Selected count
  - Projected hand type
  - Projected total chips
  - Projected multiplier (additive and x-mult components)
  - Projected final score
- For fewer than 5 selected cards, it projects the best 5-card outcome that includes selected cards.
- Verified updated main window module has no editor diagnostics errors.

## 2026-04-04 - Prompt 19 (Selected-Only Hand Preview Fix)
- Corrected hand preview behavior for fewer than 5 selected cards.
- Preview now uses only selected cards and does not auto-fill with additional cards.
- Incomplete selections (<5) are shown as High Card (Incomplete) for preview scoring.
- This fixes cases where selecting a single card incorrectly displayed advanced hand types/scores.
- Verified updated main window module has no editor diagnostics errors.

## 2026-04-04 - Prompt 20 (Variable-Size Hand Type Preview)
- Upgraded pre-play hand preview to evaluate selected cards as a variable-size hand (2-5 cards).
- Preview now correctly detects partial-size hand types like Pair/Trips/Quads/Straight/Flush where applicable.
- Flush and straight detection for partial hands now respect active joker rule modifiers (e.g., FOUR FINGERS, SHORTCUT, UNIFORM, SMEAR).
- Removed forced "High Card (Incomplete)" behavior for all selections under 5 cards.
- Verified updated main window module has no editor diagnostics errors.

## 2026-04-04 - Prompt 21 (Preview Straight/Flush Threshold Fix)
- Corrected preview thresholds for flush/straight hand types.
- Straight/Flush now require 5 selected cards by default.
- Flush can appear at 4 selected cards only with FOUR FINGERS active.
- Straight can appear at 4 selected cards only with SHORTCUT active.
- Verified updated main window module has no editor diagnostics errors.

## 2026-04-04 - Prompt 22 (Hide Hand Section During Auction)
- Updated center UI so the full "YOUR HAND" section is hidden while in auction phase.
- Hidden elements during auction include:
  - "YOUR HAND" label
  - selected-hand preview panel
  - hand card scroll area
  - play/discard action buttons
- Cleared remaining player/AI hand cards at auction start so end-of-round leftovers are removed until next round begins.
- Verified updated main window and game state modules have no editor diagnostics errors.

## 2026-04-04 - Prompt 23 (Simultaneous 5-Card Auction Flow)
- Refactored auction system from one-card-at-a-time to simultaneous bidding across all 5 revealed cards.
- Added per-card auction tracking in state:
  - card_bids list
  - card_leaders list
- Turn flow is now:
  - bidder places bids on any subset of the 5 cards during their turn
  - bidder clicks End Bidding Turn
  - after 4 turn rounds, all 5 cards resolve at once
- Implemented per-card bid placement API in game state (`place_auction_bid_for_card`) and per-card min-next-bid logic.
- Added new center auction board UI that replaces PLAYED HANDS during auction, showing for each card:
  - image
  - name
  - description
  - minimum bid / current bid / leader / next legal bid
  - bid button
- Added bottom "END BIDDING TURN" action for human.
- Updated AI auction turn logic to bid across multiple cards in one turn and then end turn.
- Legacy single-card auction controls are now hidden/disabled in behavior.
- Verified updated model/state/ai/ui modules have no editor diagnostics errors.

## 2026-04-04 - Prompt 24 (Compact Auction Card Tiles)
- Reduced auction card tile vertical footprint to keep controls accessible.
- Changed auction layout to a single-row card grid with compact per-card sizing.
- Added a constrained-height scroll area for the card board to prevent full-screen takeover.
- Reduced image, text, and button sizing inside each tile for better fit.
- Verified updated main window module has no editor diagnostics errors.

## 2026-04-04 - Prompt 25 (No Duplicate Cards Per Reveal)
- Updated auction reveal logic so the 5 revealed cards are unique by card type/name within each reveal.
- Duplicate copies remain in the overall auction deck and can still appear in later rounds.
- Added auction-card uniqueness key helper for joker/planet duplicate filtering during reveal selection.
- Verified updated game state module has no editor diagnostics errors.

## 2026-04-04 - Prompt 26 (Auction Board Indentation Error Fix)
- Fixed malformed indentation in the auction board render loop inside `_update_auction_board_ui`.
- Normalized indentation for frame/layout/image/name/description widget setup under the per-card loop.
- Resolved runtime `IndentationError` in `ui/main_window.py` and confirmed no editor diagnostics errors for that file.

## 2026-04-04 - Prompt 27 (Compact Auction Headers + Bid Reduction Button)
- Reduced vertical footprint of auction header bubbles in center panel:
  - "AUCTION BOARD" title now uses compact chip-style styling.
  - Auction turn/details line now uses a smaller fixed-height info chip.
- Added a new per-card `Bid -Min` button directly under `Bid +Min`.
- Implemented reversible per-player card bidding state so reducing works correctly against existing AI/player bids.
- Added state API `reduce_auction_bid_for_card` that subtracts by card minimum and clamps at 0.
- Updated aggregate card leader/current bid syncing after both raises and reductions.
- Verified no editor diagnostics errors in updated model/state/ui files.
