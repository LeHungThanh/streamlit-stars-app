# AppStar — Streamlit stellar evolution model

This project completes UTS 36104 Data Visualisation and Narratives, Session 2
Part D. It extends the official starter with metallicity, the low-metallicity
pair-instability outcome, and a Hertzsprung–Russell diagram.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run star_app.py
```

## Deploy

Push this directory to a public GitHub repository. In Streamlit Community
Cloud, choose that repository and branch, then set the main file path to
`star_app.py`.
