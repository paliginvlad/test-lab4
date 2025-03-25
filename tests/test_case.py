import unittest
from app.eshop import Product, ShoppingCart, Order
from unittest.mock import MagicMock


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()

    def tearDown(self):
        self.cart.remove_product(self.product)

    def test_mock_add_product(self):
        self.product.is_available = MagicMock()
        self.cart.add_product(self.product, 12345)
        self.product.is_available.assert_called_with(12345)
        self.product.is_available.reset_mock()

    def test_add_available_amount(self):
        self.cart.add_product(self.product, 11)
        self.assertEqual(self.cart.contains_product(self.product), True, 'Продукт успішно доданий до корзини')

    def test_add_non_available_amount(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.product, 22)
        self.assertEqual(self.cart.contains_product(self.product), False, 'Продукт не доданий до корзини')

    # Нові тести
    def test_product_buy_reduces_amount(self):
        initial_amount = self.product.available_amount
        self.product.buy(5)
        self.assertEqual(self.product.available_amount, initial_amount - 5,
                         'Кількість товару має зменшитися після покупки')

    def test_cart_calculate_total_empty(self):
        total = self.cart.calculate_total()
        self.assertEqual(total, 0, 'Сума порожньої корзини має бути 0')

    def test_cart_calculate_total_with_product(self):
        self.cart.add_product(self.product, 2)
        expected_total = self.product.price * 2
        self.assertEqual(self.cart.calculate_total(), expected_total,
                         'Сума корзини має відповідати ціні товару * кількість')

    def test_remove_non_existent_product(self):
        non_existent_product = Product(name='NonExistent', price=10.0, available_amount=10)
        self.cart.remove_product(non_existent_product)
        self.assertFalse(self.cart.contains_product(non_existent_product),
                         'Видалення неіснуючого продукту не повинно викликати помилок')

    def test_product_equality_by_name(self):
        product1 = Product(name='Test', price=10.0, available_amount=5)
        product2 = Product(name='Test', price=20.0, available_amount=10)
        self.assertEqual(product1, product2, 'Продукти з однаковими назвами мають бути рівні')

    def test_product_inequality_by_name(self):
        product1 = Product(name='Test1', price=10.0, available_amount=5)
        product2 = Product(name='Test2', price=10.0, available_amount=5)
        self.assertNotEqual(product1, product2, 'Продукти з різними назвами не мають бути рівні')

    def test_add_zero_amount_to_cart(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.product, 0)
        self.assertFalse(self.cart.contains_product(self.product), 'Додавання 0 кількості має викликати помилку')

    def test_submit_cart_reduces_product_amount(self):
        initial_amount = self.product.available_amount
        self.cart.add_product(self.product, 5)
        self.cart.submit_cart_order()
        self.assertEqual(self.product.available_amount, initial_amount - 5,
                         'Кількість товару має зменшитися після оформлення замовлення')

    def test_cart_multiple_products_total(self):
        product2 = Product(name='Test2', price=50.0, available_amount=10)
        self.cart.add_product(self.product, 2)
        self.cart.add_product(product2, 3)
        expected_total = (self.product.price * 2) + (product2.price * 3)
        self.assertEqual(self.cart.calculate_total(), expected_total, 'Сума має враховувати кілька продуктів')


if __name__ == '__main__':
    unittest.main()