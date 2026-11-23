import os
import json
import streamlit as st
from datetime import datetime

from langchain_helper import (
    safe_kb_query,
    create_vector_db
)

from sentiment_analyzer import SentimentAnalyzer
from escalation_engine import EscalationEngine
from tone_adjuster import ToneAdjuster
from ticket_workflow import TicketWorkflow
from multimodal_processor import MultimodalProcessor
from pii_masker import PIIMasker
from evidence_comparator import EvidenceComparator
from evidence_quality import EvidenceQualityChecker
from multimodal_safety import MultimodalSafetyGuard
from multimodal_queue import MultimodalQueue
from file_retention import FileRetentionManager

JOB_STORE_FILE = "multimodal_jobs.json"

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Service Chatbot",
    page_icon="🤖"
)

st.title("CUSTOMER SERVICE CHATBOT 🤖")


# ============================================================
# LOAD COMPONENTS
# ============================================================

@st.cache_resource
def load_components():

    return (
        SentimentAnalyzer(),
        EscalationEngine(),
        ToneAdjuster(),
        TicketWorkflow(),
        MultimodalProcessor(),
        PIIMasker(),
        EvidenceComparator(),
        EvidenceQualityChecker(),
        MultimodalSafetyGuard(),
        MultimodalQueue(),
        FileRetentionManager()
    )


(
    sentiment_analyzer,
    escalation_engine,
    tone_adjuster,
    ticket_workflow,
    multimodal_processor,
    pii_masker,
    evidence_comparator,
    evidence_quality_checker,
    multimodal_safety_guard,
    multimodal_queue,
    file_retention_manager
) = load_components()


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


if "multimodal_jobs" not in st.session_state:

    try:

        with open(
            JOB_STORE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            st.session_state.multimodal_jobs = json.load(
                file
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        st.session_state.multimodal_jobs = {}

for saved_job in st.session_state.multimodal_jobs.values():
    multimodal_queue.restore_job(saved_job)

def save_multimodal_jobs():

    with open(
        JOB_STORE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            st.session_state.multimodal_jobs,
            file,
            indent=4
        )

# ============================================================
# KNOWLEDGE BASE CREATION
# ============================================================

if st.button("Create Knowledgebase"):

    with st.spinner(
        "Creating knowledgebase..."
    ):

        create_vector_db()

    st.success(
        "Knowledgebase created successfully."
    )


# ============================================================
# USER QUESTION
# ============================================================

question = st.text_input(
    "Question:"
)


# ============================================================
# MULTIMODAL FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload an image, PDF, or text file:",
    key="multimodal_file_uploader",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "pdf",
        "txt"
    ]
)


# ============================================================
# R5: MULTIMODAL FILE PROCESSING
# ============================================================

uploaded_evidence = None
uploaded_text = ""


if "multimodal_upload_map" not in st.session_state:

    st.session_state.multimodal_upload_map = {}

    for saved_job in (
        st.session_state.multimodal_jobs.values()
    ):

        upload_key = saved_job.get(
            "upload_key"
        )

        job_id = saved_job.get(
            "job_id"
        )

        if upload_key and job_id:

            st.session_state.multimodal_upload_map[
                upload_key
            ] = job_id


if uploaded_file:

    file_bytes = uploaded_file.getvalue()

    temp_file_path = (
        ".r5_" + uploaded_file.name
    )


    with open(
        temp_file_path,
        "wb"
    ) as file:

        file.write(
            file_bytes
        )


    # ========================================================
    # FILE VALIDATION
    # ========================================================

    validation_result = (
        multimodal_processor.validate_file(
            temp_file_path
        )
    )


    if not validation_result.get(
        "valid",
        False
    ):

        st.error(
            validation_result.get(
                "reason",
                "Invalid file."
            )
        )


    else:

        # ====================================================
        # MULTIMODAL SAFETY CHECK
        # ====================================================

        safety_result = (
            multimodal_safety_guard.validate(
                uploaded_file.name
            )
        )


        if not safety_result.get(
            "safe",
            False
        ):

            st.error(
                "File rejected for security reasons."
            )


        else:

            # =================================================
            # CREATE STABLE UPLOAD KEY
            # =================================================

            import hashlib

            upload_key = hashlib.sha256(
                file_bytes
            ).hexdigest()


            # =================================================
            # SUBMIT BACKGROUND JOB ONLY ONCE
            # =================================================

            if upload_key not in (
                st.session_state.multimodal_upload_map
            ):

                job_result = (
                    multimodal_queue.submit(
                        multimodal_processor,
                        temp_file_path
                    )
                )


                job_id = job_result.get(
                    "job_id"
                )


                st.session_state.multimodal_jobs[
                    job_id
                ] = {
                    "job_id": job_id,
                    "file_name": uploaded_file.name,
                    "file_path": temp_file_path,
                    "upload_key": upload_key
                }

                save_multimodal_jobs()


                st.session_state.multimodal_upload_map[
                    upload_key
                ] = job_id

                save_multimodal_jobs()

                st.info(
                    "File submitted for background processing."
                )


            else:

                job_id = (
                    st.session_state.multimodal_upload_map[
                        upload_key
                    ]
                )


            # =================================================
            # CHECK CURRENT JOB STATUS
            # =================================================

            job_status = (
                multimodal_queue.get_status(
                    job_id
                )
            )


            current_status = job_status.get(
                "status",
                "unknown"
            )


            if current_status in (
                "queued",
                "running"
            ):

                st.info(
                    "File is still being processed in the "
                    "background. Please wait for completion."
                )


            elif current_status == "completed":

                uploaded_evidence = (
                    job_status.get(
                        "result"
                    )
                )


                if uploaded_evidence:

                    uploaded_text = (
                        uploaded_evidence.get(
                            "text",
                            ""
                        )
                    )


                    # =========================================
                    # PROMPT INJECTION CHECK
                    # =========================================

                    content_safety_result = (
                        multimodal_safety_guard.validate(
                            uploaded_text
                        )
                    )


                    if not content_safety_result.get(
                        "safe",
                        False
                    ):

                        st.error(
                            "File content rejected for "
                            "security reasons."
                        )

                        uploaded_evidence = None
                        uploaded_text = ""


                    else:

                        # =====================================
                        # EVIDENCE QUALITY CHECK
                        # =====================================

                        quality_result = (
                            evidence_quality_checker.check(
                                uploaded_text,
                                uploaded_evidence.get(
                                    "evidence",
                                    {}
                                )
                            )
                        )


                        if quality_result.get(
                            "quality"
                        ) == "LOW":

                            st.warning(
                                "The uploaded file has low-quality "
                                "or insufficient evidence. "
                                "Please upload a clearer file."
                            )


                        else:

                            st.success(
                                "File processed successfully."
                            )


                            # ================================
                            # DISPLAY EXTRACTED EVIDENCE
                            # ================================

                            st.write(
                                "**Extracted Evidence:**"
                            )


                            st.json(
                                pii_masker.mask_dict(
                                    uploaded_evidence.get(
                                        "evidence",
                                        {}
                                    )
                                )
                            )


                            # ================================
                            # EVIDENCE COMPARISON
                            # ================================

                            if question:

                                evidence_result = (
                                    evidence_comparator.compare(
                                        question,
                                        uploaded_evidence.get(
                                            "evidence",
                                            {}
                                        )
                                    )
                                )


                                st.write(
                                    "**Evidence Verification:**"
                                )


                                st.json(
                                    pii_masker.mask_dict(
                                        evidence_result
                                    )
                                )


                                if evidence_result.get(
                                    "status"
                                ) == "CONFLICT_DETECTED":

                                    st.error(
                                        "The uploaded evidence "
                                        "conflicts with the customer "
                                        "message. Please verify "
                                        "the information."
                                    )


                                elif evidence_result.get(
                                    "status"
                                ) == "CLARIFICATION_REQUIRED":

                                    st.warning(
                                        "Some required evidence "
                                        "could not be verified. "
                                        "Please provide clearer or "
                                        "more complete information."
                                    )


            elif current_status == "failed":

                st.error(
                    "Background processing failed: "
                    + str(
                        job_status.get(
                            "error",
                            "Unknown error"
                        )
                    )
                )


            else:

                st.warning(
                    "Background job status: "
                    + str(current_status)
                )


# ============================================================
# R5: FILE RETENTION CLEANUP
# ============================================================

if st.session_state.multimodal_jobs:

    for job_id, job_info in list(
        st.session_state.multimodal_jobs.items()
    ):

        job_status = (
            multimodal_queue.get_status(
                job_id
            )
        )


        if job_status.get(
            "status"
        ) in (
            "completed",
            "failed"
        ):

            file_path = job_info.get(
                "file_path"
            )


            if file_path:

                file_retention_manager.cleanup_file(
                    file_path
                )


# ============================================================
# R5: BACKGROUND JOB STATUS
# ============================================================

if st.session_state.multimodal_jobs:

    st.subheader(
        "Background File Processing"
    )


    for job_id, job_info in (
        st.session_state.multimodal_jobs.items()
    ):

        job_status = (
            multimodal_queue.get_status(
                job_id
            )
        )


        st.write(
            f"**Job:** `{job_id}`"
        )


        st.write(
            f"**File:** "
            f"{job_info.get('file_name', 'Unknown')}"
        )


        st.write(
            f"**Status:** "
            f"{job_status.get('status', 'Unknown')}"
        )


        if job_status.get(
            "status"
        ) == "failed":

            st.error(
                "Background processing failed: "
                + str(
                    job_status.get(
                        "error",
                        "Unknown error"
                    )
                )
            )


        elif job_status.get(
            "status"
        ) == "running":

            st.info(
                "Processing file in background..."
            )


        elif job_status.get(
            "status"
        ) == "queued":

            st.info(
                "File is waiting in the processing queue..."
            )


        elif job_status.get(
            "status"
        ) == "completed":

            st.success(
                "Background processing completed."
            )
            result = job_status.get(
                "result"
            )

            if result:

                st.write(
                    "**Extracted Evidence:**"
                )

                st.json(
                    pii_masker.mask_dict(
                        result.get(
                            "evidence",
                            {}
                        )
                    )
                )

# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    # ========================================================
    # R1: SENTIMENT ANALYSIS
    # ========================================================

    sentiment_result = sentiment_analyzer.analyze(
        message=question,
        conversation_history=(
            st.session_state.conversation_history
        )
    )


    sentiment = sentiment_result.get(
        "sentiment",
        "neutral"
    )


    confidence = sentiment_result.get(
        "confidence",
        0.0
    )


    # ========================================================
    # R1: ESCALATION DETECTION
    # ========================================================

    escalation_result = escalation_engine.evaluate(
        message=question,
        sentiment=sentiment,
        confidence=confidence,
        conversation_start=(
            st.session_state.conversation_start
        ),
        current_time=datetime.now(),
        conversation_history=(
            st.session_state.conversation_history
        )
    )


    # ========================================================
    # KNOWLEDGE BASE RAG
    # ========================================================

    kb_response = safe_kb_query(
        question
    )


    # ========================================================
    # KB ANSWER
    # ========================================================

    original_answer = kb_response.get(
        "result",
        "I don't know based on the available knowledge base."
    )


    # ========================================================
    # TONE ADJUSTMENT
    # ========================================================

    try:

        adjusted_answer = tone_adjuster.adjust(
            response=original_answer,
            sentiment=sentiment,
            confidence=confidence
        )


    except Exception as error:

        error_text = str(error).lower()


        if (
            "429" in error_text
            or "resource_exhausted" in error_text
            or "quota" in error_text
        ):

            adjusted_answer = original_answer

            st.warning(
                "The Gemini API request limit was reached. "
                "The knowledge-base response is being shown "
                "without tone adjustment."
            )


        elif (
            "503" in error_text
            or "unavailable" in error_text
        ):

            adjusted_answer = original_answer

            st.warning(
                "The Gemini service is temporarily unavailable. "
                "The knowledge-base response is being shown "
                "without tone adjustment."
            )


        else:

            adjusted_answer = original_answer

            st.warning(
                "Tone adjustment is temporarily unavailable. "
                "The original knowledge-base response is shown."
            )


    # ========================================================
    # ESCALATION RECORD
    # ========================================================

    escalation_record = None


    if escalation_result.get(
        "escalate",
        False
    ):

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
    # DISPLAY ANSWER
    # ========================================================

    st.header("Answer")


    st.write(
        adjusted_answer
    )


    # ========================================================
    # KB SOURCES
    # ========================================================

    source_citations = kb_response.get(
        "source_citations",
        []
    )


    if source_citations:

        st.subheader(
            "Knowledge Base Sources"
        )


        for citation in source_citations:

            st.write(
                f"- `{citation.get('source', 'Unknown')}` "
                f"(v{citation.get('version', 'Unknown')})"
            )


    blocked_sources = kb_response.get(
        "blocked_sources",
        []
    )


    if blocked_sources:

        st.warning(
            "Unsafe knowledge-base content was blocked: "
            + ", ".join(blocked_sources)
        )


    # ========================================================
    # SERVICE ERROR INFORMATION
    # ========================================================

    service_error = kb_response.get(
        "error"
    )


    if service_error:

        if service_error == "RATE_LIMIT":

            st.warning(
                "The Gemini API request limit was reached. "
                "The application is still running. "
                "The knowledge base fallback response is being used."
            )


        elif service_error == "SERVICE_UNAVAILABLE":

            st.warning(
                "The Gemini service is temporarily unavailable. "
                "The knowledge base fallback response is being used."
            )


        elif service_error not in (
            "NO_KB_RESULTS",
            "NO_KB_CONTENT"
        ):

            st.warning(
                "The AI response service is temporarily "
                "unavailable. The knowledge base response "
                "is being shown."
            )


    # ========================================================
    # FALLBACK INFORMATION
    # ========================================================

    if kb_response.get(
        "fallback",
        False
    ):

        st.info(
            "Fallback mode: The response was generated "
            "directly from the available knowledge base."
        )


    # ========================================================
    # CONVERSATION ANALYSIS
    # ========================================================

    st.subheader(
        "Conversation Analysis"
    )


    st.write(
        f"**Sentiment:** "
        f"{sentiment.capitalize()}"
    )


    st.write(
        f"**Confidence:** "
        f"{confidence:.2f}"
    )


    # ========================================================
    # ESCALATION INFORMATION
    # ========================================================

    if escalation_result.get(
        "escalate",
        False
    ):

        st.warning(
            "Escalation triggered → "
            + escalation_result.get(
                "queue",
                "priority-escalation"
            )
        )


        reasons = escalation_result.get(
            "reasons",
            []
        )


        if reasons:

            st.write(
                "**Escalation reason:** "
                + ", ".join(reasons)
            )


    # ========================================================
    # R2: SUPPORT TICKET
    # ========================================================

    if escalation_result.get(
        "escalate",
        False
    ):

        st.subheader(
            "Support Ticket"
        )


        # ----------------------------------------------------
        # Available agents
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


        # ====================================================
        # MISSING INFORMATION
        # ====================================================

        if (
            ticket_result.get("status")
            == "needs_information"
        ):

            validation = ticket_result.get(
                "validation",
                {}
            )


            clarification_message = validation.get(
                "clarification_message",
                "Please provide the required information."
            )


            st.info(
                clarification_message
            )


        # ====================================================
        # TICKET CREATED
        # ====================================================

        else:

            ticket = ticket_result.get(
                "ticket",
                {}
            )


            # ------------------------------------------------
            # Generate ticket ID
            # ------------------------------------------------

            ticket_id = (
                "TICKET-"
                + str(
                    st.session_state.ticket_counter
                ).zfill(3)
            )


            ticket["ticket_id"] = (
                ticket_id
            )


            st.session_state.ticket_counter += 1


            st.session_state.existing_tickets.append(
                ticket
            )


            # =================================================
            # TICKET DETAILS
            # =================================================

            st.write(
                f"**Ticket ID:** "
                f"{ticket_id}"
            )


            priority_result = ticket_result.get(
                "priority",
                {}
            )


            priority = priority_result.get(
                "priority",
                "high"
            )


            st.write(
                f"**Priority:** "
                f"{priority.upper()}"
            )


            sla_result = ticket_result.get(
                "sla",
                {}
            )


            st.write(
                f"**SLA Status:** "
                f"{sla_result.get('status', 'Unknown')}"
            )


            # =================================================
            # DUPLICATE DETECTION
            # =================================================

            duplicate_result = ticket_result.get(
                "duplicate",
                {}
            )


            if duplicate_result.get(
                "is_duplicate",
                False
            ):

                st.warning(
                    "Possible duplicate ticket detected."
                )


            else:

                st.success(
                    "No duplicate ticket detected."
                )


            # =================================================
            # ROUTING
            # =================================================

            routing = ticket_result.get(
                "routing",
                {}
            )


            if routing.get(
                "assigned",
                False
            ):

                st.write(
                    f"**Assigned Agent:** "
                    f"{routing.get('agent', 'Unknown')}"
                )


            else:

                st.warning(
                    f"Ticket routing: "
                    f"{routing.get('reason', 'No agent assigned')}"
                )


            # =================================================
            # AGENT HANDOFF
            # =================================================

            st.subheader(
                "Agent Handoff Summary"
            )


            st.json(
                ticket_result.get(
                    "handoff",
                    {}
                )
            )


            # =================================================
            # SLA WARNING
            # =================================================

            if sla_result.get(
                "warning",
                False
            ):

                st.warning(
                    "SLA warning: "
                    "ticket has reached 75% "
                    "of its SLA."
                )


            if sla_result.get(
                "breached",
                False
            ):

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
        st.session_state.conversation_history[
            -10:
        ]
    )
