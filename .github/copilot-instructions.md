## 概要

このファイルは、このリポジトリで自動化された AI コーディングエージェントが迅速に生産的になるための最小限かつ具体的な指示集です。

注: 現在ワークスペースに実ソースや既存のエージェント指示が見つかりませんでした。以下は「リポジトリを解析したらやること」形式の短いチェックリストと、見つかったら具体的に参照すべき例のテンプレートです。実ファイルを検出したら、下記のプレースホルダを実ファイル名に置換してください。

## 最初にやること（優先順位の高い探索）

1. ルートでまず探す: `README.md`, `package.json`, `pyproject.toml`, `requirements.txt`, `Makefile`, `Dockerfile`, `docker-compose.yml`。
   - これで使用言語、ビルド/起動/テストコマンド、依存サービスの有無が分かる。
2. 実行エントリを特定: `src/`, `app/`, `services/`, `cmd/` 配下を確認。
   - 単一アプリかモノリポかを判定（例：`/services/*` や `packages/*` があればモノレポ）
3. CI とワークフロー: `.github/workflows/` にある YAML を読み、公式に推奨されるコマンドや環境変数を抽出。
4. テストセットアップ: `tests/`, `__tests__/`, `pytest.ini`, `jest.config.js` を確認し、ローカルでのテスト実行コマンドを確定する。

## プロジェクト固有の探索ポイント（AI への命令）

- ビルドと起動コマンドはファイルを読んでから実行する（例: `package.json` の `scripts`、`Makefile` のターゲット）。
- 依存サービスは `docker-compose.yml` / `k8s/` / `.env.example` から抽出する。DB/Redis/Elasticsearch などがあればローカル起動手順を優先する。
- 設定は `config/` または `settings/` にある場合が多い。シークレットは `.env` ではなく `.env.example` を参照して動作確認する。

## よく使うコマンド例（PowerShell）

※ 実行前に該当ファイルが存在することを確認してください。

- Node.js 系 (例: `package.json` がある場合)

  ```powershell
  cd <repo-root>
  npm ci    # or pnpm install / yarn install
  npm test
  npm run dev   # 開発起動（scripts に依存）
  ```

- Python 系 (例: `pyproject.toml` / `requirements.txt` がある場合)

  ```powershell
  cd <repo-root>
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  python -m pytest
  ```

- Docker Compose がある場合（依存サービスの起動）

  ```powershell
  docker-compose up -d --build
  docker-compose logs -f
  ```

## 具体的に参照すべきファイル例（見つかったら必ず読む）

- `package.json` の `scripts`（start/test/build の中身をコピーして実行可能にする）
- `docker-compose.yml`（サービス名、環境変数、依存順）
- `README.md`（ローカルセットアップの手順があれば優先）
- `src/main.ts` / `app.py` / `cmd/*`（実行のエントリポイント）

## 出力（変更）ポリシー

- 変更は最小単位で行い、必ずユニット/統合テストがあるなら先にテストを追加/修正する。
- 既存のスタイルや命名規約に従う（例: repository に ESLint / black / prettier の設定があればそれを尊重）。

## 追記とフィードバック

このファイルはテンプレートを兼ねています。実リポジトリを解析したら、以下の情報をここに追記してください:

- 実行コマンドの最短ワンライナー（例: `npm run dev` / `python -m pytest`）
- 主要コンポーネントとそのファイルパス（例: `services/payments` が決済マイクロサービス）
- ローカルで必ず立ち上げる依存サービス（例: Postgres, Redis）とその起動コマンド

---

ファイルを更新したら、変更をコミットし、こちらへフィードバックをください。実ソースが与えられれば、さらに具体的な例と 20–50 行の最終版を作成します。
