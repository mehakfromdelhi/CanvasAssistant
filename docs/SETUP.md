# Setup Guide

## 1. Clone the repository

```powershell
git clone <your-repo-url>
cd <repo-folder>
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional:

```powershell
playwright install chromium
```

## 4. Create `.env`

Copy `.env.example` to `.env` and fill in your own values.

## 5. Run the agent

```powershell
python run_agent.py
```

