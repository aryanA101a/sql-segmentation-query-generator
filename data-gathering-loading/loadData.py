import pandas as pd
import duckdb


conn = duckdb.connect("../db/duckmart.db")

# USERS
# Read the CSV file
usersDf = pd.read_csv('registrationdata.csv')

# Data Cleaning
usersDf = usersDf.drop_duplicates()
usersDf['name'] = usersDf['first name'].str.title() + ' ' + \
    usersDf['last name'].str.title()
usersDf['subscription_plan'] = usersDf['subscription_plan'].str.lower()
usersDf['gender'] = usersDf['gender'].str.lower()
usersDf['gender'] = usersDf['gender'].replace(
    {'bigender': 'non-binary', 'genderqueer': 'non-binary', 'polygender': 'non-binary'})
usersDf['device_type'] = usersDf['device_type'].replace(
    {'Windows': 'desktop', 'Mac': 'desktop', 'Linux': 'desktop', 'Android': 'mobile', 'ios': 'mobile'})
usersDf['device_type'] = usersDf['device_type'].str.lower()
usersDf['location'] = usersDf['location'].fillna('unknown')
usersDf['location'] = usersDf['location'].str.lower()
usersDf['signup_date'] = pd.to_datetime(
    usersDf['signup_date'], format='%Y-%m-%dT%H:%M:%SZ')
usersDf = usersDf[['user_id', 'name', 'age', 'gender',
                   'location', 'signup_date', 'subscription_plan', 'device_type']]

# Into the DB
conn.execute("CREATE TABLE IF NOT EXISTS users(user_id UINTEGER PRIMARY KEY,name TEXT, age UTINYINT, gender TEXT, location TEXT, signup_timestamp TIMESTAMP, subscription_plan TEXT, device_type TEXT);")
conn.execute("INSERT INTO users SELECT * FROM usersDf;")

# EVENTS
eventsDf = pd.read_csv('eventsdata.csv')


eventsDf = eventsDf.drop_duplicates()
eventsDf = eventsDf.dropna()
eventsDf['event'] = eventsDf['event'].str.lower()
eventsDf['timestamp'] = pd.to_datetime(
    eventsDf['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')

conn.execute("CREATE TABLE IF NOT EXISTS events(event_id UINTEGER PRIMARY KEY,user_id UINTEGER,event TEXT,event_timestamp TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(user_id));")
conn.execute("INSERT INTO events SELECT * FROM eventsDf;")


print(conn.query("SELECT * FROM users;"))
print(conn.query("SELECT * FROM events;"))
