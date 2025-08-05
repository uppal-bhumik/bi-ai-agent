# BI-AI Agent

**An AI-powered business intelligence assistant for querying sales data, generating visual insights, and making data-driven decisions.**

---

## 1. Project Overview

The **BI-AI Agent** is a modular, plug-and-play solution built for Sales Employees and Data Engineers to interact with sales databases using natural language. The system uses AI to understand user queries, convert them into SQL using an LLM, and visualize results in charts and tables.

Key Features:
- Natural Language to SQL Conversion using OpenRouter (LLM)
- SQLAlchemy ORM for modular database integration
- Supports MySQL and easily extendable to other databases
- Streamlit-based interactive frontend
- Multiple chart types including Pie, Bar, Line, Area, Scatter, etc.
- Secure architecture with `.env` support
- Fully modular backend with clear route and model separation

---

## 2. Folder Structure

```
project-intern/
├── backend/
│   ├── app_v2.py
│   ├── routes_v2/
│   │   └── openai_routes_v2.py
│   ├── models_v2.py
│   ├── chart_generator_v2.py
│   ├── .env
│   └── requirements.txt
├── frontend/
│   └── dashboard_v2.py
```

---

## 3. Installation

### Step 1: Clone the Repository

```bash
git clone https://gitlab.com/ekl_intern/bi-ai-agent.git
cd bi-ai-agent

```

### Step 2: Install Dependencies

Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

Install required Python packages:

```bash
pip install -r backend/requirements.txt
```

---

## 4. Configuration

Create a `.env` file inside the `backend/` directory:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

## 5. Run the Application

### Step 1: Start the Backend Server

```bash
cd backend
python app_v2.py
```

The backend will start on: `http://localhost:5050`

### Step 2: Launch the Frontend Dashboard

In a new terminal:

```bash
cd frontend
streamlit run dashboard_v2.py
```

The dashboard will open at `http://localhost:8501`

---

## 6. Usage

1. Choose your role: Sales Employee or Data Engineer.
2. Fill in the database configuration:
3. Supported types: MySQL (more coming soon)
4. Host, Port, Username, Password, Database name
5. Enter your table name.
6. Ask a question in plain English, such as:
      “Show sales by category”
      “Give me a bar chart of quantity sold by region”
      “Show price greater than 500”
7. Get:
   Tabular data
   Charts: Pie, Bar, Line, Area, Scatter, Histogram, etc.

---

## 7. Supported Chart Types

- Pie Chart
- Bar Graph
- Line Chart
- Area Chart
- Scatter Plot
- Horizontal Bar
- Grouped and Stacked Variants (coming soon)
---

## 8. Technologies Used

- **Backend**: Python, Flask, SQLAlchemy, OpenRouter (LLM)
- **Frontend**: Streamlit
- **Database**: MySQL
- **Visualization**: Matplotlib
- **Others**: dotenv, requests

---

## 9. Deployment Notes

- The system is modular and can be adapted to any relational database supported by SQLAlchemy.
- No hardcoded values; the project is fully ready for real-world deployment.
- Ideal for dashboards, internal tools, or analytical systems.

---

## 10. Future Enhancements

- CSV and Excel file integration
- User Authentication and Role-based Access Control
- Advanced Analytics: Forecasting, Time-Series trends
- More LLM providers (optional)

--- 

8. Contact

For any queries, feedback, or collaboration:
LinkedIn: linkedin.com/in/bhumik-uppal-74a70724b
Email: uppal.bhumik1910@gmail.com

---
This project is built for educational and demonstration purposes during an internship.
---
