# 🤖 BI-AI Agent

BI-AI Agent is an AI-powered business intelligence tool that allows Sales Employees and Data Engineers to interact with structured data using natural language. Users can ask queries like _"Show me a pie chart of sales by category"_ and get tabular data or visual charts in response.

---

## 📌 Features

- 🧠 **Natural Language Querying** using OpenRouter / LM Studio models
- 📊 **Auto-generated Charts** (Pie & Bar)
- 🗂️ **Tabular Data Results** with ORM (SQLAlchemy)
- 🎨 **Interactive Streamlit Dashboard**
- 📁 **Support for multiple roles**: Sales Employee & Data Engineer

---

## 🏗️ Tech Stack

| Layer        | Tools Used                                            |
|--------------|-------------------------------------------------------|
| Backend      | Python, Flask, SQLAlchemy ORM, LM Studio / OpenRouter |
| Frontend     | Streamlit                                             |
| Database     | MySQL (or SQLite for local testing)                   |
| Charts       | Matplotlib                                            |
| LLM Model    | Mistral-7B via LM Studio or OpenRouter                |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository - To be updated when repo is public

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

- Create `.env` file in `backend/` with your OpenRouter API key:

```
OPENROUTER_API_KEY=your_key_here   #put the api key here
```

- Run the Flask API:

```bash
python app.py
```

### 3. Frontend Setup

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 📤 Example Prompts

- `Show me all orders from June`
- `Display a pie chart of sales by category`
- `Top 5 customers by quantity`
- `What is the total quantity sold in Electronics?`

> 💡 Note: You can switch between OpenRouter and LM Studio by updating `LM_API_URL` in `openai_routes.py` and adjusting `.env` as needed.

---

## 📌 Project Structure

```
bi-ai-agent/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes/
│   │   └── openai_routes.py
│   ├── utils/
│   │   └── charts.py
│   └── .env
│
├── frontend/
│   └── app.py
│
├── README.md
└── requirements.txt
```

---

## ✨ Planned / Ongoing Enhancements

- ✅ Pie and Bar Charts
- 🧪 Flat file querying (CSV, Excel, JSON)
- 🎨 Advanced Streamlit UI improvements
- 🔐 Authentication & Role Access Control
- ☁️ Azure Blob and Snowflake integration (upcoming)

---

## 📞 Contact

Created during internship @ Escorts Kubota  
For questions, reach out to: Bhumik Uppal – uppal.bhumik1910@gmail.com