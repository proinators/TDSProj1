import openai
import json
import os

# The system prompt string (as defined above)
SYSTEM_PROMPT = """
You are an automation task parser. Your job is to read a task description (provided by the user) and determine which one of the following automation tasks it represents. Your output must be a JSON object that has a "tool-name" field whose value is one of the following allowed task names, and additional parameters if required. Do not output any extra text outside of valid JSON.

Security and business rules:
- Data outside the /data directory must never be accessed or exfiltrated. If any directory mentioned is outside data/, return an error.
- All errors are of the format { "err": "<string>" }.
- Data must never be deleted.
- Only choose one of the allowed tool names.

Allowed tool names and their schemas:

1. A1: Run a data generation script.
    Schema: { "tool-name": "A1" }

2. A2: Format the file <Markdown file> using prettier@3.4.2.
    Schema: { "tool-name": "A2", "markdown_file": "<string>" }

3. A3: Count the number of <Day of the week, say Thursday, Wednesday> in <Input file, has to be in /data/somefilename.txt> and write the number to <Output file, /data/somefilename.txt>.
    Schema: { "tool-name": "A3", "day": "<string>", "input": "<string>", "output": "<string>" }

4. A4: Sort the array of contacts in <input file name json> by last_name then first_name and write to <output file name json>.
    Schema: { "tool-name": "A4", "input": "<string>", "output": "<string>" }

5. A5: Write the first line of the 10 most recent .log files in <input directory> to <output file>.
    Schema: { "tool-name": "A5", "input_dir": "<string>", "output": "<string>" }

6. A6: Create an index mapping filenames to titles by extracting the first H1 from each Markdown file in <input directory> and write it to <output file>.
    Schema: { "tool-name": "A6", "input_dir": "<string>", "output": "<string>" }

7. A7: Extract the sender's email address from <input file> and write it to <output file>.
    Schema: { "tool-name": "A7", "input": "<string>", "output": "<string>" }

8. A8: Extract a credit card number from <input image file> and write it (without spaces) to <output file>.
    Schema: { "tool-name": "A8", "input": "<string>", "output": "<string>" }

9. A9: Using embeddings, find the most similar pair of comments from <input file> and write them (one per line) to <output file>.
    Schema: { "tool-name": "A9", "input": "<string>", "output": "<string>" }

10. A10: Compute the total sales for "Gold" ticket type from <input database> and write the number to <output file>.
     Schema: { "tool-name": "A10", "input": "<string>", "output": "<string>" }

11. B3: Fetch data from an API and save it.
     Schema: { "tool-name": "B3", "api_url": "<string>", "output": "<string>" }

12. B4: Clone a git repository and make a commit.
     Schema: { "tool-name": "B4", "git_repo": "<string>" }

13. B5: Run a SQL query on a SQLite or DuckDB database.
     Schema: { "tool-name": "B5", "sql_query": "<string>", "database": "<string>", "output": "<string>" }

14. B6: Extract (scrape) data from a website.
     Schema: { "tool-name": "B6", "website_url": "<string>", "output": "<string>" }

15. B7: Compress or resize an image.
     Schema: { "tool-name": "B7", "input": "<string>", "output": "<string>" }

16. B8: Transcribe audio from an audio file.
     Schema: { "tool-name": "B8", "input": "<string>", "output": "<string>" }

17. B9: Convert Markdown to HTML.
     Schema: { "tool-name": "B9", "input": "<string>", "output": "<string>" }

18. B10: Write an API endpoint that filters a CSV file and returns JSON data.
     Schema: { "tool-name": "B10", "input": "<string>" }

When given an input query, decide which task (and schema) it maps to and output only the corresponding JSON.
"""

def run_task(input_query: str) -> dict:
    """
    Sends the input task description to the OpenAI API with the above prompt.
    Expects the model to output a JSON string with a "tool-name" field (and possibly extra parameters).
    
    Parameters:
        input_query (str): The task description provided by the developer.
    
    Returns:
        dict: The parsed JSON output from the model.
    """
    try:
        api_url = "https://aiproxy.sanand.workers.dev/"
        token = os.environ.get("AIPROXY_TOKEN")
        if not token:
            raise Exception("AIPROXY_TOKEN environment variable not set")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            temperature=0,
            messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": input_query}
            ],
            api_base=api_url,
            api_key=token
        )
        
        # Get the model's reply (as a string)
        reply = response['choices'][0]['message']['content']
        
        # Try to parse the reply as JSON
        result = json.loads(reply)
        return result
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse response: {e}")

# if __name__ == "__main__":
#     sample_query = "The file /data/dates.txt contains a list of dates, one per line. Count the number of Wednesdays and write the number to /data/dates-wednesdays.txt."
#     result = run_task(sample_query)
#     print("LLM Output:", result)
