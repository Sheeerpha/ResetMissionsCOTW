# ResetMissionsCOTW

**Reset the missions of a single map in theHunter: Call of the Wild, keeping every other map intact.**

🇧🇷 [Português](#-português) · 🇪🇸 [Español](#-español)

> ⚠️ **Beta.** Made by a player, independently. Not affiliated with or endorsed by Expansive Worlds or Avalanche Studios. It may have bugs: **back up your full save with the program's own "Back up the full save" button before changing anything.**

## ⬇️ Download

Get the latest `.zip` from **[Releases](https://github.com/Sheeerpha/ResetMissionsCOTW/releases/latest)**, extract it and run `ResetMissionsCOTW.exe`. Nothing to install (Windows 10/11). Read `README_FIRST.txt` inside the zip.

### 🛡️ "Windows protected your PC" — this is normal

The first time you open the program, Windows will probably show a blue screen saying **"Windows protected your PC"**. This happens with every program that does not have a paid code-signing certificate (bought every year by big companies). This is a free program made by a player, so it does not have one, and Windows warns you as a precaution — it does not mean the program has a virus.

1. Click **More info** (the small text below the message).
2. Click **Run anyway**.
3. Done. Usually it only shows up the first time.

Want to check first? All the code is right here, and the `.exe` in Releases is built automatically by GitHub from this code. Always download from the official pages (GitHub or Nexus Mods).

## What it does

In the game, the only way to reset missions is to delete the missions file, which wipes the mission progress of **all** maps. ResetMissionsCOTW lets you pick **one map (or several)** and reset only those.

- Changes **only mission progress** of the maps you choose. Profile, money, skills, perks, weapons, animals, trophies and everything else are untouched.
- Finds your save automatically (Steam and Epic, including Documents redirected to OneDrive). Several accounts? Pick the platform and the account.
- Shows completed / in-progress / total missions per map. Reset maps stay listed in green until you enter them in the game.
- **Automatic backup** of the missions file before every change (up to 50; the oldest one is never deleted).
- **Full save backup** button: copies the whole save folder (up to 5; the oldest one is never deleted), with one-click restore and a text file explaining how to restore by hand.
- Writes to a temporary file, re-reads and verifies everything before replacing the real file. Refuses to run while the game is open.
- **Check before you start**: finds what could get in the way (the game open, programs holding the save files via the Windows Restart Manager, Steam/Epic/OneDrive/Google Drive/Dropbox, cloud folders, read-only files) and offers buttons such as *Close Steam*, *Close OneDrive* and *Fix* — never closing anything by force. Everything runs locally.
- **Logs**: one log per session (the 5 most recent, personal data masked) in `%LOCALAPPDATA%\ResetMissionsCOTW\logs`, plus *Copy details* in error windows.
- Portuguese, English and Spanish · light and dark theme.

## How to use

1. Close the game.
2. Open `ResetMissionsCOTW.exe`. A "Before you start" warning shows up every time; the first time, a short introduction too (you can skip it).
3. Click **Back up the full save** (recommended).
4. Select the map (hold Ctrl for several) → **Reset missions of the selected map(s)** → confirm.
5. Open the game and enter the map: its missions start from scratch.

To undo: **Restore missions backup...** (only missions) or **Restore full save...** (the whole save).

### Notes

- **Controlled folder access** (Windows Defender ransomware protection): if it is on, Windows blocks writing to Documents. The program shows a yellow bar with a step-by-step guide to allow it.
- **Steam Cloud / Epic Cloud**: if a sync conflict shows up when opening the game, choose the **local** version.
- Backups live in `Documents\.BKP_ResetMissions_Saves_COTW` (hidden folder), per account, in `Backups_MISSIONS` and `Backups_SAVE`.
- Tested on Steam. Epic should work but has not been tested yet: feedback welcome!

## How it works (technical)

`missions_missiondata_adf` is a 32-byte `SAVE`/`COMP` header followed by a zlib stream that holds an Avalanche ADF file. Its root, `MissionManager_1`, has a hash table `Campaigns` keyed by **map id** (the same numbers as the `animal_population_N` files). Resetting a map removes that map's entry from the table (unlinking it from its bucket chain and returning it to the free list) — about 6 bytes change. The game recreates the map's missions from scratch the next time you enter it, exactly as for a map you have never visited. Every result is re-opened and compared byte by byte against the expected content before the real file is replaced.

## Building from source

Requires Python 3.15 on Windows.

```powershell
cd programa
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -X utf8 testes.py
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name ResetMissionsCOTW cotw_app.py
```

The tests use synthetic saves generated on the fly, so no real save is needed. Releases are built automatically by GitHub Actions (`.github/workflows/release.yml`) when a release is published.

## Bugs and suggestions

Open an [Issue](https://github.com/Sheeerpha/ResetMissionsCOTW/issues) with a screenshot and what you did before the problem.

## Support

Free, made by a player for the community. If it helped you: ☕ [Buy Me a Coffee](https://buymeacoffee.com/sheeerpha) · 💠 [LivePix](https://livepix.gg/sherpa)

Created by **Sheeerpha** · [MIT License](LICENSE)

---

## 🇧🇷 Português

**Reseta as missões de um único mapa do theHunter: Call of the Wild, sem mexer nos outros mapas.**

> ⚠️ **Beta.** Feito por um jogador, de forma independente, sem ligação com a Expansive Worlds ou a Avalanche Studios. Pode ter falhas: **faça o backup do save completo pelo botão "Fazer backup do save completo" do próprio programa antes de alterar qualquer coisa.**

**Download:** baixe o `.zip` mais recente em **[Releases](https://github.com/Sheeerpha/ResetMissionsCOTW/releases/latest)**, extraia e abra `ResetMissionsCOTW.exe`. Não precisa instalar nada.

- Altera **só o progresso das missões** dos mapas escolhidos. Perfil, dinheiro, habilidades, vantagens, armas, animais e troféus não mudam.
- Encontra o save sozinho (Steam e Epic), com escolha de plataforma e de conta.
- Backup automático das missões antes de cada alteração (até 50) e botão de **backup do save completo** (até 5). O mais antigo de cada tipo nunca é apagado.
- Em português, inglês e espanhol, com tema claro e escuro.

**Como usar:** feche o jogo → abra o programa → **Fazer backup do save completo** → escolha o mapa → **Resetar missões do(s) mapa(s) selecionado(s)** → entre no mapa no jogo.

**"O Windows protegeu o computador" é normal.** Essa tela azul aparece com todo programa sem assinatura digital paga (um certificado caro, comprado todo ano por grandes empresas). Não quer dizer que tenha vírus: clique em **Mais informações** → **Executar assim mesmo**. O código está todo aqui, e o `.exe` das Releases é gerado pelo próprio GitHub a partir dele. Leia o `LEIA-ME_PRIMEIRO.txt` do zip.

Problemas? Abra uma [Issue](https://github.com/Sheeerpha/ResetMissionsCOTW/issues).

## 🇪🇸 Español

**Reinicia las misiones de un solo mapa de theHunter: Call of the Wild, sin tocar los demás mapas.**

> ⚠️ **Beta.** Hecho por un jugador, de forma independiente, sin relación con Expansive Worlds ni Avalanche Studios. Puede tener fallos: **haz una copia de la partida completa con el botón "Copia de seguridad de la partida completa" del propio programa antes de cambiar nada.**

**Descarga:** baja el `.zip` más reciente en **[Releases](https://github.com/Sheeerpha/ResetMissionsCOTW/releases/latest)**, extráelo y abre `ResetMissionsCOTW.exe`. No hay que instalar nada.

- Modifica **solo el progreso de las misiones** de los mapas elegidos. El perfil, el dinero, las habilidades, las ventajas, las armas, los animales y los trofeos no cambian.
- Encuentra la partida solo (Steam y Epic), con elección de plataforma y de cuenta.
- Copia automática de las misiones antes de cada cambio (hasta 50) y botón de **copia de la partida completa** (hasta 5). La más antigua de cada tipo nunca se borra.
- En portugués, inglés y español, con tema claro y oscuro.

**Cómo usarlo:** cierra el juego → abre el programa → **Copia de seguridad de la partida completa** → elige el mapa → **Reiniciar misiones de los mapas seleccionados** → entra en el mapa en el juego.

**"Windows protegió su PC" es normal.** Esa pantalla azul aparece con todo programa sin firma digital de pago (un certificado caro, que las grandes empresas compran cada año). No significa que tenga virus: haz clic en **Más información** → **Ejecutar de todas formas**. Todo el código está aquí, y el `.exe` de Releases lo genera el propio GitHub a partir de él. Lee el `LEEME_PRIMERO.txt` del zip.

¿Problemas? Abre una [Issue](https://github.com/Sheeerpha/ResetMissionsCOTW/issues).
