import os
from flask import Flask, render_template, url_for, request, redirect
import stripe

app = Flask(__name__)

public_key = "pk_test_5CtyFYAaxLxeleKgqeAaD74200elm1H19G"

stripe.api_key = "sk_test_IbCpBwCdEd0Uc7g9JAdZedxL000i3LvPhN"

@app.route('/')
def index():
    return render_template('home.html')
    
@app.route('/form', methods=['GET', 'POST'])
def add_name():
    return render_template('rental_form.html')
    
@app.route('/list')
def list_item():
    return render_template('list.html')

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    name = request.args.get('name')
    return render_template('confirm.html', name = name, public_key=public_key)

@app.route('/payment', methods=['POST'])
def payment():
    customer = stripe.Customer.create(email=request.form['stripeEmail'],source=request.form['stripeToken'])

    charge = stripe.Charge.create(customer=customer.id, amount=999, currency='usd', description='Due')

    return redirect(url_for('thankyou'))

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)