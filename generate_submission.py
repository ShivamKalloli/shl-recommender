import pandas as pd
import requests
import time
import os

def generate_predictions():
    possible_names = ['test.csv', 'Gen_AI Dataset.xlsx - Test-Set.csv', 'Test-Set.csv']
    file_path = next((name for name in possible_names if os.path.exists(name)), None)
        
    print(f"Attempting to read: {file_path}")
    
    try:
        try:
            test_df = pd.read_csv(file_path)
            if len(test_df.columns) < 1 or "" in str(test_df.columns[0]):
                test_df = pd.read_excel(file_path)
        except:
            test_df = pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    submission_data = []
    print(f"Processing {len(test_df)} queries against your local API...")
    
    for index, row in test_df.iterrows():
        query = str(row.iloc[0]).strip()
        print(f"[{index+1}/{len(test_df)}] Recommending for: {query[:60]}...")
        
        try:
            res = requests.post("http://localhost:8000/recommend", json={"query": query})
            if res.status_code != 200:
                continue
                
            data = res.json()
            recommendations = data.get("recommended_assessments", [])
            urls = [rec['url'] for rec in recommendations][:3]
            
            while len(urls) < 3:
                urls.append("No further recommendation")
                
            for url in urls:
                submission_data.append({"Query": query, "Assessment_url": url})
        except Exception as e:
            print(f"  -> Error processing: {e}")
            
        time.sleep(1)

    sub_df = pd.DataFrame(submission_data)
    sub_df.to_csv("submission.csv", index=False)
    print("\n🎉 SUCCESS! Saved final SHL predictions to 'submission.csv'.")

if __name__ == "__main__":
    generate_predictions()