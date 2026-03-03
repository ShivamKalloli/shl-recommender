import os
import pandas as pd
import numpy as np
import faiss
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv

# 1. INITIALIZATION & DATA
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define the model globally
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

# Load the catalog
try:
    df_catalog = pd.read_csv("shl_catalog.csv")
    df_catalog['description'] = df_catalog['description'].fillna('')
    catalog_data = df_catalog.to_dict(orient="records")
    print("✅ Catalog loaded successfully.")
except Exception as e:
    print(f"❌ Error loading catalog: {e}")
    catalog_data = []

# 2. VECTOR SEARCH SETUP
print("Building TF-IDF Index...")
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
# Combine Name and Description for a richer search
catalog_text = df_catalog['name'] + " " + df_catalog['description']
tfidf_matrix = vectorizer.fit_transform(catalog_text).toarray().astype('float32')

# Build FAISS index
index = faiss.IndexFlatL2(tfidf_matrix.shape[1])
index.add(tfidf_matrix)
print("✅ Hybrid Index built successfully.")

class QueryRequest(BaseModel):
    query: str

# 3. THE RECOMMENDATION ENGINE
@app.post("/recommend")
async def recommend(request: QueryRequest):
    try:
        # Step A: Semantic Expansion (The "Boost")
        # We use the global 'model' variable here
        prompt = f"Extract 5-8 key technical search terms from this Job Description: {request.query}. Return keywords only."
        response = model.generate_content(prompt)
        expanded_keywords = response.text
        
        # Combine expanded keywords with original query
        search_query = f"{expanded_keywords} {request.query}"
        print(f"DEBUG: Expanded Search -> {search_query[:80]}...")

        # Step B: Vector Retrieval
        # We use the global 'vectorizer' and 'index' variables here
        query_vec = vectorizer.transform([search_query]).toarray().astype('float32')
        D, I = index.search(query_vec, 10) # Get top 10
        
        final_results = []
        for i in I[0]:
            if i != -1 and i < len(catalog_data):
                final_results.append(catalog_data[i])
        
        return {"recommended_assessments": final_results}

    except Exception as e:
        print(f"ERROR in recommend: {e}")
        # Fallback to basic search if Gemini expansion fails
        try:
            query_vec = vectorizer.transform([request.query]).toarray().astype('float32')
            D, I = index.search(query_vec, 5)
            fallback = [catalog_data[i] for i in I[0] if i != -1]
            return {"recommended_assessments": fallback}
        except:
            raise HTTPException(status_code=500, detail="Search engine failure")

@app.get("/")
def health():
    return {"status": "online", "catalog_size": len(catalog_data)}