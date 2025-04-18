from flask import Flask, render_template, request
import pandas as pd
import requests
import pygal
from pygal.style import LightColorizedStyle
from datetime import datetime

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = 'IMTO1H6UEKUDNM2G'

def get_stock_symbols():
    df = pd.read_csv('stocks.csv')
    return sorted(df['Symbol'].dropna().unique())

def get_stock_data(symbol, function):
    function_map = {
        "1": "TIME_SERIES_DAILY",
        "2": "TIME_SERIES_WEEKLY",
        "3": "TIME_SERIES_MONTHLY"
    }
    api_function = function_map.get(function, "TIME_SERIES_DAILY")

    url = f"https://www.alphavantage.co/query?function={api_function}&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    key_map = {
        "TIME_SERIES_DAILY": "Time Series (Daily)",
        "TIME_SERIES_WEEKLY": "Weekly Time Series",
        "TIME_SERIES_MONTHLY": "Monthly Time Series"
    }

    try:
        time_series = data[key_map[api_function]]
        df = pd.DataFrame.from_dict(time_series, orient="index").astype(float)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except KeyError:
        print(f"Error fetching data for {symbol}: {data.get('Error Message', 'Unknown error')}")
        return None

def plot_stock_pygal(df, chart_type, start_date=None, end_date=None):
    df_filtered = df
    if start_date:
        df_filtered = df_filtered[df_filtered.index >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered.index <= pd.to_datetime(end_date)]

    if df_filtered.empty:
        df_filtered = df[-30:]

    chart_class = pygal.Line if chart_type == "line" else pygal.Bar
    chart = chart_class(style=LightColorizedStyle, x_label_rotation=20, show_minor_x_labels=False)
    chart.title = 'Closing Price'

    chart.x_labels = [d.strftime('%Y-%m-%d') for d in df_filtered.index]
    chart.add('Close', df_filtered['4. close'])
    return chart.render_data_uri()

@app.route("/", methods=["GET", "POST"])
def index():
    symbols = get_stock_symbols()
    selected_symbol = None
    chart = None

    if request.method == "POST":
        selected_symbol = request.form.get("symbol")
        function = request.form.get("function")
        chart_type = request.form.get("chart_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        df = get_stock_data(selected_symbol, function)
        if df is not None:
            chart = plot_stock_pygal(df, chart_type, start_date, end_date)

    return render_template("index.html", symbols=symbols, selected_symbol=selected_symbol, chart=chart)

if __name__ == "__main__":
    app.run(debug=True)
