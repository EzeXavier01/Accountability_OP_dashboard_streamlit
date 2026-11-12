# Accountability & Operational Excellence: Live Dashboard

A companion app for a 20-minute talk on *Building a Culture of Accountability and Operational Excellence*. Built with Python (Streamlit, Plotly, pandas) and hosted free on Streamlit Community Cloud.

| Tab | Used on slide | What it does |
|---|---|---|
| 1 · Live poll | 1 | The audience scans a QR code and votes; the chart refreshes every 3 seconds. One vote per visitor session. |
| 2 · Why small lapses add up | 2 and 7 | Chance a whole job is done right = (chance each step is right) ^ (number of steps). 20 steps at 99% = 82%; at 99.9% = 98%; at 95% = 36%. |
| 3 · KPI scorecard | 5 | One owner, due date and status per task; overdue items highlighted; leading vs lagging measures. Simulated data. |
| 4 · Feedback | after the talk | Rating, chosen habit and comment, with an automatic summary (average score, habit chart, most-mentioned words). |

**Safeguards:** all operational data is simulated; votes and feedback are anonymous and kept in memory only; every chart is also kept as a picture in the slides in case the internet fails. Set `ADMIN_CODE` in the app's Secrets to enable the "clear poll and feedback" button.

**Run locally**

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Note:** free Streamlit apps sleep after a period of no visits. Open the link 5 minutes before the talk to wake it up.
