from flask import Blueprint, request, jsonify, session
import os
import requests
import json
import traceback
import re
from datetime import datetime, date
from sqlalchemy import create_engine, MetaData, Table, func, text, desc, asc, extract, and_, inspect
from sqlalchemy.orm import sessionmaker, Session
from chart_generator_v2 import (
    generate_pie_chart,
    generate_bar_chart,
    generate_donut_chart,
    generate_column_chart,
    generate_line_chart,
    generate_area_chart,
    generate_stacked_area_chart,
    generate_percentage_area_chart
)
from dotenv import load_dotenv

load_dotenv()

openai_bp = Blueprint("openai_bp", __name__, url_prefix="/openai")

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct:free"

HEADERS = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

# Configuration
BUSINESS_KEYWORDS = [
    'revenue', 'profit', 'sales', 'orders', 'quantity', 'price', 'total', 'sum', 'count',
    'average', 'top', 'best', 'most', 'highest', 'lowest', 'show', 'get', 'find',
    'product', 'category', 'region', 'customer', 'month', 'quarter', 'year',
    'performance', 'analysis', 'report', 'chart', 'graph'
]

CHART_KEYWORDS = ['chart', 'graph', 'plot', 'visualize', 'show me']

# ==================== DYNAMIC DATABASE CONNECTION ====================

def create_dynamic_engine(database_config):
    """Create SQLAlchemy engine dynamically based on database config"""
    try:
        db_type = database_config.get('db_type', 'mysql').lower()
        host = database_config.get('host', 'localhost')
        port = database_config.get('port', 3306)
        username = database_config.get('username', 'root')
        password = database_config.get('password', '')
        database = database_config.get('database', 'test')
        
        # Build connection string based on database type
        if db_type == 'mysql':
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'postgresql':
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'sqlite':
            # For SQLite, use the database name as the file path
            connection_string = f"sqlite:///{database}"
        elif db_type == 'sql server':
            connection_string = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        print(f"🔗 Creating dynamic connection: {db_type} -> {host}:{port}/{database}")
        engine = create_engine(connection_string, echo=False)
        
        # Test the connection
        with engine.connect() as conn:
            pass
        
        return engine
        
    except Exception as e:
        print(f"❌ Failed to create dynamic engine: {e}")
        raise e

def get_dynamic_table(engine, table_name):
    """Get table object dynamically from the provided engine"""
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if table_name not in metadata.tables:
            raise ValueError(f"Table '{table_name}' not found in database")
            
        return metadata.tables[table_name]
        
    except Exception as e:
        print(f"❌ Error getting table '{table_name}': {e}")
        raise e

# ==================== DYNAMIC SCHEMA UTILITIES ====================

def get_table_schema_dynamic(engine, table_name):
    """Get dynamic schema information for any table"""
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            return None
            
        columns = inspector.get_columns(table_name)
        
        schema_info = {
            'table_name': table_name,
            'columns': []
        }
        
        for column in columns:
            col_info = {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'primary_key': column.get('primary_key', False)
            }
            schema_info['columns'].append(col_info)
            
        return schema_info
        
    except Exception as e:
        print(f"❌ Error getting schema for table {table_name}: {e}")
        return None

def generate_schema_prompt(schema_info):
    """Generate dynamic schema prompt for LLM based on table schema"""
    if not schema_info:
        return ""
        
    table_name = schema_info['table_name']
    columns = schema_info['columns']
    
    # Build column descriptions
    column_descriptions = []
    for col in columns:
        col_desc = f"{col['name']} ({col['type']})"
        if col['primary_key']:
            col_desc += " [PRIMARY KEY]"
        column_descriptions.append(col_desc)
    
    columns_str = ", ".join(column_descriptions)
    
    schema_prompt = f"""
DATABASE SCHEMA:
Table: {table_name}
Columns: {columns_str}

BUSINESS LOGIC UNDERSTANDING:
- Look for patterns like "revenue" = quantity × price columns
- "sales" typically means revenue or quantity sold
- "profit" = revenue (if no cost data available)
- "performance" usually means revenue or quantity metrics
- "top/best/most" implies ORDER BY DESC with LIMIT
- "total" implies SUM aggregation
- "average" implies AVG aggregation
"""
    
    return schema_prompt

def detect_revenue_columns(schema_info):
    """Detect potential revenue calculation columns in any table"""
    if not schema_info:
        return None, None
        
    columns = [col['name'].lower() for col in schema_info['columns']]
    
    # Common patterns for quantity and price columns
    quantity_patterns = ['quantity', 'qty', 'amount', 'count', 'units']
    price_patterns = ['price', 'cost', 'rate', 'unitprice', 'unit_price']
    
    quantity_col = None
    price_col = None
    
    # Find quantity column
    for pattern in quantity_patterns:
        for col in schema_info['columns']:
            if pattern in col['name'].lower():
                quantity_col = col['name']
                break
        if quantity_col:
            break
    
    # Find price column
    for pattern in price_patterns:
        for col in schema_info['columns']:
            if pattern in col['name'].lower():
                price_col = col['name']
                break
        if price_col:
            break
    
    return quantity_col, price_col

# ==================== UTILITY FUNCTIONS ====================

def make_llm_request(prompt):
    """Make a request to the LLM API"""
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(URL, json=payload, headers=HEADERS)
        result = response.json()
        print(f"[LLM_RAW_RESPONSE] ==> {result}")
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"].strip()
        return None
    except Exception as e:
        print("❌ LLM request failed:", str(e))
        return None

def is_conversational(query):
    """Check if query is casual conversation or data request"""
    if not query or not query.strip():
        return True

    query_lower = query.lower()
    
    # Check if this is a chart type response first
    chart_types = ['pie', 'bar', 'line', 'donut', 'column', 'area', 'stacked_area', 'percentage_area']
    if query_lower.strip() in chart_types:
        return False
    
    if any(keyword in query_lower for keyword in BUSINESS_KEYWORDS):
        return False

    # Use LLM for classification
    prompt = (
        "Classify as 'casual' or 'data'.\n"
        "Examples: 'hey' → casual, 'show revenue' → data\n"
        f"User: {query}\nLabel:"
    )
    
    result = make_llm_request(prompt)
    return result and result.lower() == "casual"

def detect_chart_request(query):
    """Detect if user is requesting a chart visualization"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in CHART_KEYWORDS)

def parse_chart_type(query):
    """Extract chart type from user query - Enhanced with new types"""
    query_lower = query.lower().strip()
    
    # Check for specific chart types in order of specificity
    if 'donut' in query_lower:
        return 'donut'
    elif 'pie' in query_lower:
        return 'pie'
    elif 'column' in query_lower:
        return 'column'
    elif 'bar' in query_lower:
        return 'bar'
    elif 'line' in query_lower:
        return 'line'
    elif 'stacked area' in query_lower or 'stacked_area' in query_lower:
        return 'stacked_area'
    elif 'percentage area' in query_lower or 'percentage_area' in query_lower:
        return 'percentage_area'
    elif 'area' in query_lower:
        return 'area'
    
    return None

def parse_time_period(time_str):
    """Parse natural language time periods into date filters"""
    time_str = time_str.lower().strip()
    current_year = datetime.now().year
    
    # Quarter patterns
    quarter_mapping = {
        'q1': [1, 3], 'first quarter': [1, 3],
        'q2': [4, 6], 'second quarter': [4, 6],
        'q3': [7, 9], 'third quarter': [7, 9],
        'q4': [10, 12], 'fourth quarter': [10, 12]
    }
    
    for quarter, (start_month, end_month) in quarter_mapping.items():
        if quarter in time_str:
            start_date = f"{current_year}-{start_month:02d}-01"
            end_date = f"{current_year}-{end_month:02d}-31"
            return {"between": [start_date, end_date]}
    
    # Month patterns
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    for month_name, month_num in months.items():
        if month_name in time_str:
            return {"month": month_num}
    
    # Year and period patterns
    year_match = re.search(r'\b(20\d{2})\b', time_str)
    if year_match:
        year = year_match.group(1)
        if 'first 6 months' in time_str or 'first half' in time_str:
            return {"between": [f"{year}-01-01", f"{year}-06-30"]}
        elif 'last 6 months' in time_str or 'second half' in time_str:
            return {"between": [f"{year}-07-01", f"{year}-12-31"]}
        else:
            return {"between": [f"{year}-01-01", f"{year}-12-31"]}
    
    # Recent periods
    if 'this year' in time_str:
        return {"between": [f"{current_year}-01-01", f"{current_year}-12-31"]}
    elif 'last year' in time_str:
        prev_year = current_year - 1
        return {"between": [f"{prev_year}-01-01", f"{prev_year}-12-31"]}
    
    return None

def get_aggregation_function(agg_type, column):
    """Get SQLAlchemy aggregation function based on type"""
    agg_functions = {
        "sum": func.sum,
        "count": func.count,
        "avg": func.avg,
        "max": func.max,
        "min": func.min
    }
    return agg_functions.get(agg_type.lower(), func.sum)(column)

def calculate_revenue_expression(table_obj, quantity_col, price_col):
    """Return SQLAlchemy expression for revenue calculation for any table"""
    if quantity_col and price_col:
        return table_obj.c[quantity_col] * table_obj.c[price_col]
    return None
# ==================== DYNAMIC QUERY PROCESSING ====================

class DynamicQueryProcessor:
    def __init__(self, db_session, table_obj, table_name, engine):
        self.db = db_session
        self.table_obj = table_obj
        self.table_name = table_name
        self.engine = engine
        self.schema_info = get_table_schema_dynamic(engine, table_name)
        self.quantity_col, self.price_col = detect_revenue_columns(self.schema_info)
        
        # Build base query using table object
        self.query = db_session.query(self.table_obj)
    
    def get_column(self, column_name):
        """Get column from table object safely"""
        if column_name in self.table_obj.c:
            return self.table_obj.c[column_name]
        return None
    
    def apply_filters(self, filters):
        """Apply all filters to the query - now table-agnostic"""
        for key, value in filters.items():
            column = self.get_column(key)
            if column is None:
                continue
                
            if key.lower().endswith('date') and isinstance(value, dict):
                self._apply_date_filter(column, value)
            elif isinstance(value, dict):
                self._apply_numerical_filter(column, value)
            elif value and not isinstance(value, dict):
                self.query = self.query.filter(column == value)
    
    def _apply_date_filter(self, column, date_filter):
        """Apply date-specific filters"""
        if "month" in date_filter:
            self.query = self.query.filter(extract('month', column) == date_filter["month"])
        elif "between" in date_filter:
            start, end = date_filter["between"]
            self.query = self.query.filter(column.between(start, end))
        elif "year" in date_filter:
            self.query = self.query.filter(extract('year', column) == date_filter["year"])
    
    def _apply_numerical_filter(self, column, value):
        """Apply numerical filters with operators"""
        operators = {
            "gt": lambda x: column > x,
            "gte": lambda x: column >= x,
            "lt": lambda x: column < x,
            "lte": lambda x: column <= x,
            "eq": lambda x: column == x,
            "between": lambda x: column.between(*x)
        }
        
        for op, val in value.items():
            if op in operators:
                self.query = self.query.filter(operators[op](val))
    
    def apply_sorting(self, sort_config, is_aggregated=False, agg_expr=None):
        """Apply sorting to query"""
        if not sort_config:
            return
        
        sort_column = sort_config.get("column")
        sort_order = sort_config.get("order", "asc").lower()
        
        if sort_column:
            if is_aggregated and agg_expr is not None:
                order_expr = desc(agg_expr) if sort_order == "desc" else asc(agg_expr)
            else:
                column = self.get_column(sort_column)
                if column is not None:
                    order_expr = desc(column) if sort_order == "desc" else asc(column)
                else:
                    return
            
            self.query = self.query.order_by(order_expr)
    
    def apply_limit(self, limit_config):
        """Apply limit to query"""
        if limit_config and isinstance(limit_config, int) and limit_config > 0:
            self.query = self.query.limit(limit_config)
    
    def execute_revenue_query(self, group_by, projections, sort_config, limit_config):
        """Execute revenue-based queries with proper aggregation"""
        if not self.quantity_col or not self.price_col:
            return [{"error": f"Revenue calculation not possible - missing quantity or price columns in table '{self.table_name}'"}]
            
        if group_by:
            return self._execute_grouped_revenue_query(group_by, projections, sort_config, limit_config)
        else:
            return self._execute_total_revenue_query()
    
    def _execute_grouped_revenue_query(self, group_by, projections, sort_config, limit_config):
        """Execute grouped revenue calculations"""
        label_col = self.get_column(group_by[0])
        if label_col is None:
            return [{"error": f"Column '{group_by[0]}' not found in table '{self.table_name}'"}]
            
        revenue_expr = func.sum(self.table_obj.c[self.quantity_col] * self.table_obj.c[self.price_col])
        
        revenue_query = self.db.query(label_col, revenue_expr).group_by(label_col)
        
        # Apply sorting and limiting
        if sort_config:
            order_expr = desc(revenue_expr) if sort_config.get("order") == "desc" else asc(revenue_expr)
            revenue_query = revenue_query.order_by(order_expr)
        
        if limit_config:
            revenue_query = revenue_query.limit(limit_config)
        
        results = revenue_query.all()
        
        return [
            {
                group_by[0]: row[0],
                "revenue": round(float(row[1]), 2) if row[1] else 0.0
            }
            for row in results
        ]
    
    def _execute_total_revenue_query(self):
        """Execute total revenue calculation"""
        total_revenue = self.db.query(func.sum(self.table_obj.c[self.quantity_col] * self.table_obj.c[self.price_col])).scalar()
        formatted_revenue = round(float(total_revenue), 2) if total_revenue else 0.0
        
        return [{
            "total_revenue": formatted_revenue,
            "message": f"Total revenue: ${formatted_revenue:,.2f}"
        }]
    
    def execute_aggregated_query(self, group_by, projections, sort_config, limit_config):
        """Execute aggregated queries (non-revenue)"""
        label_col = self.get_column(group_by[0])
        if label_col is None:
            return [{"error": f"Column '{group_by[0]}' not found in table '{self.table_name}'"}]
            
        proj_key = list(projections.keys())[0]
        proj_value = projections[proj_key]
        
        # Parse aggregation function
        agg_match = re.match(r'(\w+)\((\w+)\)', proj_value)
        if agg_match:
            agg_func = agg_match.group(1).upper()
            agg_column = agg_match.group(2)
            
            column = self.get_column(agg_column)
            if column is not None:
                proj_expr = get_aggregation_function(agg_func, column)
            else:
                proj_column = self.get_column(proj_key)
                if proj_column is not None:
                    proj_expr = func.sum(proj_column)
                else:
                    return [{"error": f"Column '{agg_column}' or '{proj_key}' not found in table '{self.table_name}'"}]
        else:
            proj_column = self.get_column(proj_key)
            if proj_column is not None:
                proj_expr = func.sum(proj_column)
            else:
                return [{"error": f"Column '{proj_key}' not found in table '{self.table_name}'"}]
        
        # Build and execute query
        agg_query = self.db.query(label_col, proj_expr).group_by(label_col)
        
        if sort_config:
            order_expr = desc(proj_expr) if sort_config.get("order") == "desc" else asc(proj_expr)
            agg_query = agg_query.order_by(order_expr)
        
        if limit_config:
            agg_query = agg_query.limit(limit_config)
        
        results = agg_query.all()
        
        # Format results
        formatted_results = []
        for row in results:
            label = row[0]
            value = row[1]
            
            # Format value based on aggregation type
            if agg_match and agg_match.group(1).upper() == "COUNT":
                formatted_value = int(value) if value is not None else 0
            elif agg_match and agg_match.group(1).upper() == "AVG":
                formatted_value = round(float(value), 2) if value is not None else 0.0
            else:
                formatted_value = value if value is not None else 0
            
            formatted_results.append({
                group_by[0]: label,
                f"{agg_func}({proj_key})": formatted_value
            })
        
        return formatted_results
    
    def get_chart_data(self, group_by, projections):
        """Get data specifically formatted for chart generation"""
        label_col = self.get_column(group_by[0])
        if label_col is None:
            return []
            
        proj_key = list(projections.keys())[0]
        proj_value = projections[proj_key]
        
        # Handle revenue calculations for charts
        if ("revenue" in proj_key.lower() or "quantity * price" in proj_value.lower()) and self.quantity_col and self.price_col:
            proj_expr = func.sum(self.table_obj.c[self.quantity_col] * self.table_obj.c[self.price_col])
        else:
            # Parse regular aggregation
            agg_match = re.match(r'(\w+)\((\w+)\)', proj_value)
            if agg_match:
                agg_func = agg_match.group(1).upper()
                agg_column = agg_match.group(2)
                column = self.get_column(agg_column)
                if column is not None:
                    proj_expr = get_aggregation_function(agg_func, column)
                else:
                    proj_column = self.get_column(proj_key)
                    if proj_column is not None:
                        proj_expr = func.sum(proj_column)
                    else:
                        return []
            else:
                proj_column = self.get_column(proj_key)
                if proj_column is not None:
                    proj_expr = func.sum(proj_column)
                else:
                    return []
        
        return self.db.query(label_col, proj_expr).group_by(label_col).all()
    
    def get_tabular_results(self):
        """Get standard tabular results"""
        results = self.query.all()
        
        # Convert results to dictionaries using column names
        formatted_results = []
        for row in results:
            row_dict = {}
            for column in self.table_obj.c:
                col_name = column.name
                row_dict[col_name] = getattr(row, col_name, None)
                
                # Format dates
                if hasattr(row, col_name) and hasattr(getattr(row, col_name), 'strftime'):
                    row_dict[col_name] = getattr(row, col_name).strftime('%Y-%m-%d')
                    
            formatted_results.append(row_dict)
            
        return formatted_results

# ==================== SESSION MANAGEMENT ====================

def get_pending_chart_context():
    """Get pending chart context from session"""
    return session.get('pending_chart_context')

def set_pending_chart_context(context):
    """Set pending chart context in session"""
    session['pending_chart_context'] = context

def clear_pending_chart_context():
    """Clear pending chart context from session"""
    session.pop('pending_chart_context', None)

# ==================== ENHANCED CHART HANDLING FUNCTIONS ====================

def handle_chart_type_response(chart_type_response, context):
    """Handle user's response to chart type selection"""
    chart_type = parse_chart_type(chart_type_response)
    
    if not chart_type:
        return jsonify({
            "message": "Please specify a valid chart type: pie, bar, or line",
            "options": ["pie", "bar", "line"],
            "awaiting_chart_type": True
        })
    
    # Clear the pending context from the session
    clear_pending_chart_context()
    
    # Immediately process the original query with the selected chart type
    return process_business_query_dynamic(
        context["database_config"],
        context["table_name"],
        context["filters"], 
        context["group_by"], 
        context["projections"], 
        chart_type,
        context["sort_config"], 
        context["limit_config"], 
        context["derived_metrics"]
    )

def generate_chart_with_type(chart_type, chart_data):
    """Generate chart based on type with proper error handling"""
    try:
        chart_generators = {
            'pie': generate_pie_chart,
            'donut': generate_donut_chart,
            'bar': generate_bar_chart,
            'column': generate_column_chart,
            'line': generate_line_chart,
            'area': generate_area_chart,
            'stacked_area': generate_stacked_area_chart,
            'percentage_area': generate_percentage_area_chart
        }
        
        generator_func = chart_generators.get(chart_type.lower())
        if generator_func:
            return generator_func(chart_data)
        else:
            # Default to bar chart if type not recognized
            return generate_bar_chart(chart_data)
            
    except Exception as e:
        print(f"❌ Chart generation error for {chart_type}: {e}")
        return None

def process_business_query_dynamic(database_config, table_name, filters, group_by, projections, chart_type, sort_config, limit_config, derived_metrics):
    """Process the business query dynamically with database config"""
    engine = None
    db_session = None
    
    try:
        # Create dynamic engine and session
        engine = create_dynamic_engine(database_config)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()
        
        # Get table object dynamically
        table_obj = get_dynamic_table(engine, table_name)
        
        # Create processor with dynamic components
        processor = DynamicQueryProcessor(db_session, table_obj, table_name, engine)
        processor.apply_filters(filters)

        # Handle revenue-based queries
        if derived_metrics or any("revenue" in str(v).lower() or "quantity * price" in str(v).lower() for v in projections.values()):
            result_list = processor.execute_revenue_query(group_by, projections, sort_config, limit_config)
            
            # Check for errors in revenue calculation
            if result_list and "error" in result_list[0]:
                return jsonify({"error": result_list[0]["error"]}), 400
            
            # Generate chart if requested
            if chart_type and group_by:
                try:
                    chart_data = processor.get_chart_data(group_by, projections)
                    chart_result = generate_chart_with_type(chart_type, chart_data)
                    
                    if chart_result:
                        return jsonify({
                            "message": f"Here's your {chart_type} chart with the data:",
                            "chart": chart_result, 
                            "data": result_list,
                            "table_name": table_name
                        })
                    else:
                        return jsonify({
                            "message": "Generated the data, but chart creation failed:",
                            "result": result_list,
                            "table_name": table_name
                        })
                        
                except Exception as chart_error:
                    print("❌ Chart generation error:", chart_error)
                    return jsonify({
                        "message": "I found the data, but couldn't generate the chart. Here's the data instead:",
                        "result": result_list,
                        "error": f"Chart error: {str(chart_error)}",
                        "table_name": table_name
                    })
            
            return jsonify({"result": result_list, "table_name": table_name})

        # Handle chart requests for non-revenue queries
        if group_by and projections and chart_type:
            try:
                chart_data = processor.get_chart_data(group_by, projections)
                chart_result = generate_chart_with_type(chart_type, chart_data)
                
                if chart_result:
                    # Also get the aggregated results for the table
                    result_list = processor.execute_aggregated_query(group_by, projections, sort_config, limit_config)
                    return jsonify({
                        "message": f"Here's your {chart_type} chart with the data:",
                        "chart": chart_result,
                        "data": result_list,
                        "table_name": table_name
                    })
                else:
                    result_list = processor.execute_aggregated_query(group_by, projections, sort_config, limit_config)
                    return jsonify({
                        "message": "Chart generation failed, but here's your data:",
                        "result": result_list,
                        "table_name": table_name
                    })
                    
            except Exception as chart_error:
                print("❌ Chart generation error:", chart_error)
                result_list = processor.execute_aggregated_query(group_by, projections, sort_config, limit_config)
                return jsonify({
                    "message": "I found the data, but couldn't generate the chart:",
                    "result": result_list,
                    "error": f"Chart error: {str(chart_error)}",
                    "table_name": table_name
                })

        # Handle aggregated results (without charts)
        if group_by and projections and not chart_type:
            result_list = processor.execute_aggregated_query(group_by, projections, sort_config, limit_config)
            return jsonify({"result": result_list, "table_name": table_name})

        # Handle single aggregation (no grouping)
        elif projections and not group_by:
            proj_key = list(projections.keys())[0]
            proj_value = projections[proj_key]
            
            # Parse aggregation function
            agg_match = re.match(r'(\w+)\((\w+)\)', proj_value)
            if agg_match:
                agg_func = agg_match.group(1).upper()
                agg_column = agg_match.group(2)
                
                column = processor.get_column(agg_column)
                if column is not None:
                    proj_expr = get_aggregation_function(agg_func, column)
                else:
                    proj_column = processor.get_column(proj_key)
                    if proj_column is not None:
                        proj_expr = func.sum(proj_column)
                    else:
                        return jsonify({"error": f"Column '{agg_column}' or '{proj_key}' not found in table '{table_name}'"}), 400
                
                single_result = db_session.query(proj_expr).scalar()
                
                # Format result
                if agg_func == "COUNT":
                    formatted_result = int(single_result) if single_result is not None else 0
                elif agg_func == "AVG":
                    formatted_result = round(float(single_result), 2) if single_result is not None else 0.0
                else:
                    formatted_result = single_result if single_result is not None else 0
                
                result_dict = {
                    f"{agg_func}({proj_key})": formatted_result,
                    "message": f"Total {agg_func.lower()} of {proj_key}: {formatted_result}"
                }
                
                return jsonify({"result": [result_dict], "table_name": table_name})

        # Apply sorting and limiting for tabular results
        if not group_by and not projections:
            processor.apply_sorting(sort_config)
            processor.apply_limit(limit_config)

        # Return tabular results
        result_list = processor.get_tabular_results()
        return jsonify({"result": result_list, "table_name": table_name})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"❌ Error processing query for table '{table_name}': {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Database connection or query failed", "details": str(e)}), 500
    finally:
        if db_session:
            db_session.close()
        if engine:
            engine.dispose()

def parse_business_query(question, schema_info):
    """Parse business query using LLM with enhanced schema prompt - now dynamic"""
    base_schema_prompt = generate_schema_prompt(schema_info)
    
    # Add table-specific business logic
    table_name = schema_info['table_name']
    columns = [col['name'] for col in schema_info['columns']]
    schema_prompt = f"""
{base_schema_prompt}

RESPONSE FORMAT:
Return ONLY valid JSON with these keys:
- filters: {{}} (conditions to apply)
- group_by: [] (columns to group by)
- projections: {{}} (what to calculate/show)
- sort: {{}} (sorting configuration)
- limit: number (for top N results)
- chart_type: "pie"/"bar"/"line" (only if explicitly requested)
- derived_metrics: {{}} (for calculated fields like revenue)

AVAILABLE COLUMNS: {', '.join(columns)}

EXAMPLES:
1. "How much revenue did we make from [product_column]?" 
   → {{"filters": {{"{columns[0] if columns else 'column'}": "value"}}, "projections": {{"revenue": "SUM(quantity_col * price_col)"}}, "derived_metrics": {{"revenue": "quantity_col * price_col"}}}}

2. "Most selling [column]"
   → {{"group_by": ["{columns[0] if columns else 'column'}"], "projections": {{"{columns[1] if len(columns) > 1 else 'value'}": "SUM({columns[1] if len(columns) > 1 else 'value'})"}}, "sort": {{"column": "SUM({columns[1] if len(columns) > 1 else 'value'})", "order": "desc"}}, "limit": 1}}

3. "Show me a pie chart for [data]"
   → {{"group_by": ["{columns[0] if columns else 'column'}"], "projections": {{"value": "SUM({columns[1] if len(columns) > 1 else 'value'})"}}, "chart_type": "pie"}}

User Question: {question}

Analyze the business intent for table '{table_name}' and return the appropriate JSON structure.
"""

    content = make_llm_request(schema_prompt)
    if not content:
        return None

    # Clean and parse JSON
    cleaned_json = re.sub(r'//.*', '', content)
    json_match = re.search(r'{.*}', cleaned_json, re.DOTALL)
 
    if not json_match:
        return None
 
    try:
        return json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        return None

# ==================== MAIN ROUTE ====================

@openai_bp.route("/query", methods=["POST"])
def handle_query_orm():
    try:
        print("Received Request:", request.json)  
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        question = data.get("query") or data.get("question")
        table_name = data.get("table_name", "orders")
        role = data.get("role", "Sales Employee")
        database_config = data.get("database_config", {})

        print("✅ Incoming request:", data)

        if not question or not question.strip():
            return jsonify({"error": "Please provide a valid question"}), 400

        if not database_config:
            return jsonify({"error": "Database configuration is required"}), 400

        # Test database connection first
        try:
            test_engine = create_dynamic_engine(database_config)
            test_table = get_dynamic_table(test_engine, table_name)
            test_engine.dispose()
        except Exception as db_error:
            return jsonify({"error": f"Database connection failed: {str(db_error)}"}), 400

        # Get table schema for dynamic processing
        temp_engine = create_dynamic_engine(database_config)
        schema_info = get_table_schema_dynamic(temp_engine, table_name)
        temp_engine.dispose()

        if not schema_info:
            return jsonify({"error": f"Could not retrieve schema for table '{table_name}' or table does not exist"}), 400
        
        print("[DEBUG_STEP_1] ==> Initial connection test passed. Schema info retrieved.")

        # Check for pending chart context FIRST
        pending_context = get_pending_chart_context()
        if pending_context:
            # If there's a pending context, this request is the chart type response
            return handle_chart_type_response(question, pending_context)

        # Handle conversational queries
        print("[DEBUG_STEP_2] ==> Checking for conversational query.")
        if is_conversational(question):
            reply = make_llm_request(question)
            if reply:
                return jsonify({"message": reply, "table_name": table_name})
            return jsonify({"error": "No response from model"}), 500

        # Detect chart requests and chart types
        is_chart_request = detect_chart_request(question)
        specified_chart_type = parse_chart_type(question)

        # Parse business query using LLM
        print("[DEBUG_STEP_3] ==> Parsing query with LLM.")
        parsed_json = parse_business_query(question, schema_info)

        print(f"[DEBUG_STEP_4] ==> LLM response received: {parsed_json}")
        if not parsed_json:
            return jsonify({"error": "Model returned invalid format."}), 500

        filters = parsed_json.get("filters", {})
        group_by = parsed_json.get("group_by", [])
        projections = parsed_json.get("projections", {})
        sort_config = parsed_json.get("sort", {})
        limit_config = parsed_json.get("limit")
        derived_metrics = parsed_json.get("derived_metrics", {})
        chart_type = (parsed_json.get("chart_type") or specified_chart_type or "").lower()

        # This was already here, it is not a debug line
        print("✅ Parsed JSON:", parsed_json)

        # Handle chart type selection workflow
        if is_chart_request and not chart_type and group_by and projections:
            context = {
                "database_config": database_config,
                "table_name": table_name,
                "filters": filters,
                "group_by": group_by,
                "projections": projections,
                "sort_config": sort_config,
                "limit_config": limit_config,
                "derived_metrics": derived_metrics
            }
            set_pending_chart_context(context)

            return jsonify({
                "message": "What type of chart would you like to see?",
                "options": ["pie", "donut", "bar", "column", "line", "area", "stacked_area", "percentage_area"],
                "awaiting_chart_type": True,
                "table_name": table_name
            })

        # Process the business query with dynamic database connection
        print("[DEBUG_STEP_5] ==> Calling final query processor.")
        return process_business_query_dynamic(
            database_config, table_name, filters, group_by, projections,
            chart_type, sort_config, limit_config, derived_metrics
        )

    except Exception as e:
        print("❌ Error occurred:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500