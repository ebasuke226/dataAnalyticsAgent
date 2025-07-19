import os
from langchain_openai import ChatOpenAI

# 環境変数からAPIキーを取得
api_key = os.getenv("GPT_API_KEY")
if not api_key:
    raise ValueError("GPT_API_KEY environment variable not set.")

# LLMを初期化
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key)

# 判定する製品名のリスト
product_names = [
    "腐った", "ジャム", "怒り", "楽しんで", "教会", "ダッシュ", "ヒール", "副", 
    "ジャム", "障害", "スキーム", "ハードウェア", "バナー", "フェミニスト", 
    "持っていました", "デフォルト", "中世", "私", "文言", "彼女"
]

# 妥当でない製品名を格納するリスト
invalid_products = []

# 各製品名を判定
for name in product_names:
    prompt = f"""以下の単語は、一般的なeコマースサイトで販売されている「製品名」として妥当ですか？
「はい」か「いいえ」だけで答えてください。

単語: 「{name}」

回答:"""
    
    response = llm.invoke(prompt)
    answer = response.content.strip()
    
    print(f"製品名: {name}, AIの判定: {answer}")
    
    if "いいえ" in answer:
        invalid_products.append(name)

print("\n--- 削除候補の製品名リスト ---")
# 重複を排除して表示
for product in sorted(list(set(invalid_products))):
    print(product)
