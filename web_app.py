import matplotlib
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify
import io, base64, datetime, time
from datetime import date
from forex_python.converter import CurrencyRates
matplotlib.use('Agg')
currencies = [
    ("USD", "EUR"),
    ("EUR", "USD"),
    ("USD", "INR"),
    ("USD", "CAD"),
    ("CAD", "USD"),
    ("USD", "GBP"),
]
c_cache = {"data": None, "time": 0}
CACHE_TTL = 600  # 10 minutes
def get_rate():
    now=time.time()
    if c_cache["data"] and (now - c_cache["time"] < CACHE_TTL):
        print("Using cached currency rates")
        return c_cache["data"]
    else:
        print("Getting current rates...")
    c = CurrencyRates()
    rates={}
    for first, second in currencies:
        try:
            rate=c.get_rate(first,second)
            rates[f"{first}->{second}"] = rate
        except:
            rates[f"{first}->{second}"] = "ERROR"
    c_cache["data"] = rates
    c_cache["time"] = now
    return rates
def plot_2html(df_html,user_symbol,qtype):
    """type is 'stock' or 'economic'. """
    fig, ax = plt.subplots()
    if qtype == 'stock':
        ax.plot(df_html['Close'], label=user_symbol, color='red')
    else:
        ax.plot(df_html, label=user_symbol, color='red')
    ax.legend()
    ax.grid(True)
    ax.set_title(f"{user_symbol} Stock Price")
    fig.autofmt_xdate()

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_base64
app = Flask(__name__)
@app.route('/',methods=['GET','POST'])
def stock_graph():
    closing_price=None
    stock_graph_img=None
    stock_data_dic=None
    if request.method == 'POST':
        user_input=request.form.get('ticker_input')
        end=datetime.datetime.today()
        try:
            start = end.replace(year=end.year - 1)  # sets timeframe to 1 year before present
        except:
            start = end.replace(year=end.year - 1, day=28) 
        if user_input:
            df_stock = yf.download(user_input, start=start, end=end) #gets stock data
            stock_data_dic={
                '52wh':round(df_stock['Close'].max().iloc[0],2),
                '52wl':round(df_stock['Close'].min().iloc[0],2),
                'vol':df_stock['Volume'].iloc[0].mean()
            }
            print("EMPTY DF?", df_stock.empty)
            print(df_stock.tail())
            print(df_stock) # for debugging purposes
            try:
                closing_price=round(df_stock['Close'].iloc[-1,0],2)
                print(closing_price) #for debugging as well
                user_input=user_input.upper()
                stock_graph_img = plot_2html(df_stock, user_input,"stock")
            except Exception as e:
                closing_price=None
                print(f"Sorry, it looks like there was an error: {e}")

    #this code gets gold prices
    gold = yf.Ticker("GC=F")
    #gold_price = gold.info.get('regularMarketPrice')
    gold_price=gold.history(period="1d")['Close'].iloc[-1]
    #this code gets current exchange rate sbetween popular currencies
    rates=get_rate()
    return render_template("stocks.html",price=closing_price, graph=stock_graph_img,wgold_price=gold_price,rate_dic=rates,stock_dic=stock_data_dic)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
