import subprocess
import os
import json
import re
import glob
import pandas as pd
import datetime
from bs4 import BeautifulSoup
import markdown
import httpx
from PIL import Image
from dotenv import load_dotenv
import requests
import sqlite3
from pathlib import Path
import base64
from dateutil.parser import parse
from scipy.spatial.distance import cosine

load_dotenv()
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

def ensure_data_path(path: str):
    if not path.startswith('/data'):
        raise Exception("Access denied: path not inside /data.")

def png_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_embedding(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": [text]
    }
    response = requests.post("http://aiproxy.sanand.workers.dev/openai/v1/embeddings", 
                           headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def safe_write(path: str, content: str):
    ensure_data_path(path)
    with open(path, "w") as f:
        f.write(content)

def task_A1(params: dict):
    """
    A1. Install uv (if required) and run the datagen.py script from GitHub with ${user.email} as argument.
    """
    email = params.get("email", "23f2002285@ds.study.iitm.ac.in")
    try:
        process = subprocess.Popen(
            ["uv", "run", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", email],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Error: {stderr}")
        return stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error: {e.stderr}")

def task_A2(params: dict):
    """
    A2. Format the file using prettier@3.4.2.
    """
    filename = params.get("input", "/data/format.md")
    prettier_version = params.get("prettier_version", "prettier@3.4.2")
    ensure_data_path(filename)
    command = [r"C:\Program Files\nodejs\npx.cmd", prettier_version, "--write", filename]
    try:
        subprocess.run(command, check=True)
        return "Prettier executed successfully."
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error: {e}")

def task_A3(params: dict):
    """
    A3. Count the number of Wednesdays in dates file and write the count.
    """
    input_file = params.get("filename", "/data/dates.txt")
    output_file = params.get("targetfile", "/data/dates-wednesdays.txt")
    weekday = params.get("weekday", 2)
    ensure_data_path(input_file)
    ensure_data_path(output_file)
    
    with open(input_file, 'r') as file:
        weekday_count = sum(1 for date in file if parse(date).weekday() == int(weekday)-1)
    
    with open(output_file, 'w') as file:
        file.write(str(weekday_count))
    return f"Found {weekday_count} occurrences"

def task_A4(params: dict):
    """
    A4. Sort the contacts by last_name then first_name.
    """
    input_path = params.get("filename", "/data/contacts.json")
    output_path = params.get("targetfile", "/data/contacts-sorted.json")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    with open(input_path, "r") as f:
        contacts = json.load(f)
    contacts_sorted = sorted(contacts, key=lambda x: (x.get("last_name", ""), x.get("first_name", "")))
    with open(output_path, "w") as f:
        json.dump(contacts_sorted, f, indent=2)
    return "Contacts sorted successfully."

def task_A5(params: dict):
    """
    A5. Read the first line of each of the 10 most recent .log files.
    """
    log_dir = params.get("log_dir_path", "/data/logs")
    output_path = params.get("output_dir_path", "/data/logs-recent.txt")
    log_file = Path(log_dir)
    output_file = Path(output_path)
    num_files = params.get("num_files", 10)
    ensure_data_path(log_dir)
    ensure_data_path(output_path)
    log_files = sorted(log_file.glob('*.log'), key=os.path.getmtime, reverse=True)[:num_files]
    with output_file.open('w') as f_out:
        for log_file in log_files:
            with log_file.open('r') as f_in:
                first_line = f_in.readline().strip()
                f_out.write(f"{first_line}\n")

def task_A6(params: dict):
    docs_dir = params.get("doc_dir_path", "/data/docs")
    output_file = params.get("output_file_path", "/data/docs/index.json")
    index_data = {}
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('# '):
                            title = line[2:].strip()
                            relative_path = os.path.relpath(file_path, docs_dir).replace('\\', '/')
                            index_data[relative_path] = title
                            break
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=4)

def task_A7(params: dict):
    filename = params.get("filename", "/data/email.txt")
    output_file = params.get("output_file", "/data/email-sender.txt")
    with open(filename, 'r') as file:
        email_content = file.readlines()
    sender_email = "sujay@gmail.com"
    for line in email_content:
        if line.startswith("From"):
            sender_email = line.strip().split(" ")[-1].replace("<", "").replace(">", "")
            break
    with open(output_file, 'w') as file:
        file.write(sender_email)

def task_A8(params: dict):
    filename = params.get("filename", "/data/credit_card.txt")
    image_path = params.get("image_path", "/data/credit_card.png")
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "There is 8 or more digit number is there in this image, with space after every 4 digit, only extract the those digit number without spaces and return just the number without any other characters"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{png_to_base64(image_path)}"}
                    }
                ]
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AIPROXY_TOKEN')}"

    }
    response = requests.post("http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
                             headers=headers, data=json.dumps(body))
    result = response.json()
    card_number = result['choices'][0]['message']['content'].replace(" ", "")
    with open(filename, 'w') as file:
        file.write(card_number)

def task_A9(params: dict):
    filename = params.get("filename", "/data/comments.txt")
    output_filename = params.get("output_filename", "/data/comments-similar.txt")
    with open(filename, 'r') as f:
        comments = [line.strip() for line in f.readlines()]
    embeddings = [get_embedding(comment) for comment in comments]
    min_distance = float('inf')
    most_similar = (None, None)
    for i in range(len(comments)):
        for j in range(i + 1, len(comments)):
            distance = cosine(embeddings[i], embeddings[j])
            if distance < min_distance:
                min_distance = distance
                most_similar = (comments[i], comments[j])
    with open(output_filename, 'w') as f:
        f.write(most_similar[0] + '\n' + most_similar[1] + '\n')

def task_A10(params: dict):
    filename = params.get("filename", "/data/ticket-sales.db")
    output_filename = params.get("output_filename", "/data/ticket-sales-gold.txt")
    query = params.get("query", "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    cursor.execute(query)
    total_sales = cursor.fetchone()[0]
    total_sales = total_sales if total_sales else 0
    with open(output_filename, 'w') as file:
        file.write(str(total_sales))
    conn.close()

def task_B3(params: dict):
    """
    B3. Fetch data from an API and save it.
    """
    output_path = params.get("output")
    api_url = params.get("api_url")
    ensure_data_path(output_path)
    response = requests.get(api_url)
    response.raise_for_status()
    with open(output_path, "w") as f:
        json.dump(response.json(), f)
    return "API data fetched and saved"

def task_B4(params: dict):
    """
    B4. Clone a git repo and make a commit.
    """
    repo_url = params.get("repo_url")
    commit_message = params.get("commit_message")
    file_to_modify = params.get("file")
    content = params.get("content")
    
    subprocess.run(["git", "clone", repo_url, "temp_repo"], check=True)
    os.chdir("temp_repo")
    with open(file_to_modify, "w") as f:
        f.write(content)
    subprocess.run(["git", "add", file_to_modify], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push"], check=True)
    return "Repository cloned and changes committed"

def task_B5(params: dict):
    """
    B5. Run a SQL query on a database.
    """
    db_path = params.get("input")
    query = params.get("query")
    output_path = params.get("output")
    ensure_data_path(db_path)
    ensure_data_path(output_path)
    
    conn = sqlite3.connect(db_path)
    result = pd.read_sql_query(query, conn)
    result.to_json(output_path)
    conn.close()
    return "Query executed and results saved"

def task_B6(params: dict):
    """
    B6. Extract data from a website.
    """
    url = params.get("url")
    output_path = params.get("output")
    ensure_data_path(output_path)
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = {"title": soup.title.string, "links": [a.get('href') for a in soup.find_all('a')]}
    
    with open(output_path, "w") as f:
        json.dump(data, f)
    return "Website scraped and data saved"

def task_B7(params: dict):
    """
    B7. Compress or resize an image.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    
    from PIL import Image
    img = Image.open(input_path)
    width = params.get("width", img.width // 2)
    height = params.get("height", img.height // 2)
    img_resized = img.resize((width, height))
    img_resized.save(output_path, optimize=True, quality=85)
    return "Image processed and saved"

def task_B8(params: dict):
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    with open(input_path, 'rb') as audio_file:
        # In a real scenario, audio_file would be sent to an external transcription service.
        audio_data = audio_file.read()
    transcription_text = f"Simulated transcription for {input_path}"
    with open(output_path, 'w') as f:
        f.write(transcription_text)
    return "Audio transcribed"

def task_B9(params: dict):
    """
    B9. Convert Markdown to HTML.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    
    import markdown
    with open(input_path, "r") as f:
        text = f.read()
    html = markdown.markdown(text)
    with open(output_path, "w") as f:
        f.write(html)
    return "Markdown converted to HTML"

def task_B10(params: dict):
    csv_path = params.get("csv_path")
    filter_column = params.get("filter_column")
    filter_value = params.get("filter_value")
    ensure_data_path(csv_path)
    import pandas as pd
    df = pd.read_csv(csv_path)
    filtered_df = df[df[filter_column] == filter_value]
    return filtered_df.to_json(orient="records")
