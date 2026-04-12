# Releasing the Standalone Executable

## What We've Built

✅ **Standalone Windows Executable**
- Located in: `release/BalatroCartemen/BalatroCartemen.exe`
- Packaged as: `release/BalatroCartemen-Windows.zip` (47 MB)
- No Python installation required
- All dependencies bundled

## How to Publish to GitHub Releases

### Option 1: Using GitHub Web Interface (Easiest)

1. Go to https://github.com/thegrublord/BalatroCartemenPrototyping
2. Click on "Releases" in the right sidebar
3. Click "Create a new release"
4. Fill in the release details:
   - **Tag version**: `v1.0.0` (or increment accordingly)
   - **Release title**: `Balatro Certamen - v1.0.0 Prebuilt Executable`
   - **Description**:
     ```
     ## Download and Run

     Download `BalatroCartemen-Windows.zip` below, extract it, and double-click `BalatroCartemen.exe` to play!

     No Python installation required. Everything is included.

     ## What's Included
     - Standalone Windows executable
     - All game assets (cards, UI)
     - Ready to play immediately

     ## Release Notes
     - Initial release with full game functionality
     - Includes GUI and simulation engine
     ```
5. Click "Attach files" or drag `release/BalatroCartemen-Windows.zip` into the upload area
6. Click "Publish release"

### Option 2: Using Git from Command Line

```bash
# Tag the current commit
git tag -a v1.0.0 -m "Release v1.0.0 - Prebuilt Windows Executable"

# Push the tag to GitHub
git push origin v1.0.0

# Then create the release on GitHub web interface and upload the zip file
```

## File Structure for Assessors

When they download `BalatroCartemen-Windows.zip`, they'll get:

```
BalatroCartemen/
├── BalatroCartemen.exe        ← Run this!
└── _internal/                 ← Dependencies (don't modify)
    ├── assets/                ← Game cards and images
    ├── Python libraries
    └── ...
```

## Instructions for Users

1. Download `BalatroCartemen-Windows.zip` from Releases
2. Extract the ZIP file anywhere
3. Double-click `BalatroCartemen.exe`
4. Play!

That's it. No setup, no commands, no Python needed.

## Alternative: Building From Source

Users who prefer to build from source can follow the instructions in `README.md`:

1. Clone the repository
2. Install Python 3.8+
3. Run: `python main.py`

## Notes

- The executable is approximately 50 MB total (including `_internal` files)
- First launch may take a few seconds as the bundled Python environment initializes
- The game can be run from any location
- All game data is included and doesn't need external files
