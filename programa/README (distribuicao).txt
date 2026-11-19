ResetMissionsCOTW - version 0.9.5 (Beta)
Per-map mission reset - theHunter: Call of the Wild
Created by Sheeerpha
=========================================================

THIS IS A TEST VERSION (BETA).
The program was made by a player, it is not official and it may have bugs. Use
it with care and, if something goes wrong, report it on the project page (link below).


WHAT THE PROGRAM DOES
---------------------
In the game, the only way to reset missions is to delete the missions file, and
that resets the missions of ALL maps. This program resets the missions of ONE
chosen map (or several) and keeps the other maps as they are.

It only changes mission progress (the missions_missiondata_adf file). Profile,
money, skills, weapons, animals, trophies and the rest of the save are not touched.


BEFORE OPENING: THE BLUE "WINDOWS PROTECTED YOUR PC" SCREEN
-----------------------------------------------------------
The first time you open the program, Windows will probably show a blue
screen saying "Windows protected your PC".

THIS IS NORMAL. It happens with every program that does not have a
"digital signature", a paid certificate, bought every year, that big
companies use. Since this is a free program made by a player, it does
not have that signature, and Windows warns you as a precaution. It does
not mean the program has a virus.

How to get past it:
1. On the blue screen, click "More info" (the small text right below
   the message).
2. A "Run anyway" button will show up. Click it.
3. Done: the program opens. Usually this screen only shows up the
   first time.

Want to check first? The program is open source: anyone can see exactly
what it does at
https://github.com/Sheeerpha/ResetMissionsCOTW
and the program is built automatically by GitHub itself from that code.
Always download it from the official page (GitHub or Nexus Mods).


HOW TO USE
----------
1. CLOSE the game (the program does not change anything while the game is open).
2. Double-click "ResetMissionsCOTW.exe".
   If the blue Windows screen shows up, see the section above.
   Every time the program opens, the "Before you start" warning shows up.
   The first time, a quick introduction shows up too (you can skip it).
3. The program finds your save by itself and shows the list of maps with the
   completed missions, missions in progress and the total.
   (If it does not find it, click "Choose folder..." and select the save
   folder, which is usually: Documents\Avalanche Studios\COTW\Saves\<number>)

   Do you have a save on Steam AND on Epic, or more than one account? Choose the
   platform in "Platform" and the account in the "Save" list. The most recently
   played save is already selected. The program only touches the selected save.
4. RECOMMENDED: click "Back up the full save" before anything else.
   It keeps a copy of the ENTIRE save folder.
5. Click the map you want to reset (to choose several, hold Ctrl).
6. Click "Reset missions of the selected map(s)" and confirm.
7. The map turns green, with "Missions reset". Open the game and enter that
   map: its missions will start from scratch.


BACKUPS
-------
"Missions" row:
* A backup of the missions file is made automatically before each reset.
* "Restore missions backup...": undoes a reset. The table shows in yellow what
  will change before you confirm.
* Up to 50 are kept. Beyond that, the oldest one is deleted automatically,
  except the first one (🔒), which is always kept.

"Full save" row:
* "Back up the full save": copies the entire save folder.
* "Restore full save...": brings the entire save back from a backup. Warning:
  all progress made after that backup, in any part of the game, is lost.
  Before restoring, the current save is also backed up.
* Up to 5 are kept, with the first one (🔒) always kept.
* "Open folder": inside there is a file explaining how to restore by hand.

Backups are kept in Documents\.BKP_ResetMissions_Saves_COTW (hidden folder),
separated by account, in the Backups_MISSIONS and Backups_SAVE folders.


OTHER WARNINGS YOU MAY SEE
--------------------------
* Yellow bar "Windows is blocking this program..."
  It only shows up if you turned on the "Controlled folder access" protection
  of Windows Defender. Use the buttons in the bar itself: "How to allow it
  (step by step)" explains everything. Allow the program in the place where it
  is going to stay: if you move the .exe to another folder later, you will need
  to allow it again.

* Steam Cloud / Epic Cloud
  If a cloud file conflict warning shows up when opening the game, choose the
  LOCAL version (this computer). If you choose the cloud one, the reset is
  undone.


IMPORTANT
---------
* Do not run the program from inside the .zip file: extract the folder first.
* Works on Windows 10 and 11. Nothing to install.
* Language: the program opens in your Windows language (Portuguese, English or
  Spanish). To change it, use the list with the globe 🌐 in the bottom corner.
* Theme: light or dark, same as your Windows. To change it, use the
  "Dark theme" / "Light theme" button in the bottom corner.
* "How to use", in the bottom corner, shows the introduction again.
* Tested with the Steam version. It should work on Epic, but it has not been
  tested there yet.


FOUND A PROBLEM?
----------------
Open an "Issue" on the project's GitHub page, with:
- a screenshot with the error message;
- what you did before the error happened.

https://github.com/Sheeerpha/ResetMissionsCOTW/issues


PROJECT PAGE (open source)
--------------------------
https://github.com/Sheeerpha/ResetMissionsCOTW
