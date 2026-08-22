total_price = 0
discount = 0

def apply_discount(amount):
    global discount, total_price
    discount = amount
    total_price -= discount
    return total_price
