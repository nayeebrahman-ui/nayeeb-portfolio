"""Berlin Cafe & Bistro menu, transcribed from the printed menu (Oct 2026).
Descriptions come from the cafe's own menu booklet where it has one.
"""

COFFEE = {
    "Espresso classics": [
        ("Espresso", 190, 230),
        ("Americano", 220, 300),
        ("Cafe Latte", 260, 360),
        ("Cappuccino", 260, 360),
        ("Affogato", None, 280),
        ("Flavoured Latte", 340, 440),
        ("Cafe / White Mocha", 340, 440),
    ],
    "Froccinos": [
        ("Cafe Latte", 360, 460),
        ("Flavoured Latte", 400, 500),
        ("Shakes", 400, 500),
        ("Cafe / White Mocha", 440, 540),
    ],
    "Iced": [
        ("Iced Americano", 260, 360),
        ("Cold Brew", 280, 400),
        ("Iced Cafe Latte", 300, 400),
        ("Iced Flavoured Latte", 340, 450),
        ("Coconut Brew", None, 400),
        ("Iced Cafe Mocha", 380, 480),
        ("Iced White Mocha", 380, 480),
    ],
}
COFFEE_NOTES = {
    "Espresso classics": "Extra shot 80",
    "Froccinos": "Ice-blended coffee. Extra shot 80, whipped cream 100",
    "Iced": "Extra shot 80",
}
REFRESHERS = [("Fruit Fizz", "Flavoured soda", "320"), ("Mojito", "", "400"), ("Flavoured Iced Tea", "", "300")]
WATER = [("Mineral Water", "", "MRP"), ("Alkaline Water", "", "MRP")]

TEAS = [
    ("Jasmine & White Peach", "Sweet, fruity and aromatic with soft floral notes."),
    ("African Red Rooibos", "Caffeine-free, smooth and naturally sweet."),
    ("Lemongrass, Ginger & Rose", "Caffeine-free, bright and gently warming."),
    ("Blueberry & Mint", "Caffeine-free, cool and fruity."),
    ("Cherry & Rose", "Caffeine-free, soft and floral."),
    ("Raspberry & Blueberry", "A double berry blend, light and low in calories."),
]
TEA_PRICE = 220
TEA_ADDON = "Add honey 40"

BAKERY = {
    "Brownie & Cookie": [
        ("Brownie", 130), ("Choco Brownie", 160), ("Chocolate Chip Cookies", 150),
        ("Choco Lava", 140), ("Choco Lava with Ice Cream", 190), ("Red Velvet Cookie", 150),
    ],
    "Pastry": [
        ("Blueberry Cheesecake", 430), ("American Cheesecake", 360), ("Strawberry Cheesecake", 420),
        ("Oreo Cake", 300), ("Milk Cake", 260), ("Ferrero Cake", 410),
        ("Blueberry & Vanilla", 310), ("Tiramisu", 390),
    ],
    "Donuts & Croissants": [
        ("Croissant", 220), ("Chocolate Croissant", 270), ("Banana Bread", 120),
        ("Chocolate Donut", 190), ("Lemon Donut", 190), ("Mocha Donut", 190),
    ],
}

# name, description, price, image (or None)
APPETIZERS = [
    ("Crispy Chicken Tender", "Six pieces. Juicy chicken in a crisp, flavourful coating with garlic mayonnaise and hot tomato sauce.", 360, "tenders"),
    ("Chicken Cheese Blast", "Five pieces. Ground chicken with fresh herbs and spices, stuffed with mozzarella. Garlic mayonnaise and hot tomato sauce.", 390, "cheese-blast"),
    ("Fish & Chips", "Imported fish, battered and fried, with chips and tartar sauce.", 480, "fish-chips"),
    ("Berlin Special Fish & Chips", "Vetki or coral fish, battered and fried, with chips and tartar sauce.", 650, None),
    ("Bruschetta", "Toasted crusty bread topped with garlic-infused mushrooms and fresh herbs, with fries.", 350, "bruschetta"),
    ("Garlic Mushroom", "", 340, None),
    ("Huns & Kase", "Chicken with melted cheese and mushrooms in a creamy herb sauce.", 390, "huns-kase"),
    ("Chicken & Mushroom Sautéed Vegetables", "Chicken breast and mushrooms sautéed with crisp vegetables in butter and olive oil.", 350, "sauteed"),
    ("German Chicken Schnitzel", "Thin chicken cutlet in flour, egg and breadcrumbs, shallow-fried until golden. Garlic mayonnaise and hot tomato sauce.", 350, "schnitzel"),
    ("French Fry", "Imported French-cut potatoes with garlic mayo, hot tomato sauce and chef's special chaat masala.", 220, "fries"),
]
SANDWICHES = [
    ("Club Sandwich", "Triple-decker with chicken, fried egg, tomato and lettuce, served with golden chips.", 380, "club"),
    ("Chicken Mushroom Supreme", "Chicken, button and shiitake mushrooms, cheese and tomato between three slices of bread, with garlic mayonnaise.", 400, "supreme"),
    ("Berlin Special Tuna Sandwich", "", 450, None),
    ("Tortilla Chicken Wrap", "Grilled chicken breast, cream cheese, lettuce and capsicum rolled in a soft tortilla, with dipping sauce.", 350, "wrap"),
]
SALADS = [
    ("Berlin Special Cashewnut Salad", "Portion 1:2", 550, None),
    ("Healthy Apple Cashewnut Salad", "Portion 1:2", 650, None),
    ("Greek Salad", "Portion 1:2", 550, None),
]
BREAKFAST = [
    ("German Habits", "", 380, None),
    ("English Breakfast", "Eggs with golden yolks, seared sausage, mushrooms, beans and grilled tomato, with buttered toast.", 400, "english-breakfast"),
]

# The owner's favourite framed layout: six featured plates
FEATURED = [
    ("Classic Bruschetta", "Garlic mushrooms and fresh herbs on toasted bread, served with fries", 350, "bruschetta"),
    ("Tortilla Chicken Wrap", "Grilled chicken and fresh veggies in a soft tortilla, with dipping sauce", 350, "wrap"),
    ("Huns & Kase", "Chicken with melted cheese and mushrooms in a creamy herb sauce", 390, "huns-kase"),
    ("Classic Club Sandwich", "Triple-decker with chicken, fried egg, tomato and lettuce, with golden chips", 380, "club"),
    ("Chicken Cheese Blast", "Golden chicken and mozzarella croquettes with garlic mayo", 390, "cheese-blast"),
    ("German Chicken Schnitzel", "Thin breaded chicken cutlet, shallow-fried until golden", 350, "schnitzel"),
]

# Home page signature strip
SIGNATURES = [
    ("Cafe Latte", "Silky milk, a heart on top.", "260", "latte"),
    ("Chicken Cheese Blast", "Mozzarella-stuffed chicken croquettes.", "390", "cheese-blast"),
    ("Huns & Kase", "Chicken, cheese and mushroom cream.", "390", "huns-kase"),
    ("Classic Club Sandwich", "Triple-decker with golden chips.", "380", "club"),
    ("Froccinos & Shakes", "Ice-blended, piled high.", "360", "shakes"),
    ("Classic Bruschetta", "Garlic mushrooms on toasted bread.", "350", "bruschetta"),
    ("English Breakfast", "Eggs, sausage, beans and toast.", "400", "english-breakfast"),
]
