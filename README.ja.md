[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · **日本語** · [Русский](README.ru.md)

# War in the East 2 簡体字中国語 Mod プロジェクト

> **現在のバージョン v1.2.2（2026-10-28）** · [変更履歴](CHANGELOG.md) · [最新版をダウンロード](https://github.com/Pig9013/WITE2_CN/releases/latest)

## 現在の提供物

唯一の入口は次のとおり。

    mod\WitE2CN.exe

ゲームディレクトリから Mod 専用の mod\runtime コピーを作成し、mod\payload 内のフォント／overlay／翻訳辞書を読み込んで、そのコピーに WitE2CN_Text.dll を注入する。元のゲーム EXE、.scn、元の CSV は変更しない。

実行手順は mod\README.md を参照。実際の操作はユーザー本人だけが行う。プロジェクト側はファイルのビルドと静的監査のみを行い、ゲームも Steam も起動しない。

**既知の制限**：百科事典の本文は依然として英語（エンジンはシングルバイト描画で、UTF-8 と GBK の両コードページ方式とも実機では失敗した）。`.scn` は未再構築のため、ユニットのホバー表示、イベント、ターン概要は依然として英語。残る UI／表／ユニット名／百科事典のタイトルとリンクは中国語化済み。

**百科事典の中国語版（ゲーム外での閲覧用）**：本文は [docs/百科中文版_v1.0.md](docs/百科中文版_v1.0.md) に書き出し済み（1,171 件、同ディレクトリに DOCX あり）。

ゲームにパッチを当てても**起動を拒否しなくなる**。未登録のビルドでも通常どおり接続を試み、接続できなければ英語で動作する。パッチとセーブデータには影響しない。判定は logs/native.log を見る。詳細は [CHANGELOG](CHANGELOG.md) と mod/README.md の「ゲーム更新」の節を参照。

**関連マニュアル（Mod 本体には含まれない）**：Steel Inferno 公式マニュアル中国語版 v1.0・110 ページ・テキストは選択してコピーできる —— [Releases](https://github.com/Pig9013/WITE2_CN/releases) の添付ファイルを参照。

## 参考資料と謝辞

本プロジェクトの用語・文体・訳名はゼロから作ったものではなく、主に以下の中国語資料を参考にしている。原文とフィールドの意味は、ゲーム付属データ（Dat/CSV、Dat/Info）と公式英語マニュアルに従う。

### 中国語マニュアルと翻訳版

- **War in the East 2 ルールブック章別中国語訳（全 16 章 PDF、T1 層）**——用語とルール表現の第一根拠。各章の訳者：
  - 第 1 章 入門：**leninlyender**
  - 第 8、9、10、11、14 章：**Fulda**
  - 第 15 章 将軍：**Mizore**
  - 第 27 章 増援と撤収：**兔空**
  - 第 13、20、29、34、38、39、40、41 章：**克里斯蒂安-cristianwj**
  - 全体の訂正：**克里斯蒂安-cristianwj**
- **War in the East 2 ルールブック中国語全訳（809 ページ、T1B）**——長文本文・参考文献・用語の対照版。訳者：**张萧临**。
- **Steel Inferno マニュアル**——英語原著と中国語版。英語原著者 **James Wirth**。
- **初心者チュートリアル中国語版（T3）**——UI と手順の用語の参考。

対応ファイル（照合用。いずれも読み取り専用の参照で、本リポジトリには同梱しない）：「1 新手入门.pdf」…「41 附录L-编辑器.pdf」（WITE2translation 分章）、「东线战争2规则手册_中文全本.pdf」、「WITE2_Steel_Inferno_Manual_EBOOK.pdf」とその中国語版、「WITETutorialManual中文.pdf」。

### コミュニティのテキストと議論

- **kkuy678**、**zisongzi**、**魔法训练营**——本プロジェクトが参照した中国語テキストと議論を提供。用語の取捨やメカニクスの説明のいくつかはこれらの資料による。
- また、ウォーゲーム / TOAW コミュニティで WitE2 の資料を共有し、質問に答え、誤りを指摘してくれた皆さん。

### 参考図書

- 『世界人名翻訳大辞典』、新華社訳名室編、2007 年 4 月、ISBN 7500107994/Z21；Wikipedia の「外国語音訳表／英語」——人名・地名の表記の根拠。

### 特に感謝したい方々

**cristianwj、leninlyender、Fulda、Mizore、kkuy678、zisongzi、魔法训练营、兔空、张萧临**

本プロジェクトの用語・文体・訳名の多くは、あなた方の中国語テキストから学んだものだ。これらの底本がなければ、この Mod は今の形にならなかった。**功績はあなた方にある。**

また、Steel Inferno の原作者 **James Wirth**、ならびにゲーム本体と公式マニュアルの開発・販売元である **2by3 Games、Matrix Games、Slitherine** に感謝する。

漏れや著者の表記に誤りがあれば、issue で指摘してほしい。すぐに直す。


## ディレクトリ構成

    mod/
      WitE2CN.exe       ランチャー
      WitE2CN_Text.dll  ネイティブテキストフック
      payload/          runtime 辞書、フォント、checksums、package
      runtime/          ゲームの私有コピーとセーブデータ（配布対象外のコード）
      assets/           ビルドソース：GuiFonts.json、translation.csv
      build_maps.py     辞書／フォント／overlay／checksums の組み立て
      complete_font.py  フォントの欠字を補完
      finalize.py       checksums と可搬 settings の生成
      src/              ランチャーとテキストフックのソース
      README.md         使用手順

    glossary/           用語集と UI 追加語彙
    pipeline/           ローカル Qwen による抽出／翻訳／QA／用語保護
    data/               翻訳ソースと中間データ
    build/              フォントソース、基本 translation.csv、キャンペーン概要、シナリオ CSV 訳文
    integration/        テキスト抽出／生成／監査スクリプト

## ポータビリティ

- コードは本機の D:\ や Steam ライブラリのパスを直書きしない。
- ゲームは `--game` → settings.json → settings.local.json（自動記憶）→ WITE2_GAME → Steam レジストリ／全ライブラリディレクトリ／ドライブ文字の走査 → 手動選択 の順に解決する。見つからない場合はダイアログでディレクトリを選ぶ。
- `WitE2CN.exe --where` は解決結果を logs\launcher.log に書き出す。「ゲームが見つからない」ときはまずこれを見る。
- settings.json の既定値は空オブジェクト {}。game_path を手書きするのは Steam 以外のインストールのときだけ。
- runtime\WitE2CN.runtime.json の source は由来の記録にすぎない。Mod を移動した後は game_sha256 だけを検証する。
- ビルドスクリプトは MOD/PROJECT 相対パスを使う。削除済みの mod_full には依存しない。

## ビルド（ゲームを起動しない）

    python mod\build_maps.py
    python mod\complete_font.py
    python mod\finalize.py

build_maps.py は既存の訳文を読むだけで、モデルは呼び出さない。翻訳自体は pipeline のローカル Qwen が行う。

## ホットキーのテキスト

ゲーム EXE の UI キーは次のようなものがある。

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

ビルド時は EXE 内の {...} を含む文字列をすべて走査し、テンプレートを網羅的に生成する。一種類のプレースホルダーだけを扱うことはできない。

## 整理の方針

削除済み：旧 mod_full/mod_additive/install ディレクトリ、旧上書きインストール、旧 CSV swap、diagnostics のセッションログ、旧スクリーンショット／プレビュー／zip、旧 docs、テスト用 exe/pdb/lib、監査スナップショット。

保持：現在の Mod、runtime（セーブデータを含む）、翻訳ソース、シナリオ CSV の訳文、フォントソース、ビルド／監査スクリプト、用語集。

## よくある質問

**ランチャーが「中国語化パッケージのファイルが見つからないか破損している：payload\...」と表示する**

2026-10-25 より前のリポジトリ版は Git の改行変換の影響を受けていた。payload 配下の txt/csv/json がコミット時に LF に変換され、ダウンロード後は payload\checksums.json の SHA-256 と一致しなかった（ファイル自体はあり、バイトが変わっていた）。.gitattributes で mod/payload/** に -text を設定して修正済み。このメッセージが出たら、古いフォルダーを削除して最新版をダウンロードし直す。新旧のディレクトリを混在させない。

## 検証

静的検証の内容は次のとおり。

- translations.bin の W2CNMAP1 ヘッダーとエントリ数。
- フォントの cmap カバレッジ（欠字 0）。
- checksums の 25 ファイルがすべて一致。
- シナリオ CSV の行数／フィールド数／ヘッダー／BOM／非テキスト列を元のエクスポートと比較。
- settings.json が {} で、ランチャーが Steam 版ゲームを自動で見つけられる。

実機検証はユーザーが行う。プロジェクト側はゲームを起動しない。
