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
ESSENTIALS = 7.5 # Sugar satchets, stirrer, tissues, fork
MISC = 6

def generate_packaging_rules():
  """
  Dynamically scans products.CATALOG and builds a dictionary matching 
  the rules based on the category parent key.
  """
  rules = {}
  
  for category, items_dict in products.CATALOG.items():
    # Clean the category string to accurately detect drinks
    category_clean = str(category).strip().lower()
    print(f"category_clean is {category_clean}",flush=True)
    if isinstance(items_dict, dict):
      for item_name in items_dict.keys():
        # If the item belongs to a "drinks" or "beverages" parent tag
        if "drink" in category_clean or "beverage" in category_clean:
          rules[item_name] = {"type": "liquid"}
              
        # Otherwise, default the parent association to food packaging rules
        else:
          # Dynamically set packaging fees based on food name keywords
          pack_cost = 10.0  # Default food container baseline fee
          if "burger" in item_name.lower():
              pack_cost = 15.0
          elif "pop" in item_name.lower() or "fry" in item_name.lower():
              pack_cost = 8.0

          rules[item_name] = {
              "type": "food", 
          }
                  
  return rules

# 2. Automatically generate the rules dictionary on import
PACKAGING_RULES = generate_packaging_rules()
