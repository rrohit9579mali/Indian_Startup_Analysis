import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout='wide', page_title='StartUp Analysis')

# Load and Clean Data
df = pd.read_csv('startup_cleaned.csv')

# Drop rows with critical missing values
df.dropna(subset=['date', 'startup', 'amount', 'investors', 'vertical'], inplace=True)

# Convert date column
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df.dropna(subset=['date'], inplace=True)
st.title('Indian Startup Analysis')
# Ensure amount is numeric
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
df.dropna(subset=['amount'], inplace=True)

# Remove empty investor/startup names
df = df[df['investors'].str.strip().astype(bool)]
df = df[df['startup'].str.strip().astype(bool)]

# Reset index
df.reset_index(drop=True, inplace=True)

# Create time features
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year


#  starttup information
def startup_info(name):
    st.title('StartUp Analysis')
    col1, col2, col3 = st.columns(3)

    with col1:
        # pass  # No content here
        st.write('Startup Name: ', name)
    with col2:
        # Get unique cities for this startup
        city = df.groupby('startup')['city'].agg(lambda x: ', '.join(set(x)))[name]
        st.write('City: ', city)
    with col3:
        # Get unique verticals for this startup
        verti = df.groupby('startup')['vertical'].agg(lambda x: ', '.join(set(x)))[name]
        st.write('Vertical: ', verti)

    # Ensure no 0 or NaN in subvertical before using
    df['subvertical'] = df['subvertical'].replace(0, np.nan)
    df['subvertical'] = df['subvertical'].fillna('Education')  # Default subvertical to 'Education' if NaN

    # Subvertical info
    subvertical = df.groupby('startup')['subvertical'].agg(lambda x: ', '.join(set(x)))[name]

    col4, col5 = st.columns(2)
    with col4:
        st.write('Subvertical: ', subvertical)

# startup and investors
# startup and investors
def startupandinvestors(name):
    st.markdown("### Startup + Investor Details")
    st.markdown("---")

    startup_df = df[df['startup'] == name]

    # All investors list (multiple investors may be in one row)
    investor_list = startup_df['investors'].str.split(',').explode().str.strip()
    investor_funding = pd.DataFrame({
        'investor': investor_list,
        'amount': startup_df.loc[startup_df.index.repeat(startup_df['investors'].str.count(',') + 1), 'amount'].values
    })

    # Group by investor to get total funding per investor
    grouped_investor = investor_funding.groupby('investor')['amount'].sum().sort_values(ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### All Investors of", name)
        for inv in grouped_investor.index:
            st.write("•", inv)

    with col2:
        st.metric(label='Total Unique Investors', value=len(grouped_investor))

    # ✅ Bar Chart: Investor-wise funding
    st.subheader(f"Funding by Each Investor in '{name}'")
    if not grouped_investor.empty:
        fig, ax = plt.subplots()
        ax.bar(grouped_investor.index, grouped_investor.values, color='orange')
        ax.set_xlabel('Investor')
        ax.set_ylabel('Funding Amount (Cr)')
        ax.set_title(f'Funding Contribution by Investors in {name}')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
    else:
        st.warning("No detailed investor data available for this startup.")



# Overall Analysis
def load_overall_analysis():
    st.title('Overall Analysis')

    total = round(df['amount'].sum())
    max_funding = df.groupby('startup')['amount'].max().sort_values(ascending=False).head(1).values[0]
    avg_funding = df.groupby('startup')['amount'].sum().mean()
    num_startups = df['startup'].nunique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric('Total', str(total) + 'Cr')
    with col2:
        st.metric('Max', str(max_funding) + 'Cr')
    with col3:
        st.metric('Avg', str(round(avg_funding)) + ' Cr')
    with col4:
        st.metric('Funded Startups', num_startups)

    st.header('MoM graph')
    selected_option = st.selectbox('Select Type', ['Total', 'Count'])
    if selected_option == 'Total':
        temp_df = df.groupby(['year', 'month'])['amount'].sum().reset_index()
    else:
        temp_df = df.groupby(['year', 'month'])['amount'].count().reset_index()

    temp_df['x_axis'] = temp_df['month'].astype('str') + '-' + temp_df['year'].astype('str')

    fig3, ax3 = plt.subplots()
    ax3.plot(temp_df['x_axis'], temp_df['amount'])

    st.pyplot(fig3)


# Investor Details
def load_investor_details(investor):
    st.title(investor)
    last5_df = df[df['investors'].str.contains(investor)].head()[
        ['date', 'startup', 'vertical', 'city', 'round', 'amount']]
    st.subheader('Most Recent Investments')
    st.dataframe(last5_df)

    col1, col2 = st.columns(2)

    with col1:
        big_series = df[df['investors'].str.contains(investor)].groupby('startup')['amount'].sum().sort_values(
            ascending=False).head()
        st.subheader('Biggest Investments')
        if big_series.empty:
            st.warning("Data nahiye plot sathi.")
            return
        fig, ax = plt.subplots()
        ax.bar(big_series.index, big_series.values)
        st.pyplot(fig)

    with col2:
        verical_series = df[df['investors'].str.contains(investor)].groupby('vertical')['amount'].sum().head()
        st.subheader('Sectors invested in')
        if verical_series.empty:
            st.warning("Sector data nahiye.")
            return
        fig1, ax1 = plt.subplots()
        ax1.pie(verical_series, labels=verical_series.index, autopct="%0.01f%%")
        st.pyplot(fig1)

    df['year'] = df['date'].dt.year
    year_series = df[df['investors'].str.contains(investor)].groupby('year')['amount'].sum()

    st.subheader('YoY Investment')
    if not year_series.empty:
        fig2, ax2 = plt.subplots()
        ax2.plot(year_series.index, year_series.values)
        st.pyplot(fig2)
    else:
        st.warning("YoY Investment data available nahiye.")


# Sector-wise Analysis
def load_sector_analysis():
    st.title("Top 5 Sectors by Total Investment")

    top_sectors = df.groupby('vertical')['amount'].sum().sort_values(ascending=False).head(5)

    st.subheader("Investment in Top 5 Sectors")
    st.dataframe(top_sectors.reset_index().rename(columns={'vertical': 'Sector', 'amount': 'Total Investment'}))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Bar Chart")
        fig_bar, ax_bar = plt.subplots()
        ax_bar.bar(top_sectors.index, top_sectors.values, color='skyblue')
        ax_bar.set_xlabel("Sector")
        ax_bar.set_ylabel("Investment (Cr)")
        ax_bar.set_title("Top 5 Sector-wise Investment")
        plt.xticks(rotation=45)
        st.pyplot(fig_bar)

    with col2:
        st.subheader("Pie Chart")
        fig_pie, ax_pie = plt.subplots()
        ax_pie.pie(top_sectors.values, labels=top_sectors.index, autopct="%0.1f%%", startangle=140)
        ax_pie.set_title("Investment Distribution in Top 5 Sectors")
        st.pyplot(fig_pie)


# Sidebar Navigation
st.sidebar.title('Startup Funding Analysis')
option = st.sidebar.selectbox('Select One', ['Overall Analysis', 'StartUp', 'Investor', 'Sector Analysis'])

if option == 'Overall Analysis':
    load_overall_analysis()

elif option == 'StartUp':
    name = st.sidebar.selectbox('Select StartUp', sorted(df['startup'].unique().tolist()))
    btn1 = st.sidebar.button('Find StartUp Details')
    if btn1:
        startup_info(name)
        startupandinvestors(name)
elif option == 'Investor':
    selected_investor = st.sidebar.selectbox('Select StartUp', sorted(set(df['investors'].str.split(',').sum())))
    btn2 = st.sidebar.button('Find Investor Details')
    if btn2:
        load_investor_details(selected_investor)

elif option == 'Sector Analysis':
    load_sector_analysis()
