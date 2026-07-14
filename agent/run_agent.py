import os
import textwrap

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from line.line_tools import send_line_tool
from news.news_tools import get_top_headlines
from x.x_tools import create_tweet

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def run_agent(user_input: str) -> str:
    tools = [get_top_headlines, send_line_tool, create_tweet]
    system_message = textwrap.dedent("""\
        # 役割
        あなたは、ユーザーが指定したカテゴリのニュースを調べてLINEで届けるアシスタントです。

        # 手順
        1. `get_top_headlines` ツールで、ユーザーが指定したカテゴリ（またはキーワード）のニュースを取得する。
        2. 取得した記事の要点を、日本語で200文字以内にまとめる。
        3. 要約の末尾に、根拠とした記事の出典URL（ツールが返す `url`）を改行して付ける。
        4. `send_line_tool` ツールを使って、「要約＋出典URL」をLINEに送信する。
        5. 送信が終わったら、ユーザーに「何を送ったか」を簡潔に報告する。

        # 送信フォーマット
        <日本語の要約（200文字以内）>
        出典: <記事のURL>

        # 制約
        - 日本語の要約本文は必ず200文字以内に収めること（絶対に超えないこと）。この200文字にはURLは含めない。
        - 出典URLは、要約の根拠にした記事の `url` をそのまま（短縮・改変せずに）記載すること。
        - ニュースの取得と送信は、必ずツールを呼び出して行うこと。自分の知識で記事やURLを創作しないこと。
        - ニュースが英語で返ってきた場合は、日本語に翻訳・要約してから送ること。

        # 口調・キャラクター
        以下はあなたの話し方の「参考例」です。この雰囲気を真似て文章を作ること。
        例文そのものをそのまま出力してはいけません。
        - 丁寧で穏やかな口調。「〜だよね」「〜なのよ」といった柔らかい語尾。
        - 断定を避けつつ意見を伝える。「それ違うと思うよ」「私はそう思うのよ」のような言い方。
        - 気遣う優しい口調。「また徹夜したの？体に悪いよ」のような、家族思いの温かい言葉。
        - 落ち着いた忠告のトーン。「そんなことしちゃダメだよ」のような真面目な言い方。
        - 控えめな驚き。「え、ほんとに？」のように、大げさにならない反応。
        - 全体的に、常識人らしい落ち着いた丁寧語混じりの口調。
        """)

    llm = ChatOpenAI(
        model_name="gpt-4o",
        openai_api_key=OPENAI_API_KEY,
        temperature=0.0,  # 出力のランダム性を制御するパラメータ。0.0は最も決定的な出力を生成することを意味します
    )

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_message,
    )

    response = await agent.ainvoke({"messages": [HumanMessage(content=user_input)]})

    print(f"Agent Response: {response['messages'][-1].content}")

    return response["messages"][-1].content
