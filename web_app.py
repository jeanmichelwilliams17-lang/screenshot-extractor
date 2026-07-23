"""
Screenshot Session Organizer — Browser UI
Run:  pip install flask && python web_app.py
Then open http://localhost:5000 in your browser.
"""

import os
import sys
import shutil
import re
import threading
import time
import base64
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

# ── State ──────────────────────────────────────────────────────────
current_folder = None
watching = False
pending = {}
moved_files = []
watcher_thread = None
stop_event = threading.Event()


def default_screenshot_folder():
    project_dir = Path(__file__).resolve().parent
    screenshots_dir = project_dir / "Screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    if sys.platform.startswith("win"):
        guess = Path(r"C:\Users\ralme\OneDrive\Pictures\Screenshots 1")
        return str(guess) if guess.exists() else str(screenshots_dir)
    elif sys.platform == "darwin":
        return str(screenshots_dir)
    return str(screenshots_dir)


def sanitize(name):
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name or "untitled"


# ── Routes ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    tpl = Path(app.template_folder) / "index.html"
    print(f"\n=== SERVING TEMPLATE: {tpl.resolve()} ===")
    print(f"=== FILE SIZE: {tpl.stat().st_size} bytes ===")
    print(f"=== HAS SELECT: {'subjectSelect' in tpl.read_text()} ===\n")
    return render_template(
        "index.html", default_source=default_screenshot_folder(), datetime=datetime
    )


@app.route("/api/create-folder", methods=["POST"])
def api_create_folder():
    global current_folder
    data = request.json
    year = sanitize(data.get("year", ""))
    subject = sanitize(data.get("subject", ""))
    if not subject:
        return jsonify({"error": "Subject is required"}), 400

    base = Path.home() / "Desktop"
    if not base.exists():
        base = Path.home()
    folder = base / f"{year}_{subject}"
    folder.mkdir(parents=True, exist_ok=True)
    current_folder = folder
    return jsonify({"path": str(folder), "name": folder.name})


@app.route("/api/start-watch", methods=["POST"])
def api_start_watch():
    global watching, watcher_thread, pending, moved_files
    if watching:
        return jsonify({"error": "Already watching"}), 400
    if not current_folder:
        return jsonify({"error": "Create a session folder first"}), 400

    data = request.json
    source = Path(data.get("source", ""))
    if not source.exists():
        return jsonify({"error": f"Source folder not found: {source}"}), 400

    watching = True
    pending = {}
    moved_files = []
    stop_event.clear()
    watcher_thread = threading.Thread(
        target=_watch_loop, args=(source, current_folder), daemon=True
    )
    watcher_thread.start()
    return jsonify(
        {"status": "watching", "source": str(source), "dest": current_folder.name}
    )


@app.route("/api/stop-watch", methods=["POST"])
def api_stop_watch():
    global watching
    watching = False
    stop_event.set()
    return jsonify({"status": "stopped"})


@app.route("/api/status")
def api_status():
    return jsonify(
        {
            "watching": watching,
            "folder": str(current_folder) if current_folder else None,
            "moved_files": moved_files[-50:],
        }
    )


@app.route("/api/list-images", methods=["POST"])
def api_list_images():
    data = request.json
    folder = data.get("folder", "")
    if not folder or not Path(folder).exists():
        return jsonify({"error": "Invalid folder"}), 400

    folder = Path(folder)
    images = sorted(
        [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS],
        key=lambda f: f.stat().st_mtime,
    )

    result = []
    for img in images:
        try:
            thumb = base64.b64encode(img.read_bytes()).decode()
            ext = img.suffix.lower().lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            result.append(
                {
                    "name": img.name,
                    "data": f"data:image/{mime};base64,{thumb}",
                }
            )
        except Exception:
            result.append({"name": img.name, "data": None})

    return jsonify({"images": result, "count": len(result)})


@app.route("/api/rename", methods=["POST"])
def api_rename():
    data = request.json
    names = [n.strip() for n in data.get("names", "").splitlines() if n.strip()]
    folder = data.get("folder", "")
    ordered_files = data.get("ordered_files", None)

    if not names:
        return jsonify({"error": "No names provided"}), 400
    if not folder or not Path(folder).exists():
        return jsonify({"error": "Invalid folder"}), 400

    folder = Path(folder)

    if ordered_files:
        images = []
        for fname in ordered_files:
            p = folder / fname
            if p.exists() and p.suffix.lower() in IMAGE_EXTS:
                images.append(p)
    else:
        images = sorted(
            [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS],
            key=lambda f: f.stat().st_mtime,
        )

    if not images:
        return jsonify({"error": "No images found in folder"}), 400

    count = min(len(images), len(names))
    width = len(str(len(names)))
    renamed = []
    skipped_names = []
    for i in range(count):
        img = images[i]
        new_name = f"{sanitize(names[i])}{img.suffix.lower()}"
        new_path = img.parent / new_name
        c = 1
        while new_path.exists():
            new_path = (
                img.parent / f"{new_name.rsplit('.', 1)[0]}_{c}{img.suffix.lower()}"
            )
            c += 1
        img.rename(new_path)
        renamed.append(new_path.name)

    if len(names) > count:
        skipped_names = names[count:]

    return jsonify(
        {
            "renamed": renamed,
            "count": count,
            "skipped_names": skipped_names,
            "total_images": len(images),
            "total_names": len(names),
        }
    )


@app.route("/api/upload", methods=["POST"])
def api_upload():
    folder = request.form.get("folder", "")
    if not folder or not Path(folder).exists():
        return jsonify({"error": "Invalid folder"}), 400

    folder = Path(folder)
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    saved = []
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in IMAGE_EXTS:
            continue
        dest = folder / f.filename
        c = 1
        while dest.exists():
            dest = folder / f"{Path(f.filename).stem}_{c}{ext}"
            c += 1
        f.save(str(dest))
        saved.append(dest.name)

    return jsonify({"saved": saved, "count": len(saved)})


@app.route("/api/delete", methods=["POST"])
def api_delete():
    data = request.json
    folder = data.get("folder", "")
    filenames = data.get("files", [])

    if not folder or not Path(folder).exists():
        return jsonify({"error": "Invalid folder"}), 400

    folder = Path(folder)
    deleted = []
    for fname in filenames:
        p = folder / fname
        if p.exists():
            try:
                p.unlink()
                deleted.append(fname)
            except Exception:
                pass
    return jsonify({"deleted": deleted, "count": len(deleted)})


# ── File Watcher ───────────────────────────────────────────────────
def _watch_loop(source: Path, dest: Path):
    global pending, moved_files, watching

    # Snapshot files already present — skip them
    try:
        existing = {f for f in source.iterdir() if f.suffix.lower() in IMAGE_EXTS}
    except Exception:
        existing = set()
    known = {f: f.stat().st_size for f in existing}

    while watching and not stop_event.is_set():
        try:
            candidates = [f for f in source.iterdir() if f.suffix.lower() in IMAGE_EXTS]
        except Exception:
            candidates = []

        still_pending = {}
        for f in candidates:
            if f in known and f not in pending:
                # Was here before we started and wasn't in pending — skip
                continue
            try:
                size = f.stat().st_size
            except Exception:
                continue
            if f in pending and pending[f] == size:
                try:
                    target = dest / f.name
                    c = 1
                    while target.exists():
                        target = dest / f"{f.stem}_{c}{f.suffix}"
                        c += 1
                    shutil.move(str(f), str(target))
                    moved_files.append(target.name)
                except Exception:
                    pass
            else:
                still_pending[f] = size
        pending = still_pending
        time.sleep(1)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
