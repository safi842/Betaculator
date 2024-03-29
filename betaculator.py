import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
import plotly.io as pio
import plotly.graph_objs as go
from plotly import subplots
from sklearn.linear_model import LinearRegression

class EstimateBeta:
    def __init__(self,stock,market=None,start=None,end=None,years=2,interval="1wk"):
        self.stock = stock
        self.years = years
        self.weeks = (52*self.years)+1
        self.interval = interval
        self.end = date.today() if end == None else end
        self.start = str(self.end - relativedelta(weeks=self.weeks)) if start == None else start
        self.stock_ticker = yf.Ticker(stock)
        #self.name = self.stock_ticker.info["longName"]
        #na = self.stock_ticker.history(period="1d")
        #self.currency = self.stock_ticker.get_history_metadata()["currency"]
        #if self.currency == "INR":
        #    self.market = "^NSEI"
        #elif self.currency == "USD":
        #    self.market = "^GSPC"
        #else:
        self.market = market
            
    def compute_returns(self):
        df = yf.download([self.stock,self.market],start=self.start,end=self.end,interval=self.interval)
        self.df = df
        df = df["Adj Close"][[self.stock,self.market]].pct_change()[1:] * 100
        df.rename(columns = {self.stock:self.stock+" returns %",self.market:self.market+" returns %"}, inplace = True)
        df = df.dropna()
        return df
    
    def calculate_beta(self, plot=True):
        df = self.compute_returns()
        X = df[self.market+" returns %"].values.reshape(-1,1)
        y = df[self.stock+" returns %"].values
        reg = LinearRegression().fit(X, y)
        self.raw_beta = reg.coef_[0]
        self.intercept = reg.intercept_
        self.r2_score = reg.score(X,y)
        self.adj_beta = (2/3)*self.raw_beta + (1/3) #Bloomberg estimate
        if plot:
            exp_return = self.raw_beta*X.reshape(1,-1)[0] + self.intercept
            trace0 = go.Scatter(
                x = X.reshape(1,-1)[0], 
                y = y,
                mode = "markers",
                name = "Real Returns")

            trace1 = go.Scatter(
                x = X.reshape(1,-1)[0],
                y = exp_return,
                mode = "lines",
                name = f"R_{self.stock} : {self.intercept:.3f} + {self.raw_beta:.3f}R_{self.market[1:]}")

            data = [trace0,trace1]
            fig = go.Figure(data)
            fig.update_layout(title = self.stock+" : Beta estimation", 
                  xaxis_title = self.market+" returns %", yaxis_title = self.stock+" returns %", 
                  template = "plotly_dark")
            fig.update_layout(legend=dict(yanchor="top", y=1.15, xanchor="left", x=0.35))
            fig.show()
            
        return self.adj_beta

st.title('Betaculator')

with st.expander('How to Use'):
    st.write("This app lets you calculate the **Beta** of any company you're interested in. All you have to do is enter the company ticker and the application will either automatically search for the relevant Market Index or ask you to enter the corresponding ticker. You can then select a time interval and period for analysis, yielding both adjusted and raw beta values")

st.header('General company information')
stock_ticker_input = st.text_input('Please enter the company ticker here:').upper()
market_ticker = st.text_input('Please enter the market index ticker here. Eg:: S&P 500 : "^GSPC" ; NIFTY 50 : "^NSEI"').upper()
#status_radio = st.radio('Please click Search when you are ready.', ('Entry', 'Search'))

if stock_ticker_input != None and market_ticker != None:
    st.header('Beta Estimation')
    status_radio = st.radio('Mode of entering the time period', ('Number of years', 'Start and End Dates of a period'))
    if status_radio == "Start and End Dates of a period":
        years = 0
        start_date = st.date_input("Start Date", date.today()-relativedelta(weeks = 105),date.today()-relativedelta(years=35))
        end_date = st.date_input("End Date", date.today(),date.today()-relativedelta(years=35))
        
    else:
        start_date = None
        end_date = None
        years = st.number_input("No. of years to be considered for analysis",2,10,2,1)
    interval = st.selectbox("Choose the interval", ["Weekly","Daily","Monthly"])
    interval_dict = {"Daily":"1d","Weekly":"1wk","Monthly":"1mo"}
    interval = interval_dict[interval]
    
    try:
        e = EstimateBeta(stock_ticker_input, market_ticker, start_date, end_date, years, interval)
        e.calculate_beta()
    except ValueError:
        st.error("Start Date cannot be after the End Date")
    
    
st.markdown("<div style='text-align: center;'>Data Source : Yahoo Finance®</div>",unsafe_allow_html=True)
st.markdown('<div style="text-align: center;">Copyright (c)     2023 Mohammad Safiuddin</div>', unsafe_allow_html=True)
