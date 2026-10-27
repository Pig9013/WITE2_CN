[中文](README.md) · **English** · [Français](README.fr.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

# War in the East 2 Simplified Chinese Mod Project

> **Current version v1.2.2 (2026-10-28)** · [Changelog](CHANGELOG.md) · [Download the latest release](https://github.com/Pig9013/WITE2_CN/releases/latest)

## Current delivery

The only entry point is:

    mod\WitE2CN.exe

It creates a private mod\runtime copy from the game directory, loads the fonts/overlay/translation dictionary from mod\payload, and injects WitE2CN_Text.dll into that copy. The original game EXE, .scn files and original CSV are not modified.

Usage instructions are in mod\README.md. Only the user performs the actual operations; the project side only does file builds and static audits, and never starts the game or Steam.

**Known limitations**: the encyclopedia body text is still in English (the engine renders single-byte; both the UTF-8 and GBK code page approaches failed on real machines); `.scn` files have not been rebuilt, so unit tooltips, events and turn summaries are still in English. Everything else — interface, tables, unit names, encyclopedia titles and links — has been localized.

**Chinese encyclopedia (for reading outside the game)**: the body text has been exported to [docs/百科中文版_v1.0.md](docs/百科中文版_v1.0.md) (1,171 entries; a DOCX sits in the same directory).

After a game patch it **no longer refuses to start**: unregistered builds still attempt the hook as usual, and if it does not attach the game runs in English; patches and saves are unaffected. For the verdict, check logs/native.log; details are in [CHANGELOG](CHANGELOG.md) and the "Game updates" section of mod/README.md.

**Companion manual (not part of the Mod itself)**: the official Steel Inferno manual, Chinese edition v1.0 · 110 pages · text can be selected and copied — see the attachment on [Releases](https://github.com/Pig9013/WITE2_CN/releases).

## References and acknowledgements

The terminology, phrasing and translated names in this project do not come from nowhere; they draw mainly on the following Chinese materials. Source text and field semantics follow the data shipped with the game (Dat/CSV, Dat/Info) and the official English manual.

### Chinese manuals and translations

- **War in the East 2 rulebook, Chinese translation by chapter (16-chapter PDF, T1 tier)** — the primary basis for terminology and rules wording. Chapter translators:
  - Chapter 1, Getting Started: **leninlyender**
  - Chapters 8, 9, 10, 11, 14: **Fulda**
  - Chapter 15, Commanders: **Mizore**
  - Chapter 27, Reinforcements and Withdrawals: **兔空**
  - Chapters 13, 20, 29, 34, 38, 39, 40, 41: **克里斯蒂安-cristianwj**
  - Whole-book corrections: **克里斯蒂安-cristianwj**
- **War in the East 2 rulebook, complete Chinese edition (809 pages, T1B)** — the parallel text for long passages, bibliography and terminology; translator: **张萧临**.
- **The Steel Inferno manual** — English original and Chinese edition; original English author **James Wirth**.
- **Beginner tutorial, Chinese edition (T3)** — reference for interface and workflow wording.

Corresponding files (for verification only; cited read-only and not distributed with this repository): "1 新手入门.pdf"…"41 附录L-编辑器.pdf" (the WITE2translation chapters), "东线战争2规则手册_中文全本.pdf", "WITE2_Steel_Inferno_Manual_EBOOK.pdf" and its Chinese edition, "WITETutorialManual中文.pdf".

### Community texts and discussion

- **kkuy678**, **zisongzi**, **魔法训练营** — provided the Chinese texts and discussions this project draws on; several terminology choices and mechanics explanations come from these materials.
- And everyone in the wargame / TOAW community who shared WitE2 material, answered questions and sent errata.

### Reference works

- A Comprehensive Dictionary of Translated Personal Names, compiled by the Proper Names Translation Office of Xinhua News Agency, April 2007, ISBN 7500107994/Z21; Wikipedia's "Foreign-language transcription table/English" — the basis for rendering personal and place names.

### Special thanks

**cristianwj, leninlyender, Fulda, Mizore, kkuy678, zisongzi, 魔法训练营, 兔空, 张萧临**

Much of this project's terminology, phrasing and translated names was learned from your Chinese texts. Without those source texts, this Mod could not have turned out the way it has. **The credit is yours.**

Thanks also to **James Wirth**, original author of Steel Inferno, and to **2by3 Games, Matrix Games, Slitherine**, developers and publishers of the game and the official manual.

If anything is missing or an author is misattributed, please open an issue and we will fix it at once.


## Directory layout

    mod/
      WitE2CN.exe       Launcher
      WitE2CN_Text.dll  Native text hook
      payload/          Runtime dictionary, fonts, checksums, package
      runtime/          Private game copy and saves (not distributable code)
      assets/           Build sources: GuiFonts.json, translation.csv
      build_maps.py     Assembles dictionary/fonts/overlay/checksums
      complete_font.py  Fills in missing glyphs
      finalize.py       Generates checksums and portable settings
      src/              Launcher and text hook sources
      README.md         Usage notes

    glossary/           Glossary and extra UI word list
    pipeline/           Local Qwen extraction/translation/QA/term protection
    data/               Translation sources and intermediate data
    build/              Font sources, base translation.csv, campaign briefings, scenario CSV translations
    integration/        Text extraction/generation/audit scripts

## Portability

- The code does not hardcode this machine's D:\ or Steam library paths.
- The game is resolved in the order `--game` → settings.json → settings.local.json (remembered automatically) → WITE2_GAME → Steam registry / all library folders / drive-letter scan → manual selection; if nothing is found, a dialog asks for the folder.
- `WitE2CN.exe --where` writes the resolution result to logs\launcher.log; when debugging "game not found", check that first.
- settings.json defaults to an empty object {}; game_path only has to be written by hand for a non-Steam installation.
- The source field in runtime\WitE2CN.runtime.json is only a provenance record; after moving the Mod, only game_sha256 is checked.
- Build scripts use MOD/PROJECT-relative paths; they no longer depend on the removed mod_full.

## Build (without starting the game)

    python mod\build_maps.py
    python mod\complete_font.py
    python mod\finalize.py

build_maps.py reads existing translations and does not call a model. The translation itself is done by the local Qwen in pipeline.

## Hotkey text

UI keys in the game EXE may be:

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

The build scans every string in the EXE that contains {...} and generates the full set of templates; it cannot handle just one kind of placeholder.

## Cleanup policy

Removed: the old mod_full/mod_additive/install directories, the old overwrite install, the old CSV swap, diagnostics session logs, old screenshots/previews/zips, old docs, test exe/pdb/lib, audit snapshots.

Kept: the current Mod, runtime (with saves), translation sources, scenario CSV translations, font sources, build/audit scripts, the glossary.

## FAQ

**The launcher reports "localization package files missing or corrupted: payload\..."**

Repository versions before 2026-10-25 were affected by Git's line-ending conversion: txt/csv/json files under payload were turned into LF on commit, so after download their SHA-256 did not match payload\checksums.json (the files were there, only the bytes had changed). Fixed by setting -text for mod/payload/** in .gitattributes. If you see this message, delete the old folder, download the latest version again, and do not mix old and new directories.

## Verification

Static verification covers:

- the W2CNMAP1 header and entry count of translations.bin;
- font cmap coverage (0 missing glyphs);
- checksums pass for all 25 files;
- scenario CSV row count/field count/header/BOM/non-text columns compared against the original export;
- settings.json is {}, and the launcher finds the Steam game automatically.

On-machine verification is performed by the user; the project side does not start the game.
