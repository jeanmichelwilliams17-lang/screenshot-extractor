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
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CAPE Screenshot Organizer</title>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --text: #e4e4e7; --muted: #71717a; --accent: #6366f1;
    --accent-hover: #818cf8; --green: #22c55e; --green-hover: #4ade80;
    --red: #ef4444; --red-hover: #f87171; --yellow: #eab308;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
  .container { max-width: 740px; margin: 0 auto; padding: 24px 20px 60px; }

  h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 24px; text-align: center; }
  h1 span { color: var(--accent); }

  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  .step-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); margin-bottom: 12px; }

  .row { display: flex; gap: 10px; align-items: center; }
  .row > * { flex: 1; }

  label { display: block; font-size: 0.8rem; color: var(--muted); margin-bottom: 4px; }
  input[type="text"], input[type="number"] {
    width: 100%; padding: 10px 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-size: 0.9rem; outline: none; transition: border 0.15s;
  }
  input:focus { border-color: var(--accent); }
  input.source-input { flex: 1; }

  textarea {
    width: 100%; padding: 10px 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-size: 0.9rem; font-family: inherit;
    resize: vertical; min-height: 140px; outline: none; transition: border 0.15s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }

  select {
    width: 100%; padding: 10px 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-size: 0.9rem; outline: none;
  }
  select:focus { border-color: var(--accent); }

  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
    padding: 10px 20px; border: none; border-radius: 8px; font-size: 0.85rem;
    font-weight: 600; cursor: pointer; transition: background 0.15s, transform 0.1s;
    color: #fff; white-space: nowrap;
  }
  .btn:active { transform: scale(0.97); }
  .btn-accent { background: var(--accent); }
  .btn-accent:hover { background: var(--accent-hover); }
  .btn-green { background: var(--green); }
  .btn-green:hover { background: var(--green-hover); }
  .btn-red { background: var(--red); }
  .btn-red:hover { background: var(--red-hover); }
  .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
  .btn-outline:hover { background: var(--surface); border-color: var(--muted); }
  .btn-sm { padding: 6px 12px; font-size: 0.75rem; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .folder-status { font-size: 0.85rem; color: var(--muted); margin-top: 10px; min-height: 22px; }
  .folder-status.ok { color: var(--green); }
  .folder-status.err { color: var(--red); }

  .watch-row { display: flex; gap: 10px; align-items: center; margin-top: 12px; }
  .watch-status { font-size: 0.8rem; color: var(--muted); margin-top: 8px; }
  .watch-status.ok { color: var(--green); }

  .log-box {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    height: 120px; overflow-y: auto; padding: 8px 12px; margin-top: 10px;
    font-size: 0.8rem; font-family: 'Cascadia Code', 'Fira Code', monospace; color: var(--muted);
  }
  .log-box .entry { padding: 2px 0; }
  .log-box .entry::before { content: '\2192 '; color: var(--green); }
  .log-empty { color: var(--muted); font-style: italic; }

  /* Image Grid */
  .grid-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }
  .grid-count { font-size: 0.8rem; color: var(--muted); }

  .image-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 8px; min-height: 60px;
  }
  .image-grid.empty {
    display: flex; align-items: center; justify-content: center;
    border: 2px dashed var(--border); border-radius: 8px; min-height: 80px;
    color: var(--muted); font-size: 0.8rem; font-style: italic;
  }

  .img-card {
    position: relative; border-radius: 8px; overflow: hidden;
    border: 2px solid transparent; cursor: grab; transition: border-color 0.15s, opacity 0.15s;
    background: var(--bg); aspect-ratio: 4/3;
  }
  .img-card:hover { border-color: var(--accent); }
  .img-card.dragging { opacity: 0.4; border-color: var(--accent); }
  .img-card.drag-over { border-color: var(--green); background: rgba(34,197,94,0.08); }

  .img-card img { width: 100%; height: 100%; object-fit: cover; display: block; }

  .img-card .badge-num {
    position: absolute; top: 4px; left: 4px;
    background: rgba(0,0,0,0.7); color: #fff; font-size: 0.65rem; font-weight: 700;
    padding: 2px 6px; border-radius: 4px; pointer-events: none;
  }
  .img-card .badge-name {
    position: absolute; bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.8)); color: #fff;
    font-size: 0.6rem; padding: 12px 4px 3px; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; pointer-events: none;
  }
  .img-card .remove-btn {
    position: absolute; top: 4px; right: 4px;
    background: rgba(239,68,68,0.85); color: #fff; border: none; border-radius: 50%;
    width: 18px; height: 18px; font-size: 0.7rem; cursor: pointer; display: none;
    align-items: center; justify-content: center; line-height: 1;
  }
  .img-card:hover .remove-btn { display: flex; }

  /* Rename Result */
  .rename-result {
    margin-top: 12px; padding: 12px; background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; font-size: 0.8rem; font-family: monospace; display: none;
  }
  .rename-result.show { display: block; }
  .rename-result .line { padding: 2px 0; color: var(--green); }
  .skipped-list { margin-top: 8px; padding: 8px; background: rgba(234,179,8,0.08); border: 1px solid rgba(234,179,8,0.2); border-radius: 6px; }
  .skipped-list .title { color: var(--yellow); font-weight: 600; margin-bottom: 4px; }
  .skipped-list .name { color: var(--muted); padding: 1px 0; }

  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid var(--border);
    border-top-color: var(--accent); border-radius: 50%; animation: spin .6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
  .badge-on { background: rgba(34,197,94,0.15); color: var(--green); }
  .badge-off { background: rgba(113,113,122,0.15); color: var(--muted); }

  .hint { font-size: 0.75rem; color: var(--muted); margin-top: 6px; }

  /* Lightbox */
  .lightbox {
    position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.92);
    display: none; align-items: center; justify-content: center; flex-direction: column;
    backdrop-filter: blur(4px);
  }
  .lightbox.open { display: flex; }

  .lightbox-img {
    max-width: 85vw; max-height: 75vh; object-fit: contain; border-radius: 8px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5); user-select: none;
  }

  .lightbox-info {
    margin-top: 16px; text-align: center; max-width: 80vw;
  }
  .lightbox-counter {
    font-size: 0.8rem; color: var(--muted); margin-bottom: 6px;
  }
  .lightbox-name {
    font-size: 1.1rem; font-weight: 600; color: var(--text);
    min-height: 1.4em;
  }
  .lightbox-name.unnamed { color: var(--muted); font-style: italic; }
  .lightbox-filename {
    font-size: 0.75rem; color: var(--muted); margin-top: 4px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
  }

  .lightbox-close {
    position: absolute; top: 16px; right: 20px;
    background: rgba(255,255,255,0.1); border: none; color: #fff;
    width: 36px; height: 36px; border-radius: 50%; font-size: 1.2rem;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .lightbox-close:hover { background: rgba(255,255,255,0.2); }

  .lightbox-arrow {
    position: absolute; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,0.08); border: none; color: #fff;
    width: 48px; height: 48px; border-radius: 50%; font-size: 1.4rem;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .lightbox-arrow:hover { background: rgba(255,255,255,0.18); }
  .lightbox-arrow:disabled { opacity: 0.2; cursor: default; }
  .lightbox-prev { left: 16px; }
  .lightbox-next { right: 16px; }

  .lightbox-hint {
    position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
    font-size: 0.7rem; color: rgba(255,255,255,0.35); white-space: nowrap;
  }
</style>
</head>
<body>

<div class="container">
  <h1>CAPE <span>Screenshot Organizer</span></h1>

  <!-- Step 1 -->
  <div class="card">
    <div class="step-label">Step 1 &mdash; Create session folder</div>
    <div class="row">
      <div>
        <label>Year</label>
        <input type="number" id="year" value="{{ year }}">
      </div>
      <div style="flex:2">
        <label>Subject</label>
        <div style="display:flex;gap:6px">
          <select id="subjectSelect" onchange="onSubjectChange()">
            <option value="">-- Pick a subject --</option>
            <option value="BiologyU1">Biology U1</option>
            <option value="BiologyU2">Biology U2</option>
            <option value="ChemistryU1">Chemistry U1</option>
            <option value="ChemistryU2">Chemistry U2</option>
            <option value="PhysicsU1">Physics U1</option>
            <option value="PhysicsU2">Physics U2</option>
            <option value="AppliedMathematicsU1">Applied Mathematics U1</option>
            <option value="AppliedMathematicsU2">Applied Mathematics U2</option>
            <option value="__custom__">Custom...</option>
          </select>
          <input type="text" id="subject" placeholder="Type subject" style="display:none;flex:1">
        </div>
      </div>
    </div>
    <div style="margin-top:12px">
      <button class="btn btn-accent" onclick="createFolder()" id="createBtn">Create New Folder</button>
    </div>
    <div class="folder-status" id="folderStatus">No folder created yet.</div>
  </div>

  <!-- Step 2 -->
  <div class="card">
    <div class="step-label">Step 2 &mdash; Add screenshots</div>
    <label>Source folder (where your capture tool saves images)</label>
    <div class="row" style="margin-top:4px">
      <input type="text" class="source-input" id="sourceFolder" value="{{ default_source }}">
      <button class="btn btn-outline" onclick="pickFolder()" style="flex:0">Browse</button>
    </div>
    <div class="watch-row">
      <button class="btn btn-green" id="watchBtn" onclick="toggleWatch()">Start Auto-Move</button>
      <span id="watchBadge" class="badge badge-off">OFF</span>
    </div>
    <div class="watch-status" id="watchStatus">Not watching.</div>
    <label style="margin-top:12px">Moved files</label>
    <div class="log-box" id="logBox">
      <div class="log-empty">No files moved yet.</div>
    </div>

    <div style="border-top:1px solid var(--border); margin-top:16px; padding-top:16px">
      <label style="margin:0; margin-bottom:8px">Or manually select screenshots</label>
      <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap">
        <input type="file" id="fileInput" accept="image/*" multiple style="display:none" onchange="handleUpload(this.files)">
        <button class="btn btn-outline btn-sm" onclick="document.getElementById('fileInput').click()">Select Images</button>
        <span class="grid-count" id="uploadStatus"></span>
      </div>
    </div>
  </div>

  <!-- Step 3 -->
  <div class="card">
    <div class="step-label">Step 3 &mdash; Arrange &amp; rename</div>

    <div class="grid-header">
      <label style="margin:0">Images in session folder (drag to reorder)</label>
      <div style="display:flex;gap:6px;align-items:center">
        <span class="grid-count" id="gridCount">0 images</span>
        <button class="btn btn-outline btn-sm" onclick="loadImages()">Refresh</button>
        <button class="btn btn-outline btn-sm" onclick="deleteAllImages()" style="color:var(--red);border-color:var(--red)">Delete All</button>
      </div>
    </div>
    <div class="image-grid empty" id="imageGrid">
      Create a folder and start capturing to see images here
    </div>

    <label style="margin-top:16px">Diagram names, one per line, in page order</label>
    <textarea id="namesBox" placeholder="Cell Structure&#10;Mitosis Phases&#10;DNA Replication&#10;..."></textarea>

    <div style="margin-top:12px; display:flex; gap:10px; align-items:center; flex-wrap:wrap">
      <button class="btn btn-accent" id="renameBtn" onclick="renameScreenshots()">Rename Screenshots</button>
      <label style="margin:0; font-size:0.8rem; color:var(--muted)">Target folder:</label>
      <input type="text" id="renameFolder" placeholder="Same as session folder" style="flex:1; min-width:200px">
    </div>
    <div class="hint">Leave folder blank to use the session folder from Step 1. Drag images above to fix the order before renaming.</div>
    <div class="rename-result" id="renameResult"></div>
  </div>
</div>

<!-- Lightbox -->
<div class="lightbox" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <button class="lightbox-arrow lightbox-prev" id="lbPrev" onclick="lightboxNav(-1)">&#8249;</button>
  <button class="lightbox-arrow lightbox-next" id="lbNext" onclick="lightboxNav(1)">&#8250;</button>
  <img class="lightbox-img" id="lbImg" src="" alt="">
  <div class="lightbox-info">
    <div class="lightbox-counter" id="lbCounter"></div>
    <div class="lightbox-name" id="lbName"></div>
    <div class="lightbox-filename" id="lbFile"></div>
  </div>
  <div class="lightbox-hint">Arrow keys to navigate &middot; Esc to close</div>
</div>

<script>
  let sessionFolder = null;
  let imageOrder = [];
  let allImages = [];

  async function api(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  // Step 1
  function onSubjectChange() {
    const sel = document.getElementById('subjectSelect');
    const custom = document.getElementById('subject');
    if (sel.value === '__custom__') {
      custom.style.display = '';
      custom.focus();
    } else {
      custom.style.display = 'none';
      custom.value = '';
    }
  }

  function getSubject() {
    const sel = document.getElementById('subjectSelect');
    if (sel.value === '__custom__') return document.getElementById('subject').value;
    return sel.value;
  }

  async function createFolder() {
    const year = document.getElementById('year').value;
    const subject = getSubject();
    const status = document.getElementById('folderStatus');
    const btn = document.getElementById('createBtn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating...';

    try {
      const data = await api('/api/create-folder', { year, subject });
      if (data.error) {
        status.className = 'folder-status err';
        status.textContent = data.error;
      } else {
        sessionFolder = data.path;
        status.className = 'folder-status ok';
        status.textContent = 'Folder ready: ' + data.path;
        document.getElementById('renameFolder').placeholder = data.path;
        loadImages();
      }
    } catch (e) {
      status.className = 'folder-status err';
      status.textContent = 'Error: ' + e.message;
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Create New Folder';
    }
  }

  function pickFolder() {
    const v = prompt('Paste the source folder path:', document.getElementById('sourceFolder').value);
    if (v !== null) document.getElementById('sourceFolder').value = v;
  }

  async function handleUpload(files) {
    if (!files.length) return;
    const folder = document.getElementById('renameFolder').value || sessionFolder;
    const status = document.getElementById('uploadStatus');
    if (!folder) {
      status.textContent = 'Create a session folder first';
      status.style.color = 'var(--red)';
      return;
    }
    status.textContent = 'Uploading ' + files.length + ' file(s)...';
    status.style.color = 'var(--muted)';
    const form = new FormData();
    form.append('folder', folder);
    for (const f of files) form.append('files', f);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.error) {
        status.textContent = data.error;
        status.style.color = 'var(--red)';
      } else {
        status.textContent = 'Added ' + data.count + ' image(s)';
        status.style.color = 'var(--green)';
        loadImages();
      }
    } catch (e) {
      status.textContent = 'Upload failed: ' + e.message;
      status.style.color = 'var(--red)';
    }
    document.getElementById('fileInput').value = '';
  }

  // Step 2 - Watch
  let isWatching = false;
  let pollInterval = null;

  async function toggleWatch() {
    const btn = document.getElementById('watchBtn');
    const status = document.getElementById('watchStatus');
    const badge = document.getElementById('watchBadge');

    if (isWatching) {
      await fetch('/api/stop-watch', { method: 'POST' });
      isWatching = false;
      btn.className = 'btn btn-green';
      btn.textContent = 'Start Auto-Move';
      badge.className = 'badge badge-off';
      badge.textContent = 'OFF';
      status.className = 'watch-status';
      status.textContent = 'Not watching.';
      clearInterval(pollInterval);
      return;
    }

    const source = document.getElementById('sourceFolder').value;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Starting...';

    try {
      const data = await api('/api/start-watch', { source });
      if (data.error) {
        status.className = 'watch-status';
        status.style.color = 'var(--red)';
        status.textContent = data.error;
      } else {
        isWatching = true;
        btn.className = 'btn btn-red';
        btn.textContent = 'Stop Auto-Move';
        btn.disabled = false;
        badge.className = 'badge badge-on';
        badge.textContent = 'ON';
        status.className = 'watch-status ok';
        status.textContent = 'Watching ' + source + ' \u2192 ' + data.dest;
        startPolling();
      }
    } catch (e) {
      status.style.color = 'var(--red)';
      status.textContent = 'Error: ' + e.message;
    } finally {
      btn.disabled = false;
      if (!isWatching) btn.innerHTML = 'Start Auto-Move';
    }
  }

  function startPolling() {
    pollInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const logBox = document.getElementById('logBox');
        if (data.moved_files.length === 0) {
          logBox.innerHTML = '<div class="log-empty">Waiting for screenshots...</div>';
        } else {
          logBox.innerHTML = data.moved_files.map(function(f){ return '<div class="entry">' + f + '</div>'; }).join('');
          logBox.scrollTop = logBox.scrollHeight;
        }
        if (!data.watching) {
          isWatching = false;
          clearInterval(pollInterval);
        }
      } catch {}
    }, 1500);
  }

  // Image Grid
  async function loadImages() {
    const folder = sessionFolder;
    if (!folder) return;
    try {
      const data = await api('/api/list-images', { folder: folder });
      if (!data || data.error) return;

      const freshImages = Array.isArray(data.images) ? data.images : [];

      // Update the full image data (thumbnails etc.) from server
      allImages = freshImages;

      const freshNames = new Set(freshImages.map(function(i){ return i.name; }));

      // 1. Remove images that no longer exist on disk
      imageOrder = imageOrder.filter(function(n){ return freshNames.has(n); });

      // 2. Append any brand-new images (not already in the current order)
      const knownNames = new Set(imageOrder);
      freshImages.forEach(function(img){
        if (!knownNames.has(img.name)) imageOrder.push(img.name);
      });

      renderGrid();
    } catch(err) { console.error('loadImages error:', err); }
  }

  function renderGrid() {
    const grid = document.getElementById('imageGrid');
    const count = document.getElementById('gridCount');

    if (allImages.length === 0) {
      grid.className = 'image-grid empty';
      grid.innerHTML = 'No images yet \u2014 start capturing!';
      count.textContent = '0 images';
      return;
    }

    grid.className = 'image-grid';
    count.textContent = allImages.length + ' image' + (allImages.length !== 1 ? 's' : '');

    var names = getNamesList();
    var html = '';
    for (var i = 0; i < imageOrder.length; i++) {
      var name = imageOrder[i];
      var img = allImages.find(function(a){ return a.name === name; });
      if (!img) continue;
      var assignedName = i < names.length ? names[i] : '';
      var thumb = img.data
        ? '<img src="' + img.data + '" alt="' + name + '" draggable="false">'
        : '<div style="padding:20px;text-align:center;color:var(--muted);font-size:0.7rem">' + name + '</div>';
      html += '<div class="img-card" draggable="true" data-idx="' + i + '" data-name="' + name + '">'
        + thumb
        + '<div class="badge-num">' + String(i + 1).padStart(2, '0') + '</div>'
        + (assignedName ? '<div class="badge-name">' + assignedName + '</div>' : '')
        + '<button class="remove-btn" onclick="deleteImage(' + i + ', event)" title="Delete from disk">&times;</button>'
        + '</div>';
    }
    grid.innerHTML = html;

    var cards = grid.querySelectorAll('.img-card');
    for (var c = 0; c < cards.length; c++) {
      cards[c].addEventListener('dragstart', onDragStart);
      cards[c].addEventListener('dragend', onDragEnd);
      cards[c].addEventListener('dragover', onDragOver);
      cards[c].addEventListener('dragleave', onDragLeave);
      cards[c].addEventListener('drop', onDrop);
      cards[c].addEventListener('click', function(e) {
        if (e.target.closest('.remove-btn')) return;
        openLightbox(parseInt(this.dataset.idx));
      });
    }
  }

  async function deleteImage(idx, e) {
    if (e) e.stopPropagation();
    var name = imageOrder[idx];
    var folder = document.getElementById('renameFolder').value || sessionFolder;
    try {
      await api('/api/delete', { folder: folder, files: [name] });
      imageOrder.splice(idx, 1);
      allImages = allImages.filter(function(i){ return i.name !== name; });
      renderGrid();
    } catch {}
  }

  async function deleteAllImages() {
    if (!imageOrder.length) return;
    var folder = document.getElementById('renameFolder').value || sessionFolder;
    try {
      await api('/api/delete', { folder: folder, files: imageOrder.slice() });
      imageOrder = [];
      allImages = [];
      renderGrid();
    } catch {}
  }

  // Drag & Drop
  var dragIdx = null;

  function onDragStart(e) {
    dragIdx = parseInt(this.dataset.idx);
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragIdx);
  }

  function onDragEnd() {
    this.classList.remove('dragging');
    var cards = document.querySelectorAll('.img-card');
    for (var c = 0; c < cards.length; c++) cards[c].classList.remove('drag-over');
    dragIdx = null;
  }

  function onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
  }

  function onDragLeave() {
    this.classList.remove('drag-over');
  }

  function onDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
    var from = parseInt(e.dataTransfer.getData('text/plain'));
    var to = parseInt(this.dataset.idx);
    if (from === to || isNaN(from) || isNaN(to)) return;
    var item = imageOrder.splice(from, 1)[0];
    imageOrder.splice(to, 0, item);
    renderGrid();
  }

  // Helpers
  function getNamesList() {
    return document.getElementById('namesBox').value
      .split('\n').map(function(s){ return s.trim(); }).filter(Boolean);
  }

  // Rename
  async function renameScreenshots() {
    var names = document.getElementById('namesBox').value;
    var folder = document.getElementById('renameFolder').value || sessionFolder;
    var result = document.getElementById('renameResult');
    var btn = document.getElementById('renameBtn');

    if (!names.trim()) {
      result.className = 'rename-result show';
      result.innerHTML = '<div style="color:var(--yellow)">Paste at least one diagram name first.</div>';
      return;
    }
    if (!folder) {
      result.className = 'rename-result show';
      result.innerHTML = '<div style="color:var(--yellow)">Create a session folder first or specify a target folder.</div>';
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Renaming...';

    try {
      var data = await api('/api/rename', { names: names, folder: folder, ordered_files: imageOrder });
      if (data.error) {
        result.className = 'rename-result show';
        result.innerHTML = '<div style="color:var(--red)">' + data.error + '</div>';
      } else {
        var html = '<div style="color:var(--green);margin-bottom:6px">Renamed ' + data.count + ' of ' + data.total_names + ' screenshots:</div>';
        data.renamed.forEach(function(n){ html += '<div class="line">' + n + '</div>'; });
        if (data.skipped_names && data.skipped_names.length > 0) {
          html += '<div class="skipped-list">';
          html += '<div class="title">Skipped ' + data.skipped_names.length + ' name(s) \u2014 no matching image:</div>';
          data.skipped_names.forEach(function(n){ html += '<div class="name">  ' + n + '</div>'; });
          html += '</div>';
        }
        result.className = 'rename-result show';
        result.innerHTML = html;
        loadImages();
      }
    } catch (e) {
      result.className = 'rename-result show';
      result.innerHTML = '<div style="color:var(--red)">Error: ' + e.message + '</div>';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Rename Screenshots';
    }
  }

  // Lightbox
  var lbIdx = 0;

  function openLightbox(idx) {
    if (!imageOrder.length) return;
    lbIdx = idx;
    renderLightbox();
    document.getElementById('lightbox').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
    document.body.style.overflow = '';
  }

  function lightboxNav(dir) {
    lbIdx += dir;
    if (lbIdx < 0) lbIdx = imageOrder.length - 1;
    if (lbIdx >= imageOrder.length) lbIdx = 0;
    renderLightbox();
  }

  function renderLightbox() {
    var name = imageOrder[lbIdx];
    var img = allImages.find(function(a){ return a.name === name; });
    var names = getNamesList();
    var assigned = lbIdx < names.length ? names[lbIdx] : '';

    document.getElementById('lbImg').src = img && img.data ? img.data : '';
    document.getElementById('lbCounter').textContent = (lbIdx + 1) + ' / ' + imageOrder.length;

    var nameEl = document.getElementById('lbName');
    if (assigned) {
      nameEl.textContent = assigned;
      nameEl.className = 'lightbox-name';
    } else {
      nameEl.textContent = 'No name assigned yet';
      nameEl.className = 'lightbox-name unnamed';
    }

    document.getElementById('lbFile').textContent = name;
    document.getElementById('lbPrev').disabled = imageOrder.length <= 1;
    document.getElementById('lbNext').disabled = imageOrder.length <= 1;
  }

  document.addEventListener('keydown', function(e) {
    var lb = document.getElementById('lightbox');
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') lightboxNav(-1);
    if (e.key === 'ArrowRight') lightboxNav(1);
  });

  document.getElementById('lightbox').addEventListener('click', function(e) {
    if (e.target === e.currentTarget) closeLightbox();
  });

  document.getElementById('namesBox').addEventListener('input', renderGrid);
  document.getElementById('subject').addEventListener('keydown', function(e) { if (e.key === 'Enter') createFolder(); });
  document.getElementById('subjectSelect').addEventListener('keydown', function(e) { if (e.key === 'Enter') createFolder(); });
</script>
</body>
</html>"""


# ── State ──────────────────────────────────────────────────────────
current_folder = None
watching = False
pending = {}
moved_files = []
watcher_thread = None
stop_event = threading.Event()


def default_screenshot_folder():
    if sys.platform.startswith("win"):
        guess = Path(r"C:\Users\ralme\OneDrive\Pictures\Screenshots 1")
        return str(guess) if guess.exists() else str(Path.home() / "Pictures")
    elif sys.platform == "darwin":
        return str(Path.home() / "Desktop")
    return str(Path.home())


def sanitize(name):
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name or "untitled"


# ── Routes ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        year=datetime.now().year,
        default_source=default_screenshot_folder(),
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
