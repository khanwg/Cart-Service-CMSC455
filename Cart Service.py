#CMSC 455
#Wahaaj Khan
#Assignment 2
import requests
from flask import Flask, jsonify
from flask_httpauth import HTTPDigestAuth
from flask_sqlalchemy import SQLAlchemy
from flask import request
import os

#App configuration
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'UNguessable'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'user_cart.sqlite')
db = SQLAlchemy(app)
auth = HTTPDigestAuth()

#Usernames and passwords to access carts
USERS = {
    "happyuser": "P@ssword!",
    "subzero99": "scorpion20!",
    "ashrah0914": "datushA12!",
    "marisagladius": "jamieLuke1!",
    "kenmasters": "middleAged34!",
    "saibot321": "Enenr4h!",
    "mirafulgore": "mayaJago!!"
}


# User Model for db
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(70), unique=True, nullable=False)


# Cart Model for db
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)




@auth.get_password
def get_pw(username):
    if username in USERS:
        return USERS.get(username)
    return None
# Sends requests to product endpoints
def productDataRequest(product_id):
    url = 'https://product-service-wk.onrender.com'
    response = requests.get(f'{url}/products/{product_id}',auth=('khanwg', 'P@ssword!'))

    if response.status_code == 200:
        return response.json().get('product')
    else:
        print(f"No product found for the ID: {product_id}")
        return {}


# Endpoint 1 : Retrieves the current contents of a user's shopping cart
@app.route('/cart/<int:user_id>', methods=['GET'])
@auth.login_required
def getUserCart(user_id):

    loggedInUser = auth.current_user()


    if loggedInUser != User.query.get(user_id).username:
        return jsonify({"error": "Access denied"}), 403
    user = User.query.get(user_id)
    if user:
        cartProducts = Cart.query.filter_by(user_id=user_id).all()
        shopping_cart = []


        response_data = {
            "user_id": user.id,
            "username": user.username,
            "shopping_cart": shopping_cart
        }

        # Gets the product data and adds it to the shopping cart
        for item in cartProducts:
            product_data = productDataRequest(item.product_id)
            print(f"Product Data: {product_data}")  # Print the product_data for debugging
            if product_data:
                shopping_cart.append({
                    "product_id": product_data.get('id'),
                    "name": product_data.get('name'),
                    "quantity": item.quantity
                })


        response_data["shopping_cart"] = shopping_cart

        return jsonify(response_data)
    if not user:
        return jsonify({"error": "User not found"}), 404


# Endpoint 2: Add a specified quantity of a product to the user’s cart.
@app.route('/cart/<int:user_id>/add', methods=['POST'])
@auth.login_required
def add_product_to_cart(user_id):
    loggedInUser = auth.current_user()

    if loggedInUser != User.query.get(user_id).username:
        return jsonify({"error": "Invalid login"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not product_id or not quantity:
        return jsonify({"error": "Please Use a valid product ID and quantity"}), 400

    product_information = productDataRequest(product_id)

    cartItem = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cartItem:
        cartItem.quantity = cartItem.quantity + quantity

    else:
        cartItem = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cartItem)

    db.session.commit()

    return jsonify({"message": "Product has been added to the shopping cart successfully"})


#Endpoint 3: Remove a specified quantity of a product from the user's cart
@app.route('/cart/<int:user_id>/remove', methods=['POST'])
@auth.login_required
def remove_product_from_cart(user_id):
    loggedInUser = auth.current_user()

    if loggedInUser != User.query.get(user_id).username:
        return jsonify({"error": "Access denied"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not product_id or not quantity:
        return jsonify({"error": "Product ID and quantity are required"}), 400

    product_information = productDataRequest(product_id)
    cartItem = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cartItem:

        if cartItem.quantity >= quantity:
            cartItem.quantity -= quantity
            db.session.commit()
            return jsonify({"message": "Product has been removed from the cart successfully"})
        else:
            return jsonify({"error": "Quantity being removed is more than the amount that is currently in the cart"}), 400


if __name__ == '__main__':
    # with app.app_context():
    # db.create_all()
    app.run(port=5001)
