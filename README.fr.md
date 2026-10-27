[中文](README.md) · [English](README.en.md) · **Français** · [日本語](README.ja.md) · [Русский](README.ru.md)

# Projet de mod en chinois simplifié pour War in the East 2

> **Version actuelle v1.2.2 (2026-10-28)** · [Journal des modifications](CHANGELOG.md) · [Télécharger la dernière version](https://github.com/Pig9013/WITE2_CN/releases/latest)

## Livraison actuelle

L'unique point d'entrée est :

    mod\WitE2CN.exe

Il crée une copie privée mod\runtime à partir du répertoire du jeu, charge depuis mod\payload les polices, l'overlay et le dictionnaire de traduction, puis injecte WitE2CN_Text.dll dans cette copie. L'EXE d'origine du jeu, les .scn et les CSV d'origine ne sont pas modifiés.

Les instructions d'utilisation sont dans mod\README.md. Seul l'utilisateur effectue les opérations réelles ; le côté projet se limite à la construction des fichiers et à l'audit statique, et ne lance ni le jeu ni Steam.

**Limites connues** : le corps de l'encyclopédie reste en anglais (le moteur rend en mono-octet ; les deux approches de page de code, UTF-8 et GBK, ont échoué sur machine réelle) ; les `.scn` n'ont pas été reconstruits, donc les infobulles d'unité, les événements et les résumés de tour restent en anglais. Le reste — interface, tableaux, noms d'unités, titres et liens de l'encyclopédie — a été traduit.

**Encyclopédie en chinois (lecture hors du jeu)** : le corps du texte a été exporté vers [docs/百科中文版_v1.0.md](docs/百科中文版_v1.0.md) (1,171 entrées, avec un DOCX dans le même dossier).

Après un patch du jeu, il **ne refuse plus de démarrer** : les builds non répertoriés tentent l'accroche comme d'habitude, et si elle échoue le jeu tourne en anglais ; patches et sauvegardes ne sont pas affectés. Le verdict se lit dans logs/native.log ; détails dans [CHANGELOG](CHANGELOG.md) et dans la section « Mises à jour du jeu » de mod/README.md.

**Manuel d'accompagnement (hors du Mod lui-même)** : le manuel officiel Steel Inferno, version chinoise v1.0 · 110 pages · texte sélectionnable et copiable — voir la pièce jointe des [Releases](https://github.com/Pig9013/WITE2_CN/releases).

## Références et remerciements

La terminologie, les formulations et les noms traduits de ce projet ne sortent pas de nulle part : ils s'appuient principalement sur les documents chinois ci-dessous. Le texte source et la sémantique des champs suivent les données livrées avec le jeu (Dat/CSV, Dat/Info) et le manuel officiel en anglais.

### Manuels et traductions en chinois

- **Manuel de règles de War in the East 2, traduction chinoise chapitre par chapitre (PDF de 16 chapitres, niveau T1)** — référence première pour la terminologie et la formulation des règles. Traducteurs par chapitre :
  - Chapitre 1, Prise en main : **leninlyender**
  - Chapitres 8, 9, 10, 11, 14 : **Fulda**
  - Chapitre 15, Généraux : **Mizore**
  - Chapitre 27, Renforts et retraits : **兔空**
  - Chapitres 13, 20, 29, 34, 38, 39, 40, 41 : **克里斯蒂安-cristianwj**
  - Corrections sur l'ensemble de l'ouvrage : **克里斯蒂安-cristianwj**
- **Manuel de règles de War in the East 2, édition chinoise intégrale (809 pages, T1B)** — version de référence pour les longs passages, la bibliographie et la terminologie ; traducteur : **张萧临**.
- **Le manuel Steel Inferno** — version originale anglaise et version chinoise ; auteur original **James Wirth**.
- **Tutoriel débutant, version chinoise (T3)** — référence pour la terminologie de l'interface et des procédures.

Fichiers correspondants (pour vérification, cités en lecture seule et non distribués avec ce dépôt) : « 1 新手入门.pdf »…« 41 附录L-编辑器.pdf » (chapitres WITE2translation), « 东线战争2规则手册_中文全本.pdf », « WITE2_Steel_Inferno_Manual_EBOOK.pdf » et sa version chinoise, « WITETutorialManual中文.pdf ».

### Textes et discussions de la communauté

- **kkuy678**, **zisongzi**, **魔法训练营** — ont fourni les textes chinois et les discussions sur lesquels s'appuie ce projet ; plusieurs choix terminologiques et explications de mécanismes en proviennent.
- Et toutes les personnes de la communauté wargame / TOAW qui ont partagé des documents WitE2, répondu aux questions et signalé des errata.

### Ouvrages de référence

- Grand dictionnaire de traduction des noms de personnes, établi par le bureau de traduction des noms propres de l'agence Xinhua, avril 2007, ISBN 7500107994/Z21 ; « Table de transcription des langues étrangères/anglais » de Wikipédia — base pour la transcription des noms de personnes et de lieux.

### Remerciements particuliers

**cristianwj, leninlyender, Fulda, Mizore, kkuy678, zisongzi, 魔法训练营, 兔空, 张萧临**

Une grande partie de la terminologie, des formulations et des noms traduits de ce projet a été apprise à partir de vos textes chinois. Sans ces textes de référence, ce Mod ne serait pas ce qu'il est. **Le mérite vous revient.**

Merci aussi à **James Wirth**, auteur original de Steel Inferno, ainsi qu'à **2by3 Games, Matrix Games, Slitherine**, développeurs et éditeurs du jeu et du manuel officiel.

En cas d'oubli ou d'attribution erronée, ouvrez une issue : nous corrigerons immédiatement.


## Arborescence

    mod/
      WitE2CN.exe       Lanceur
      WitE2CN_Text.dll  Hook de texte natif
      payload/          Dictionnaire runtime, polices, checksums, package
      runtime/          Copie privée du jeu et sauvegardes (code non distribuable)
      assets/           Sources de build : GuiFonts.json, translation.csv
      build_maps.py     Assemblage dictionnaire/polices/overlay/checksums
      complete_font.py  Complète les glyphes manquants
      finalize.py       Génère les checksums et les settings portables
      src/              Sources du lanceur et du hook de texte
      README.md         Notice d'utilisation

    glossary/           Glossaire et vocabulaire UI supplémentaire
    pipeline/           Extraction/traduction/QA/protection terminologique par Qwen en local
    data/               Sources de traduction et données intermédiaires
    build/              Sources de polices, translation.csv de base, briefings de campagne, traductions des CSV de scénarios
    integration/        Scripts d'extraction/génération/audit de texte

## Portabilité

- Le code ne fige en dur ni le chemin D:\ de la machine ni les chemins des bibliothèques Steam.
- Le jeu est résolu dans l'ordre `--game` → settings.json → settings.local.json (mémorisé automatiquement) → WITE2_GAME → registre Steam / tous les dossiers de bibliothèque / balayage des lettres de lecteur → sélection manuelle ; si rien n'est trouvé, une boîte de dialogue demande le dossier.
- `WitE2CN.exe --where` écrit le résultat de la résolution dans logs\launcher.log ; en cas de « jeu introuvable », commencez par ce fichier.
- settings.json vaut par défaut un objet vide {} ; game_path ne s'écrit à la main que pour une installation hors Steam.
- Le champ source de runtime\WitE2CN.runtime.json n'est qu'un enregistrement de provenance ; après un déplacement du Mod, seul game_sha256 est vérifié.
- Les scripts de build utilisent des chemins relatifs à MOD/PROJECT ; ils ne dépendent plus du mod_full supprimé.

## Build (sans lancer le jeu)

    python mod\build_maps.py
    python mod\complete_font.py
    python mod\finalize.py

build_maps.py lit les traductions existantes et n'appelle aucun modèle. La traduction elle-même est assurée par Qwen en local, dans pipeline.

## Textes des raccourcis

Les clés d'UI de l'EXE du jeu peuvent se présenter ainsi :

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

Lors du build, toutes les chaînes de l'EXE contenant {...} sont analysées et l'ensemble des modèles est généré ; on ne peut pas traiter un seul type de placeholder.

## Politique de nettoyage

Supprimés : les anciens dossiers mod_full/mod_additive/install, l'ancienne installation par écrasement, l'ancien CSV swap, les journaux de session diagnostics, les anciennes captures/aperçus/zip, les anciens docs, les exe/pdb/lib de test, les instantanés d'audit.

Conservés : le Mod actuel, runtime (sauvegardes comprises), les sources de traduction, les traductions des CSV de scénarios, les sources de polices, les scripts de build/audit, le glossaire.

## FAQ

**Le lanceur affiche « fichiers du paquet de traduction chinoise manquants ou corrompus : payload\... »**

Les versions du dépôt antérieures au 2026-10-25 subissaient la conversion des fins de ligne de Git : les txt/csv/json sous payload étaient convertis en LF au commit, et après téléchargement leur SHA-256 ne correspondait plus à celui de payload\checksums.json (les fichiers étaient bien là, seuls les octets avaient changé). Corrigé en définissant -text pour mod/payload/** dans .gitattributes. Si ce message apparaît, supprimez l'ancien dossier, retéléchargez la dernière version et ne mélangez pas anciens et nouveaux dossiers.

## Vérification

La vérification statique couvre :

- l'en-tête W2CNMAP1 et le nombre d'entrées de translations.bin ;
- la couverture cmap des polices (0 glyphe manquant) ;
- les checksums des 25 fichiers, tous validés ;
- le nombre de lignes/champs, l'en-tête, le BOM et les colonnes non textuelles des CSV de scénarios, comparés à l'export d'origine ;
- settings.json vaut {}, et le lanceur trouve seul le jeu Steam.

La vérification sur machine est effectuée par l'utilisateur ; le côté projet ne lance pas le jeu.
