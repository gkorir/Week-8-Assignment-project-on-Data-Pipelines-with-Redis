# -*- coding: utf-8 -*-
"""Assignment project on Data Pipelines with Redis-Geoffrey Korir.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ui7dPWClrO-Scq5RfvLjovpcEfXLzCu8
"""

import pandas as pd
import psycopg2
import redis

# Redis Cloud Instance Information
redis_host = 'redis-15321.c114.us-east-1-4.ec2.cloud.redislabs.com'
redis_port = 15321
redis_password = 'kNCwxO32b7hdUiTqekLaZlH3TxkaMFY3'


# Postgres Database Information
pg_host = '22.237.226.11'
pg_database = 'telecommunications_data'
pg_user = 'postgresDB'
pg_password = 'password01'


# Redis Client Object
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)

def extract_data():
    # Extract data from CSV file using pandas
    data = pd.read_csv('customer_call_logs.csv')
    
    # Cache data in Redis for faster retrieval
    redis_client.set('customer_call_logs', data.to_json())
   

def transform_data():
    # Retrieve data from Redis cache
    #filename = "customer_call_logs.csv"
    #with open(filename.decode('utf-8'), 'r') as f:
    #data = pd.read_json(redis_client.get('customer_call_logs.csv'))
    data_bytes = redis_client.get('customer_call_logs')
    data_decode = data_bytes.decode('utf-8')
    data = pd.read_json(data_decode)


    # Transform data (clean, structure, format)
    transformed_data = data.copy()
    transformed_data['call_cost_usd'] = transformed_data['call_cost'].str.replace('$', '').astype(float)
    transformed_data['call_date'] = pd.to_datetime(transformed_data['call_date'])
    transformed_data['call_duration_min'] = pd.to_timedelta(transformed_data['call_duration']).dt.total_seconds() / 60.0
    transformed_data = transformed_data[['customer_id', 'call_cost_usd', 'call_destination', 'call_date', 'call_duration_min']]
    
    return transformed_data

def load_data(transformed_data):
    # Connect to Postgres database
    conn = psycopg2.connect(host=pg_host, database=pg_database, user=pg_user, password=pg_password)

    # Create a cursor object
    cur = conn.cursor()

    # Create a table to store the data
    cur.execute('CREATE TABLE IF NOT EXISTS customer_call_logs (\
                 customer_id INT,\
                 call_cost_usd FLOAT,\
                 call_destination VARCHAR,\
                 call_date TIMESTAMP,\
                 call_duration_min FLOAT\
                 )')

    # Insert the transformed data into the database
    for i, row in transformed_data.iterrows():
        cur.execute(f"INSERT INTO customer_call_logs (customer_id, call_cost_usd, call_destination, call_date, call_duration_min) VALUES ({row['customer_id']}, {row['call_cost_usd']}, '{row['call_destination']}', '{row['call_date']}', {row['call_duration_min']})")

    # Commit the changes
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

def data_pipeline():
    # Data pipeline function
    extract_data()
    transformed_data = transform_data()
    load_data(transformed_data)
    

if __name__ == '__main__':
    # Run the data pipeline function
    data_pipeline()