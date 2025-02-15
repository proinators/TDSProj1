import os
import json
import glob
import subprocess
import sqlite3
import re
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

import functions
import llm_parser

app = FastAPI(
    title="DataWorks Agent API",
    description=(
        "POST /run?task=<task description> executes a plain-English task. The agent parses the instruction, "
        "executes one or more internal steps (including taking help from an LLM), and produces the final output. "
        "On success, it returns a 200 OK; if the task instruction is invalid, it returns a 400 Bad Request; "
        "if the agent encounters an error, it returns a 500 Internal Server Error. "
        "GET /read?path=<file path> returns the content of the specified file as plain text, returning 200 OK on success "
        "or 404 Not Found if the file does not exist."
    )
)

TOOLS = {
    "A1": functions.task_A1,
    "A2": functions.task_A2,
    "A3": functions.task_A3,
    "A4": functions.task_A4,
    "A5": functions.task_A5,
    "A6": functions.task_A6,
    "A7": functions.task_A7,
    "A8": functions.task_A8,
    "A9": functions.task_A9,
    "A10": functions.task_A10,
    "B3": functions.task_B3,
    "B4": functions.task_B4,
    "B5": functions.task_B5,
    "B6": functions.task_B6,
    "B7": functions.task_B7,
    "B8": functions.task_B8,
    "B9": functions.task_B9,
    "B10": functions.task_B10,
}

@app.post("/run")
async def run_task(task: str = Query(..., description="Plain-English task description")):
    try:
        parsed = llm_parser.run_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Task parsing error: {str(e)}")
    tool_code = parsed.get("tool-name")
    params = {k: v for k, v in parsed.items() if k != "tool-name"}
    if tool_code not in TOOLS:
        raise HTTPException(status_code=400, detail="Tool not supported.")
    try:
        result = TOOLS[tool_code](params)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/read", response_class=PlainTextResponse)
async def read_file(path: str = Query(..., description="Path to file inside /data")):
    try:
        functions.ensure_data_path(path)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        with open(path, "r") as f:
            content = f.read()
        return content
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
