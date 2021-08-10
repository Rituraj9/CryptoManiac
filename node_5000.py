# -*- coding: utf-8 -*-
"""
Created on Fri Jun 25 00:29:31 2021

@author: avikr
"""

#creating the blockchain

import datetime
import hashlib
from random import randint
import json
from flask import Flask,jsonify,request, render_template
import requests
from uuid import uuid4
from urllib.parse import urlparse
import os

#building cryptocurrency using blockchain 

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transaction = []
        self.create_block(proof=1,prev_hash='0')
        self.nodes = set()
        
    def create_block(self,proof,prev_hash):
        block={
                'index': len(self.chain)+1,
               'timestamp': str(datetime.datetime.now()),
               'proof': proof,
               'previous_hash': prev_hash,
               'transactions':self.transaction
              }
        self.transaction = []
        self.chain.append(block)
        #print(block)
        return block
    
    def get_prev_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,prev_proof):
        new_proof=1
        check=False
        while check is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            #print(hash_operation)
            if hash_operation[:4]=='0000':
                check=True
            else:
                new_proof+=1
        return new_proof
    
    def hash(self,block):
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block = chain[0]
        i=1
        while i<len(chain):
            block = chain[i]
            if block['previous_hash']!=self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]!='0000':
                return False
            previous_block = block
            i+=1
        return True
    
    def add_transaction(self,sender,receiver,amount):
        self.transaction.append({
                'sender':sender,
                'receiver': receiver,
                'amount': amount
                })
        previous_block = self.get_prev_block()
        return previous_block['index']+1
    
    def add_node(self,address):
        parsed = urlparse(address)
        self.nodes.add(parsed.netloc)
        
    def replace_chain(self):
        network = self.nodes
        long_chain = None
        max_len = len(self.chain)
        for node in network:
           res = requests.get(f'http://{node}/get_chain')
           if res.status_code == 200:
               length = res.json()['length']
               chain = res.json()['chain']
               if length>max_len and self.is_chain_valid(chain):
                   max_len = length
                   long_chain = chain
        if long_chain:
            self.chain = long_chain
            return True
        return False
    

#Mining Blockchain
app=Flask(__name__)

node_address = str(uuid4()).replace('=','')

blockchain = Blockchain()

@app.route("/", methods=["GET"])
def mainpage():
    return render_template("index.html")

@app.route("/transactions", methods=['GET','POST'])
def transactions():
    return render_template("transactions.html")

@app.route("/mine_block",methods=['GET'])
def mine_block():
    previous_block = blockchain.get_prev_block()
    
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    
    previous_hash = blockchain.hash(previous_block)
    
    blockchain.add_transaction(sender = node_address,receiver='Vaibhav',amount=randint(10,100))
    
    block = blockchain.create_block(proof,previous_hash)
    
    response = {'message':'Congratulations! You Just Created a Block!',
                'index':block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash'],
                'transaction':block['transactions']
                }
    #return jsonify(response),200
    return render_template("mine_block.html", mining = response)

@app.route('/get_chain',methods=['GET'])
def get_chain():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)
                }
    #return jsonify(response),200
    return render_template("get_chain.html", responsek = response)

@app.route('/wallet',methods=['GET'])
def wallet():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)
                }
    #return jsonify(response),200
    return render_template("wallet.html", responsek = response)

@app.route('/is_valid',methods=['GET'])
def valid():
    chain=blockchain.chain
    print(chain)
    x=blockchain.is_chain_valid(chain)
    print(x)
    if x==True:
        response = {'message':'Valid Blockchain Congo!!'
                }
    else:
        response = {'message':'InValid Blockchain'
                }
    return jsonify(response),200



@app.route('/add_transaction',methods = ["GET", "POST"])
def add_transaction():
    # js = request.get_json()
    # SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    # json_url = os.path.join(SITE_ROOT, "transactions.json")
    # jsond = json.load(open(json_url))
    # transaction_key = ['sender','receiver','amount']
    # if not all (key in jsond for key in transaction_key):
    #     return 'Some Keys are Missing in transaction',400
    # index = blockchain.add_transaction(jsond['sender'],jsond['receiver'],jsond['amount'])
    if request.method == "POST":
        index = blockchain.add_transaction(request.form.get("sender"), request.form.get("receiver"), request.form.get("amount"))
        response = {'message': f'This Transaction will be added to the block {index}'}
        #return jsonify(response),201
        return render_template("transactions.html", transaction_response = response)
    return render_template("transactions.html")    

@app.route('/connect_node',methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All Nodes are Connected.The ChimsCoin now contains the nodes',
                'total_nodes':list(blockchain.nodes)}
    return jsonify(response),201
    #render_template("connect_node.html", connect = response)

@app.route('/replace_chain',methods=['GET'])
def replace_chain():
    x=blockchain.replace_chain()
    if x:
        response = {'message':'Node is replaced with longest One',
                    'new_chain': blockchain.chain
                }
    else:
        response = {'message':'All good Chain is Already longest',
                    'actual_chain':blockchain.chain
                }
    return jsonify(response),200
#Decentralization

if __name__ == '__main__':
    app.run(debug=True)