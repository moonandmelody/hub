import products

# Fixed box configurations for liquid drinks
SMALL_CARTON = 20.5
BIG_CARTON = 23.5
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
        item_name = str(item_name).strip().lower()
        # If the item belongs to a "drinks" or "beverages" parent tag
        if "sipping chocolate" in category_clean or "gourmet tea" in category_clean or "gourmet coffee" in category_clean:
          rules[item_name] = {"type": "liquid"}
              
        elif "sides" in category_clean:
          print(f"item_name is {item_name}", flush=True)
          item_name = str(item_name).strip().lower()
          if "potato pops" in item_name or "garlic breadsticks" in item_name:
            rules[item_name] = {"type": "food","packaging_type":"long_box"}
          else:
            rules[item_name] = {"type": "food","packaging_type":"square_box"}
            
        else:
          print(f"item_name is {item_name}", flush=True)
          item_name = str(item_name).strip().lower()
          if "whipped cream" in item_name:
            rules[item_name] = {"type": "food","packaging_type":"big_dip_cup"}
          else:
            rules[item_name] = {"type": "food","packaging_type":"small_dip_cup"}
          

  print(f"Rules are {rules}",flush=True)
  return rules

# 2. Automatically generate the rules dictionary on import
PACKAGING_RULES = generate_packaging_rules()
