import sys
sys.path.append("..") # Adds higher directory to python modules path.

import os
import json
import logging
import datetime
import requests
import paypalrestsdk
import random
import string

from lib import core_sdk
from flask import Flask, render_template, request, jsonify, session, url_for
from classes import Memory, Blockchain, Block
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] =  os.urandom(24)

app.config['mem-pool'] = {}

configure = {'access-token':os.environ.get('ACCESS_TOKEN')}

mem = Memory.StorageAPI(json)
bc = Blockchain.Blockchain(mem, Block)
bc.settings = mem.load_json(os.path.join("settings.json"))

#// 1. Set up your server to make calls to PayPal

#// 1a. Add your client ID and secret

PAYPAL_LIVE = {
    "mode": "live", # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_SECRET')}
PAYPAL_SANDBOX = {
    "mode": "sandbox", # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_SECRET')}

paypalrestsdk.configure(PAYPAL_SANDBOX)
    
@app.route("/", methods=["POST", "GET"])
def home():
    return render_template('index.html')

@app.route("/payments")
@app.route("/payments/")
def payments():
    return render_template('payments.html')

@app.route('/set-express-checkout', methods=['POST', 'GET'])
@app.route('/set-express-checkout/', methods=['POST', 'GET'])
def set_express_checkout():
    if not 'total' in request.form: return jsonify(success=False, status=401)
    if not 'id_token' in session: return jsonify(success=False, status=401)
    # Name needs to be unique so just generating a random one
    wpn = ''.join(random.choice(string.ascii_uppercase) for i in range(12))

    web_profile = paypalrestsdk.WebProfile({
        "name": wpn,
        "input_fields": {
            "allow_note": False,
            "no_shipping": 1,
            },
        })
    if web_profile.create():print("Web Profile[%s] created successfully" % (web_profile.id))
    else:print(web_profile.error)
    
    d = {'intent':'sale',
         'experience_profile_id': web_profile.id,
         'payer': {
             'payment_method':'paypal'
             },
         'transactions': [{
             'amount': {
                 'total': request.form['total'],
                 'currency':'USD'},
             'description':f"purchase->{request.form['coinsReceived']}"
             }],
         'redirect_urls': {
             'return_url': 'https://example.com',
             'cancel_url': 'https://example.com'}
         }
    payment = paypalrestsdk.Payment(d)

    if payment.create():
        print("Payment[%s] created successfully" % (payment.id))
        return jsonify(paymentID=payment.id, status=200)
    else:
        print(payment.error)
        return jsonify(success=False,status=404)

def memoize_transaction(transaction_object):
    app.config['mem-pool'][transaction_object[
        'paymentID']] = transaction_object;

@app.route('/express-checkout-return-url', methods=['POST', 'GET'])
@app.route('/express-checkout-return-url/', methods=['POST', 'GET'])
def do_express_checkout():
    # ID of the payment. This ID is provided when creating payment.
    payment = paypalrestsdk.Payment.find(request.form['paymentID'])

    # PayerID is required to approve the payment.
    if payment.execute({"payer_id": request.form['payerID']}):
        amount = payment.transactions[0]['amount']['total']
        fee = payment.transactions[0]['related_resources'][0]['sale']['transaction_fee']['value']
        print(amount)
        print(fee)
        session['paymentID'] = {'id_token':session['id_token'],
                                'paymentID':payment.id,
                                'amount':float(amount)-float(fee),
                                'coin':float(f"{payment.transactions[0]['description']}".split('->')[1]),
                                'create_time':payment.create_time}
        memoize_transaction({'id_token':session['id_token'],
                             'paymentID':payment.id,
                             'amount':float(amount)-float(fee),
                             'coin':float(f"{payment.transactions[0]['description']}".split('->')[1]),
                             'timestamp':payment.create_time})
        print("Payment[%s] execute successfully" % (payment.id))
        return jsonify(success=True)
    print(payment.error)
    return jsonify(success=False)

@app.route('/error-checks', methods=['POST', 'GET'])
@app.route('/error-checks/', methods=['POST', 'GET'])
def do_error_check():return jsonify(success=True)

@app.route("/payments-complete")
@app.route("/payments-complete/")
def payments_complete():
    if not 'paymentID' in session: return "unauthorized", 401
    return render_template('payments-complete.html',
                           date=session['paymentID']['create_time'],
                           paymentID=session['paymentID']['paymentID'])

@app.route("/transfers")
@app.route("/transfers/")
def make_transfer():pass

@app.route("/transfers-complete")
@app.route("/transfers-complete/")
def transfers_complete():
    #if not 'paymentID' in session: return "unauthorized", 401
    return render_template('transfers-complete.html')

@app.route("/withdrawals")
@app.route("/withdrawals/")
def make_withdrawal():pass

@app.route("/withdrawals-complete")
@app.route("/withdrawals-complete/")
def withdrawals_complete():
    #if not 'paymentID' in session: return "unauthorized", 401
    return render_template('withdrawals-complete.html')

#TODO:: disable disputes, disclaimers & terms

@app.route('/connect', methods=['POST'])
@app.route('/connect/', methods=['POST'])
def connect_google_openid_session():    
    data = request.get_json()['kR']
    session['id_token'] = data
    return jsonify(success=True, data=data)

@app.route('/requests_conversion_from_coin', methods=['POST'])
@app.route('/requests_conversion_from_coin/', methods=['POST'])
def requests_conversion_from_coin():
    data = request.get_json()
    value = json.loads(data)['amount']
    print(value)
    return jsonify(success=True)

def is_grantable_access_token(config:dict): return True

def write_to_wallets(id_token, data):
    last_known = mem.load_json(os.path.join(bc.settings['wallets-dir'],f"{id_token}.json"))
    if not last_known:
        data['last-seen-amount'] = 0
        data['last-seen-coin'] = 0
        mem.write_json(data, os.path.join(bc.settings['wallets-dir'],f"{id_token}.json"))
        return
    data['last-seen-amount'] = last_known['last-seen-amount'] + last_known['amount']
    data['last-seen-coin'] = last_known['last-seen-coin'] + last_known['coin']
    mem.write_json(data, os.path.join(bc.settings['wallets-dir'],f"{id_token}.json"))

def clear_mem(data:dict):
    t = []
    amount_tally = 0
    coin_tally = 0
    for i in data:
        amount_tally += app.config['mem-pool'][i]['amount']
        coin_tally += app.config['mem-pool'][i]['coin']
        id_token = app.config['mem-pool'][i]['id_token']
        write_to_wallets(id_token, app.config['mem-pool'][i])
        t.append(app.config['mem-pool'][i])
        app.config['mem-pool'].pop(i)
    bc.publish(t, configure['access-token'])
    published_supply = mem.load_json(os.path.join(bc.settings['wallets-dir'],"supply.json"))
    if not published_supply:
        supply = coin_tally
        amount = amount_tally
        d = {'total-supply-published':supply,'total-banked': amount}
        mem.write_json(d, os.path.join(bc.settings['wallets-dir'],"supply.json"))
        return
    published_supply['total-supply-published'] = published_supply['total-supply-published'] + coin_tally
    published_supply['total-banked'] = published_supply['total-banked'] + amount_tally
    mem.write_json(published_supply, os.path.join(bc.settings['wallets-dir'],"supply.json"))
    
def is_valid_broadcast(config:dict, data:dict):
    if not is_grantable_access_token(config): return False
    clear_mem(data)
    return True

@app.route('/latest-pipeline-feed', methods=['POST'])
@app.route('/latest-pipeline-feed/', methods=['POST'])
def latest_pipeline_feed():
    if not is_grantable_access_token(request.form.get('access-token')):pass
    return jsonify(success=True, data=app.config['mem-pool'], code=200)

@app.route('/latest-pipeline-broadcast', methods=['POST'])
@app.route('/latest-pipeline-broadcast/', methods=['POST'])
def latest_pipeline_broadcast():
    d = request.form.to_dict(flat=False)
    k = [i for i in request.form.keys() if not i in ['access-token',
                                                     'reason']][0]
    return jsonify(success=True, code=200) if is_valid_broadcast(d['access-token'], d[k]) else jsonify(success=False, code=401)

def administration_pipelines():pass
if __name__ == "__main__": app.run(debug=True,host='localhost')
