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


def setup_composio_connection():
    """Setup Composio connection once and store in session state"""
    if 'composio_connected' not in st.session_state or not st.session_state['composio_connected']:
        try:
            # Initialize Composio SDK
            composio = Composio(api_key=st.secrets["COMPOSIO_API_KEY"])
            user_id = "agentickaushik@gmail.com"
            
            # Initialize connection request for Gmail
            connection_request = composio.connected_accounts.initiate(
                user_id=user_id,
                auth_config_id=st.secrets["GMAIL_AUTH_CONFIG_ID"]
            )
            
            # Wait for the connection to be established
            connected_account = connection_request.wait_for_connection()
            
            # Store the connected composio instance and user_id in session state
            st.session_state['composio'] = composio
            st.session_state['user_id'] = user_id
            st.session_state['composio_connected'] = True
            
            st.success("Composio Gmail connection established successfully!")
            return True
            
        except Exception as e:
            st.error(f"Failed to set up Composio connection: {e}")
            return False
    return True

async def News_Tool():
    agent = Agent(name="Assistant", tools=[WebSearchTool()], instructions="You are a helpful assistant who collects news from the internet from reliable sources and summarizes them.")
    result1 = await Runner.run(agent, "What is the latest news about AI? Give a brief summary in 100 words for each news. Only give me news in the last 72 hours. Always quote the source and date of the news.")
    return result1.final_output

def Email_Tool(news, email):
    prompt = hub.pull("hwchase17/openai-functions-agent")
    
    try:
        # Check if Composio is connected, if not, show setup button
        if 'composio_connected' not in st.session_state or not st.session_state['composio_connected']:
            st.warning("Composio connection not established. Please click 'Setup Composio Connection' first.")
            return None
        
        # Get stored Composio instance and user_id
        composio = st.session_state['composio']
        user_id = st.session_state['user_id']
        
        # Get Gmail tools from Composio
        tools = composio.tools.get(user_id=user_id, tools=["GMAIL_SEND_EMAIL"])
        
        # Create agent with the tools
        agent = create_openai_functions_agent(model, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        # Prepare email task
        subject = "Daily AI News by Kaushik's Agent"
        body = news
        task = f"Send an email to {email} with the subject '{subject}' and the body containing the following news: {body}"
        
        # Execute the task using the agent executor
        result = agent_executor.invoke({"input": task})
        return result
        
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return None

st.header(":blue[Daily AI News]")

# Composio Connection Setup
if st.button("🔗 Setup Composio Connection", type="secondary"):
    with st.spinner("Setting up Composio connection..."):
        setup_composio_connection()

# Show connection status
if 'composio_connected' in st.session_state and st.session_state['composio_connected']:
    st.success("✅ Composio Gmail connection is active")
else:
    st.warning("⚠️ Composio connection not established. Please click 'Setup Composio Connection' first.")

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
