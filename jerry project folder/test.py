from db_service import init_db, add_or_update_property, get_all_properties, delete_property

# Step 1: Init DB
init_db()

# Step 2: Add or Update properties
add_or_update_property("123 Main St, Toronto", "$250,000", "1800 sqft", "Heating: Yes | Cooling: Yes")
add_or_update_property("456 King St, Montreal", "$350,000", "2200 sqft", "Heating: Yes | Cooling: No")

# Step 3: Show all properties
df = get_all_properties()
print("Current Properties:")
print(df)

# Step 4: Delete one property
delete_property("123 Main St, Toronto")

# Step 5: Show properties after delete
df = get_all_properties()
print("After Delete:")
print(df)
