from flask import Flask, render_template, request, redirect, session
import uuid
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import bcrypt
import re


app = Flask(__name__)
bcrypt = Bcrypt(app)
# Configure the SQLAlchemy database

app.secret_key = 'MySecretKey123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use your preferred database UR
db = SQLAlchemy(app)
#db = SQLAlchemy(app, binds={"default": "sqlite:///users.db"})
#Creating a class for the users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(80), nullable=False)
    phonenumber = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    occupation = db.Column(db.String(80), nullable=False)
    account_type = db.Column(db.String(80), nullable=False)

    #constructor
    def __init__(self, username, email, phonenumber, password, address, country, occupation, account_type):
       self.username = username
       self.email = email
       self.phonenumber = phonenumber
       self.password = password
       self.address = address
       self.country = country
       self.occupation = occupation
       self.account_type = account_type

    def check_password(self,password):
       return bcrypt.checkpw(password.encode('utf-8'),self.password.encode())
    



class Account(db.Model):                                                       
    account_number = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50))
    balance = db.Column(db.Float)
    password = db.Column(db.String(50))
    transactions = db.relationship('Transaction', backref='account', lazy=True)


    def add_transaction(self, amount, description):
        transaction = Transaction(amount=amount, description=description, account_number=self.account_number)
        db.session.add(transaction)
        db.session.commit()



class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(10), db.ForeignKey('account.account_number'))
    date = db.Column(db.DateTime, default=datetime.now)
    amount = db.Column(db.Float)
    description = db.Column(db.String(100))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')



@app.route('/freeze', methods=['POST'])
def freeze_account():
    account_number = request.form['account_number']

    account = Account.query.filter_by(account_number=account_number).first()
    if account:
        account.status = 'Frozen'
        db.session.commit()

    return redirect('/')

@app.route('/unfreeze', methods=['POST'])
def unfreeze_account():
    account_number = request.form['account_number']

    account = Account.query.filter_by(account_number=account_number).first()
    if account:
        account.status = 'Active'
        db.session.commit()

    return redirect('/')

@app.route('/search', methods=['POST'])
def search_account():
    search_query = request.form['search_query']

    search_results = Account.query.filter(Account.account_number.like(f'%{search_query}%')).all()

    if len(search_results) == 0:
        return render_template('not_found.html', search_query=search_query)
    else:
        return render_template('search.html', search_results=search_results, search_query=search_query)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # User authentication successful
            account = Account.query.filter_by(name=username).first()
            if account:
                session['account_number'] = account.account_number
                return redirect('/dashboard')
            else:
                return 'Account not found'
        else:
            # User authentication failed
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    def generate_unique_account_number():
        account_number = str(uuid.uuid4().int)[:5]  # Generate a UUID and extract the first 10 digits
        return account_number

    user = None  # Initialize the user variable
    error_message = None  # Initialize the error message variable

    if request.method == 'POST':
        # handle request
        username = request.form['username']
        email = request.form['email']
        phonenumber = request.form['phonenumber']
        password = request.form['password']
        address = request.form['address']
        country = request.form['country']
        occupation = request.form['occupation']
        account_type = request.form['account_type']

        # Perform password validation
        if not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            error_message = "Password must contain both letters and numbers."

        # Perform phone number validation
        if not phonenumber.isdigit() or len(phonenumber) != 9 or not re.match(r'^(67|69|68|65)', phonenumber):
            error_message = "Phone number must be a 9-digit number starting with 67, 69, 68, or 65."
            
        if error_message:
            return render_template('registration.html', error_message=error_message, accounts=Account.query.all())

        if error_message is None:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            user = User(username=username, email=email, phonenumber=phonenumber, password=hashed_password,
                        address=address, country=country, occupation=occupation, account_type=account_type)
            db.session.add(user)
            db.session.commit()

            # Create an associated account for the user
            account_number = generate_unique_account_number()
            name = username
            balance = 0.0
            account_password = hashed_password

            account = Account(account_number=account_number, name=name, balance=balance, password=account_password)
            db.session.add(account)
            db.session.commit()
            return redirect('/login')
        return redirect('/login')
    return render_template('registration.html', user=user, error_message=error_message)


@app.route("/dashboard", methods=['GET'])
def dashboard():
    account_number = session.get('account_number')
    account = Account.query.filter_by(account_number=account_number).first()
    if account:
        return render_template('bank.html', account=account, account_number=account_number, balance=account.balance, name=account.name)
    return 'Account not found'

@app.route('/transfer', methods=['GET', 'POST']  )
def transfer():
    account_number = session.get('account_number')
    account = Account.query.filter_by(account_number=account_number).first()
    if request.method == 'POST':
        sender_account_number = session.get('account_number')
        recipient_account_number = request.form['recipient-account-number']
        recipient_name = request.form['recipient-name']
        amount = float(request.form['amount'])
        password = request.form['password']

        sender = Account.query.filter_by(account_number=sender_account_number).first()
        recipient = Account.query.filter_by(account_number=recipient_account_number, name=recipient_name).first()

        # Validation checks
        error_message = None

        if not sender:
            error_message = "Sender account number is invalid."
        elif not recipient:
            error_message = "Recipient account number or name is invalid."
        elif amount > sender.balance:
            error_message = "Insufficient balance."
        elif not bcrypt.check_password_hash(sender.password, password):
            error_message = "Incorrect password."

        if error_message:
            return render_template('transfer.html', account=account, account_number=account_number, balance=account.balance, error_message=error_message, accounts=Account.query.all(),)

        # Transfer logic
        sender.balance -= amount
        recipient.balance += amount

        # Add transactions to sender and recipient accounts
        sender.add_transaction(-amount, f"Transferred to {recipient_account_number}")
        recipient.add_transaction(amount, f"Received from {sender_account_number}")

        # Save changes to the database
        db.session.commit()

        success_message = f"Successfully transferred {amount} to {recipient_account_number}."

        return render_template('transfer.html', account=account, account_number=account_number, balance=account.balance, success_message=success_message, accounts=Account.query.all())
    else:
        return render_template('transfer.html', account=account, account_number=account_number, balance=account.balance, accounts=Account.query.all())



@app.route('/history', methods=['GET', 'POST'])
def history():
    
    account_number = session.get('account_number')
    account = Account.query.filter_by(account_number=account_number).first()
    if request.method == 'POST':
        account_number = request.form['account-number']
        current = Account.query.filter_by(account_number=account_number).first()
        error_message = None
        account_num = session.get('account_number') 
        
        if account_number != account_num:
            error_message = "Invalid account number."
            return render_template('history_form.html', account=current, account_number=account_number, account_num=account_num, error_message=error_message)

        transactions = Transaction.query.filter_by(account_number=account_number).all()

        return render_template('history.html', account=current, account_number=account_number, transactions=transactions, account_num=account_num)
    else:
        return render_template('history_form.html', account=account, account_number=account_number, balance=account.balance, name=account.name)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw_form():
    error_message = None
    success_message = None
    updated_balance = None
    account_number = session.get('account_number')
    account = Account.query.filter_by(account_number=account_number).first()

    if request.method == 'POST':
        account_number = request.form.get('account-number')
        withdraw_amount = float(request.form.get('withdraw-amount'))
        account = Account.query.filter_by(account_number=account_number).first()
        account_num = session.get('account_number')

        try:
            if account:
                current_balance = account.balance
                if withdraw_amount > current_balance:
                    error_message = "Insufficient balance."
                else:
                    new_balance = current_balance - withdraw_amount
                    account.balance = new_balance
                    db.session.commit()
                    updated_balance = new_balance
                    success_message = f"Withdrawal of {withdraw_amount}FCFA successful😊👍. Updated balance: {updated_balance}FCFA"
                if account_number != account_num:
                    error_message = "Invalid account number."
            else:
                account_number != account_num
                error_message = "Invalid account number."

        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            
            # Add transactions to sender and recipient accounts
        account.add_transaction(+withdraw_amount, f"withdraw  from {account.name} with account number {account_number}")
        # Save changes to the database
        db.session.commit()


    return render_template('withdraw.html',  error_message=error_message, success_message=success_message, account=account, account_number=account_number, balance=account.balance, name=account.name)


@app.route('/deposit', methods=['GET', 'POST'])
def deposit_form():
    error_message = None
    success_message = None
    updated_balance = None
    account_number = session.get('account_number')
    account = Account.query.filter_by(account_number=account_number).first()
    if request.method == 'POST':
        account_number = request.form['account-number']
        deposit_amount = float(request.form['deposit-amount'])
        account = Account.query.filter_by(account_number=account_number).first()
        account_num = session.get('account_number')

        try:
            if account:
                if deposit_amount <= 0:
                    error_message = "Amount needs to be greater than 0."
                else:
                    current_balance = account.balance
                    new_balance = current_balance + deposit_amount
                    account.balance = new_balance
                    db.session.commit()
                    updated_balance = new_balance
                    success_message = f"Deposit of {deposit_amount}FCFA successful😊👍. Updated balance: {updated_balance}FCFA"
                if account_number != account_num:
                    error_message = "Invalid account number."
            else:
                error_message = "Invalid account number."

        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
        # Add transactions to sender and recipient accounts
        account.add_transaction(+deposit_amount, f"Deposit  to {account_number}")
        # Save changes to the database
        db.session.commit()

    return render_template('deposit.html',account=account, account_number=account_number, balance=account.balance, name=account.name, error_message=error_message, success_message=success_message)

#db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
    app.app_context()
    db.create_all()
    app.run(debug=True)

