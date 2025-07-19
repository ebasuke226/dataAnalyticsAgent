from crewai import Agent, Task, Crew
from .llm import get_llm

llm = get_llm()

# エージェントの定義
sql_developer_agent = Agent(
    role='シニアSQLデベロッパー',
    goal='ユーザーの要求と提供されたスキーマ情報に基づいて、SQLiteで動作する効率的で正確なSQLクエリを作成する。',
    backstory='あなたはデータベース設計とクエリ最適化に20年の経験を持つ専門家です。特に複雑なJOINやサブクエリの構築に長けています。',
    llm=llm,
    allow_delegation=False,
    verbose=True
)

sql_reviewer_agent = Agent(
    role='データベース管理者',
    goal='提示されたSQLクエリをレビューし、構文の正確性、パフォーマンス、ベストプラクティスへの準拠を確認する。',
    backstory='あなたは大規模システムのデータベース運用を担当しており、わずかなパフォーマンスの低下も見逃さない鋭い目を持っています。SQLのアンチパターンに精通しています。',
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# タスクの定義
def create_sql_generation_crew(user_query: str, schema: str) -> Crew:
    """ユーザーの要求とスキーマに基づいてSQL生成クルーを作成する"""
    create_sql_task = Task(
        description=f"""ユーザーの要求とデータベーススキーマに基づいて、SQLiteで動作する最適なSQLクエリを作成してください。

        ### ユーザーの要求:
        {user_query}

        ### データベーススキーマ:
        {schema}
        """,
        agent=sql_developer_agent,
        expected_output='実行可能な単一のSQLクエリ文字列。クエリ以外のテキスト（解説や```sqlのようなマークダウン）は絶対に含めないでください。'
    )

    review_sql_task = Task(
        description="""作成されたSQLクエリをレビューし、問題があれば修正してください。特に、ユーザーの要求を完全に満たしているか、構文は正しいか、パフォーマンスは問題ないかを確認してください。""",
        agent=sql_reviewer_agent,
        expected_output='レビュー済みの最終的なSQLクエリ文字列。クエリ以外のテキスト（解説や```sqlのようなマークダウン）は絶対に含めないでください。'
    )

    return Crew(
        agents=[sql_developer_agent, sql_reviewer_agent],
        tasks=[create_sql_task, review_sql_task],
        verbose=True
    )
