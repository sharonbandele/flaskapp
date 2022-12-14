#importing relevant libraries/modules
from binance.client import Client
from flask import Flask, render_template
from pymongo import MongoClient
from urllib.parse import quote_plus
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from flask_apscheduler import APScheduler
import json
import secret1
import pandas as pd
import datetime


#initializing flask app
app = Flask(__name__)

#initializing scheduler
scheduler = APScheduler()

#defining a function to run the scheduler
def job_function():
  print("scheduler is running!")
scheduler.add_job(id='job_function', func=job_function, trigger='interval', seconds=20)
scheduler.start()


@app.route("/")
def dashboard_view():
  #initializing Binance client
  client = Client(secret1.api_key, secret1.api_security)

  #making api call to get the data
  info_btcusdt = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")
  info_ethusdt = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")
  info_allprices = client.get_all_tickers()
  print(info_allprices)

  #converting BTCUSDT data into a pandas dataframe
  df_btcusdt = pd.DataFrame(info_btcusdt, columns=['openTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])

  #converting ETHUSDT data into a pandas dataframe
  df_ethusdt = pd.DataFrame(info_ethusdt, columns=['openTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])

  #converting allprices into a pandas dataframe
  df_allprices = pd.DataFrame(info_allprices, columns=['symbol', 'price'])
  

  #converting dataframes into a json string type
  json_str_btcusdt = df_btcusdt.to_json()
  json_str_ethusdt = df_ethusdt.to_json()
  json_str_allprices = df_allprices.to_json()

  #converting json string to json object
  json_obj_btcusdt = json.loads(json_str_btcusdt)
  json_obj_ethusdt = json.loads(json_str_ethusdt)
  json_obj_allprices = json.loads(json_str_allprices)

  #establishing connection with the database
  client = MongoClient("mongodb+srv://group5members:1234@cluster0.egqrypy.mongodb.net/?retryWrites=true&w=majority")
  dbs_list = client.list_database_names()
  print(dbs_list)

  #creating a database
  db = client["crypto_db"]

  #creating a collections
  btcusdt_collection = db["btcusdt_collection"]
  ethusdt_collection = db["ethusdt_collection"]
  allprices_collection = db["allprices_collection"]

  #deleting collections to avoid duplication of data
  btcusdt_collection.delete_many({})
  ethusdt_collection.delete_many  ({})
  allprices_collection.delete_many({})

  #inserting data into the collection (uncomment to insert data once and comment out after inserting)
  btcusdt_collection.insert_one({"_id": 0, "data": json_obj_btcusdt})
  ethusdt_collection.insert_one({"_id": 1, "data": json_obj_ethusdt})
  allprices_collection.insert_one({"_id": 2, "data": json_obj_allprices})  

  #reading data from the collection
  btcusdt_data = db['btcusdt_collection'].find()
  ethusdt_data = db['ethusdt_collection'].find()
  allprices_data = db['allprices_collection'].find()

  #creating cursor and converting data from the collection into a list
  btcusdt_list = list(btcusdt_data)
  ethusdt_list = list(ethusdt_data)
  allprices_list = list(allprices_data)

  #conveting to json
  btcusdt_json = dumps(btcusdt_list, indent = 3)
  ethusdt_json = dumps(ethusdt_list, indent = 3)
  allprices_json = dumps(allprices_list, indent = 3)

  #dumping data into a json File for readability
  filename = "btcusdt.json"
  with open(filename, 'w') as fobj:
    fobj.write(btcusdt_json)

  filename = "ethusdt.json"
  with open(filename, 'w') as fobj:
    fobj.write(ethusdt_json)

  filename = "allprices.json"
  with open(filename, 'w') as fobj:
    fobj.write(allprices_json)

  #loading json for btcusdt and ethusdt from data dump
  filename = 'btcusdt.json'
  with open(filename) as fobj:
    btcusdt = json.load(fobj)

  filename = 'ethusdt.json'
  with open(filename) as fobj:
    ethusdt = json.load(fobj)

  filename = 'allprices.json'
  with open(filename) as fobj:
    allprices = json.load(fobj)

  #creating a list to store opening time and prices of BTCUSDT and ETHUSDT
  crypto_curr_price, btcusdt_open_time, btcusdt_open_prices, ethusdt_open_time, ethusdt_open_prices = [], [], [], [], []
  attributes = ['openTime', 'open']
  
  #extracting the current price, opening time and prices of BTCUSDT and ETHUSDT
  for i in range(len(allprices)):
    crypto_curr_price.append(float(allprices[i]['data']['price']['11']))
    crypto_curr_price.append(float(allprices[i]['data']['price']['12']))
  
  print(crypto_curr_price)

  for i in range(len(btcusdt)):
    btcusdt_open_time.append(btcusdt[i]['data']['openTime'])
    btcusdt_open_prices.append(btcusdt[i]['data']['open'])
  
  for i in range(len(ethusdt)):
    ethusdt_open_time.append(ethusdt[i]['data']['openTime'])
    ethusdt_open_prices.append(ethusdt[i]['data']['open'])

  #creating list to hold final data for the charts
  btcusdt_open_time_final, btcusdt_open_prices_final, ethusdt_open_time_final, ethusdt_open_prices_final = [], [], [], []

  for value in btcusdt_open_time[0].values():
    btcusdt_open_time_final.append(datetime.datetime.fromtimestamp(value/1000).strftime('%Y-%m-%d %H:%M:%S'))
  
  for value in btcusdt_open_prices[0].values():
    btcusdt_open_prices_final.append(float(value))

  for value in ethusdt_open_time[0].values():
    ethusdt_open_time_final.append(datetime.datetime.fromtimestamp(value/1000).strftime('%Y-%m-%d %H:%M:%S'))
  
  for value in ethusdt_open_prices[0].values():
    ethusdt_open_prices_final.append(float(value))
 

  #creating a dictionary to store the data for the charts
  chart_1 = {
  'x': btcusdt_open_time_final,
  'y': btcusdt_open_prices_final
  }

  chart_2 = {
    'x': ethusdt_open_time_final,
    'y': ethusdt_open_prices_final
  }

  chart_3 = {
  'btcusdt': crypto_curr_price[0],
  'ethusdt': crypto_curr_price[1],
  }

  return render_template("dashboard.html", chart_1=chart_1, chart_2=chart_2, chart_3=chart_3)  

# dashboard_view()

if __name__ == "__main__":
  app.run()