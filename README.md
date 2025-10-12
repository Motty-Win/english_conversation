# English Conversation App

AI翻訳機能を備えた英会話練習アプリケーション

## 機能

- 音声入力による英会話練習
- AI による翻訳機能
- 音声出力機能

## 必要要件

- Python 3.x
- Streamlit
- その他の依存関係は `requirements.txt` を参照

## セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/Motty-Win/english_conversation.git
cd english_conversation
```

2. 仮想環境を作成・有効化
```bash
python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

4. 環境変数を設定
`.env` ファイルを作成し、必要なAPIキーを設定してください

5. アプリケーションを起動
```bash
streamlit run main.py
```

## 使い方

アプリケーションを起動後、ブラウザで表示されるインターフェースから英会話練習を開始できます。

## ライセンス

MIT License
