from flask import Flask, render_template, request, jsonify, session, redirect, make_response, url_for
import datetime
import threading
import hashlib
import os
import requests
import base64
import json
import paypalrestsdk
import logging
from lib import core_sdk

app = Flask(__name__)
app.secret_key = os.urandom(24)
logging.basicConfig(level=logging.INFO)

app.config['mem-pool'] = {}
app.config['logs-of-latest-work'] = {}

GOOGLE_APPLICATION_NAME = "Arpeggio Merchants"

#// 1. Set up your server to make calls to PayPal

#// 1a. Add your client ID and secret
PAYPAL_CLIENT = ''
PAYPAL_SECRET = ''
PAYPAL_SANDBOX_CLIENT = 'AZju-GnsK4OkeJgRtKOSmfVb9I0nxmLO8rit1_QRNQsnfiGRmGuhT5g5eW45Zh-EJ-96PDbUMH8t4tSk'
PAYPAL_SANDBOX_SECRET = 'EFBkVMzW6Mn9Peu_wDaEDRwvCrQj89j0klsuQi48USbnnEEf0v7O9TnRHx-G9wxXU4Zurig1GTJROY3S'

PAYPAL_LIVE = {
    "mode": "live", # sandbox or live
    "client_id": PAYPAL_CLIENT,
    "client_secret": PAYPAL_SECRET}
PAYPAL_SANDBOX = {
    "mode": "sandbox", # sandbox or live
    "client_id": PAYPAL_SANDBOX_CLIENT,
    "client_secret": PAYPAL_SANDBOX_SECRET}

paypalrestsdk.configure(PAYPAL_SANDBOX)
    
@app.route("/", methods=["POST", "GET"])
def home():
    return render_template('index.html')

@app.route("/payments")
@app.route("/payments/")
def payments():
    return render_template('payments.html',date=datetime.datetime.now())

@app.route('/set-express-checkout', methods=['POST', 'GET'])
@app.route('/set-express-checkout/', methods=['POST', 'GET'])
def set_express_checkout():
    if not 'total' in request.form: return jsonify({'unauthorized':'401'})
    d = {'intent':'sale',
         'payer': {
             'payment_method':'paypal'
             },
         'transactions': [{
             'amount': {
                 'total': request.form['total'],
                 'currency':'USD'},
             'description':'{"smart-token":f"session["id_token"]"}'
             }],
         'redirect_urls': {
             'return_url': 'https://example.com',
             'cancel_url': 'https://example.com'}
         }
    payment = paypalrestsdk.Payment(d)

    if payment.create():
        print("Payment[%s] created successfully" % (payment.id))
        return jsonify({'paymentID':payment.id})
    else:
        print(payment.error)
        return jsonify({'error':'404'})

def memoize_transaction(transaction_object):
    app.config['mem-pool'][transaction_object['paymentID']] = transaction_object;

@app.route('/express-checkout-return-url', methods=['POST', 'GET'])
@app.route('/express-checkout-return-url/', methods=['POST', 'GET'])
def do_express_checkout():
    # ID of the payment. This ID is provided when creating payment.
    payment = paypalrestsdk.Payment.find(request.form['paymentID'])

    # PayerID is required to approve the payment.
    if payment.execute({"payer_id": f"{request.form['payerID']}"}):  # return True or False
        session['paymentID'] = request.form['paymentID']
        memoize_transaction({'paymentID':payment.id,'timestamp':payment.create_time})
        print(app.config['mem-pool'])
        print("Payment[%s] execute successfully" % (payment.id))
        return jsonify({'verified':True})
    else:
        print(payment.error)
        return jsonify({'verified':False})

@app.route("/payments-complete")
@app.route("/payments-complete/")
def payments_complete():
    if not 'paymentID' in session: return "unauthorized", 401
    return render_template('payments-complete.html', date=datetime.datetime.now(), paymentID=session['paymentID'])

@app.route('/connect', methods=['POST'])
@app.route('/connect/', methods=['POST'])
def connect_google_openid_session():    
    data = request.get_json()
    session['id_token'] = data
    return jsonify(status="success", data=data)

def is_grantable_access_token_access(configuration):
    return True

@app.route('/latest-pipeline-feed', methods=['POST'])
@app.route('/latest-pipeline-feed/', methods=['POST'])
def latest_pipeline_feed():
    if not is_grantable_access_token_access(request.args.get('configuration')):pass
    return jsonify(status="success", data=app.config['mem-pool'])

if __name__ == "__main__":
    app.run(debug=False,host='localhost')
