import streamlit as st
from datetime import datetime

from langchain_helper import get_qa_chain, create_vector_db
from sentiment_analyzer import SentimentAnalyzer
from escalation_engine import EscalationEngine
from tone_adjuster import ToneAdjuster


st.set_page_config(
    page_title="Customer Service Chatbot",
    page_icon="🤖"
)

st.title("CUSTOMER SERVICE CHATBOT 🤖")


# Initialize components
@st.cache_resource
def load_components():
    return (
        SentimentAnalyzer(),
        EscalationEngine(),
        ToneAdjuster()
    )


sentiment_analyzer, escalation_engine, tone_adjuster = load_components()


# Initialize conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "conversation_start" not in st.session_state:
    st.session_state.conversation_start = datetime.now()


# Knowledgebase button
if st.button("Create Knowledgebase"):
    with st.spinner("Creating knowledgebase..."):
        create_vector_db()

    st.success("Knowledgebase created successfully.")


# Customer question
question = st.text_input("Question:")


if question:

    # Analyze sentiment using current message + history
    sentiment_result = sentiment_analyzer.analyze(
        message=question,
        conversation_history=st.session_state.conversation_history
    )

    sentiment = sentiment_result["sentiment"]
    confidence = sentiment_result["confidence"]

    # Evaluate escalation conditions
    escalation_result = escalation_engine.evaluate(
        message=question,
        sentiment=sentiment,
        confidence=confidence,
        conversation_start=st.session_state.conversation_start,
        current_time=datetime.now(),
        conversation_history=st.session_state.conversation_history
    )

    # Generate normal RAG response
    chain = get_qa_chain()

    response = chain.invoke(
        {"query": question}
    )

    original_answer = response["result"]

    # Adjust response tone based on sentiment
    adjusted_answer = tone_adjuster.adjust(
        response=original_answer,
        sentiment=sentiment,
        confidence=confidence
    )

    # Create escalation record if required
    escalation_record = None

    if escalation_result["escalate"]:

        escalation_record = escalation_engine.create_escalation_record(
            escalation_result=escalation_result,
            conversation_history=st.session_state.conversation_history,
            current_message=question
        )

    # Display answer
    st.header("Answer")
    st.write(adjusted_answer)

    # Display sentiment information
    st.subheader("Conversation Analysis")

    st.write(
        f"**Sentiment:** {sentiment.capitalize()}"
    )

    st.write(
        f"**Confidence:** {confidence:.2f}"
    )

    # Display escalation information
    if escalation_result["escalate"]:

        st.warning(
            f"Escalation triggered → {escalation_result['queue']}"
        )

        st.write(
            "**Escalation reason:** "
            + ", ".join(escalation_result["reasons"])
        )

    # Add current message to conversation history
    st.session_state.conversation_history.append(question)

    # Keep only the most recent 10 messages
    st.session_state.conversation_history = (
        st.session_state.conversation_history[-10:]
    )