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
cs = core_sdk.Splitting(1050000)


PAYPAL_LIVE = {
    "mode": "live", # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID_LIVE'),
    "client_secret": os.environ.get('PAYPAL_SECRET_LIVE')}
PAYPAL_SANDBOX = {
    "mode": "sandbox", # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_SECRET')}

paypalrestsdk.configure(PAYPAL_LIVE)

# -- TEMPLATES/VIEWS
    
@app.route("/", methods=["POST", "GET"])
def home():
    published_supply = mem.load_json(os.path.join(
        bc.settings['wallets-dir'],"supply.json"))
    supply = 0 if not published_supply else published_supply[
        'total-supply-published']

    dir_ = None
    balance = 0 if not 'balance'in session.keys() else session['balance']
    return render_template('index.html', mint=supply
                           ,net_target=supply/cs.net_target
                           ,balance=balance)

@app.route("/payments")
@app.route("/payments/")
def payments():return render_template('payments.html')

@app.route("/payments-complete")
@app.route("/payments-complete/")
def payments_complete():
    if not 'paymentID' in session: return "unauthorized", 401
    return render_template('payments-complete.html',
                           date=session['paymentID']['create_time'],
                           paymentID=session['paymentID']['paymentID'])

# -- END

# -- SERVER-SIDE METHODS FOR TEMPLATES/VIEWS

def compile_information(tokens:int):
    p_fees = bc.settings['paypal-fees']
    n_fee = bc.settings['network-fee']
    a = tokens * 100 * 1.00
    first_option = [app.config['mem-pool'][i] for i in sorted(
        app.config['mem-pool'].keys())]
    if len(first_option):
        option = first_option[len(first_option)-1]
        n = option['coin']/(option['amount']-option['fee'])
        a = (a+a*(1-n))
        return a + n_fee + p_fees["fixed-amount"] + (a * p_fees["conversion-rate"]) + (a * p_fees["all-payments-rate"])
    second_option = bc.last_block_added
    if second_option:
        print(second_option)
        n = second_option['transactions'][0]['coin']/(second_option['transactions'][0]['amount']-second_option['transactions'][0]['fee'])
        a = tokens * 100 * 1.00
        a = (a+a*(1-n))
        return a + n_fee + p_fees["fixed-amount"] + (a * p_fees["conversion-rate"]) + (a * p_fees["all-payments-rate"])
    return a + n_fee + p_fees["fixed-amount"] + (a * p_fees["conversion-rate"]) + (a * p_fees["all-payments-rate"])

@app.route('/requests-cryto-to-fiat-rates', methods=['POST'])
@app.route('/requests-cryto-to-fiat-rates/', methods=['POST'])
def crypto_to_fiat():
    data = request.get_json()
    value = json.loads(data)['amount']
    info = compile_information(value)
    return jsonify(success=True,total=info)

# -- END

# -- GOOGLE

@app.route('/google-authorised', methods=['POST'])
@app.route('/google-authorised/', methods=['POST'])
def broadcasts_google_openid_authorisation():    
    id_token = request.get_json()['ER']
    h = Blockchain.sha256_string(f"{id_token}")
    session['id_token'] = h

    try:
        dir_ = mem.load_json(os.path.join(
            bc.settings['wallets-dir'], f"{h}.json"))   
        session['balance'] = dir_['last-seen-amount'] - dir_['last-seen-fee']
    except IOError:
        data = {}
        data['last-seen-amount'] = 0
        data['last-seen-coin'] = 0
        data['last-seen-fee'] = 0
        mem.write_json(data, os.path.join(
            bc.settings['wallets-dir'],f"{h}.json"))
    finally:return jsonify(success=True, data=h)

# -- END

# -- PAYPAL

def paypal_web_profile_json_request_object():
    wpn = ''.join(random.choice(string.ascii_uppercase) for i in range(12))
    web_profile = paypalrestsdk.WebProfile({
        "name": wpn,
        "input_fields": {
            "allow_note": False,
            "no_shipping": 1,
            },
        })
    return web_profile

def paypal_create_web_profile():
    try:
        web_profile = paypal_web_profile_json_request_object()
        if web_profile.create():
            print("Web Profile[%s] created successfully" % (web_profile.id))
            return web_profile
    except IOError:print(web_profile.error)
    return None

def paypal_payment_json_object(request_object):
    print(request_object.form['total'].split("$")[1])
    session['coin'] = float(request_object.form['coinsReceived'])
    web_profile = paypal_create_web_profile()
    d = {'intent':'sale',
         'experience_profile_id': web_profile.id,
         'payer': {
             'payment_method':'paypal'
             },
         'transactions': [{
             'amount': {
                 'total': request_object.form['total'].split("$")[1],
                 'currency':'USD'},
             'description':f"purchase->{request.form['coinsReceived']}"
             }],
         'redirect_urls': {
             'return_url': 'https://example.com',
             'cancel_url': 'https://example.com'}
         }
    return d

@app.route('/set-express-checkout', methods=['POST', 'GET'])
@app.route('/set-express-checkout/', methods=['POST', 'GET'])
def paypal_set_express_checkout():
    if not 'total' in request.form: return jsonify(success=False, status=401)
    if not 'id_token' in session: return jsonify(success=False, status=401)

    try:
        data = paypal_payment_json_object(request)
        payment = paypalrestsdk.Payment(data)
        if payment.create():
            print("Payment[%s] created successfully" % (payment.id))
            return jsonify(paymentID=payment.id, status=200)
    except IOError:print(payment.error)
    return jsonify(success=False,status=404)

def memoize_transaction(transaction_object):
    app.config['mem-pool'][transaction_object[
        'paymentID']] = transaction_object;

def return_transaction_object(payment, amount, fee, coin):
    return {'id_token':session['id_token'],
            'paymentID':payment.id,
            'amount':amount,
            'fee':fee,
            'coin':coin,
            'create_time':payment.create_time}

@app.route('/do-express-checkout', methods=['POST', 'GET'])
@app.route('/do-express-checkout/', methods=['POST', 'GET'])
def paypal_do_express_checkout():
    try:
        payment = paypalrestsdk.Payment.find(request.form['paymentID'])
        if payment.execute({"payer_id": request.form['payerID']}):
            amount = float(payment.transactions[0]['amount']['total'])
            fee = float(payment.transactions[0]['related_resources'][0]['sale']['transaction_fee']['value'])
            coin = session['coin']
            session['paymentID'] = return_transaction_object(payment, amount, fee, coin)
            memoize_transaction(return_transaction_object(payment, amount, fee, coin))
            print("Payment[%s] execute successfully" % (payment.id))
            return jsonify(success=True)
    except IOError:print(payment.error)
    finally:return jsonify(success=False)

# -- END

# -- BANKING

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

@app.route("/handle-disputes")
@app.route("/handle-disputes/")
def disputes_webhook():pass

# -- END

# -- DLEDGER PARALLEL PUBLISHING ACCESS POINTS

def is_grantable_access_token(config:dict): return True

def write_to_wallets(id_token, data):
    last_known = mem.load_json(os.path.join(
        bc.settings['wallets-dir'],f"{id_token}.json"))
    if not last_known:
        data['last-seen-amount'] = 0
        data['last-seen-coin'] = 0
        data['last-seen-fee'] = 0
        mem.write_json(data, os.path.join(
            bc.settings['wallets-dir'],f"{id_token}.json"))
        return
    print(last_known)
    data['last-seen-amount'] = last_known["last-seen-amount"] + data['amount']
    data['last-seen-coin'] = last_known["last-seen-coin"] + data['coin']
    data['last-seen-fee'] = last_known["last-seen-fee"] + data['fee']
    session['balance'] = data['last-seen-coin'] - data['last-seen-fee']
    mem.write_json(data, os.path.join(
        bc.settings['wallets-dir'],f"{id_token}.json"))

def clear_mem(data:dict):
    t = []
    amount_tally = 0
    coin_tally = 0
    fee_tally = 0
    for i in data:
        amount_tally += app.config['mem-pool'][i]['amount']
        coin_tally += app.config['mem-pool'][i]['coin']
        fee_tally += app.config['mem-pool'][i]['fee']
        id_token = app.config['mem-pool'][i]['id_token']
        write_to_wallets(id_token, app.config['mem-pool'][i])
        t.append(app.config['mem-pool'][i])
        app.config['mem-pool'].pop(i)
    bc.publish(t, configure['access-token'])
    published_supply = mem.load_json(os.path.join(
        bc.settings['wallets-dir'],"supply.json"))
    if not published_supply:
        supply = coin_tally
        amount = amount_tally
        fee = fee_tally
        d = {'total-supply-published':supply,'total-banked': amount, 'total-fees': fee_tally}
        mem.write_json(d, os.path.join(
            bc.settings['wallets-dir'],"supply.json"))
        return
    published_supply['total-supply-published'] = published_supply['total-supply-published'] + coin_tally
    published_supply['total-banked'] = published_supply['total-banked'] + amount_tally
    published_supply['total-banked'] = published_supply['total-fees'] + fee_tally
    mem.write_json(published_supply, os.path.join(
        bc.settings['wallets-dir'],"supply.json"))
    
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

# -- END

def administration_pipelines():pass
if __name__ == "__main__":
    #443 for https 80 for http
    context = ('sircoin.org_ssl_certificate.cer', '_.sircoin.org_private_key.key')
    app.run(debug=True,host='192.168.0.118', port=443, ssl_context=context)
