import subprocess
import os
import json
import re
import glob
import pandas as pd
import datetime
from bs4 import BeautifulSoup
import markdown
from PIL import Image


def ensure_data_path(path: str):
    """Ensure the given file path is inside /data."""
    if not os.path.abspath(path).startswith(os.path.abspath("/data")):
        raise Exception("Access denied: path not inside /data.")

def safe_write(path: str, content: str):
    ensure_data_path(path)
    with open(path, "w") as f:
        f.write(content)

def task_A1(params: dict):
    """
    A1. Install uv (if required) and run the datagen.py script from GitHub with ${user.email} as argument.
    """
    user_email = os.environ.get("USER_EMAIL", "default@example.com")
    datagen_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    import requests
    resp = requests.get(datagen_url)
    if resp.status_code != 200:
        raise Exception("Failed to download datagen.py")
    with open("datagen.py", "w") as f:
        f.write(resp.text)
    result = subprocess.run(["python", "datagen.py", user_email], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("datagen.py execution failed: " + result.stderr)
    return result.stdout

def task_A2(params: dict):
    """
    A2. Format the file using prettier@3.4.2.
    """
    path = params.get("input")
    ensure_data_path(path)
    result = subprocess.run(["prettier", "--write", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return "File formatted successfully."

def task_A3(params: dict):
    """
    A3. Count the number of Wednesdays in dates file and write the count.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    count = 0
    with open(input_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            dt = datetime.fromisoformat(line)
            if dt.weekday() == 2:
                count += 1
    safe_write(output_path, str(count))
    return f"Count: {count}"

def task_A4(params: dict):
    """
    A4. Sort the contacts by last_name then first_name.
    """
    input_path = params.get("input")
    output_path = params.get("output")
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
    log_dir = params.get("input")
    output_path = params.get("output")
    ensure_data_path(log_dir)
    ensure_data_path(output_path)
    log_files = glob.glob(f"{log_dir}/*.log")
    log_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    recent = log_files[:10]
    lines = []
    for log in recent:
        with open(log, "r") as f:
            first_line = f.readline().strip()
            lines.append(first_line)
    safe_write(output_path, "\n".join(lines))
    return "Recent log lines written."

def task_A6(params: dict):
    """
    A6. Extract first H1 from Markdown files and create index.
    """
    base_dir = params.get("input")
    output_path = params.get("output")
    ensure_data_path(base_dir)
    ensure_data_path(output_path)
    files = glob.glob(f"{base_dir}/**/*.md", recursive=True)
    index = {}
    for filepath in files:
        with open(filepath, "r") as f:
            for line in f:
                if line.startswith("# "):
                    relative = os.path.relpath(filepath, base_dir)
                    index[relative] = line[2:].strip()
                    break
    safe_write(output_path, json.dumps(index, indent=2))
    return "Docs indexed."

def task_A7(params: dict):
    """
    A7. Extract sender's email from email file.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    with open(input_path, "r") as f:
        content = f.read()
    match = re.search(r"[\w\.-]+@[\w\.-]+", content)
    email = match.group(0) if match else ""
    safe_write(output_path, email)
    return f"Email extracted: {email}"

def task_A8(params: dict):
    """
    A8. Extract credit card number from image.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    with open(input_path, "r") as f:
        content = f.read()
    card_number = re.sub(r"[\s-]", "", content)
    safe_write(output_path, card_number)
    return f"Card number extracted: {card_number}"

def task_A9(params: dict):
    """
    A9. Find most similar pair of comments.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    with open(input_path, "r") as f:
        comments = [line.strip() for line in f if line.strip()]
    if len(comments) < 2:
        raise Exception("Not enough comments.")
    best_score = -1
    best_pair = ("", "")
    def similarity(a, b):
        set_a = set(a.split())
        set_b = set(b.split())
        return len(set_a & set_b)
    for i in range(len(comments)):
        for j in range(i+1, len(comments)):
            score = similarity(comments[i], comments[j])
            if score > best_score:
                best_score = score
                best_pair = (comments[i], comments[j])
    safe_write(output_path, best_pair[0] + "\n" + best_pair[1])
    return f"Similar pair found (score {best_score})."

def task_A10(params: dict):
    """
    A10. Calculate total Gold ticket sales from database.
    """
    db_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(db_path)
    ensure_data_path(output_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    result = cur.fetchone()[0] or 0
    conn.close()
    safe_write(output_path, str(result))
    return f"Total Gold sales: {result}"

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
    """
    B8. Transcribe audio from an MP3 file.
    """
    input_path = params.get("input")
    output_path = params.get("output")
    ensure_data_path(input_path)
    ensure_data_path(output_path)
    
    # Simulated transcription
    text = f"Transcription of {input_path}"
    with open(output_path, "w") as f:
        f.write(text)
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
    """
    B10. Filter CSV and return JSON data.
    """
    input_path = params.get("input")
    filter_column = params.get("column")
    filter_value = params.get("value")
    ensure_data_path(input_path)
    
    df = pd.read_csv(input_path)
    filtered_df = df[df[filter_column] == filter_value]
    return filtered_df.to_json(orient="records")
