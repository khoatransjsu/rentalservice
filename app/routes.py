from flask import render_template, flash, redirect, url_for, request, jsonify, json, session
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetForm
from app.models import User, Orders, Items
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.orm import Session
from werkzeug.urls import url_parse
import stripe, re, datetime


public_key = "pk_test_5CtyFYAaxLxeleKgqeAaD74200elm1H19G"
stripe.api_key = "sk_test_IbCpBwCdEd0Uc7g9JAdZedxL000i3LvPhN"

#-------------------------------------------------------------------------------------------------------------------------
#----- index
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/')
@app.route('/index')
#@login_required  #use this for pages that requires user logged in
def index():
    if session.get('cart') == None:
        session['cart'] = []
    items = Items.query.all()
    itemCount = cartCount()
    return render_template('home.html', items=items, itemCount=itemCount, title='Home')
#-------------------------------------------------------------------------------------------------------------------------
#----- Order History
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/orders')
@login_required  #use this for pages that requires user logged in
def orders():
	# query all orders from authorized user
    orders = Orders.query.filter_by(user_id=current_user.id).order_by(Orders.id.desc()).all()

    for eachOrder in orders:
		# All items data in each order request
        itemsData = Items.query.filter(Items.id.in_(stringToList(eachOrder.item_id))).all()
		# create blank arrays in each order to store additional information, this will add to original orders array
        eachOrder.names = []
        eachOrder.dueDates = []
        eachOrder.dueDays = []
		
		# Get each item detail from items model
        for item in itemsData:
			# create due date for each item in each order
            dueDate = addDaysToDate(eachOrder.timestamp, item.duration + 1);
			# add to blank arrays
            eachOrder.names.append(item.name)
            eachOrder.dueDates.append(dueDate)
            eachOrder.dueDays.append(daysCount(dueDate))

		# combines arrays for loop in template
        eachOrder.items = zip(eachOrder.names, eachOrder.dueDates, eachOrder.dueDays)
        print(eachOrder.items)
        #eachOrder.names = listToString(eachOrder.names)
		
    itemCount = cartCount()
    return render_template('orders.html', orders=orders, itemCount=itemCount, title='Orders History') 
def daysCount(date):
    if date is None:
        return 0
    d1 = datetime.datetime.now() 
    d2 = datetime.datetime.strptime(date, "%A %d, %B %Y")
    delta = d2 - d1
    print(delta.days)
    return delta.days

def addDaysToDate(date, days):
    if date is None or days is None:
        return 0
    #https://docs.python.org/2/library/datetime.html
    u = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S.%f")
    d = datetime.timedelta(days=days)
    t = datetime.datetime.strftime(u + d, "%A %d, %B %Y")
    return t
#-------------------------------------------------------------------------------------------------------------------------
#----- Show Item & add item
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/item/<int:product_id>', methods=['GET'])
def getItem(product_id):
    item = Items.query.filter_by(id=product_id).first()
    itemCount = cartCount()
    return render_template('item.html', item=item, itemCount=itemCount, title=item.name) 
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/add/<int:product_id>', methods=['GET'])
def addItem(product_id):
	# add item to cart (temporary save product id in cookie and server session)
    if product_id in session['cart']:
        flash('Item is already added to cart.')
    else:
        session['cart'].append(product_id)
        flash('Added to cart.')
    
    item = Items.query.filter_by(id=product_id).first()
    itemCount = cartCount()

    return render_template('item.html', item=item, itemCount=itemCount, title=item.name) 
#-------------------------------------------------------------------------------------------------------------------------
#----- Shopping Cart Stuff
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/cart', methods=['GET', 'POST'])
def cart(): 
    items = Items.query.filter(Items.id.in_(session['cart'])).all()
    totalCost = getCartTotalCost(items)
    itemCount = len(items)

    return render_template('cart.html', items=items, total=totalCost, itemCount=itemCount, title='Shopping Cart')
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/cartUpdate', methods=['POST'])
def cartUpdate(): 
    if request.is_json:
        session['cart'] = request.get_json()
        items = Items.query.filter(Items.id.in_(session['cart'])).all()
        total = getCartTotalCost(items)
        return str(total)
    return '0'
#-------------------------------------------------------------------------------------------------------------------------
# get cart item counts
def cartCount(): 
    items = Items.query.filter(Items.id.in_(session['cart'])).all()
    total = len(items)

    return str(total)

# get cart total cost function based on data given
def getCartTotalCost(data):
    total = 0
    for item in data:
        total += item.price
    return total
#-------------------------------------------------------------------------------------------------------------------------
#----- Checkout & Payment Process
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/checkout', methods=['POST'])
@login_required #required user to login
def checkout(): 
    items = Items.query.filter(Items.id.in_(session['cart'])).all()
    totalCost = getCartTotalCost(items)
    itemCount = len(items)

    return render_template('checkout.html', items=items, total=totalCost, amount=totalCost*100, itemCount=itemCount, 
            email=current_user.email, name=current_user.firstname+' '+current_user.lastname, 
			public_key=public_key, title='Checkout')
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/payment', methods=['POST'])
@login_required
def payment():
    items = Items.query.filter(Items.id.in_(session['cart'])).all()
    itemsList = listToString(session['cart'])
    cost = getCartTotalCost(items)
    invoice_no=getInvoiceNumber()
	# stripe payment stuff
    #customer = stripe.Customer.create(email=current_user.email,source=request.form['stripeToken'])
    #charge = stripe.Charge.create(customer=customer.id, amount=cost*100, currency='usd', description='A payment for '+invoice_no)

    # add to orders Database
    order = Orders(user_id=current_user.id, 
			invoice_no=invoice_no,
			comment=remove_tags(request.form['specialRequest']),
			cost=cost,
			item_id=itemsList)
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        print("\n FAILED entry: {}\n".format(json.dumps(order)))
        print(e)

    # Update to items inventory Database
    for item in session['cart']:
        u = db.session.query(Items).get(item)
        if u.inventory > 0:
            u.inventory -= 1
            db.session.commit()

    session['cart'] = []
    return render_template('thankyou.html', title='Order Placed', receipt=invoice_no)
#-------------------------------------------------------------------------------------------------------------------------
#----- User login / Registation / Logout
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
	# if user logged in, go to main home page
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()
	# validate form
	if not form.validate_on_submit():
		itemCount = cartCount()
		return render_template('login.html', form=form, itemCount=itemCount, title='Login')

	# look at first result first()
	user = User.query.filter_by(email=form.email.data).first()

	if user is None or not user.check_password(form.password.data):
		flash('Invalid username or password')
		return redirect(url_for('login'))

	#login_user(user, remember=form.remember_me.data)
	login_user(user)

	# return to page before user got asked to login
	next_page = request.args.get('next')

	if not next_page or url_parse(next_page).netloc != '':
		next_page = url_for('index')

	return redirect(next_page)
#-------------------------------------------------------------------------------------------------------------------------
# if sign-up validate registration form and create user
@app.route('/register', methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
			
	form = RegistrationForm()
	if not form.validate_on_submit():
		itemCount = cartCount()
		return render_template('register.html', form=form, itemCount=itemCount, title='Register')

	user = User(email=form.email.data, 
				firstname=form.firstname.data, 
				lastname=form.lastname.data,
				studentid=form.studentid.data)
	user.set_password(form.password.data)
	try:
		db.session.add(user)
		db.session.commit()
	except Exception as e:
		print("\n FAILED entry: {}\n".format(json.dumps(user)))
		print(e)
	flash('Congratulations, you are now a registered user!')
	login_user(user)
	return redirect(url_for('index'))
#-------------------------------------------------------------------------------------------------------------------------
# reset-login
@app.route('/reset', methods=['GET', 'POST'])
def reset():
	form = ResetForm()
	flash('reset function not set yet')
	return redirect(url_for('login'))
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/db')
@login_required
def showDB():
    if current_user.email == 'admin':
        users = User.query.all()
        orders = Orders.query.all()
        items = Items.query.all()
        itemCount = cartCount()
        totalItems = len(items)
        return render_template('result.html', users=users, orders=orders, items=items, itemCount=itemCount, totalItems=totalItems, title='Database')
    return redirect(url_for('index'))
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/itemUpdate/<int:id>', methods=['POST'])
def itemUpdate(id):
    data = request.get_json()
    print(data)
    for key, value in data.items():
        field = remove_tags(value)

    # Update to items inventory Database
    item = db.session.query(Items).get(id)
    if item is not None:
        item.name = data['name']
        item.description = data['description']
        item.duration = data['duration']
        item.inventory = data['inventory']
        item.price = data['price']
        item.imgUrl = data['imgUrl']
        db.session.commit()
        return 'id #'+str(id)+' has been updated'
    else:
        new_entry = Items(name=data['name'], 
						description=data['description'], 
						inventory=data['inventory'], 
						duration=data['duration'], 
						price=data['price'], 
						imgUrl=data['imgUrl'])

        db.session.add(new_entry)
        db.session.commit()
        return 'Added '+str(data['name'])+' to items list'

    return "id not found"
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/itemDelete/<int:id>', methods=['POST'])
def itemDelete(id):
    item = db.session.query(Items).get(id)
    print(item)
    if item is not None:
        db.session.delete(item)
        db.session.commit()
        return 'id #'+str(id)+' has been deleted'

    return "id not found"
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/deluser/<int:user_id>')
def delID(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return "id not found"
    else:
        db.session.delete(user)
        db.session.commit()
    data = User.query.all()
    return redirect(url_for('showDB'))
#-------------------------------------------------------------------------------------------------------------------------
@app.route('/delorder/<int:order_id>')
def delitems(order_id):
    order = Orders.query.filter_by(id=order_id).first()
    if order is None:
        return "id not found"
    else:
        db.session.delete(order)
        db.session.commit()
    return redirect(url_for('showDB'))
#-------------------------------------------------------------------------------------------------------------------------
# run this first time to fill db
@app.route('/filldb')
def fillCheck():
    user = User.query.first()
    if not user is None:
        return str(user.email)
    fillDB()
    return redirect(url_for('showDB'))

def fillDB():
    db.create_all()
    # create admin user
    admin = User(firstname='admin', lastname='', studentid='123456', email='admin')
    admin.set_password('1234')
    try:
        db.session.add(admin)
        db.session.commit()
    except Exception as e:
        return "FAILED entry: "+str(e)
    #create items
    objects = [
        {'name':'iPad',
            'description':'iPad Pro 1000', 
            'inventory':10, 
            'duration':4, 
            'price':19.99, 
            'imgUrl':'ipad.png'},
        {'name':'Laptop', 
            'description':'Top of the line mac book air', 
            'inventory':10, 
            'duration':4, 
            'price':29.99, 
            'imgUrl':'laptop.png'},
        {'name':'Calculator', 
            'description':'Ti 84-Plus', 
            'inventory':10, 
            'duration':2, 
            'price':9.99, 
            'imgUrl':'calculator.png'},
        {'name':'Surface Pro 6', 
            'description':'Newest modest of 2018', 
            'inventory':10, 
            'duration':4, 
            'price':29.99, 
            'imgUrl':'sp6.png'}
    ]
    try:
        items_entries = []
        for item in objects:
            new_entry = Items(name=item['name'], description=item['description'], inventory=item['inventory'], duration=item['duration'], price=item['price'], imgUrl=item['imgUrl'])
            items_entries.append(new_entry)

        db.session.add_all(items_entries)
        db.session.commit()
    except Exception as e:
        return "FAILED entry: "+str(e)
#-------------------------------------------------------------------------------------------------------------------------
#----- Helper functions
#-------------------------------------------------------------------------------------------------------------------------
TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)
#-------------------------------------------------------------------------------------------------------------------------
def stringToList(string): 
    li = list(string.split(",")) 
    return li 
#-------------------------------------------------------------------------------------------------------------------------
def listToString(s): 
    str1 = " " 
    print(s)
    return (','.join(str(v) for v in s))
#-------------------------------------------------------------------------------------------------------------------------
def getInvoiceNumber():
    last_invoice = Orders.query.order_by(Orders.id.desc()).first()
    if not last_invoice:
         return 'RS0001'
    invoice_no = last_invoice.invoice_no
    invoice_int = int(invoice_no.split('RS')[-1])
    new_invoice_int = invoice_int + 1
    new_invoice_no = 'RS' + str(new_invoice_int).zfill(4)
    return new_invoice_no
#-------------------------------------------------------------------------------------------------------------------------