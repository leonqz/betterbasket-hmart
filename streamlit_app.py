import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CREDENTIALS = {
    "minho.lee@hmart.com": "mlee1234!!"
}


def login_screen():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if username in CREDENTIALS and CREDENTIALS[username] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
        else:
            st.error("Invalid username or password")

def main_app():

    # Load and preprocess the data
    data = pd.read_csv("HSERVICE_ITEM.csv")
    data.columns = data.columns.str.strip()  # Remove trailing spaces
    data['Date'] = pd.to_datetime(data['Date'])

    # Sort data by Date
    data = data.sort_values(by=['ItemCode', 'Date'])

    # Add Price Percentile Groups (Quartiles) for each ItemCode, dynamically handling duplicate edges
    def assign_price_quartiles(group):
        num_bins = 4
        labels = [f"{i*100//num_bins}-{(i+1)*100//num_bins}%" for i in range(num_bins)]
        try:
            return pd.qcut(group, q=num_bins, labels=labels, duplicates='drop')
        except ValueError:
            return pd.Series(index=group.index, dtype='object')  
    
    data['Price_Quartile'] = data.groupby('ItemCode')['Average_Sales_Price'].transform(assign_price_quartiles)

    # Add a Promotion flag for each ItemCode
    data['Is_Promotion'] = data['Price_Quartile'] == "0-25%"  # Adjust logic based on actual promo data

    # Sidebar for selecting an ItemCode
    item_codes = data['ItemCode'].unique()
    default_index = list(item_codes).index("1314105032") if "1314105032" in item_codes else 0
    selected_item_code = st.sidebar.selectbox("Select ItemCode", item_codes, index=default_index)

    # Filter data for the selected ItemCode
    filtered_data = data[data['ItemCode'] == selected_item_code]



    # Calculate average sales quantity, average price, and revenue by Price Quartile and Promotion for the selected item
    quartile_analysis = filtered_data.groupby(['Price_Quartile', 'Is_Promotion']).agg({
    'Total_Sales_Quantity': 'mean',
    'Average_Sales_Price': 'mean'
    }).reset_index()

    # Calculate revenue
    # Calculate revenue
    quartile_analysis['7 Day Average Revenue'] = quartile_analysis['Total_Sales_Quantity'] * quartile_analysis['Average_Sales_Price']

    # Format revenue to two decimal places with a dollar sign
    quartile_analysis['7 Day Average Revenue'] = quartile_analysis['7 Day Average Revenue'].apply(lambda x: f"${x:.2f}")

    # Rename columns
    quartile_analysis.rename(columns={
        'Total_Sales_Quantity': '7 Day Average Sales Quantity',
        'Average_Sales_Price': '7 Day Average Sales Price'
    }, inplace=True)

    # Add Promotion Label
    quartile_analysis['Promotion_Label'] = quartile_analysis['Is_Promotion'].replace({True: 'Promotion', False: 'Non-Promotion'})

    # Title and Instructions
    st.title("Promotion Efficacy Analysis")
    st.write(f"Selected Item: {selected_item_code}")

    # Line Chart: Sales vs. Price Over Time
    st.subheader("Sales vs. Price Over Time")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
    x=filtered_data['Date'],
    y=filtered_data['Total_Sales_Quantity'],
    mode='lines+markers',
    name='Sales Quantity',
    line=dict(color='orange'),
    marker=dict(color='orange'),
    hovertemplate='Date: %{x}<br>7 Day Average Sales Quantity: %{y:.2f}<extra></extra>'
    ))
    fig_line.add_trace(go.Scatter(
    x=filtered_data['Date'],
    y=filtered_data['Average_Sales_Price'],
    mode='lines+markers',
    name='7 Day Average Sales Price',
    line=dict(color='blue'),
    marker=dict(color='blue'),
    hovertemplate='Date: %{x}<br>7 Day Average Sales Price: %{y:.2f}<extra></extra>'
    ))
    fig_line.update_layout(
    title="7 Day Average Sales Quantity vs. 7 Day Average Sales Price Over Time",
    xaxis_title="Date",
    yaxis_title="7 Day Average Sales Quantity",
    yaxis2=dict(
        title="7 Day Average Sales Price",
        overlaying='y',
        side='right',
        titlefont=dict(color="blue"),
        tickfont=dict(color="blue")
    ),
    legend=dict(x=0, y=1),
    hovermode="x"
    )
    st.plotly_chart(fig_line)

    # Bar Chart: Segmentation by Price Quartiles
    st.subheader("Segmentation by Price Quartiles")
    fig_bar = px.bar(
    quartile_analysis,
    x='Price_Quartile',
    y='7 Day Average Revenue',
    color='Promotion_Label',
    barmode='group',
    labels={
        'Price_Quartile': 'Price Quartile',
        '7 Day Average Revenue': '7 Day Average Revenue',
        'Promotion_Label': 'Promotion Status'
    },
    title="7 Day Average Revenue by Price Quartiles and Promotion"
    )
    st.plotly_chart(fig_bar)


    st.write("Price Quartile Analysis with 7 Day Averages:")
    st.dataframe(quartile_analysis)
# Check if user is logged in
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_app()
else:
    login_screen()