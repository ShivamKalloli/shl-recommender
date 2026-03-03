import streamlit as st
import requests

# The URL of your backend API (change this to your deployed URL later)
API_URL = "http://localhost:8000/recommend"

st.set_page_config(page_title="SHL Assessment Recommender", layout="centered")

st.image("https://www.shl.com/assets/logos/Logo-SHL-1200.png", width=150)
st.title("Intelligent Assessment Recommender")
st.write("Enter a job description or HR query below to get balanced assessment recommendations.")

query = st.text_area("Enter Query / Job Description:", height=150, placeholder="e.g., I want to hire a Senior Data Analyst with 5 years of experience...")

if st.button("Get Recommendations"):
    if not query.strip():
        st.warning("Please enter a query first.")
    else:
        with st.spinner("Analyzing intent and retrieving assessments..."):
            try:
                response = requests.post(API_URL, json={"query": query})
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommended_assessments", [])
                    
                    if recommendations:
                        st.success(f"Found {len(recommendations)} recommended assessments!")
                        for i, rec in enumerate(recommendations):
                            with st.expander(f"{i+1}. {rec['name']} ({', '.join(rec['test_type'])})"):
                                st.write(f"**Description:** {rec['description']}")
                                st.write(f"**Duration:** {rec['duration']} minutes")
                                st.write(f"**Remote Support:** {rec['remote_support']} | **Adaptive:** {rec['adaptive_support']}")
                                st.markdown(f"[View Assessment on SHL Catalog]({rec['url']})")
                    else:
                        st.info("No relevant assessments found for this query.")
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the backend API. Ensure app.py is running. Error: {e}")