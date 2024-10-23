import pandas as pd
import os
import shutil

import subprocess


# File names
PRODUCTS_FILE = 'products.csv'
AVAILABLE_FILE = 'available.csv'
SOLD_FILE = 'sold.csv'

# File paths and GitHub repository info
GITHUB_PUBLIC_REPO = "https://github.com/mica-92/fily.git"
GITHUB_PRIVATE_REPO = "https://github.com/mica-92/fily_private.git"


# Function to add products
def add_product():
    df = pd.read_csv(PRODUCTS_FILE)

    # Input product details
    print("\nTypes: type (S = Sneakers, T = T-Shirts, H = Hoodies, J = Jacket, O = Other)")
    product_type_input = input("Enter product type: ")
    print("\nTypes: type (J = Jordans, W = Women, M = Men, K = Kids, NG = No Gender)")
    gender_input = input("Enter Gender: ")
    
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

    # Use pd.concat to append the new product
    new_row_df = pd.DataFrame([{
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
    }])
    
    df = pd.concat([df, new_row_df], ignore_index=True)
    df.to_csv(PRODUCTS_FILE, index=False)
    print(f"Product added with ID: {product_id}")

    # Also add to available products
    available_df = pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Count'])

    for size, count in size_counts.items():
        available_product = {
            'ID': product_id,
            'Type': product_type_input,
            'Gender': gender_input,
            'Brand': brand,
            'Name': name,
            'Color': color,
            'Cost (USD)': cost,
            'Expected Price (USD)': expected_price,
            'Trip #': trip_number,
            'Sizes': size,  # Store each size in a new row
            'Count': count  # Store the count for this size
        }
        available_df = pd.concat([available_df, pd.DataFrame([available_product])], ignore_index=True)

    # Write to available.csv
    if os.path.exists(AVAILABLE_FILE):
        existing_available_df = pd.read_csv(AVAILABLE_FILE)
        available_df = pd.concat([existing_available_df, available_df], ignore_index=True)

    available_df.to_csv(AVAILABLE_FILE, index=False)

# Function to process sold items
def process_sold_item():
    available_df = pd.read_csv(AVAILABLE_FILE)  # Load available products from the available file
    sold_df = pd.read_csv(SOLD_FILE)  # Load sold items from the sold file

    product_id = input("Enter product ID sold: ")
    
    # Find the available sizes for the product ID
    available_sizes = available_df[available_df['ID'] == product_id]['Sizes'].values
    if available_sizes.size == 0:
        print("Product ID not found.")
        return
    
    # Display the available sizes
    sizes_list = available_sizes.tolist()
    print(f"Available sizes for {product_id}: [{', '.join(size.strip() for size in sizes_list)}]")

    size = input("Enter size sold: ")
    selling_date = input("Enter selling date (YYYY-MM-DD): ")
    final_price = float(input("Enter final price (USD): "))
    customer = input("Enter customer name: ")
    notes = input("Enter notes: ")

    # Check if the product ID and size are available
    sold_item = available_df[(available_df['ID'] == product_id) & (available_df['Sizes'] == size)]
    
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
    available_df.loc[(available_df['ID'] == product_id) & (available_df['Sizes'] == size), 'Count'] -= 1  # Decrement the count by 1
    
    # Remove entries where count is zero
    available_df = available_df[available_df['Count'] > 0]

    # Save changes to available products
    available_df.to_csv(AVAILABLE_FILE, index=False)
    print("Item processed and recorded as sold.")

# Function to calculate expected profit
def calculate_expected_profit():
    df = pd.read_csv(PRODUCTS_FILE)
    
    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Calculate the number of products based on the sizes
    df['Number_of_Products'] = df['Sizes'].apply(lambda x: len(x.split(',')))  # Count the number of sizes available
    df['Gross_Cost'] = df['Cost (USD)'] * df['Number_of_Products']  # Calculate gross cost
    df['Expected_Selling_Price'] = df['Expected Price (USD)'] * df['Number_of_Products']  # Calculate expected selling price

    # Group by Trip # and aggregate costs and expected prices
    profit_summary = df.groupby('Trip #').agg(
        Gross_Cost=('Gross_Cost', 'sum'),
        Expected_Selling_Price=('Expected_Selling_Price', 'sum'),  # Use the updated expected selling price
        Number_of_Products=('Number_of_Products', 'sum')  # Total number of products based on sizes
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

def generate_html(df, filename='index.html', include_price=False):
    # Create a DataFrame to hold unique products and their sizes
    unique_products = {}

    # Sort the products based on the specified order: S, J, H, T, O
    type_order = ['S', 'J', 'H', 'T', 'O']
    
    # Sort the dataframe by Type using a categorical type for the order
    df['Type'] = pd.Categorical(df['Type'], categories=type_order, ordered=True)
    df = df.sort_values('Type')  # Sort the DataFrame by Type

    for _, row in df.iterrows():
        product_id = row['ID']
        
        if product_id not in unique_products:
            unique_products[product_id] = {
                'Type': row['Type'],
                'Brand': row['Brand'],
                'Name': row['Name'],
                'Color': row['Color'],
                'Expected Price (USD)': row['Expected Price (USD)'],
                'Sizes': [row['Sizes']],  # Convert sizes
                'Image': f"images/{product_id}.png"  # Path to the image
            }
        else:
            # If the product already exists, add the sizes to the list if not already present
            if row['Sizes'] not in unique_products[product_id]['Sizes']:
                unique_products[product_id]['Sizes'].append(row['Sizes'])
    
    # Start generating the HTML
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"""<html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>fily Importados</title>

            <!-- Favicon -->
            <link rel="icon" href="favicon.ico" type="image/x-icon">

            <!-- Google Fonts -->
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica:ital@0;1&family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900&display=swap" rel="stylesheet">

            <style>
                body {{
                    font-family: 'Roboto', sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                    color: #333;
                }}

                header {{
                    color: black;
                    padding: 20px;
                    text-align: center;
                }}

                header h1 {{
                    font-family: 'IM Fell DW Pica', serif;
                    font-size: 3.5em;
                    margin: 0;
                }}

                header h2 {{
                    font-family: 'IM Fell DW Pica', serif;
                    font-size: 1.5em;
                    margin: 20px 0;
                }}

                .social-media-icons {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                }}

                .social-media-icons img {{
                    width: 30px;
                    height: auto;
                }}

                .info-bar {{
                    padding: 10px;
                    text-align: center;
                    margin-top: 10px;
                    font-size: 0.9em;
                    display: inline-block;
                    width: 50%;
                    border-top: 1px solid #333;
                    border-bottom: 1px solid #333;
                }}

                .filter-menu {{
                    text-align: center;
                    margin-bottom: 20px;
                }}

                .filter-menu button {{
                    padding: 5px 10px;
                    border: 1px solid black;
                    border-radius: 5px;
                    background-color: white;
                    color: black;
                    font-size: 1em;
                    margin: 5px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }}

                .filter-menu button:hover {{
                    background-color: #f0f0f0;
                }}

                .product-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around;
                    padding: 20px;
                }}

                .product {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    margin: 20px;
                    padding: 20px;
                    width: calc(25% - 40px);
                    text-align: center;
                    transition: transform 0.2s;
                    display: none;  /* Initially hide all products */
                }}

                .product.show {{
                    display: block;  /* Only show filtered products */
                }}

                .product:hover {{
                    transform: scale(1.05);
                }}

                .product img {{
                    width: 100%;
                    height: auto;
                    max-width: 300px;
                    object-fit: cover;
                    object-position: center;
                    border-bottom: 2px solid black;
                    display: block;
                    margin: 0 auto;
                }}

                .product h3 {{
                    font-family: 'Roboto', sans-serif;
                    font-size: 1.2em;
                    margin: 15px 0;
                }}

                .product p {{
                    font-family: 'Roboto', sans-serif;
                    font-size: 1em;
                    margin: 5px 0;
                }}

                .product-id {{
                    font-size: 1em;
                    margin: 5px 0;
                    font-weight: bold;
                }}

                .price {{
                    font-size: 1.2em;
                    margin: 10px 0;
                    font-weight: bold;
                }}

                .sizes-container {{
                    display: flex;
                    justify-content: center;
                    gap: 5px;
                    margin-top: 10px;
                }}

                .size {{
                    padding: 5px 10px;
                    border: 1px solid black;
                    border-radius: 5px;
                    font-size: 1em;
                    background-color: white;
                    color: black;
                }}

                footer {{
                    background-color: #333;
                    color: white;
                    padding: 5px;
                    font-size: 0.6em;
                    text-align: center;
                    position: fixed;
                    width: 100%;
                    bottom: 0;
                }}

                footer a {{
                    color: white;
                    font-weight: bold;
                }}

                @media (max-width: 768px) {{
                    .product {{
                        width: calc(50% - 40px);
                    }}

                    .info-bar {{
                        width: 90%;
                    }}

                    .product img {{
                        max-width: 100%;
                    }}
                }}

                @media (max-width: 500px) {{
                    .product {{
                        width: calc(100% - 40px);
                    }}

                    .info-bar {{
                        width: 90%;
                    }}
                }}
            </style>
            <script>
                function openPopup() {{
                    window.open('sizes.png', 'popup', 'width=600,height=600');
                }}

                // JavaScript function to filter products by type
                function filterProducts(type) {{
                    const products = document.querySelectorAll('.product');
                    products.forEach(product => {{
                        if (product.classList.contains(type) || type === 'all') {{
                            product.classList.add('show');
                        }} else {{
                            product.classList.remove('show');
                        }}
                    }});
                }}

                // Automatically show all products on page load
                window.onload = function() {{
                    filterProducts('all');
                }}
            </script>
        </head>
        <body>

            <header>
                <h1>fily</h1>
                <h2> productos de USA a ARG </h2> 
                <div class="social-media-icons">
                    <a href="https://www.instagram.com/fily.importados/">
                        <img src="instagram.png" alt="Instagram"> 
                    </a>
                    <a href="https://api.whatsapp.com/send?phone=5491122887256">
                        <img src="whatsapp.png" alt="WhatsApp">
                    </a>
                </div>
            </header>

            <div class="filter-menu">
                <button onclick="filterProducts('all')">Todos</button>
                <button onclick="filterProducts('T')">Remeras</button>
                <button onclick="filterProducts('S')">Jordan</button>
                <button onclick="filterProducts('H')">Buzos</button>
                <button onclick="filterProducts('J')">Camperas</button>
                <button onclick="filterProducts('O')">Accesorios</button>
            </div>

            <div class="product-container">
        """)

        for product_id, details in unique_products.items():
            sizes_html = ''.join([f"<span class='size'>{size}</span>" for size in details['Sizes']])
            price_without_decimal = int(details['Expected Price (USD)'])
            price_ars = price_without_decimal * 1100  # ARS price conversion

            # Include price only if requested (catalogue mode)
            price_html = f"""
                <p class='price'>${price_without_decimal} USD</p>
                <p class='price'>${price_ars:,} ARS</p>
            """ if include_price else ""

            f.write(f"""
                <div class="product {details['Type']}">  <!-- Add product type as a class for filtering -->
                    <img src='{details['Image']}' alt='{details['Name']}'>
                    <h3>{details['Name']}</h3>
                    <p class="product-id">Código: {product_id}</p>
                    {price_html}
                    <div class="sizes-container">
                        {sizes_html}
                    </div>
                </div>
            """)

        f.write("""
            </div>
            <footer>
                <p>Los talles de las zapatillas son de US Men.<br>  
                    <a href="javascript:void(0)" onclick="openPopup()">Tabla de Conversiones</a>.</p>
            </footer>
        </body>
        </html>
        """)

    print(f"HTML file {filename} generated successfully.")


# Function to create both internal and catalogue versions
def create_html_files(df):
    # Create the internal (without price) version
    generate_html(df, filename='index.html', include_price=False)
    
    # Create the catalogue (with price) version
    generate_html(df, filename='catalogue.html', include_price=True)

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

# Function to view available products
def view_available_products():
    df = pd.read_csv(AVAILABLE_FILE)  # Load from available.csv

    # Ensure 'Sizes' column is treated as a string
    df['Sizes'] = df['Sizes'].astype(str)

    # Initialize a list to collect available products
    available_products = []

    for index, row in df.iterrows():
        size = row['Sizes']  # Use the size directly
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
            'Sizes': size,  # Show the available size
            'Count': row['Count']  # Show the count for this size
        })

    # Create a DataFrame from the available products
    available_df = pd.DataFrame(available_products)

    # Display the available products
    print(available_df)

    return available_df  # Return the DataFrame for further use

# Function to modify a product
def modify_product():
    df = pd.read_csv(PRODUCTS_FILE)
    
    product_id = input("Enter the product ID to modify: ")
    
    if product_id not in df['ID'].values:
        print("Product ID not found.")
        return
    
    # Display the current product details
    current_product = df[df['ID'] == product_id].iloc[0]
    print(f"\nCurrent details for product {product_id}:")
    print(current_product)
    
    # Get the new values from the user (or leave unchanged if they press Enter)
    new_type = input(f"Enter new type ({current_product['Type']}): ") or current_product['Type']
    new_gender = input(f"Enter new gender ({current_product['Gender']}): ") or current_product['Gender']
    new_brand = input(f"Enter new brand ({current_product['Brand']}): ") or current_product['Brand']
    new_name = input(f"Enter new name ({current_product['Name']}): ") or current_product['Name']
    new_color = input(f"Enter new color ({current_product['Color']}): ") or current_product['Color']
    new_cost = input(f"Enter new cost ({current_product['Cost (USD)']}): ") or current_product['Cost (USD)']
    new_price = input(f"Enter new expected price ({current_product['Expected Price (USD)']}): ") or current_product['Expected Price (USD)']
    new_sizes = input(f"Enter new sizes ({current_product['Sizes']}): ") or current_product['Sizes']
    new_trip_number = input(f"Enter new trip number ({current_product['Trip #']}): ") or current_product['Trip #']
    
    # Update the product in the DataFrame
    df.loc[df['ID'] == product_id, ['Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Sizes', 'Trip #']] = \
        [new_type, new_gender, new_brand, new_name, new_color, float(new_cost), float(new_price), new_sizes, new_trip_number]
    
    # Save the updated DataFrame
    df.to_csv(PRODUCTS_FILE, index=False)
    print(f"Product {product_id} updated successfully.")
    
    # Now update available.csv
    available_df = pd.read_csv(AVAILABLE_FILE)
    
    # Remove the old entries for the product in available.csv
    available_df = available_df[available_df['ID'] != product_id]
    
    # Add updated product sizes and counts back into available.csv
    size_counts = {size.strip(): new_sizes.split(',').count(size.strip()) for size in new_sizes.split(',')}
    
    # Create a list of new rows to add
    new_rows = []
    for size, count in size_counts.items():
        new_rows.append({
            'ID': product_id,
            'Type': new_type,
            'Gender': new_gender,
            'Brand': new_brand,
            'Name': new_name,
            'Color': new_color,
            'Cost (USD)': float(new_cost),
            'Expected Price (USD)': float(new_price),
            'Trip #': new_trip_number,
            'Sizes': size,
            'Count': count
        })
    
    # Concatenate the new rows to the available DataFrame
    available_df = pd.concat([available_df, pd.DataFrame(new_rows)], ignore_index=True)
    
    # Save the updated available_df to available.csv
    available_df.to_csv(AVAILABLE_FILE, index=False)
    print(f"Product {product_id} updated in available.csv successfully.")

# Function to delete a product
def delete_product():
    df = pd.read_csv(PRODUCTS_FILE)
    
    product_id = input("Enter the product ID to delete: ")
    
    if product_id not in df['ID'].values:
        print("Product ID not found.")
        return
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete product {product_id}? (y/n): ").lower()
    if confirm != 'y':
        print("Deletion canceled.")
        return
    
    # Remove the product from the DataFrame
    df = df[df['ID'] != product_id]
    df.to_csv(PRODUCTS_FILE, index=False)
    print(f"Product {product_id} deleted from products.csv.")
    
    # Now remove the product from available.csv
    available_df = pd.read_csv(AVAILABLE_FILE)
    available_df = available_df[available_df['ID'] != product_id]
    available_df.to_csv(AVAILABLE_FILE, index=False)
    print(f"Product {product_id} deleted from available.csv.")

# Function to modify a sale
def modify_sale():
    sold_df = pd.read_csv(SOLD_FILE)
    
    product_id = input("Enter the product ID of the sale to modify: ")
    
    # Check if the product exists in sold.csv
    if product_id not in sold_df['ID'].values:
        print("Product ID not found in sales records.")
        return
    
    # Display the current sale record
    current_sale = sold_df[sold_df['ID'] == product_id].iloc[0]
    print(f"\nCurrent details for sale of product {product_id}:")
    print(current_sale)
    
    # Get the new sale values from the user
    new_size_sold = input(f"Enter new size sold ({current_sale['Size Sold']}): ") or current_sale['Size Sold']
    new_selling_date = input(f"Enter new selling date ({current_sale['Selling Date']}): ") or current_sale['Selling Date']
    new_final_price = input(f"Enter new final price ({current_sale['Final Price']}): ") or current_sale['Final Price']
    new_customer = input(f"Enter new customer name ({current_sale['Customer']}): ") or current_sale['Customer']
    new_notes = input(f"Enter new notes ({current_sale['Notes']}): ") or current_sale['Notes']
    
    # Update the sale in the DataFrame
    sold_df.loc[sold_df['ID'] == product_id, ['Size Sold', 'Selling Date', 'Final Price', 'Customer', 'Notes']] = \
        [new_size_sold, new_selling_date, float(new_final_price), new_customer, new_notes]
    
    # Save the updated DataFrame
    sold_df.to_csv(SOLD_FILE, index=False)
    print(f"Sale record for product {product_id} updated successfully.")

# Function to push files to GitHub
def git_push(repo_url, commit_message):
    """
    Executes git commands to push changes to the specified repository.
    """
    subprocess.run(['git', 'init'])
    subprocess.run(['git', 'remote', 'remove', 'origin'], stderr=subprocess.DEVNULL)  # Remove existing remote if it exists
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', commit_message])
    subprocess.run(['git', 'branch', '-M', 'main'])
    subprocess.run(['git', 'remote', 'add', 'origin', repo_url])
    subprocess.run(['git', 'push', '-u', 'origin', 'main', '--force'])

# Function to generate HTML files and push to GitHub
def create_html_and_push(df):
    # Create the public (index.html) and private (catalogue.html) versions
    generate_html(df, filename='index.html', include_price=False)
    generate_html(df, filename='catalogue.html', include_price=True)

    # --- Push to the public repository (fily) ---
    public_repo_folder = 'fily_public'
    if not os.path.exists(public_repo_folder):
        os.makedirs(public_repo_folder)
    if not os.path.exists(os.path.join(public_repo_folder, 'images')):
        os.makedirs(os.path.join(public_repo_folder, 'images'))

    # Copy index.html and images to the public folder using shutil
    shutil.copy('index.html', public_repo_folder)
    shutil.copytree('images', os.path.join(public_repo_folder, 'images'), dirs_exist_ok=True)

    # Change directory to the public repository folder and push
    os.chdir(public_repo_folder)
    git_push(GITHUB_PUBLIC_REPO, "Update public index.html")
    os.chdir("..")  # Go back to the root directory

    # --- Move catalogue.html to /docs and rename it to index.html ---
    docs_folder = 'docs'
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)

    # Rename and move catalogue.html to docs/index.html
    shutil.move('catalogue.html', os.path.join(docs_folder, 'index.html'))

    # --- Push to the private repository (fily_private) ---
    private_repo_folder = 'fily_private'
    if not os.path.exists(private_repo_folder):
        os.makedirs(private_repo_folder)

    # Copy all files to the private folder, excluding .git folder, public files, and docs
    shutil.copytree('.', private_repo_folder, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', 'fily_public', 'fily_private', 'docs'))

    # Copy the /docs folder into the private folder to upload it as well
    shutil.copytree(docs_folder, os.path.join(private_repo_folder, 'docs'), dirs_exist_ok=True)

    # Change directory to the private repository folder and push
    os.chdir(private_repo_folder)
    git_push(GITHUB_PRIVATE_REPO, "Update private docs and catalogue")
    os.chdir("..")  # Go back to the root directory

    print("HTML reports generated and pushed to GitHub successfully.")

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
        print("9. Modify a Product")
        print("10. Delete a Product")
        print("11. Modify a Sale")
        print("12. Exit")

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
            create_html_and_push(available_df)  # Generate HTML and push to GitHub
        elif choice == '7':
            search_available_items()
        elif choice == '8':
            view_sales_records()
        elif choice == '9':
            modify_product()
        elif choice == '10':
            delete_product()
        elif choice == '11':
            modify_sale()
        elif choice == '12':
            break
        else:
            print("Invalid choice. Please try again.")



# Run the main menu
if __name__ == "__main__":
    # Create empty CSV files if they do not exist
    if not os.path.exists(PRODUCTS_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes']).to_csv(PRODUCTS_FILE, index=False)
    if not os.path.exists(AVAILABLE_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Count']).to_csv(AVAILABLE_FILE, index=False)
    if not os.path.exists(SOLD_FILE):
        pd.DataFrame(columns=['ID', 'Type', 'Gender', 'Brand', 'Name', 'Color', 'Cost (USD)', 'Expected Price (USD)', 'Trip #', 'Sizes', 'Selling Date', 'Final Price', 'Customer', 'Notes']).to_csv(SOLD_FILE, index=False)

    main_menu()
