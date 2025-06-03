import os
import streamlit as st
from elasticsearch import Elasticsearch
from groq import Groq

# Initialize Groq client
client = Groq(
    api_key="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"
)

# Elasticsearch setup
es_client = Elasticsearch('http://localhost:9200')
index_name = "course-questions"

# Search function
def elastic_search(query, course="data-engineering-zoomcamp"):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "text", "section"],
                        "type": "best_fields"
                    }
                },
                "filter": {
                    "term": {"course": course}
                }
            }
        }
    }
    response = es_client.search(index=index_name, body=search_query)
    return [hit['_source'] for hit in response['hits']['hits']]

# Prompt builder
def build_prompt(query, search_results):
    prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.
If the CONTEXT doesn’t contain the answer, output NONE.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""
    for doc in search_results:
        context += f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['text']}\n\n"
    
    return prompt_template.format(question=query, context=context).strip()

# Call Groq LLM
def llm(prompt):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("📚 Course Assistant (Groq + Elasticsearch)")
st.markdown("Ask any question about the **Data Engineering Zoomcamp** course.")

query = st.text_input("Enter your question here:")
if query:
    with st.spinner("Searching and generating an answer..."):
        search_results = elastic_search(query)
        prompt = build_prompt(query, search_results)
        answer = llm(prompt)

        st.subheader("📢 Answer")
        st.markdown(answer)

        st.subheader("🔍 Retrieved Context")
        for i, doc in enumerate(search_results):
            with st.expander(f"{i+1}. {doc['section']}"):
                st.markdown(f"**Q:** {doc['question']}")
                st.markdown(f"**A:** {doc['text']}")
