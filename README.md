# AidGen

AidGen is a disaster guidance and emergency assistance web application that provides quick, actionable information for different natural disasters like earthquakes, floods, fires, and tsunamis.

## 🚀 Features

* Frontend pages for each disaster: Earthquake, Fire, Flood, and Tsunami
* Easy-to-read emergency instructions
* Clean UI with HTML/CSS
* Backend built with Flask
* Modular service structure (LLM, templates, translation, SOS, resources)
* Centralized resources stored in JSON

## 📂 Project Structure

```
aidgen/
│
├── backend/
│   ├── data/
│   │   └── resources.json
│   ├── models/
│   │   └── Modelfile
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── resource_service.py
│   │   ├── sos_service.py
│   │   ├── template_service.py
│   │   └── translate_service.py
│   ├── templates/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── earthquake.html
│   ├── flood.html
│   ├── fire.html
│   ├── tsunami.html
│   ├── styles.css
│   ├── status-styles.css
│   └── script.js
│
├── db/
├── .env
└── .gitignore
```

## 🛠 Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Flask (Python)
* **LLM & Services:** Modular Python services
* **Storage:** JSON for static data

## ▶️ How to Run

1. Create and activate virtual environment:

```
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

2. Install dependencies:

```
pip install -r backend/requirements.txt
```

3. Run the server:

```
python backend/app.py
```

4. Open the frontend HTML files in your browser.

## 📘 License

This project is open-source and free to use.

---
