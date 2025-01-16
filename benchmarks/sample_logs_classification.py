import argparse
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import re
import difflib
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

load_dotenv()

trieve_api_key = os.getenv('TRIEVE_API_KEY')
trieve_dataset_id = os.getenv('DATASET_ID')
trieve_api_host = os.getenv('TRIEVE_HOST')

# Load valid UIDs into a list for fast lookup
valid_uids = []
with open('valid-uids.txt', 'r') as f:
    for line in f:
        uid = line.strip()
        if uid:  # Skip empty lines
            valid_uids.append(uid)  # uid is already a string since it comes from reading a text file

def count_diffs(file1_path, file2_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()
        
        differ = difflib.Differ()
        diffs = list(differ.compare(file1_lines, file2_lines))
        
        diff_count = sum(1 for line in diffs if line.startswith(('- ', '+ ', '? ')))
        
        return diff_count

def search_trieve(log_message: str):
    headers = {
        'Authorization': f'Bearer {trieve_api_key}',
        'TR-Dataset': trieve_dataset_id
    }

    payload = {
        'search_type': 'fulltext',
        'query': log_message
    }

    response = requests.post(f'{trieve_api_host}/api/chunk/search', 
                           headers=headers,
                           json=payload)
    
    if response.status_code == 200:
        resp = response.json()
        chunks = resp['chunks']
        ids = [chunk["chunk"]["id"] for chunk in chunks]
        return ids
    else:
        raise Exception(f"Search failed with status code {response.status_code}: {response.text}")

def classify(chunk_ids: list[str], log_message: str) -> str:
    headers = {
        'Authorization': f'Bearer {trieve_api_key}',
        'TR-Dataset': trieve_dataset_id
    }

    payload = {
        'chunk_ids': chunk_ids,
        'prev_messages': [
            {
                'role': 'system',
                'content': 'You are an expert at classifying security logs into OCSF schema. Given a log entry, analyze the relevant documentation and determine the correct OCSF class - return just the class uid.'
            },
            {
                'role': 'user',
                'content': f'Provide the correct class uid for this log:\n{log_message}'
            }
        ],
        'temperature': 0.3,
        'stream_response': False
    }

    response = requests.post(
        f'{trieve_api_host}/api/chunk/generate',
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        words = response.text.split()
        for word in words:
            num_word = re.sub(r'[^0-9]', '', word)
            if num_word in valid_uids:
                return num_word
        return None
    else:
        raise Exception(f"RAG generation failed with status code {response.status_code}: {response.text}")

def get_template(uid: str):
    templates_dir = Path('./templates')
    # Look for files matching pattern: {uid}_*_required_template.json
    matching_files = list(templates_dir.glob(f'{uid}_*.json'))
    
    if not matching_files:
        raise FileNotFoundError(f"No template file found for UID {uid} matching pattern '{uid}_*_required_template.json'")
    
    # Use the first matching file
    template_path = matching_files[0]
    with open(template_path, 'r') as f:
        return json.load(f)

def extract_json(input_text: str):
    json_text = re.search(r"```json(.*?)```", input_text, re.DOTALL).group(1)
    clean_json = json_text.replace("\\n", "").replace('\\"', '"')
    try:
        parsed_json = json.loads(clean_json)
        return parsed_json  
    except json.JSONDecodeError as e:
        print(f"Error: {e}")
        print("clean_json: ", clean_json)
        return None


def get_ocsf_transformation(log_message: str, template: dict):
    headers = {
        'Authorization': f'Bearer {trieve_api_key}',
        'TR-Dataset': trieve_dataset_id
    }

    payload = {
        'chunk_ids': [],
        'prev_messages': [
            {
                'role': 'system',
                'content': 'You are an expert at transforming security logs into OCSF schema. Given a log entry and a template, generate the OCSF-compliant JSON transformation as a CLEAN JSON block in markdown, with no comments.'
            },
            {
                'role': 'user',
                'content': f'Transform this log entry into OCSF format using this template as a guide.\nLog:\n{log_message}\n\nTemplate:\n{json.dumps(template, indent=2)}'
            }
        ],
        'temperature': 0.3,
        'stream_response': False
    }

    response = requests.post(
        f'{trieve_api_host}/api/chunk/generate',
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        return extract_json(response.text)
    else:
        raise Exception(f"RAG generation failed with status code {response.status_code}: {response.text}")

def process_log_files(sample_logs_path: Path):
    event_files = []
    for path in sample_logs_path.rglob('*.event'):
        event_files.append(path)
    
    # Create transformed directory if it doesn't exist
    transformed_dir = Path('./transformed')
    os.makedirs(transformed_dir, exist_ok=True)
    
    for event_file in sorted(event_files):
        try:
            with open(event_file, 'r') as f:
                log_message = f.read()
                search_results = search_trieve(log_message)
                classification = classify(search_results, log_message)
                if classification:
                    print(f"\nFile: {event_file.name}")
                    print(f"Classification: {classification}")
                    try:
                        template = get_template(classification)
                        transformation = get_ocsf_transformation(log_message, template)
                        if transformation:
                            # Extract event code from filename (e.g., "4624" from "4624_0.event")
                            event_code = event_file.stem.split('_')[0]
                            
                            # Save transformation to file
                            output_file = transformed_dir / f"{event_code}.json"
                            with open(output_file, 'w') as f:
                                json.dump(transformation, f, indent=2)
                                print(f"Saved transformation to: {output_file}")
                    except FileNotFoundError as e:
                        print(f"Warning: {str(e)}")
                else:
                    print(f"\nFile: {event_file.name}")
                    print("No valid classification found")
        except Exception as e:
            print(f"Error processing {event_file.name}: {e}")

    total_fields = {}
    matching_fields_counts = {}
    class_uid_matches = {}
    
    for ground_truth_file in sample_logs_path.rglob('*.json'):
        event_code = ground_truth_file.stem.split('_')[0]
        transformed_file = transformed_dir / f"{event_code}.json"

        print("ground_truth_file: ", ground_truth_file)
        print("transformed_file: ", transformed_file)

        event_code_json = {}
        with open(ground_truth_file, 'r') as f:
            event_code_json = json.load(f)

        transformed_json = {}
        with open(transformed_file, 'r') as f:
            transformed_json = json.load(f)

        for key in transformed_json.keys():
            total_fields[event_code] = total_fields.get(event_code, 0) + 1
            if key in event_code_json.keys():
                if transformed_json[key] == event_code_json[key]:
                    matching_fields_counts[event_code] = matching_fields_counts.get(event_code, 0) + 1
                if key == "class_uid":
                    class_uid_matches[event_code] = transformed_json[key] == event_code_json[key]

    print(f"Total fields: {total_fields}")
    print(f"Matching fields: {matching_fields_counts}")
    print(f"Class UID matches: {class_uid_matches}")

    """
    Total fields: {'4663': 11, '4624': 17, '4625': 16, '4661': 11, '4689': 10, '4673': 9, '4688': 11}
    Matching fields: {'4663': 3, '4624': 11, '4625': 5, '4661': 3, '4689': 5, '4673': 2, '4688': 5}
    Class UID matches: {'4663': True, '4624': True, '4625': True, '4661': True, '4689': True, '4673': True, '4688': True}
    """

    # Set the style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (15, 12)

    # Create figure with subplots
    fig = plt.figure(constrained_layout=True)
    gs = fig.add_gridspec(2, 2)

    # Prepare data for fields comparison
    df_fields = pd.DataFrame({
        'Event Code': list(total_fields.keys()),
        'Total Fields': list(total_fields.values()),
        'Matching Fields': [matching_fields_counts.get(code, 0) for code in total_fields.keys()]
    })

    # Calculate match percentage
    df_fields['Match Percentage'] = (df_fields['Matching Fields'] / df_fields['Total Fields'] * 100).round(1)

    # Plot 1: Bar plot comparing total vs matching fields
    ax1 = fig.add_subplot(gs[0, :])
    x = np.arange(len(df_fields['Event Code']))
    width = 0.35

    ax1.bar(x - width/2, df_fields['Total Fields'], width, label='Total Fields', color='#2ecc71')
    ax1.bar(x + width/2, df_fields['Matching Fields'], width, label='Matching Fields', color='#3498db')

    # Add percentage labels on top of bars
    for i, pct in enumerate(df_fields['Match Percentage']):
        ax1.text(i, df_fields['Total Fields'].iloc[i], f'{pct}%', 
                ha='center', va='bottom')

    ax1.set_ylabel('Number of Fields')
    ax1.set_title('Field Matching Analysis by Event Code', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_fields['Event Code'])
    ax1.legend()

    # Plot 2: Pie chart of class UID matches
    ax2 = fig.add_subplot(gs[1, :])
    match_counts = pd.Series(class_uid_matches).value_counts()
    colors = ['#2ecc71' if x else '#e74c3c' for x in match_counts.index]
    
    # Check if there are any non-matching events before creating labels
    matching_count = match_counts.get(True, 0)
    non_matching_count = match_counts.get(False, 0)
    
    if non_matching_count == 0:
        # If all events match, only show one slice
        ax2.pie([matching_count], labels=[f'Matching ({matching_count} events)'],
                colors=['#2ecc71'], autopct='%1.1f%%', startangle=90)
    else:
        # Show both matching and non-matching slices
        ax2.pie([matching_count, non_matching_count], 
                labels=[f'Matching ({matching_count} events)', 
                       f'Non-matching ({non_matching_count} events)'],
                colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%', startangle=90)
    
    ax2.set_title('Class UID Match Distribution', pad=20)

    # Adjust layout and save
    plt.savefig('field_matching_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Average match percentage: {df_fields['Match Percentage'].mean():.1f}%")
    print(f"Best matching event: {df_fields.loc[df_fields['Match Percentage'].idxmax(), 'Event Code']} "
          f"({df_fields['Match Percentage'].max():.1f}%)")
    print(f"Worst matching event: {df_fields.loc[df_fields['Match Percentage'].idxmin(), 'Event Code']} "
          f"({df_fields['Match Percentage'].min():.1f}%)")
    
def main():
    parser = argparse.ArgumentParser(description='Process sample logs for classification benchmarking')
    parser.add_argument('--sample-logs-path', 
                       type=str,
                       required=True,
                       help='Path to the directory containing sample log files')
    
    args = parser.parse_args()
    sample_logs_path = Path(args.sample_logs_path)
    
    if not sample_logs_path.exists() or not sample_logs_path.is_dir():
        raise ValueError(f"Sample logs path '{sample_logs_path}' does not exist or is not a directory")
    
    process_log_files(sample_logs_path)

if __name__ == '__main__':
    main()
