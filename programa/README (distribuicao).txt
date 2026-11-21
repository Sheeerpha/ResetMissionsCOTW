==========================================================================
  ResetMissionsCOTW  -  version 0.9.9 (Beta)
  Per-map mission reset  -  theHunter: Call of the Wild
  Made by Sheeerpha  -  free and open source
==========================================================================


SUMMARY IN 30 SECONDS
---------------------
  In the game, resetting missions wipes them on ALL maps at once.
  This program only touches the map YOU choose, in two ways:

    * RESET EVERYTHING: clears all missions on the map (like a new
      character).
    * GO BACK STORY MISSIONS: goes back just a few missions and you replay
      from there (great for a mission that got stuck or bugged).

  What does NOT change: other maps, level, XP, money, skills, weapons,
  animals, trophies and the rest of the save.

  In short:
    1. Extract the .zip
    2. Close the game
    3. Open ResetMissionsCOTW.exe
    4. Follow the steps on the left, top to bottom (each one unlocks the
       next) and choose what to do in the map panel
    5. Open the game and enter the map

  This is a test version (Beta). The program is not official and may have
  bugs. That is why it backs up everything first and lets you undo.


==========================================================================
 PART 1 - BEFORE OPENING
==========================================================================

[1] EXTRACT THE FOLDER FROM THE .ZIP
    Right-click the .zip file and choose "Extract All...".
    Use the program from the extracted folder, never from inside the .zip.
    Tip: keep the folder in a fixed place (for example, the Desktop).

[2] CLOSE THE GAME
    With the game open, the program does not change anything.

[3] THE BLUE "WINDOWS PROTECTED YOUR PC" SCREEN
    The first time, Windows will probably show this blue screen.

    It is NORMAL. It shows up for every program without a "digital
    signature" (a paid certificate, renewed every year, that big companies
    buy). This program is free and made by a player, so it does not have
    one. The warning is just a precaution: it does not mean there is a virus.

    To get past it:
      a) Click "More info" (the small text below the message).
      b) Click the "Run anyway" button.
      Done. This usually only happens the first time.

    Want to check first? The code is open and anyone can see what the
    program does: https://github.com/Sheeerpha/ResetMissionsCOTW
    The .exe is built by GitHub itself from that code.
    Always download it from the official page.


==========================================================================
 PART 2 - USING THE PROGRAM
==========================================================================

When it opens, the "Before you start" notice and the "How to use" tutorial
appear. Two other tutorials open on their own at the right moment: "Reset
everything × Go back missions" (when you reach the map choice) and "How to
undo" (after each change). They show up every time until you tick "Don't
show automatically again"; after that they are still available from the
links in the window ("How to use", "Which one?" and "How does it work?").

ON THE LEFT are steps 1 to 4. Each step only unlocks the next one (locked
steps show a 🔒). When done, a step gets a green ✓.
ON THE RIGHT is the map panel (step 5), with the map picture at the top.

STEP 1 - CHECK
    The program checks on its own whether the game, Steam or another
    program is using the save files.
    * Something that BLOCKS (e.g. the game is open): the step stays locked.
      Click "See what to do", fix it and then "Check again".
    * Just a WARNING (e.g. Steam is open): read it in "details" and click
      "I read the warning, continue".

STEP 2 - YOUR SAVE
    The program finds your save on its own (Steam or Epic) and shows the
    character's LEVEL, XP, MONEY and missions, so you can be sure it is
    yours. The "MOST RECENT" badge marks the save you played last. If it is
    right, click "Yes, this is my save".
    * More than one save? Click "Change" and pick one.
    * It did not find your save? Click "Choose folder".
      It is usually: Documents\Avalanche Studios\COTW\Saves\<number>

STEP 3 - FULL BACKUP (required)
    If you do not have one yet, click "Back up the full save": it keeps a
    copy of ALL the save files. You can give it a name (e.g. "before DLC").
    If the last backup is more than 2 days old, the step turns yellow and
    suggests a new one. You can keep the old one with "Continue with the
    X-day-old one".

STEP 4 - CHOOSE THE MAP
    Click the map in the list. The small bar shows how much of the story
    you have done (e.g. "Story 5/8"). "↺ reset" = map already reset.

STEP 5 - WHAT TO DO ON THIS MAP?
    At the top, "You are on:" shows the NAME of the story mission you are
    on. Pick one of the two cards:

    RESET EVERYTHING
      Clears ALL missions on the map (story and side). To reset several
      maps at once, tick the boxes in the list (or "Tick all"). Click the
      green "Reset" button and confirm.

    GO BACK STORY MISSIONS
      Use the − and + buttons (or drag the slider) to choose how many
      missions to go back. The program shows the NAME of the mission you
      will restart at and highlights in orange, on the timeline, everything
      that goes back.
      * 0 = restarts only the mission you are on, from the beginning (for a
        stuck mission).
      * Side missions LINKED to the missions that go back also go back (the
        program shows their names first). Other side missions do not change.
      * When you replay missions, the game may give XP and money again.
      * If a mission changed in a game update after you played it, the
        program does not let you go back to it (for safety).
      Click the orange "Go back N missions" button and confirm.

    Not sure? Click "Which one? See the difference" (tutorial).

    Before changing anything, the program backs up the missions on its own.
    Other maps never change.

    Mission names come from the game installed on your PC (nothing from the
    game is inside the program). If the game is not found, you will see
    "Story mission 5" and you can use "Choose the game folder".

AFTERWARDS (the "Done!" screen reminds you)
    1. Open the game normally.
    2. If Steam Cloud or Epic Cloud asks which version to use, choose the
       LOCAL one (from this computer).
       (If you choose the cloud one, the change is undone.)
    3. Enter the map: the mission will already be active for you to replay.


==========================================================================
 PART 3 - HOW TO UNDO
==========================================================================

At the bottom of the window is the "NEED TO UNDO?" box, ALWAYS available.
The "How does it work?" link opens an illustrated tutorial.

  * "Restore missions"  ->  brings back ONLY the missions.
    1. Click "Restore missions".
    2. Pick the backup in the list. The first one right below the 🔒 is the
       most recent (e.g. "Before going back missions on Revontuli Coast (4)").
    3. Check the table below: the YELLOW rows are the ones that will change.
    4. Click "Restore this backup" and confirm.

  * "Restore full save"  ->  brings back the WHOLE save.
    Pick a full backup (the name you gave it shows in the list).
    Warning: everything you played after that backup is lost.
    (The current save is kept first, just in case.)

  * "Backups folder"
    Opens the folder with the copies. Inside Backups_SAVE there is a file
    explaining how to restore by hand, if you prefer.

YOUR ORIGINAL BACKUP 🔒 (ALWAYS KEPT)
    The first time you use the program, it keeps your missions as they
    were. This original backup stays FOREVER.
    To bring everything back as it was before using the program:
      "Restore missions" -> pick the green "🔒 Original backup" row, always
      at the top of the list -> "Restore this backup" -> confirm.

Where the backups are:
    Documents\.BKP_ResetMissions_Saves_COTW   (hidden folder)
    -> Backups_MISSIONS : up to 50 missions backups. Beyond that, the
       oldest goes away on its own, EXCEPT the original backup 🔒.
    -> Backups_SAVE     : up to 5 full save backups. The oldest one stays
       protected for up to 2 days; after that, the protection moves to the
       next one. The newest backup is never deleted.


==========================================================================
 PART 4 - IF A WARNING SHOWS UP
==========================================================================

"Could not write to the Documents folder" / "Windows is blocking..."
    This happens when Windows Defender's "Controlled folder access"
    protection is on. Click "How to allow it (step by step)": the program
    shows 5 illustrated steps and a button to copy the program's path. It
    takes about 1 minute.
    Note: every new version (or the program in another folder) must be
    allowed again.

"● ... problem(s) block changes" (step 1)
    Something is using the save files (the game, Steam, OneDrive...).
    Click "See what to do". The screen shows what it is and offers buttons
    like "Close Steam" or "Fix". The program NEVER closes anything on its
    own or by force: only when you click. Close the game from its own menu.
    This check only happens on your computer: nothing goes to the internet.

"I could not find the save on my own"
    Use "Choose folder" in step 2.

The game asked which save version to use (cloud)
    Choose the LOCAL one. If you choose the cloud one, the change is undone.


==========================================================================
 PART 5 - OTHER TIPS
==========================================================================

  * Language: the program opens in the Windows language (Portuguese,
    English or Spanish). To change it, click the language name at the top.
  * Light/dark theme: opens like Windows. To change it, click
    "Dark theme" / "Light theme" at the top.
  * "How to use", at the top, shows the tutorial again.
  * New version: every time the program opens, it checks whether one is
    out; if so, a green bar appears at the top with a "Download" link. It
    only checks the project's GitHub page, sends no personal data and
    downloads nothing on its own.
  * The map pictures are the program's own drawings (not from the game).
  * Works on Windows 10 and 11. Nothing to install.
  * Tested on the Steam version. It should work on Epic, but it has not
    been tested yet.


==========================================================================
 FOUND A PROBLEM?
==========================================================================

Open an "Issue" on the project page:
    https://github.com/Sheeerpha/ResetMissionsCOTW/issues

Include:
    1. a screenshot with the message;
    2. what you did before it happened;
    3. the log: click "Logs" at the top of the program and send the most
       recent file. Or, in the error window, click "Copy details" and paste
       it into your report.

The log is in %LOCALAPPDATA%\ResetMissionsCOTW\logs (the 5 most recent are
kept). Your user name and personal data are masked.


==========================================================================
 LIKED IT?
==========================================================================

The program is free and always will be. If it helped you, you can support
it with the "Like it? Support the project" button at the bottom of the
window. Leaving a star on GitHub and telling your friends also helps a lot.
Thank you!

Project page (open source):
    https://github.com/Sheeerpha/ResetMissionsCOTW
