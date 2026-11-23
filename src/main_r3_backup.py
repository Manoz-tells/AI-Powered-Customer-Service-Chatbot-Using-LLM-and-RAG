import streamlit as st
from datetime import datetime

from langchain_helper import (
    get_qa_chain,
    get_kb_qa_chain,
    create_vector_db
)

from sentiment_analyzer import SentimentAnalyzer
from escalation_engine import EscalationEngine
from tone_adjuster import ToneAdjuster
from ticket_workflow import TicketWorkflow


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Service Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 CUSTOMER SERVICE CHATBOT")


# ============================================================
# LOAD COMPONENTS
# ============================================================

@st.cache_resource
def load_components():

    return (
        SentimentAnalyzer(),
        EscalationEngine(),
        ToneAdjuster(),
        TicketWorkflow()
    )


(
    sentiment_analyzer,
    escalation_engine,
    tone_adjuster,
    ticket_workflow
) = load_components()


# ============================================================
# LOAD RAG CHAINS
# ============================================================

@st.cache_resource
def load_qa_chains():

    original_chain = get_qa_chain()
    kb_chain = get_kb_qa_chain()

    return original_chain, kb_chain


(
    original_chain,
    kb_chain
) = load_qa_chains()


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


if "conversation_start" not in st.session_state:
    st.session_state.conversation_start = datetime.now()


if "existing_tickets" not in st.session_state:
    st.session_state.existing_tickets = []


if "ticket_counter" not in st.session_state:
    st.session_state.ticket_counter = 1


# ============================================================
# KNOWLEDGEBASE MANAGEMENT
# ============================================================

st.subheader("Knowledge Base")

if st.button("Create Knowledgebase"):

    with st.spinner("Creating knowledgebase..."):

        create_vector_db()

    st.success(
        "Original knowledgebase created successfully."
    )


# ============================================================
# USER QUESTION
# ============================================================

question = st.text_input(
    "Question:",
    placeholder="Ask your customer service question..."
)


# ============================================================
# MAIN CHATBOT FLOW
# ============================================================

if question:

    # ========================================================
    # R1: SENTIMENT ANALYSIS
    # ========================================================

    sentiment_result = sentiment_analyzer.analyze(
        message=question,
        conversation_history=st.session_state.conversation_history
    )

    sentiment = sentiment_result["sentiment"]
    confidence = sentiment_result["confidence"]


    # ========================================================
    # R1: ESCALATION DETECTION
    # ========================================================

    escalation_result = escalation_engine.evaluate(
        message=question,
        sentiment=sentiment,
        confidence=confidence,
        conversation_start=st.session_state.conversation_start,
        current_time=datetime.now(),
        conversation_history=st.session_state.conversation_history
    )


    # ========================================================
    # R3: KNOWLEDGE BASE RAG
    # ========================================================

    kb_response = kb_chain.invoke(
        {
            "query": question
        }
    )

    kb_answer = kb_response["result"]

    kb_sources = [
        document.metadata.get("source")
        for document in kb_response.get(
            "source_documents",
            []
        )
        if document.metadata.get("source")
    ]


    # ========================================================
    # ANSWER SELECTION
    # ========================================================

    # If the KB provides an actual answer, use it.
    # Otherwise fall back to the original RAG chatbot.

    if (
        kb_answer
        and "I don't know based on the available knowledge base."
        not in kb_answer
    ):

        original_answer = kb_answer

    else:

        response = original_chain.invoke(
            {
                "query": question
            }
        )

        original_answer = response["result"]


    # ========================================================
    # R1: TONE ADJUSTMENT
    # ========================================================

    adjusted_answer = tone_adjuster.adjust(
        response=original_answer,
        sentiment=sentiment,
        confidence=confidence
    )


    # ========================================================
    # R1: ESCALATION RECORD
    # ========================================================

    escalation_record = None

    if escalation_result["escalate"]:

        escalation_record = (
            escalation_engine.create_escalation_record(
                escalation_result=escalation_result,
                conversation_history=(
                    st.session_state.conversation_history
                ),
                current_message=question
            )
        )


    # ========================================================
    # ANSWER
    # ========================================================

    st.header("Answer")

    st.write(adjusted_answer)


    # ========================================================
    # R3: KNOWLEDGE BASE SOURCES
    # ========================================================

    if kb_sources:

        st.subheader("Knowledge Base Sources")

        unique_sources = list(
            dict.fromkeys(kb_sources)
        )

        for source in unique_sources:

            st.write(
                f"- `{source}`"
            )


    # ========================================================
    # R1: CONVERSATION ANALYSIS
    # ========================================================

    st.subheader("Conversation Analysis")

    st.write(
        f"**Sentiment:** {sentiment.capitalize()}"
    )

    st.write(
        f"**Confidence:** {confidence:.2f}"
    )


    # ========================================================
    # R1: ESCALATION INFORMATION
    # ========================================================

    if escalation_result["escalate"]:

        st.warning(
            "Escalation triggered → "
            + escalation_result["queue"]
        )

        st.write(
            "**Escalation reason:** "
            + ", ".join(
                escalation_result["reasons"]
            )
        )


    # ========================================================
    # R2: SUPPORT TICKET
    # ========================================================

    if escalation_result["escalate"]:

        st.subheader("Support Ticket")


        # ----------------------------------------------------
        # Agent configuration
        # ----------------------------------------------------

        agents = [

            {
                "name": "Agent A",
                "skills": [
                    "payment",
                    "refund"
                ],
                "available": True,
                "workload": 5
            },

            {
                "name": "Agent B",
                "skills": [
                    "payment",
                    "technical"
                ],
                "available": True,
                "workload": 2
            },

            {
                "name": "Agent C",
                "skills": [
                    "technical"
                ],
                "available": False,
                "workload": 0
            }
        ]


        # ----------------------------------------------------
        # Ticket workflow
        # ----------------------------------------------------

        ticket_result = ticket_workflow.process(

            message=question,

            existing_tickets=(
                st.session_state.existing_tickets
            ),

            conversation_history=(
                st.session_state.conversation_history
            ),

            start_time=(
                st.session_state.conversation_start
            ),

            current_time=datetime.now(),

            severity="high",

            sentiment=sentiment,

            customer_impact="high",

            issue_type="payment",

            agents=agents
        )


        # ----------------------------------------------------
        # Missing information
        # ----------------------------------------------------

        if ticket_result["status"] == "needs_information":

            st.info(
                ticket_result[
                    "validation"
                ]["clarification_message"]
            )


        else:

            ticket = ticket_result["ticket"]


            # ------------------------------------------------
            # Ticket ID
            # ------------------------------------------------

            ticket_id = (
                "TICKET-"
                + str(
                    st.session_state.ticket_counter
                ).zfill(3)
            )

            ticket["ticket_id"] = ticket_id


            st.session_state.ticket_counter += 1


            st.session_state.existing_tickets.append(
                ticket
            )


            # ------------------------------------------------
            # Ticket Details
            # ------------------------------------------------

            st.write(
                f"**Ticket ID:** {ticket_id}"
            )

            st.write(
                f"**Priority:** "
                f"{ticket_result['priority']['priority'].upper()}"
            )

            st.write(
                f"**SLA Status:** "
                f"{ticket_result['sla']['status']}"
            )


            # ------------------------------------------------
            # Duplicate Detection
            # ------------------------------------------------

            if ticket_result["duplicate"]["is_duplicate"]:

                st.warning(
                    "Possible duplicate ticket detected."
                )

            else:

                st.success(
                    "No duplicate ticket detected."
                )


            # ------------------------------------------------
            # Routing
            # ------------------------------------------------

            routing = ticket_result["routing"]


            if routing["assigned"]:

                st.write(
                    f"**Assigned Agent:** "
                    f"{routing['agent']}"
                )

            else:

                st.warning(
                    f"Ticket routing: "
                    f"{routing['reason']}"
                )


            # ------------------------------------------------
            # Agent Handoff
            # ------------------------------------------------

            st.subheader(
                "Agent Handoff Summary"
            )

            st.json(
                ticket_result["handoff"]
            )


            # ------------------------------------------------
            # SLA Warning
            # ------------------------------------------------

            if ticket_result["sla"]["warning"]:

                st.warning(
                    "SLA warning: "
                    "ticket has reached 75% of its SLA."
                )


            if ticket_result["sla"]["breached"]:

                st.error(
                    "SLA breached: "
                    "ticket requires escalation."
                )


    # ========================================================
    # CONVERSATION HISTORY
    # ========================================================

    st.session_state.conversation_history.append(
        question
    )


    # Keep only the latest 10 messages

    st.session_state.conversation_history = (
        st.session_state.conversation_history[-10:]
    )