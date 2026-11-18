"""Execute a notebook's code cells in one Python namespace and store their outputs.

Used where Jupyter/nbclient is unavailable. Usage:
    python run_notebook_inprocess.py NOTEBOOK.ipynb [WORKDIR]
"""
import base64
import contextlib
import io
import json
import os
import sys
import time
import traceback

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

nb_path = os.path.abspath(sys.argv[1])
workdir = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.dirname(nb_path)
os.chdir(workdir)

nb = json.load(open(nb_path, encoding="utf-8"))
current_outputs = []


def _flush_stream(buffer, name):
    text = buffer.getvalue()
    if text:
        current_outputs.append({"output_type": "stream", "name": name, "text": text.splitlines(keepends=True)})
    buffer.seek(0)
    buffer.truncate(0)


class _Capture:
    def __init__(self):
        self.out = io.StringIO()
        self.err = io.StringIO()


cap = _Capture()


def display(obj):
    _flush_stream(cap.out, "stdout")
    data = {}
    if hasattr(obj, "to_string"):
        try:
            data["text/plain"] = obj.to_string().splitlines(keepends=True)
        except TypeError:
            data["text/plain"] = repr(obj).splitlines(keepends=True)
    else:
        data["text/plain"] = repr(obj).splitlines(keepends=True)
    if hasattr(obj, "to_html"):
        data["text/html"] = obj.to_html().splitlines(keepends=True)
    current_outputs.append({"output_type": "display_data", "data": data, "metadata": {}})


def _show(*_args, **_kwargs):
    _flush_stream(cap.out, "stdout")
    for num in plt.get_fignums():
        fig = plt.figure(num)
        if not fig.get_axes():
            continue
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=80, bbox_inches="tight")
        current_outputs.append({
            "output_type": "display_data",
            "data": {"image/png": base64.b64encode(buf.getvalue()).decode("ascii"), "text/plain": [repr(fig)]},
            "metadata": {},
        })
    plt.close("all")


plt.show = _show
namespace = {"__name__": "__main__", "display": display}
count = 0
start_all = time.time()
for index, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") != "code":
        continue
    count += 1
    current_outputs = []
    source = "".join(cell["source"])
    started = time.time()
    print(f"[cell {index}] running...", file=sys.__stdout__, flush=True)
    try:
        with contextlib.redirect_stdout(cap.out), contextlib.redirect_stderr(cap.err):
            exec(compile(source, f"<cell {index}>", "exec"), namespace)
            plt.close("all")
    except Exception as exc:
        _flush_stream(cap.out, "stdout")
        current_outputs.append({
            "output_type": "error", "ename": type(exc).__name__, "evalue": str(exc),
            "traceback": traceback.format_exc().splitlines(),
        })
        cell["outputs"] = current_outputs
        cell["execution_count"] = count
        json.dump(nb, open(nb_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(traceback.format_exc(), file=sys.__stderr__)
        sys.exit(1)
    _flush_stream(cap.out, "stdout")
    cap.err.seek(0)
    cap.err.truncate(0)  # warnings are suppressed in the notebook; drop stray stderr noise
    cell["outputs"] = current_outputs
    cell["execution_count"] = count
    print(f"[cell {index}] done in {time.time() - started:.1f}s", file=sys.__stdout__, flush=True)

json.dump(nb, open(nb_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Executed {count} code cells in {time.time() - start_all:.0f}s -> {nb_path}", file=sys.__stdout__)
