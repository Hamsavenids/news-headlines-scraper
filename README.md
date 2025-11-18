# News Headlines Scraper

This project fetches the **4 most recent news headlines** from two online RSS news sources:

- **TechCrunch**
- **Economic Times – Top Stories**

The script saves the headlines into **CSV** and **Excel (.xlsx)** files and prints the **top 2 headlines** in a formatted summary inside the terminal.

---

## 📁 Files in This Repository

| File | Description |
|------|-------------|
| `news_scraper.py` | Main Python script |
| `news_headlines.csv` | Output CSV file with scraped headlines |
| `news_headlines.xlsx` | Output Excel file with scraped headlines |
| `Run_Screenshot1.png` | Terminal screenshot showing script running |
| `Run_Screenshot2.png` | Additional output screenshot |
| `README.md` | Project documentation |

---

## ▶️ How to Run the Script

Run these commands in your terminal:

```bash
pip install feedparser pandas openpyxl requests python-dateutil
python news_scraper.py
```
This will:

- Install the required Python libraries  
- Run the script  
- Fetch headlines from both RSS sources  
- Print the top 2 headlines  
- Save results into:  
  - `news_headlines.csv`  
  - `news_headlines.xlsx`


📊 Output Columns

The generated CSV/Excel files contain:

- source  
- title  
- link  
- published  
- published_dt_iso  
- scraped_at  

👩‍💻 Author

Hamsaveni D S
