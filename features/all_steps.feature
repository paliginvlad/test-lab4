Feature: Comprehensive testing of Product, ShoppingCart, and Order classes

  Scenario: Product creation with valid parameters
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    Then The product should have name "Laptop", price 1000.0, and availability 10

  Scenario: Product creation with invalid price (negative value)
    Given I create a product with name "Laptop", price -1000.0, and availability 10
    Then The product creation should fail

  Scenario: Product creation with invalid availability (negative value)
    Given I create a product with name "Laptop", price 1000.0, and availability -10
    Then The product creation should fail

  Scenario: Check product availability with sufficient stock
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    When I check if the product is available in amount 5
    Then The product should be available

  Scenario: Check product availability with insufficient stock
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    When I check if the product is available in amount 15
    Then The product should not be available

  Scenario: Add product to cart with valid amount
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    And I have an empty shopping cart
    When I add the product to the cart in amount 5
    Then The product should be added to the cart successfully

  Scenario: Add product to cart with invalid amount (more than available)
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    And I have an empty shopping cart
    When I add the product to the cart in amount 15
    Then The product should not be added to the cart successfully

  Scenario: Remove product from cart
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    And I have an empty shopping cart
    And I add the product to the cart in amount 5
    When I remove the product from the cart
    Then The cart should be empty

  Scenario: Submit order with products in cart
    Given I create a product with name "Laptop", price 1000.0, and availability 10
    And I have an empty shopping cart
    And I add the product to the cart in amount 5
    When I place an order
    Then The cart should be empty
    And The product availability should be 5

  Scenario: Submit order with empty cart
    Given I have an empty shopping cart
    When I place an order
    Then The cart should remain empty