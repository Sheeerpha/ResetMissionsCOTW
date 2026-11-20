==========================================================================
  ResetMissionsCOTW  -  version 0.9.7 (Beta)
  Per-map mission reset  -  theHunter: Call of the Wild
  Made by Sheeerpha  -  free and open source
==========================================================================


SUMMARY IN 30 SECONDS
---------------------
  In the game, resetting missions wipes them on ALL maps at once.
  This program resets only the maps that YOU choose.

  What changes:        only the missions of the maps you tick.
  What does NOT change: the other maps, profile, money, skills, weapons,
                        animals, trophies and everything else in the save.

  In short:
    1. Extract the .zip
    2. Close the game
    3. Open ResetMissionsCOTW.exe
    4. Follow the 4 steps of the window, from top to bottom
    5. Open the game and enter the map: its missions start from scratch

  This is a test version (Beta). The program is not official and may have
  bugs. That is why it backs everything up first and lets you undo.


==========================================================================
 PART 1 - BEFORE OPENING
==========================================================================

[1] EXTRACT THE FOLDER FROM THE .ZIP
    Right-click the .zip file and choose "Extract All...".
    Run the program from the extracted folder, never from inside the .zip.
    Tip: keep the folder in a fixed place (for example, on the Desktop).

[2] CLOSE THE GAME
    While the game is open, the program does not change anything.

[3] THE BLUE SCREEN "WINDOWS PROTECTED YOUR PC"
    The first time, Windows will probably show this blue screen.

    IT IS NORMAL. It shows up for every program without a "digital
    signature" (a paid certificate, renewed every year, that big companies
    buy). This program is free and made by a player, so it does not have
    that signature. The warning is just a precaution: it does not mean the
    program has a virus.

    To get past it:
      a) Click "More info" (the small text below the message).
      b) Click the "Run anyway" button.
      Done. Usually this happens only the first time.

    Want to check first? The code is open and anyone can see what the
    program does: https://github.com/Sheeerpha/ResetMissionsCOTW
    The .exe is built by GitHub itself from that code.
    Always download it from the official page.


==========================================================================
 PART 2 - USING THE PROGRAM
==========================================================================

When it opens, the "Before you start" notice appears (every time) and,
only the first time, a quick 6-screen tutorial (you can skip it).

The window has 4 NUMBERED STEPS, from top to bottom. The step still to do
has its number in green; the ones already done get a ✓.

STEP 1 - CHOOSE THE SAVE
    The program finds your save on its own (Steam or Epic) and picks the
    one you played last. Usually you do not need to do anything.
    * More than one save (two accounts, or Steam and Epic)? Click
      "Change" and choose. The program only touches the chosen save.
    * It did not find your save? Click "Choose folder" and select it.
      It is usually: Documents\Avalanche Studios\COTW\Saves\<number>

STEP 2 - BACK UP THE FULL SAVE (recommended)
    Click "Back up the full save". It keeps a copy of ALL the save files,
    not just the missions. It takes a few seconds.
    It is optional, but do it at least the first time.

STEP 3 - TICK THE MAPS YOU WANT TO START OVER
    Click the box (or the name) of each map. You can tick several.
    * The small bar and the number (e.g. 53/76) show how many missions of
      that map you have completed. Hover over the name to also see how
      many are in progress.
    * "↺ reset" = this map has already been reset and is ready.

STEP 4 - RESET
    Click the green "Reset" button and confirm.
    Before changing anything, the program backs up the missions on its
    own. The other maps do not change.

AFTER THE RESET
    1. Open the game normally.
    2. If Steam Cloud or Epic Cloud asks which version to use, choose the
       LOCAL one (this computer).
       (If you choose the cloud one, the reset is undone.)
    3. Enter the map: its missions start from scratch.


==========================================================================
 PART 3 - HOW TO UNDO
==========================================================================

Right below the "Reset" button there is the line "Need to undo?":

  * "Restore missions"
    Brings the missions of all maps back to how they were in a backup.
    The window shows, in yellow, what will change before you confirm.

  * "Restore full save"
    Brings the WHOLE save back to how it was in a full backup.
    Warning: everything you played after that backup is lost.
    (The current save is kept first, just in case.)

  * "Backups folder"
    Opens the folder with the copies. Inside Backups_SAVE there is a file
    explaining how to restore by hand, if you prefer.

Where the backups are:
    Documents\.BKP_ResetMissions_Saves_COTW   (hidden folder)
    -> Backups_MISSIONS : up to 50 mission backups
    -> Backups_SAVE     : up to 5 full save backups
    Beyond the limit, the oldest one is removed automatically, EXCEPT the
    very first one (🔒), which is always kept.


==========================================================================
 PART 4 - IF A NOTICE SHOWS UP
==========================================================================

"Windows is preventing the program from saving files" (yellow notice)
    It only happens if the Windows Defender "Controlled folder access"
    protection is on. Click "How to allow it (step by step)": the program
    shows 5 steps with pictures and a button to copy the program path. It
    takes about 1 minute and only needs to be done once.
    Note: if you later move the program to another folder, you need to
    allow it again.

"● ... problem(s) prevent changes" (status line at the top)
    Something is using the save files (the game, Steam, OneDrive...).
    Click "details". The screen shows what it is and offers buttons such
    as "Close Steam" or "Fix". The program NEVER closes anything on its own
    or by force: only when you click. Close the game from its own menu.
    This check happens only on your computer: nothing goes to the internet.

"Could not find the save automatically"
    Use "Choose folder" in step 1 (see Part 2).

The game asked which save version to use (cloud)
    Choose LOCAL. If you choose the cloud one, the reset is undone.


==========================================================================
 PART 5 - OTHER TIPS
==========================================================================

  * Language: the program opens in the Windows language (Portuguese,
    English or Spanish). To change it, click the language name at the top
    of the window.
  * Light/dark theme: it opens like your Windows. To change it, click
    "Dark theme" / "Light theme" at the top of the window.
  * "How to use", at the top of the window, shows the tutorial again.
  * New version: when one comes out, a green notice shows up at the top of the
    window with a "Download" link. The program only checks the project page on
    GitHub (at most once a day), sends no personal data and downloads nothing by
    itself.
  * Works on Windows 10 and 11. Nothing to install.
  * Tested with the Steam version. It should work on Epic, but it has not
    been tested there yet.


==========================================================================
 FOUND A PROBLEM?
==========================================================================

Open an "Issue" on the project page:
    https://github.com/Sheeerpha/ResetMissionsCOTW/issues

Please include:
    1. a screenshot of the message;
    2. what you did before it happened;
    3. the log: click "Logs" at the top of the program and send the most
       recent file. Or, in the error window, click "Copy details" and paste
       it into your report.

The log is in %LOCALAPPDATA%\ResetMissionsCOTW\logs (the 5 most recent
are kept). Your user name and personal data are masked.


==========================================================================
 LIKE IT?
==========================================================================

The program is free and always will be. If it helped you, you can support
it with the "Like it? Support the project" button at the bottom of the
window. A star on GitHub and telling your friends also helps a lot.
Thank you!

Project page (open source):
    https://github.com/Sheeerpha/ResetMissionsCOTW
