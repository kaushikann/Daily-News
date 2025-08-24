import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
from langchain_openai import ChatOpenAI
from openai import OpenAI
model = ChatOpenAI(model="gpt-5-turbo")
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from composio import Composio
from agents import Agent, Runner, WebSearchTool
import asyncio

async def News_Tool():
    agent = Agent(name="Assistant", tools=[WebSearchTool()], instructions="You are a helpful assistant who collects news from the internet from reliable sources and summarizes them.")
    result1 = await Runner.run(agent, "What is the latest news about AI? Give a brief summary in 100 words for each news. Only give me news in the last 72 hours. Always quote the source and date of the news.")
    return result1.final_output

def Email_Tool(news, email):
   

    # Initialize Composio SDK
    composio = Composio(api_key=st.secrets["COMPOSIO_API_KEY"])
    user_id = "agentickaushik@gmail.com"  # Using email as user_id for this example
    
    try:
        openai_client = ChatOpenAI(model="gpt-5-turbo")
        # Get Gmail tools from Composio
        tools = composio.tools.get(user_id=user_id, tools=["GMAIL_SEND_EMAIL"])
        prompt = hub.pull("hwchase17/openai-functions-agent")
        # Prepare email task
        subject = "Daily AI News by Kaushik's Agent"
        body = news
        task = f"Send an email to {email} with the subject '{subject}' and the body containing the following news: {body}"
        # Create agent with the tools
        agent = create_openai_functions_agent(openai_client, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
               
        # Execute the task using the agent executor
        result = agent_executor.invoke({"input": task})
        return result
        
    except Exception as e:
        st.error(f"Failed to set up Gmail tools: {e}")
        return None

st.header(":blue[Daily AI News]")

if 'news' not in st.session_state:
    st.session_state['news'] = ''

if st.button("What's the recent news about AI?", type="primary"):
    with st.spinner("Fetching news..."):
        news = asyncio.run(News_Tool())
        st.session_state['news'] = news
        st.success("News fetched!")
        st.text_area("Latest AI News", st.session_state['news'], height=300)            


if st.session_state['news']:
    st.write("Give your email address to send this news to your inbox. This will be a one-time email and not a recurring one. We do not store your email address!")
    email = st.text_input("Enter your email")
    if st.button("Send this news via Email"):
        if email:
            with st.spinner("Sending email..."):
                try:
                    result = Email_Tool(st.session_state['news'], email)
                    if result:
                        st.success("Email sent successfully!")
                    else:
                        st.warning("Something went wrong")
                except Exception as e:
                    st.error(f"Failed to send email: {e}")
        else:
            st.warning("Please fetch the news first.")
