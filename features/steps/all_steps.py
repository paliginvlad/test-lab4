from behave import given, when, then
from app.eshop import Product, ShoppingCart, Order

@given('I create a product with name "{name}", price {price}, and availability {availability}')
def step_create_product(context, name, price, availability):
    try:
        context.product = Product(name=name, price=float(price), available_amount=int(availability))
    except ValueError:
        context.product = None

@then('The product should have name "{name}", price {price}, and availability {availability}')
def step_check_product(context, name, price, availability):
    assert context.product is not None, "Product creation failed"
    assert context.product.name == name, f"Expected name {name}, got {context.product.name}"
    assert context.product.price == float(price), f"Expected price {price}, got {context.product.price}"
    assert context.product.available_amount == int(availability), f"Expected availability {availability}, got {context.product.available_amount}"

@then('The product creation should fail')
def step_product_creation_failed(context):
    assert context.product is None, "Product creation should have failed"

@given('I have an empty shopping cart')
def step_empty_cart(context):
    context.cart = ShoppingCart()

@when('I add the product to the cart in amount {amount}')
def step_add_product_to_cart(context, amount):
    try:
        context.cart.add_product(context.product, int(amount))
        context.add_successfully = True
    except ValueError:
        context.add_successfully = False

@then('The product should be added to the cart successfully')
def step_product_added_successfully(context):
    assert context.add_successfully, "Product should have been added successfully"

@then('The product should not be added to the cart successfully')
def step_product_not_added_successfully(context):
    assert not context.add_successfully, "Product should not have been added successfully"

@when('I remove the product from the cart')
def step_remove_product_from_cart(context):
    context.cart.remove_product(context.product)

@then('The cart should be empty')
def step_cart_is_empty(context):
    assert len(context.cart.products) == 0, "Cart should be empty"

@when('I place an order')
def step_place_order(context):
    context.order = Order()
    context.order.cart = context.cart
    context.order.place_order()

@then('The product availability should be {availability}')
def step_check_product_availability(context, availability):
    assert context.product.available_amount == int(availability), f"Expected availability {availability}, got {context.product.available_amount}"

@when('I check if the product is available in amount {amount}')
def step_check_availability(context, amount):
    context.is_available = context.product.is_available(int(amount))

@then('The product should be available')
def step_product_should_be_available(context):
    assert context.is_available, "Product should be available"

@then('The product should not be available')
def step_product_should_not_be_available(context):
    assert not context.is_available, "Product should not be available"