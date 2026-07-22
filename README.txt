SCREENSHOT SESSION ORGANIZER — SETUP GUIDE
============================================

Put all 4 files in the same folder (on each computer you'll use this on):
  - screenshot_organizer.py
  - Start_Windows.bat
  - Start_Mac.command
  - README.txt (this file)

------------------------------------------
ONE-TIME SETUP (do this once per computer)
------------------------------------------

WINDOWS:
1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python" button.
3. Run the installer. IMPORTANT: on the first screen, tick the box
   "Add python.exe to PATH" before clicking Install Now.
4. That's it — no further setup needed.

MAC:
1. Go to https://www.python.org/downloads/
2. Download and run the macOS installer (not the Homebrew version —
   the official installer includes the UI toolkit this tool needs).
3. The first time you double-click Start_Mac.command, macOS may show
   a warning like "cannot be opened because it is from an unidentified
   developer." If that happens: right-click (or Control-click) the file,
   choose "Open", then click "Open" again in the popup. You only need
   to do this once.
4. If double-clicking still does nothing, open Terminal, drag the
   Start_Mac.command file into the Terminal window, press Enter once —
   this also only needs doing once, after which double-click works.

--------------------------
EVERYDAY USE (every time)
--------------------------
Windows: double-click Start_Windows.bat
Mac: double-click Start_Mac.command

A window will open with:
  Step 1: type the year + subject, click "Create New Folder"
          (this creates and opens a folder on your Desktop, e.g. 2026_Biology)
  Step 2: click "Start Auto-Move". The tool now watches wherever your
          capture tool saves screenshots and automatically moves any new
          one into your session folder within a second or two. Just snip
          normally - there's nothing to save manually.
  Step 3: paste the list of diagram names (one per line, in page order)
          into the big text box
  Click "Rename Screenshots", pick the folder, and it renames everything
  at once, in order, e.g. 01_Cell_Structure.png, 02_Mitosis_Phases.png...

IMPORTANT - MAKE SURE AUTO-MOVE CAN FIND YOUR SCREENSHOTS:

WINDOWS (Snipping Tool, Windows 11): auto-save to Pictures\Screenshots is
on by default, and the tool already points there. If it's been turned
off, open Snipping Tool -> the "..." menu (top right) -> Settings ->
turn on "Automatically save screenshots you capture."

WINDOWS 10 (Snip & Sketch): this older app has no auto-save option, so
either update to the modern Snipping Tool via the Microsoft Store, or
just save each snip manually into wherever you've set "Source folder"
to point in the tool, or straight into the session folder itself.

MAC (Cmd+Shift+3/4/5): screenshots save to the Desktop by default, which
is already the tool's default source folder. If you've changed your
save location (via the on-screen capture bar's Options), update the
"Source folder" field in the tool to match.

TIP: To get the ordered list of diagram names for Step 3, upload the PDF
to Claude and ask it to list the figures/diagrams in the order they
appear in the document. Paste that list straight into the tool.
