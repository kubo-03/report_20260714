import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent, ToolNode

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


## 掛け算をする関数
@tool
def multiply_numbers(a: int, b: int) -> int:
    """2つの数値を掛け算する関数"""
    return a * b


## 足し算する関数
@tool
def add_numbers(a: int, b: int) -> int:
    """2つの数値を足し算する関数"""
    return a + b

def decide_next():


def run_agent(user_input: str) -> str:
    tools = [multiply_numbers, add_numbers]
    system_message = (
        "ユーザーの質問に対して、必要に応じてツールを使って答えてください。"
    )

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

    response = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    print(f"Agent Response: {response['messages'][-1].content}")

    return response
