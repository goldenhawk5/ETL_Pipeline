import requests
import psycopg2
from web3 import Web3
from datetime import datetime
from dotenv import load_dotenv
import os

# --- LOAD ENVIRONMENT VARIABLES 
load_dotenv()

QUICKNODE_URL = os.getenv("QUICKNODE_URL")
DB_URI = os.getenv("DB_URI")

# --- CONNECT TO WEB3 ---
web3 = Web3(Web3.HTTPProvider(QUICKNODE_URL))
assert web3.is_connected(), "Failed to connect to QuickNode"


# --- GET LATEST BLOCK ---
latest_block = web3.eth.get_block("latest", full_transactions=True)

# --- CONNECT TO DATABASE ---
conn = psycopg2.connect(DB_URI)
cur = conn.cursor()

# --- CREATE TABLE IF NOT EXISTS ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS arbitrum_transactions (
        hash TEXT PRIMARY KEY,
        from_address TEXT,
        to_address TEXT,
        block_number BIGINT,
        value NUMERIC,
        gas BIGINT,
        timestamp TIMESTAMP
    );
""")
conn.commit()

# --- PROCESS EACH TRANSACTION ---
for tx in latest_block.transactions:
    tx_hash = tx.hash.hex()
    from_address = tx["from"]
    to_address = tx["to"] if tx["to"] else None
    block_number = tx.blockNumber
    value = web3.fromWei(tx.value, 'ether')
    gas = tx.gas
    block = web3.eth.get_block(tx.blockNumber)
    timestamp = datetime.fromtimestamp(block.timestamp)

    cur.execute("""
        INSERT INTO arbitrum_transactions (
            hash, from_address, to_address, block_number, value, gas, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (hash) DO NOTHING;
    """, (tx_hash, from_address, to_address, block_number, value, gas, timestamp))

conn.commit()
cur.close()
conn.close()

print(f"Inserted {len(latest_block.transactions)} transactions from block {latest_block.number}")
