# 📊 Xenuxa RepoLens

Xenuxa RepoLens is a professional, high-performance CLI repository structure analyzer and source code documenter built entirely in Python. 

It safely and recursively scans local directories, maps out complex project hierarchies using stylized trees, and crunches absolute data metrics (Lines of Code, file counts, and percentage distribution) per language.

---

## 📸 Preview
<img src="screenshot results Xenuxa.png" width="100%">

<img src="screensshot analytic Xenuxa.png" width="100%">

---

## ⚡ Performance Breakdown
- **Scanned Dataset:** 237 files (~40,553 Lines of Code)
- **Processing Engine:** Asynchronous-safe `os.scandir` pipeline
- **RAM Footprint:** Minimal (< 60MB)
- **Execution:** Instantaneous real-time streaming

---

## ✨ Key Features
- **Fast Traversal:** Built using `os.scandir` framework for maximum directory crawling performance.
- **Smart Filters:** Automatically bypasses bloated or temporary directories (`.git`, `__pycache__`, `node_modules`, `bin`, `obj`, etc.).
- **Line-by-Line Metrics:** Calculates actual **Lines of Code (LoC)** instead of basic file sizes, giving real development insights.
- **Gorgeous TUI:** Powered by `rich` to bring high-end tree structures, progress spinners, and colored language share bars right into your terminal.
- **Auto-Generated Blueprint:** Instantly exports a clean Markdown structure report (`xenuxa_structure.md`) into your root directory.

---

## 📦 Quick Start

### 1. Requirements
Ensure you have Python 3.11+ and the `rich` library installed:
```bash
pip install rich

```

### 2. Execution

Run Xenuxa RepoLens by providing the path to any local project directory you want to analyze:

```bash
python repolens.py /path/to/your/project

```

*(Tip: Use `python repolens.py .` to scan your current directory)*

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Developed with 💻 by [XenuxaRootDEV](https://www.google.com/search?q=https://github.com/XenuxaRootDEV)

```

### 💡 Son Adım:
Yazıyı yapıştırdıktan sonra sağ üstteki veya en alttaki yeşil **"Commit changes..."** butonuna basarak kaydet. 

Ardından, terminalden aldığın o efsane renkli tablonun ekran görüntüsünü bilgisayarında **`lens_preview.png`** olarak isimlendirip repoya yükle ("Add file" -> "Upload files").

Bunu da yaptıktan sonra iki projen de GitHub'da tamamen kusursuz bir şekilde sergilenmiş olacak olm. Kaydedebildin mi, ana sayfa nasıl durdu?

```
