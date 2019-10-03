#Loading libraries


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import pandas_datareader.data as web
from datetime import datetime, timedelta
from ta import *
import datetime as dt
import json

import plotly
from plotly import tools
import plotly.plotly as py
import plotly.graph_objs as go

import requests
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import bs4

from fastnumbers import isfloat
from fastnumbers import fast_float
from multiprocessing.dummy import Pool as ThreadPool

tools.set_credentials_file(username='abhishek4108', api_key='djKaDto2dyULbgEJMFGE')


style.use('ggplot')

from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)

def unix_time_millis(dtt):
#     dtt = datetime.strptime(dtt, '%Y-%m-%d')
#     print(dtt)
    return int(dtt.timestamp())

def movingaverage(interval, window_size=10):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

def ffloat(string):
    if string is None:
        return np.nan
    if type(string)==float or type(string)==np.float64:
        return string
    if type(string)==int or type(string)==np.int64:
        return string
    return fast_float(string.split(" ")[0].replace(',','').replace('%',''),
                      default=np.nan)

def ffloat_list(string_list):
    return list(map(ffloat,string_list))

def remove_multiple_spaces(string):
    if type(string)==str:
        return ' '.join(string.split())
    return string

def get_children(html_content):
    children = list()
    for item in html_content.children:
        if type(item)==bs4.element.Comment:
            continue
        if type(item)==bs4.element.Tag or len(str(item).replace("\n","").strip())>0:
            children.append(item)

    return children

def get_table_simple(table,is_table_tag=True):
    elems = table.find_all('tr') if is_table_tag else get_children(table)
    table_data = list()
    for row in elems:

        row_data = list()
        row_elems = get_children(row)
        for elem in row_elems:
            text = elem.text.strip().replace("\n","")
            text = remove_multiple_spaces(text)
            if len(text)==0:
                continue
            row_data.append(text)
        table_data.append(row_data)
    return table_data


def get_scrip_info(stock):

    if stock == 'BAJFINANCE.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/finance-leasing-hire-purchase/bajajfinance/BAF"
    elif stock == 'BAJAJFINSV.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/finance-investments/bajajfinserv/BF04"
    elif stock == 'TCS.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/computers-software/tataconsultancyservices/TCS"
    elif stock == 'YESBANK.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/banks-private-sector/yesbank/YB"
    elif stock == 'GOLDIAM.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/diamond-cutting-jewellery-precious-metals/goldiaminternational/GI10"
    elif stock == 'HCLTECH.NS':
        url = "https://www.moneycontrol.com/india/stockpricequote/computers-software/hcltechnologies/HCL02"




    original_url = url
    key_val_pairs = {}

    page_response = requests.get(url, timeout=240)
    page_content = BeautifulSoup(page_response.content, "html.parser")
    stock_name = page_content.find("h1").text
    price = ffloat(page_content.find('div',attrs={'id':'Nse_Prc_tick_div'}).text)
    name = page_content.find('h1',attrs={'class':'company_name'}).text
    n_52wk_low = ffloat(page_content.find('span',attrs={'id':'n_52low'}).text)
    n_52wk_high = ffloat(page_content.find('span',attrs={'id':'n_52high'}).text)
    yearly_high = page_content.find('span',attrs={'id':'n_52high'}).text.strip()
    yearly_low = page_content.find('span',attrs={'id':'n_52low'}).text.strip()
    html_data_content = page_content.find('div', attrs={'id': 'mktdet_1'})

    petable = get_table_simple(get_children(html_data_content)[0],is_table_tag=False)
    pbtable = get_table_simple(get_children(html_data_content)[1],is_table_tag=False)
    volume = ffloat(page_content.find('span',attrs={'id':'nse_volume'}).text)

    html_data_content_1 = page_content.find('div', attrs={'id': 'findet_11'})
    balance_sheet_table = get_table_simple(get_children(html_data_content_1)[1],is_table_tag=False)

    data_table = list()
    data_table.extend(petable)
    data_table.extend(pbtable)
    data_table.extend(balance_sheet_table)

    collector = {row[0]:ffloat(row[1]) if len(row)==2 else None for row in data_table}

    html_data_content_2 = page_content.find('div', attrs={'id': 'acc_hd7'})
    share_holding_pattern = get_table_simple(html_data_content_2.find('table'))[1:]
    collector_2 = {row[0]:ffloat(row[1]) if len(row)==5 else None for row in share_holding_pattern}

#     print(collector)
    key_val_pairs["Stock Name"] = stock_name
    key_val_pairs["Stock Price"] = price
    key_val_pairs["P/E"] = collector['P/E']
    key_val_pairs["Book Value (Rs.)"] = collector['BOOK VALUE (Rs)']
#     key_val_pairs["deliverables"] = collector['DELIVERABLES (%)']
    if 'MARKET CAP (Rs Cr)' in collector:
        key_val_pairs["Market Cap (Cr)"] = collector['MARKET CAP (Rs Cr)']
    elif '**MARKET CAP (Rs Cr)' in collector:
        key_val_pairs["Market Cap (Cr)"] = collector['**MARKET CAP (Rs Cr)']
    key_val_pairs["Price / Book"] = collector['PRICE/BOOK']
    key_val_pairs["Div Yield %"] = collector['DIV YIELD.(%)']
    key_val_pairs['Volume Traded'] = volume
    key_val_pairs['52 wk low'] = n_52wk_low
    key_val_pairs['52 wk high'] = n_52wk_high
    key_val_pairs["Yearly low"] = ffloat(yearly_low)
    key_val_pairs["Yearly high"] = ffloat(yearly_high)
    key_val_pairs["Equity"] = collector['Total Share Capital']
    key_val_pairs["Debt"] = collector['Total Debt']
    key_val_pairs["Net Worth (NCAV)"] = collector['Net Worth']
    key_val_pairs["Promoter"] = collector_2['Promoter']
    return key_val_pairs


def plot_chart(stock,timerange):
    # start = dt.datetime(2018, 1, 1)
    # end = dt.datetime(2019, 4, 19)
    start = datetime.today() - timedelta(days = int(timerange)*30)
    end = datetime.today() - timedelta(days = 1)
    df = web.DataReader(stock, 'yahoo',start,end)
    df.reset_index(inplace=True)

    epoch = dt.datetime.utcfromtimestamp(0)

    df = df.rename(columns={'Volume': 'Volume_BTC'})
    df = df.drop(['Adj Close'],axis=1)
    df['Timestamp'] = df['Date'].apply(unix_time_millis)
    df = add_all_ta_features(df, "Open", "High", "Low", "Close", "Volume_BTC", fillna=True)

    INCREASING_COLOR = 'green'
    DECREASING_COLOR = 'red'

    data = [ dict(
        type = 'candlestick',
        open = df['Open'],
        high = df['High'],
        low = df['Low'],
        close = df['Close'],
        x = df['Date'],
        yaxis = 'y3',
        name = stock,
        increasing = dict( line = dict( color = INCREASING_COLOR ) ),
        decreasing = dict( line = dict( color = DECREASING_COLOR ) ),
    ) ]

    layout = go.Layout(
        # autosize=False,
        height=500,
        margin = go.layout.Margin(
            t = 10,
            b = 40,
            r = 40,
            l = 40,
            pad=4
        ),
        plot_bgcolor = 'rgb(250, 250, 250)',
        xaxis = dict(
            rangeselector = dict( visible = False ),
            rangeslider = dict( visible = False ),
            showgrid = False
        ),
        yaxis = dict(
            domain = [0, 0.08],
            showticklabels =False
        ),
        yaxis2 =dict(
            domain = [0.13, 0.25],
            showticklabels = False
        ),
        yaxis3 =dict(
            domain = [0.28, 0.9],
            showgrid = False
        ),
        showlegend = False
        # legend = dict(
        #     orientation = 'h',
        #     x = 0.3,
        #     y = 0.9,
        #     yanchor = 'bottom'
        # ),
    )

    # fig = dict( data=data, layout=layout )

    # fig['layout'] = dict()
    # fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
    # fig['layout']['xaxis'] = dict( rangeslider = dict( visible = False ))
    # fig['layout']['yaxis'] = dict( domain = [0, 0.08], showticklabels = False )
    # fig['layout']['yaxis2'] = dict( domain = [0.13, 0.25], showticklabels = False)
    # fig['layout']['yaxis3'] = dict( domain = [0.28, 0.8],showgrid=False)
    # fig['layout']['legend'] = dict( orientation = 'h', y=0.9, x=0.3, yanchor='bottom' )
    # fig['layout']['margin'] = dict( t=0, b=40, r=40, l=40 )
    # fig['layout']['height'] = 800
    # fig['layout']['showlegend'] = False




    # rangeselector=dict(
    #     visible = True,
    #     x = 0, y = 0.9,
    #     bgcolor = 'rgba(150, 200, 250, 0.4)',
    #     font = dict( size = 13 ),
    #     buttons=list([
    #         dict(count=1,
    #             label='reset',
    #             step='all'),
    #         dict(count=1,
    #             label='1yr',
    #             step='year',
    #             stepmode='backward'),
    #         dict(count=3,
    #             label='3 mo',
    #             step='month',
    #             stepmode='backward'),
    #         dict(count=1,
    #             label='1 mo',
    #             step='month',
    #             stepmode='backward'),
    #         dict(step='all')
    #     ]))

    # fig['layout']['xaxis']['rangeselector'] = rangeselector


    # mv_y = movingaverage(df.Close)
    # mv_x = list(df.Date)

    # # Clip the ends
    # mv_x = mv_x[5:-5]
    # mv_y = mv_y[5:-5]

    # fig['data'].append( dict( x=mv_x, y=mv_y, type='scatter', mode='lines',
    #                         line = dict( width = 1 ),
    #                         marker = dict( color = '#E377C2' ),
    #                         yaxis = 'y3', name='Moving Average' ) )


    # colors = []

    # for i in range(len(df.Close)):
    #     if i != 0:
    #         if df.Close[i] > df.Close[i-1]:
    #             colors.append(INCREASING_COLOR)
    #         else:
    #             colors.append(DECREASING_COLOR)
    #     else:
    #         colors.append(DECREASING_COLOR)

    data.append( dict( x=df.Date, y=df.momentum_stoch,type='scatter',yaxis='y2',
                            line = dict( width = 1 ),
                            marker=dict(color='#ccc'), legendgroup='STOCH', name='STOCH', showlegend=False) )

    data.append( dict( x=df.Date, y=df.momentum_stoch_signal,type='scatter',yaxis='y2',
                            line = dict( width = 1 ),
                            marker=dict(color='red'), legendgroup='STOCH',name='STOCH', showlegend=False) )

    data.append( dict( x=df.Date, y=df.trend_cci,type='scatter',yaxis='y',
                            line = dict( width = 1 ),
                            marker=dict(color='#aaaaaa'),name='CCI' ) )

    # fig['data'].append( dict( x=df.Date, y=df.volatility_bbh, type='scatter', yaxis='y3',
    #                         line = dict( width = 1 ),
    #                         marker=dict(color='#ccc'), hoverinfo='none',
    #                         legendgroup='Bollinger Bands', name='Bollinger Bands') )

    # fig['data'].append( dict( x=df.Date, y=df.volatility_bbl, type='scatter', yaxis='y3',
    #                         line = dict( width = 1 ),
    #                         marker=dict(color='#ccc'), hoverinfo='none',
    #                         legendgroup='Bollinger Bands', showlegend=False ) )


    fig = go.Figure(data=data, layout=layout)
    # print(fig.layout)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        stock = request.form['stock_name']
        timerange = request.form['select_timerange']
        # print(stock)
        graph = plot_chart(stock,timerange)
        stock_detail = get_scrip_info(stock)
        # print(stock_detail)
        return render_template('index.html',plot=graph,stock_sel=stock,timerange = timerange,stock_detail = stock_detail)
    else:
        return render_template('index.html')



if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
