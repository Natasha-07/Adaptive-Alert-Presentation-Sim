import asyncio
from pathlib import Path

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient


path = Path("soc_alert_fatigue_simulation.ipynb")
notebook = nbformat.read(path, as_version=4)
print("Starting notebook execution", flush=True)
client = NotebookClient(notebook, timeout=3600, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}})


def checkpoint(**_):
    """Persist completed cell outputs during long executions."""
    nbformat.write(notebook, path)


client.on_cell_complete = checkpoint
client.execute()
print("Notebook execution finished; writing outputs", flush=True)
nbformat.write(notebook, path)
print(f"Executed {path}")
