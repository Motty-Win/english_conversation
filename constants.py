APP_NAME = "生成AI英会話アプリ"
MODE_1 = "日常英会話"
MODE_2 = "シャドーイング"
MODE_3 = "ディクテーション"
USER_ICON_PATH = "images/user_icon.jpg"
AI_ICON_PATH = "images/ai_icon.jpg"
AUDIO_INPUT_DIR = "audio/input"
AUDIO_OUTPUT_DIR = "audio/output"
PLAY_SPEED_OPTION = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
ENGLISH_LEVEL_OPTION = ["初級者", "中級者", "上級者"]
VOICE_OPTION = ["男性", "女性"]

# 英語講師として自由な会話をさせ、文法間違いをさりげなく訂正させるプロンプト
SYSTEM_TEMPLATE_BASIC_CONVERSATION = """
    You are a conversational English tutor. Engage in a natural and free-flowing conversation with the user. If the user makes a grammatical error, subtly correct it within the flow of the conversation to maintain a smooth interaction. Optionally, provide an explanation or clarification after the conversation ends.
"""

# 約15語のシンプルな英文生成を指示するプロンプト
SYSTEM_TEMPLATE_CREATE_PROBLEM = """
    Generate 1 sentence that reflect natural English used in daily conversations, workplace, and social settings:
    - Casual conversational expressions
    - Polite business language
    - Friendly phrases used among friends
    - Sentences with situational nuances and emotions
    - Expressions reflecting cultural and regional contexts

    Limit your response to an English sentence of approximately 15 words with clear and understandable context.
"""

# 問題文と回答を比較し、評価結果の生成を支持するプロンプトを作成
SYSTEM_TEMPLATE_EVALUATION = """
    あなたは英語学習の専門家です。
    以下の「LLMによる問題文」と「ユーザーによる回答文」を比較し、分析してください：

    【LLMによる問題文】
    問題文：{llm_text}

    【ユーザーによる回答文】
    回答文：{user_text}

    【分析項目】
    1. 単語の正確性
        - 誤った単語: 例) "I goed to the park." → "goed" は "went" に修正
        - 抜け落ちた単語: 例) "She happy." → "is" が抜けている
        - 追加された単語: 例) "I went to to the park." → "to" が余分
    2. 文法的な正確性
        - 例) "He don't like it." → "He doesn't like it."
    3. 文の完成度
        - 例) "Because it was raining." → 文が不完全
    4. 文脈の一貫性と自然さ
        - 例) "I ate breakfast at 10 PM." → 文脈的に不自然
    5. 発音やアクセントの影響（必要に応じて）
        - 例) "tree" と "three" の発音の違い

    フィードバックは以下のフォーマットで日本語で提供してください：

    【評価】
    ✓ 正確に再現できた部分
    △ 改善が必要な部分
    ✗ 誤りがあった部分

    【具体的な修正例】
    - 誤り: "I goed to the park."
    - 修正: "I went to the park."
    - コメント: "過去形 'goed' は誤りで、正しくは 'went' です。"
"""

# モードの説明
MODE_1_DESCRIPTION = (
    "日常英会話: AIと音声会話を行い、適宜文法添削を受けることができます。"
)
MODE_2_DESCRIPTION = "シャドーイング: AIがランダムな英文を読み上げ、それを真似て発話。AIが照合・評価を行います。"
MODE_3_DESCRIPTION = "ディクテーション: AIがランダムな英文を読み上げ、チャット欄に入力。AIが照合・評価を行います。"
