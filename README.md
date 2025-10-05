# 🌐 FastAPI Cloud-Based Application with Azure Maps

## 🧭 Overview

This is a **FastAPI application built with Python 3.13**, designed as a cloud-based solution that integrates **Azure Maps** to deliver real-time data. The application helps users plan their leisure time by:

- 🚦 Analyzing traffic and accident data
- 📍 Recommending 3 optimal leisure locations
- 🌍 Detecting global events near selected locations on a given day

The app serves as a **recommendation engine**, allowing users to choose thematic categories (e.g. culture, music, creativity) or enter custom preferences to discover nearby activities and events.

---

## ⚙️ Local Setup (Windows, Python 3.13)

### ✅ 1. Clone the repository


git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

### Instal venv
```
python -m venv venv

venv\Scripts\activate
```
### or Powershell
```
venv\Scripts\Activate.ps1
```
```
pip install -r requirements.txt
````
### Run App
```
uvicorn main:app 
```