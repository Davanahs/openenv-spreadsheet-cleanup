from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import pandas as pd
import io
from models import Action
from typing import Optional

from env import SpreadsheetCleanupEnv

app = FastAPI(title="Spreadsheet Cleanup Agent")

env = SpreadsheetCleanupEnv()


@app.post("/load_data")
async def load_data(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    dataset: Optional[str] = Form(None),
    auto: bool = Form(True)
):
    df = None

    try:
        if file:
            contents = await file.read()
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            elif file.filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(contents))

        elif url:
            df = pd.read_csv(url)

        elif dataset:
            df = pd.read_json(io.StringIO(dataset))

        else:
            return {"error": "No input provided"}

        env.reset(df.to_dict(orient="list"))

        # AUTO MODE DEFAULT
        if auto:
            return env.auto_clean()

        # MANUAL MODE
        return {
            "message": "Manual mode started",
            "state": env.state(),
            "available_actions": env._available_actions()
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/step")
def step(action: Optional[Action] = None):
    """
    Take one cleaning step.
    
    Example actions:
    - fill_missing
    - normalize_values
    - remove_duplicates
    """
    if action:
        return env.step(action.dict())
    return env.step()


@app.get("/state")
def state():
    return env.state()


@app.post("/reset")
def reset(data: dict):
    return env.reset(data)