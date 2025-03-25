from behave import given, when, then
from app.eshop import Product

@given('The product with name "Product1" has availability of "{availability}"')
def create_product_with_name(context, availability):
    context.product = Product(name="Product1", price=10.0, available_amount=int(availability))

@when('I check if product is available in amount "{amount}"')
def check_availability(context, amount):
    context.is_available = context.product.is_available(int(amount))

@then("Product is available")
def assert_available(context):
    assert context.is_available == True, "Product should be available"

@then("Product is not available")
def assert_not_available(context):
    assert context.is_available == False, "Product should not be available"
