import os
import json
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Ghar Ka Guru Sandbox", layout="wide")

st.title("Ghar Ka Guru — Text RAG Sandbox")

with st.sidebar:
    st.header("Configuration")
    api_base = st.text_input("API Base URL", value=API_BASE)
    student_id = st.text_input("Student ID", value="student_001")
    target_exam = st.selectbox("Target Exam", ["NEET", "JEE", "UPSC/IAS"])
    language = st.selectbox("Language", ["English", "Hindi", "Marathi", "Telugu", "Tamil", "Bhojpuri"]) 
    st.markdown("---")
    st.write("Upload a syllabus PDF and test chat with the model.")

tabs = st.tabs(["Syllabus Upload", "Daily Timetable", "Live Tutor Chat"])

with tabs[0]:
    st.header("Syllabus Upload")
    uploaded = st.file_uploader("Upload syllabus PDF", type=["pdf"])
    if uploaded is not None:
        if st.button("Ingest syllabus to Pinecone"):
            with st.spinner("Uploading and ingesting..."):
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                params = {"student_id": student_id}
                try:
                    r = requests.post(f"{api_base}/api/v1/ingest-syllabus", params=params, files=files, timeout=120)
                    r.raise_for_status()
                    st.success(f"Ingested {r.json().get('ingested_chunks')} chunks")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

with tabs[1]:
    st.header("Generate Daily Timetable")
    baseline = st.number_input("Baseline hours/week", value=10, min_value=1)
    weeks = st.number_input("Prep weeks", value=4, min_value=1)
    if st.button("Generate Timetable"):
        payload = {"student_id": student_id, "baseline_hours_per_week": int(baseline), "prep_weeks": int(weeks)}
        try:
            r = requests.post(f"{api_base}/api/v1/generate-timetable", json=payload, timeout=30)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed: {e}")

with tabs[2]:
    st.header("Live Tutor Chat")
    chat_input = st.text_area("Ask the tutor a question", height=120)
    if st.button("Send") and chat_input.strip():
        payload = {"student_id": student_id, "target_exam": target_exam, "language": language, "query_text": chat_input}
        try:
            r = requests.post(f"{api_base}/api/v1/chat", json=payload, timeout=60)
            r.raise_for_status()
            ans = r.json().get("answer")
            st.markdown("**Tutor response:**")
            st.write(ans)
        except Exception as e:
            st.error(f"Chat failed: {e}")

st.markdown("---")
st.caption("Ghar Ka Guru — Phase 1 sandbox. For voice features see README roadmap.")
