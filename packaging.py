import products
# Fixed box configurations for liquid drinks
SMALL_CARTON_COST = 20.5
BIG_CARTON_COST = 23.5
LONG_BOX_WITH_WINDOW = 15.5
SQUARE_BOX = 15.5
BIG_DIP_CUP = 3
SMALL_DIP_CUP = 2.5
STICKER = 1.5
RIPPLE_CUP = 3
CARRY_BAG = 2
MISC = 6
  
# Direct item-to-profile mapping
PACKAGING_RULES = {
  # Liquid Drinks
  "Midnight Luxe": {
    "type": "liquid"
  },
  "Moon Dance": {
    "type": "liquid"
  },
  "Midnight Luxe Vegan": {
    "type": "liquid"
  },
    
  # Food Items (Maps flat individual packaging rates)
  "Potato Pops": {"type": "food", "pack_cost": 10.0},
  "Classic Burger": {"type": "food", "pack_cost": 15.0}
}
