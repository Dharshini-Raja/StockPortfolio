from flask import Flask, render_template, request, redirect, url_for
import os
import requests
import random
import pandas as pd
import networkx as nx
from networkx.algorithms import tree

app = Flask(__name__)

# Get the API key from environment variable
API_KEY = 'cnvrb4pr01qmeb8u8rt0cnvrb4pr01qmeb8u8rtg'

# Function to get stock data from API
def get_stock_data(symbol):
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        stock_data = {
            'symbol': symbol,
            'current_price': data.get('c'),
            'day_change': data.get('d'),
            'day_change_percent': data.get('dp'),
            'high': data.get('h'),
            'low': data.get('l'),
            'open': data.get('o'),
            'previous_close': data.get('pc'),
            'timestamp': data.get('t'),
        }
        return stock_data
    else:
        print(f"Failed to fetch data for symbol: {symbol} Status Code: {response.status_code}")
        return None



# Algorithm: Prim's
def prims_algorithm(correlation_matrix):
    # Replace NaN values with a default weight (e.g., 0)
    correlation_matrix = correlation_matrix.fillna(0)
    
    G = nx.from_numpy_matrix(correlation_matrix.values)
    
    # Get the edges with non-zero weights
    edges = [(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] > 0]
    
    MST = tree.minimum_spanning_edges(G, algorithm='prim', data=False, weight='weight')
    MST_edges = list(MST)
    return MST_edges


# Merge Sort implementation
def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]

    left = merge_sort(left)
    right = merge_sort(right)

    return merge(left, right)

def merge(left, right):
    result = []
    left_idx, right_idx = 0, 0

    while left_idx < len(left) and right_idx < len(right):
        if float(left[left_idx]['current_price']) < float(right[right_idx]['current_price']):
            result.append(left[left_idx])
            left_idx += 1
        else:
            result.append(right[right_idx])
            right_idx += 1

    result.extend(left[left_idx:])
    result.extend(right[right_idx:])
    return result

# Algorithm: Knapsack
def knapsack(stocks, capacity):
    n = len(stocks)
    dp = [[0 for _ in range(int(capacity) + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, int(capacity) + 1):
            if stocks[i - 1]['day_change_percent'] and float(stocks[i - 1]['day_change_percent']) <= j:
                dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - int(float(stocks[i - 1]['day_change_percent']) * 100)] + float(stocks[i - 1]['day_change_percent']) * 100)
            else:
                dp[i][j] = dp[i - 1][j]
    return dp[n][int(capacity)]


# Home page with form to input stock symbols
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        symbols = request.form.get('symbols')
        return redirect(url_for('options', symbols=symbols))
    return render_template('index.html')

# Options page after entering symbols
@app.route('/options/<symbols>', methods=['GET', 'POST'])
def options(symbols):
    symbols_list = symbols.split(',') if symbols else []
    if request.method == 'POST':
        option = request.form.get('option')
        if option == 'data_organization':
            return redirect(url_for('data_organization', symbols=symbols))
        elif option == 'portfolio_construction':
            return redirect(url_for('portfolio_construction', symbols=symbols))
        elif option == 'correlation_analysis':
            return redirect(url_for('correlation_analysis', symbols=symbols))
    return render_template('options.html', symbols=symbols_list)

# Data Organization module
@app.route('/data_organization/<symbols>', methods=['GET', 'POST'])
def data_organization(symbols):
    symbols_list = symbols.split(',') if symbols else []
    stocks = []
    for symbol in symbols_list:
        stock_data = get_stock_data(symbol.strip())
        if stock_data:
            stocks.append(stock_data)
    
    sorted_stocks = merge_sort(stocks)  # Using Merge Sort
    return render_template('data_organization.html', stocks=sorted_stocks)

# Portfolio Construction module
@app.route('/portfolio_construction/<symbols>', methods=['GET', 'POST'])
def portfolio_construction(symbols):
    symbols_list = symbols.split(',') if symbols else []
    stocks = []
    for symbol in symbols_list:
        stock_data = get_stock_data(symbol.strip())
        if stock_data:
            stocks.append(stock_data)
    
    max_return = knapsack(stocks, 0.05)  # Example risk tolerance of 0.05
    selected_stocks = [stock for stock in stocks if stock['day_change_percent'] and float(stock['day_change_percent']) >= max_return]
    
    # Sort selected_stocks by day_change_percent from max to min
    sorted_stocks = sorted(selected_stocks, key=lambda x: float(x['day_change_percent']), reverse=True)
    
    return render_template('portfolio_construction.html', selected_stocks=sorted_stocks)


# Correlation Analysis module
@app.route('/correlation_analysis/<symbols>', methods=['GET', 'POST'])
def correlation_analysis(symbols):
    print(symbols, "symbols")
    symbols_list = symbols.split(',')
    stocks = []
    for symbol in symbols_list:
        stock_data = get_stock_data(symbol.strip())
        if stock_data:
            stocks.append(stock_data)
    # print(stocks,"stocks")
    # Create DataFrame from stock data
    df = pd.DataFrame(stocks)
    # Calculate correlations
    corr_matrix = df.corr()

    # Call Prim's algorithm to get Minimum Spanning Tree edges
    MST_edges = prims_algorithm(corr_matrix)
    # Create a list of edges with corresponding symbols
    edge_list = []
    for edge in MST_edges:
        if edge[0] < len(df) and edge[1] < len(df):  # Check valid indices
                symbol1 = df.loc[edge[0], 'symbol']
                symbol2 = df.loc[edge[1], 'symbol']
                correlation_value = corr_matrix.iloc[edge[0], edge[1]]
                edge_list.append((symbol1, symbol2, correlation_value))

    print(edge_list, "edge list")
    
    return render_template('correlation_analysis.html', edge_list=edge_list)

if __name__ == '__main__':
    app.run(debug=True)
