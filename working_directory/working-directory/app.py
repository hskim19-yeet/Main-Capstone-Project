from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/stockcraft_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    lastname = db.Column(db.String(120), nullable=False)
    firstname = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False) 

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, nullable=False)
    stock_id = db.Column(db.Integer, nullable=False)
 
class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)     
    user_id  = db.Column(db.Integer, nullable=False)
    stock_id = db.Column(db.Integer, nullable=False)
    
class Stock(db.Model):
	stock_id = db.Column(db.String(80), primary_key=True)
	stock_ticker = db.Column(db.String(80), unique=True, nullable=False)
	company = db.Column(db.String(120), unique=True, nullable=False)
	initial_price = db.Column(db.Float, nullable=False)
	available_stocks = db.Column(db.Integer, nullable=False)


    
    
with app.app_context():
    db.create_all()

@app.route("/orders")
def orders():
    orders = Order.query.order_by(Order.order_id.desc()).all()
    return render_template("orders.html", orders=orders)

@app.route("/orders/add/<int:user_id>/<int:stock_id>")
def add_order(user_id, stock_id):
    try:
        o = Order(user_id=user_id, stock_id=stock_id)
        db.session.add(o)
        db.session.commit()
        t = Transaction(
            order_id=o.order_id,
            user_id=user_id,
            stock_id=stock_id,
        )
        db.session.add(t)
        db.session.commit()
        flash("Order added.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding order: {e}")
    return redirect(url_for("orders"))

@app.route("/orders/sell/<int:order_id>")
def sell_order(order_id):
    try:
        o = Order.query.get(order_id)
        if not o:
            flash("Order not found.")
        else:
            db.session.delete(o) 
            db.session.commit()
            flash(f"Order {order_id} sold.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error selling order: {e}")
    return redirect(url_for("orders"))

@app.route("/users")
def users():
    rows = User.query.order_by(User.user_id.desc()).all()
    return render_template("user.html", users=rows)

@app.route('/add_user/<string:username>/<string:email>/<string:lastname>/<string:firstname>/<string:password>')
def add_user(username, email, lastname, firstname, password):
    if not username or not email:
        flash('Both username and email are required!', 'error')
        return redirect(url_for('users'))

    new_user = User(username=username, 
                    email=email,
                    lastname=lastname,
                    firstname=firstname,
                    password=password)

    try:
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {username} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding user: {str(e)}', 'error')

    return redirect(url_for('users'))

@app.route('/stocks')
def stocks():
    stocks = Stock.query.all()
    return render_template('stocks.html', stocks=stocks)

@app.route('/add_stock/<string:stock_id>/<string:stock_ticker>/<string:company>/<float:initial_price>/<int:available_stocks>')
def add_stock(stock_id, stock_ticker, company, initial_price, available_stocks):
    if not (stock_id and stock_ticker and company and initial_price and available_stocks):
        flash('Missing required information!', 'error')
        return redirect(url_for('stocks'))

    new_stock = Stock(stock_id=stock_id, 
                    stock_ticker=stock_ticker,
                    company=company,
                    initial_price=initial_price, 
                    available_stocks=available_stocks,
                    )

    try:
        db.session.add(new_stock)
        db.session.commit()
        flash(f'Stock {stock_id} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding stock: {str(e)}', 'error')

    return redirect(url_for('stocks'))





## Christian's part ##
class CashAccount(db.Model):
    __tablename__ = 'cash_account'
    cash_account_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), unique=True, nullable=False)
    current_balance = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp(), nullable=False)

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    portfolio_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    stock_id = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp(), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_id', name='uq_portfolio_user_stock'),)

with app.app_context():
    db.create_all()

@app.route("/portfolio")
def portfolio_index():
    u = User.query.order_by(User.user_id.asc()).first()
    if not u:
        flash("No users yet.", "error")
        return redirect(url_for("users"))
    return redirect(url_for("portfolio", user_id=u.user_id))

@app.route("/portfolio/<int:user_id>")
def portfolio(user_id):
    user = User.query.get_or_404(user_id)
    acct = CashAccount.query.filter_by(user_id=user_id).first()
    positions = Portfolio.query.filter_by(user_id=user_id).all()
    return render_template("portfolio.html", user=user, acct=acct, positions=positions)

@app.route("/cash_accounts")
def cash_accounts():
    rows = CashAccount.query.order_by(CashAccount.cash_account_id.desc()).all()
    return render_template("cash_account.html", cash_accounts=rows)

@app.route('/add_cash/<int:user_id>/<float:amount>')
def add_cash(user_id, amount):
    acct = CashAccount.query.filter_by(user_id=user_id).first()
    if not acct:
        acct = CashAccount(user_id=user_id, current_balance=amount)
        db.session.add(acct)
    else:
        acct.current_balance = acct.current_balance + amount
    db.session.commit()
    flash(f'Added ${amount:.2f} to cash account.', 'success')
    return redirect(url_for('portfolio', user_id=user_id))

@app.route('/withdraw_cash/<int:user_id>/<float:amount>')
def withdraw_cash(user_id, amount):
    acct = CashAccount.query.filter_by(user_id=user_id).first()
    if acct and acct.current_balance >= amount:
        acct.current_balance = acct.current_balance - amount
        db.session.commit()
        flash(f'Withdrew ${amount:.2f} from cash account.', 'success')
    else:
        flash('Insufficient funds or no account.', 'error')
    return redirect(url_for('portfolio', user_id=user_id))

@app.route('/add_position/<int:user_id>/<int:stock_id>/<int:quantity>')
def add_position(user_id, stock_id, quantity):
    pos = Portfolio.query.filter_by(user_id=user_id, stock_id=stock_id).first()
    if pos:
        pos.quantity = pos.quantity + quantity
    else:
        pos = Portfolio(user_id=user_id, stock_id=stock_id, quantity=quantity)
        db.session.add(pos)
    db.session.commit()
    flash(f'Position updated for stock {stock_id}.', 'success')
    return redirect(url_for('portfolio', user_id=user_id))

@app.route('/delete_position/<int:portfolio_id>')
def delete_position(portfolio_id):
    pos = Portfolio.query.get_or_404(portfolio_id)
    db.session.delete(pos)
    db.session.commit()
    flash('Position deleted.', 'success')
    return redirect(url_for('portfolio', user_id=pos.user_id))



@app.route("/")
def home():
    
    return render_template("home.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/wallet")
def wallet():
    return render_template("wallet.html")

if __name__ == "__main__":
    app.run(debug=True)