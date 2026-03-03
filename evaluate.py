import pandas as pd
import requests
import time
import os
import urllib.parse

def get_slug(url):
    # Extracts the last meaningful part of the URL, ignoring slashes and decodes characters
    clean_url = urllib.parse.unquote(str(url).strip())
    parts = [p for p in clean_url.split('/') if p]
    return parts[-1].lower() if parts else ""

def calculate_recall():
    possible_names = ['train.csv', 'Gen_AI Dataset.xlsx - Train-Set.csv', 'Train-Set.csv']
    file_path = next((name for name in possible_names if os.path.exists(name)), None)
        
    if not file_path:
        print("❌ CRITICAL ERROR: Could not find the training file.")
        return
        
    print(f"Attempting to read: {file_path}")
    
    try:
        try:
            df = pd.read_csv(file_path)
            if len(df.columns) < 2:
                df = pd.read_excel(file_path)
        except:
            df = pd.read_excel(file_path)
            
        df = df.iloc[:, :2]
        df.columns = ['Query', 'Assessment_url']
        
        ground_truth = {}
        for _, row in df.iterrows():
            query = str(row['Query']).strip()
            url = str(row['Assessment_url']).strip()
            
            if query not in ground_truth:
                ground_truth[query] = set()
                
            # Store the SLUG instead of the full URL
            ground_truth[query].add(get_slug(url))
            
        print(f"✅ Successfully read {len(ground_truth)} unique queries for evaluation!")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    total_recall = 0.0
    processed = 0

    print("\nStarting Evaluation...")
    for query, true_slugs in ground_truth.items():
        print(f"Evaluating: {query[:60]}...")
        try:
            res = requests.post("http://localhost:8000/recommend", json={"query": query})
            if res.status_code == 200:
                data = res.json()
                recommendations = data.get("recommended_assessments", [])
                
                # Extract SLUGS from your API's predictions
                predicted_slugs = [get_slug(rec['url']) for rec in recommendations]
                
                # Calculate Recall (How many true slugs are in our predicted slugs?)
                hits = sum(1 for slug in true_slugs if slug in predicted_slugs)
                recall = hits / len(true_slugs) if len(true_slugs) > 0 else 0
                
                print(f"  -> Ground Truths: {len(true_slugs)} | Hits: {hits} | Recall: {recall:.2f}")
                
                total_recall += recall
                processed += 1
            else:
                print(f"  -> API Error: {res.status_code}")
        except Exception as e:
            print(f"  -> Connection Error: {e}")
            
        time.sleep(1) # Prevent rate limits

    if processed > 0:
        mean_recall = total_recall / processed
        print(f"\n" + "="*40)
        print(f"🏆 FINAL EVALUATION SCORE")
        print(f"Mean Recall: {mean_recall:.2f} ({(mean_recall*100):.1f}%)")
        print("="*40)
        print("Copy this score to include in your 2-page approach document!")

if __name__ == "__main__":
    calculate_recall()