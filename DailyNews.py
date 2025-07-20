import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini")
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from composio_langchain import ComposioToolSet, Action, App
from agents import Agent, Runner, WebSearchTool
import asyncio

async def News_Tool():
    agent = Agent(name="Assistant", tools=[WebSearchTool()], instructions="You are a helpful assistant who collects news from the internet from reliable sources and summarizes them.")
    result1 = await Runner.run(agent, "What is the latest news about AI? Give a brief summary in 100 words for each news. Only give me news in the last 72 hours. Always quote the source and date of the news.")
    return result1.final_output

def Email_Tool(news, email):
    prompt = hub.pull("hwchase17/openai-functions-agent")

    composio_toolset = ComposioToolSet(api_key=st.secrets["COMPOSIO_API_KEY"])
    tools = composio_toolset.get_tools(actions=['GMAIL_SEND_EMAIL'])
    agent = create_openai_functions_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    email1 = email
    subject = "Daily AI News"
    body = news
    task = f"Send an email to {email1} with the subject {subject} and the body {body}"
    result = agent_executor.invoke({"input": task})
    return result

st.header(":blue[Daily AI News]")

if 'news' not in st.session_state:
    st.session_state['news'] = ''

if st.button("What's the recent news about AI?", type="primary"):
    with st.spinner("Fetching news..."):
        news = asyncio.run(News_Tool())
        st.session_state['news'] = news
        st.success("News fetched!")
st.text_area("Latest AI News", st.session_state['news'], height=300)            
st.write("Give your email address to send this news to your inbox. We do not store your email address!")
email = st.text_input("Enter your email")
if st.button("Send this news via Email"):
    if st.session_state['news']:
        with st.spinner("Sending email..."):
            try:
                Email_Tool(st.session_state['news'],email)
                st.success("Email sent!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
    else:
        st.warning("Please fetch the news first.")





