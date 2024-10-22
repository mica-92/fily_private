import pandas as pd
import os

# File names
PRODUCTS_FILE = 'products.csv'
AVAILABLE_FILE = 'available.csv'
SOLD_FILE = 'sold.csv'


# Function to add products
def add_product():
    df = pd.read_csv(PRODUCTS_FILE)

    # Input product details
    product_type_input = input("Enter product type (Sneakers, T-Shirts, Hoodies, Jacket, Other): ")
    gender_input = input("Enter gender (Jordans, Women, Men, Kids, No Gender): ")
    
    brand = input("Enter brand: ")
    name = input("Enter name: ")
    color = input("Enter color: ")
    cost = float(input("Enter cost (USD): "))
    expected_price = float(input("Enter expected price (USD): "))
    trip_number = input("Enter trip number: ")
    sizes = input("Enter available sizes (comma separated): ").strip().split(",")

    # Clean sizes and count occurrences
    size_counts = {}
    for size in sizes:
        size = size.strip()  # Clean up size string
        if size in size_counts:
            size_counts[size] += 1  # Increment count if size already exists
        else:
            size_counts[size] = 1  # Initialize count for new size

    # Generate product ID in the format {Type}{Gender}01 (e.g., HW01)
    type_code = product_type_input[0].upper()  # Get the first letter of the type
    gender_code = gender_input[0].upper()  # Get the first letter of the gender
    
    # Find the next number for the ID
    existing_ids = df[df['ID'].str.startswith(f"{type_code}{gender_code}")]['ID']

    if existing_ids.empty:
        new_number = 1  # Start numbering from 1 if none exist
    else:
        existing_numbers = existing_ids.str.extract(r'(\d+)$').astype(int)
        new_number = existing_numbers.max()[0] + 1

    # Format the ID
    product_id = f"{type_code}{gender_code}{new_number:02d}"  # Generate ID like HW01

    # Create a new product entry with the counts in a separate column
    new_product = {
        'ID': product_id,
        'Type': product_type_input,
        'Gender': gender_input,
        'Brand': brand,
        'Name': name,
        'Color': color,
        'Cost (USD)': cost,
        'Expected Price (USD)': expected_price,
        'Trip #': trip_number,
        'Sizes': ', '.join(size_counts.keys()),  # Store sizes as a comma-separated string
        'Count': sum(size_counts.values())  # Store total count
    }

    # Use pd.concat to append the new product
    new_row_df = pd.DataFrame([new_product])
    df = pd.concat([df, new_row_df], ignore_index=True)
    df.to_csv(PRODUCTS_FILE, index=False)
    print(f"Product added with ID: {product_id}")


# Function to process sold items
def process_sold_item():
    available_df = pd.read_csv(PRODUCTS_FILE)  # Load available products from the products file
    sold_df = pd.read_csv(SOLD_FILE)  # Load sold items from the sold file

    product_id = input("Enter product ID sold: ")
    
    # Find the available sizes for the product ID
    available_sizes = available_df[available_df['ID'] == product_id]['Sizes'].values
    if available_sizes.size == 0:
        print("Product ID not found.")
        return
    
    # Display the available sizes in brackets
    sizes_list = available_sizes[0].strip('"').split(',')
    print(f"Available sizes for {product_id}: [{', '.join(size.strip() for size in sizes_list)}]")

    size = input("Enter size sold: ")
    selling_date = input("Enter selling date (YYYY-MM-DD): ")
    final_price = float(input("Enter final price (USD): "))
    customer = input("Enter customer name: ")
    notes = input("Enter notes: ")

    # Check if the product ID and size are available
    sold_item = available_df[(available_df['ID'] == product_id) & (available_df['Sizes'].str.contains(size))]
    
    if sold_item.empty:
        print("Item not available in the specified size.")
        return

    # Update sold items DataFrame
    sold_entry = {
        **sold_item.iloc[0].to_dict(),
        'Selling Date': selling_date,
        'Final Price': final_price,
        'Customer': customer,
        'Notes': notes,
        'Size Sold': size  # Store the sold size
    }

    # Convert sold_entry to DataFrame and concatenate
    sold_entry_df = pd.DataFrame([sold_entry])
    sold_df = pd.concat([sold_df, sold_entry_df], ignore_index=True)
    sold_df.to_csv(SOLD_FILE, index=False)

    # Update available items: Decrease the count for the sold size
    available_df.loc[(available_df['ID'] == product_id), 'Count'] -= 1  # Decrement the count by 1
    
    # If count becomes zero, remove that size from the Sizes column
    if available_df.loc[available_df['ID'] == product_id, 'Count'].values[0] <= 0:
        available_df.loc[(available_df['ID'] == product_id), 'Sizes'] = available_df['Sizes'].apply(
            lambda x: ', '.join([s.strip() for s in x.split(',') if s.strip() != size])
        )
    
    # Update counts
    available_df['Count'] = available_df['Count'].clip(lower=0)  # Ensure no negative counts
    
    # Remove entries where count is zero
    available_df = available_df[available_df['Count'] > 0]
    
    available_df.to_csv(PRODUCTS_FILE, index=False)  # Save changes to the available products
    print("Item processed and recorded as sold.")


# Function to calculate expected profit
def calculate_expected_profit():
    df = pd.read_csv(PRODUCTS_FILE)
    
    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Group by Trip # and aggregate costs and expected prices
    profit_summary = df.groupby('Trip #').agg(
        Gross_Cost=('Cost (USD)', 'sum'),
        Expected_Selling_Price=('Expected Price (USD)', 'sum'),
        Number_of_Products=('ID', 'count')  # Count all entries
    ).reset_index()

    # Calculate Expected Profit
    profit_summary['Expected_Profit'] = profit_summary['Expected_Selling_Price'] - profit_summary['Gross_Cost']
    
    # Print the summary
    print(profit_summary)


# Function to calculate net profit based on sales period
def calculate_net_profit(start_date, end_date):
    sold_df = pd.read_csv(SOLD_FILE)
    sold_df['Selling Date'] = pd.to_datetime(sold_df['Selling Date'])

    filtered_sales = sold_df[(sold_df['Selling Date'] >= start_date) & (sold_df['Selling Date'] <= end_date)]
    
    total_cost = sum(filtered_sales['Cost (USD)'])
    total_revenue = sum(filtered_sales['Final Price'])
    net_profit = total_revenue - total_cost
    number_of_products = len(filtered_sales)

    print(f"Net Profit: {net_profit}, Number of Products Sold: {number_of_products}")

# Function to view available products
def view_available_products():
    df = pd.read_csv(PRODUCTS_FILE)

    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Initialize 'Count' based on the sizes
    df['Count'] = df['Sizes'].apply(lambda x: len(x.split(',')))  # Count the number of sizes available

    # Initialize a list to collect available products
    available_products = []

    for index, row in df.iterrows():
        sizes = row['Sizes'].split(",")  # Split sizes into a list and strip whitespace
        size_count = {size.strip(): sizes.count(size.strip()) for size in sizes}  # Count occurrences of each size

        for size, count in size_count.items():
            available_products.append({
                'ID': row['ID'],
                'Type': row['Type'],
                'Gender': row['Gender'],
                'Brand': row['Brand'],
                'Name': row['Name'],
                'Color': row['Color'],
                'Cost (USD)': row['Cost (USD)'],
                'Expected Price (USD)': row['Expected Price (USD)'],
                'Trip #': row['Trip #'],
                'Sizes': ', '.join(size_count.keys()),  # Store unique sizes without extra characters
                'Available Size': size.strip(),  # Include the available size
                'Count': count  # Show the correct count
            })

    # Create a DataFrame from the available products
    available_df = pd.DataFrame(available_products)

    # Display the available products
    print(available_df)

    return available_df  # Return the DataFrame for further use


# Function to generate HTML page for products
def generate_html(df, filename='products.html'):
    # Create a DataFrame to hold unique products and their sizes
    unique_products = {}

    for _, row in df.iterrows():
        product_id = row['ID']
        size = row['Available Size']
        
        if product_id not in unique_products:
            unique_products[product_id] = {
                'Type': row['Type'],
                'Brand': row['Brand'],
                'Name': row['Name'],
                'Color': row['Color'],
                'Cost (USD)': row['Cost (USD)'],
                'Expected Price (USD)': row['Expected Price (USD)'],
                'Trip #': row['Trip #'],
                'Sizes': [size],  # Start with the first size
                'Image': f"images/{product_id}.png"  # Path to the image
            }
        else:
            # If the product already exists, add the size to the list if not already present
            if size not in unique_products[product_id]['Sizes']:
                unique_products[product_id]['Sizes'].append(size)

    # Debugging: Print the unique products dictionary
    print("Unique Products Dictionary:")
    for product_id, details in unique_products.items():
        print(f"Product ID: {product_id}, Details: {details}")

    # Start generating the HTML
    with open(filename, 'w') as f:
        f.write("<html><body><h1>Available Products</h1>\n")
        for product_id, details in unique_products.items():
            f.write(f"<div>\n")
            f.write(f"<img src='{details['Image']}' alt='{details['Name']}' style='width:200px;'><br>\n")
            f.write(f"Brand: {details['Brand']}<br>\n")
            f.write(f"Type: {details['Type']}<br>\n")
            f.write(f"Color: {details['Color']}<br>\n")
            f.write(f"Price: ${details['Expected Price (USD)']} USD<br>\n")
            f.write(f"Available Sizes: {', '.join(details['Sizes'])}(ALOHA)<br>\n")
            f.write("</div><br><br>\n")
        f.write("</body></html>\n")

    print(f"HTML file {filename} generated successfully.")

# Function to search available items
def search_available_items():
    df = pd.read_csv(AVAILABLE_FILE)
    search_term = input("Enter search term (leave blank for all items): ")
    filtered_df = df[df['Name'].str.contains(search_term, case=False) | (search_term == '')]

    print(filtered_df)

    # Generate HTML for search results
    html_content = "<html><body><h1>Search Results</h1><table border='1'>"
    html_content += "<tr><th>ID</th><th>Name</th><th>Available Sizes</th><th>Price</th><th>Image</th></tr>"

    for index, row in filtered_df.iterrows():
        sizes = ", ".join(row['Sizes'])
        image_path = f"{row['ID']}.png"
        html_content += f"<tr><td>{row['ID']}</td><td>{row['Name']}</td><td>{sizes}</td><td>{row['Expected Price (USD)']}</td><td><img src='{image_path}' alt='{row['Name']}' width='100'/></td></tr>"

    html_content += "</table></body></html>"

    with open('search_results.html', 'w') as f:
        f.write(html_content)

    print("Search results HTML file created.")

# Function to view sales records
def view_sales_records():
    sold_df = pd.read_csv(SOLD_FILE)
    print(sold_df)


# Main menu function
def main_menu():
    while True:
        print("\nMenu:")
        print("1. Add Product")
        print("2. View Available Products")
        print("3. Process Sold Item")
        print("4. Calculate Expected Profit")
        print("5. Calculate Net Profit by Period")
        print("6. Create HTML Report of Available Items")
        print("7. Search Available Items")
        print("8. View Sales Records")
        print("9. Exit")

        choice = input("Choose an option: ")
        
        if choice == '1':
            add_product()
        elif choice == '2':
            available_df = view_available_products()  # Save the DataFrame for use later
        elif choice == '3':
            process_sold_item()
        elif choice == '4':
            calculate_expected_profit()
        elif choice == '5':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            calculate_net_profit(start_date, end_date)
        elif choice == '6':
            generate_html(available_df)  # Pass the available DataFrame to the generate_html function
        elif choice == '7':
            search_available_items()
        elif choice == '8':
            view_sales_records()
        elif choice == '9':
            break
        else:
            print("Invalid choice. Please try again.")



# Run the main menu
if __name__ == "__main__":
    # Create empty CSV files if they do not exist
    if not os.path.exists(PRODUCTS_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes']).to_csv(PRODUCTS_FILE, index=False)
    if not os.path.exists(AVAILABLE_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes']).to_csv(AVAILABLE_FILE, index=False)
    if not os.path.exists(SOLD_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Selling Date', 'Final Price', 'Customer', 'Notes']).to_csv(SOLD_FILE, index=False)

    main_menu()
