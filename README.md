# Press Project

このリポジトリは「政治家・公人の情報収集と自動記事生成」サービスの骨組みです。
目的: 政治や公人に関する経歴・発言・活動履歴を自動収集し、定期的に記事（Markdown/HTML）として出力するパイプラインのプロトタイプを提供します。

主な構成:
- `data/` : SQLite DB（`database.sqlite3`）と生データ
- `src/` : 実装コード（collectors, db, generators, utils）
- `site/` : 生成された Markdown/HTML を配置（GitHub Pages で公開）
- `.github/workflows/pages.yml` : GitHub Actions によるデプロイ設定

クイックスタート（PowerShell）:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py
```

テスト（簡易）:
```powershell
python -c "from src.db import repository as r; r.init_db('src/db/schema.sql'); print('DB OK')"
```

注意: ネットワーク依存の example_flow は `SKIP_NETWORK=1` を設定して回避できます。
<<<<<<< HEAD
# pressProject
自動記事作成
=======
# Press Project (scaffold)

このリポジトリは「政治家・公人の情報収集と自動記事生成」サービスの骨組みです。

主な構成:

- `data/` : SQLite DB（`database.sqlite3`）と生データ
- `src/` : 実装コード（collectors, db, generators, utils）
- `site/` : 生成された Markdown/HTML を配置（GitHub Pages で公開）
- `.github/workflows/pages.yml` : GitHub Actions によるデプロイ設定

クイックスタート（PowerShell）:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py
```

テスト（簡易）:

```powershell
python -c "from src.db import repository as r; r.init_db('src/db/schema.sql'); print('DB OK')"
```

注意: ネットワーク依存の example_flow は `SKIP_NETWORK=1` を設定して回避できます。
>>>>>>> e52d097 (Initial scaffold: add project files)
