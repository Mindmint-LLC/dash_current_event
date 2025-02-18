
import streamlit as st
from dbharbor.bigquery import SQL
# from streamlit_authentication.google_oauth import authenticate
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import datetime as dt


refresh_mins = 1


#%%

def StyleDF(df):
    fmt_cash = lambda x: '-' if pd.isna(x) or int(x) == 0 else '${:,.0f}'.format(int(x)) if int(x) >= 0 else '$({:,.0f})'.format(abs(int(x)))
    fmt_int = lambda x: '-' if pd.isna(x) or int(x) == 0 else '{:,.0f}'.format(int(x)) if int(x) >= 0 else '({:,.0f})'.format(abs(int(x)))

    clmn_format_dict = {}
    for clmn in ['PIF Cash', '3 Pay Cash', 'Total Cash']:
        clmn_format_dict[clmn] = fmt_cash
    for clmn in ['PIF Sales', '3 Pay Sales', 'Total Sales']:
        clmn_format_dict[clmn] = fmt_int


    dfg_all_formatted = df.style\
        .hide(axis="index")\
        .set_properties(**{'text-align': 'left'})\
        .set_properties(**{'font-size': '18px;'})\
        .set_properties(**{'font-family': 'Century Gothic, sans-serif;'})\
        .set_properties(**{'padding': '3px 20px 3px 5px;'})\
        .set_table_styles([
            # Column Headers
            {
                'selector': 'thead th',
                'props': 'background-color: #FFFFFF;\
                    color: #305496;\
                    border-bottom: 2px solid #305496;\
                    text-align: left;\
                    font-size: 20px;\
                    font-family: Century Gothic, sans-serif;\
                    padding: 0px 20px 0px 5px;'
            },
            # Last Column Header
            {
                'selector': 'thead th:last-child',
                'props': 'color: black;'
            },
            # Even Rows
            {
                'selector': 'tbody tr:nth-child(even)',
                'props': 'background-color: white;\
                    color: black;'
            },
            # Odd Rows
            {
                'selector': 'tbody tr:nth-child(odd)',
                'props': 'background-color: #D9E1F2;'
            },
            # Last Row
            {
                'selector': 'tbody tr:last-child td',
                'props': 'font-weight: bold;\
                    border-top: 2px solid #305496;'
            },
            # First Column
            {
                'selector': 'tbody td:first-child',
                'props': 'border-right: 2px solid #305496;'
            },
            # Last Column
            {
                'selector': 'tbody td:last-child',
                'props': 'font-weight: bold;\
                    border-left: 2px solid #305496;'
            },
            ])\
        .format(clmn_format_dict)
    html = dfg_all_formatted.to_html()
    html = html.replace('<style type="text/css">', '<style type="text/css">\ntable {\n\tborder-spacing: 0;\n}')
    return html


@st.cache_data(ttl=refresh_mins * 59)
def GetData():
    con = SQL()
    sql = '''
    with mysql as (
        select *
        FROM EXTERNAL_QUERY("bbg-platform.us.mastermind", """

            SELECT email
                , dt
                , product
                , amount
            FROM kbb_evergreen.tracking_orders d
            WHERE d.dt >= "2024-10-25"
                and `status` = "paid"
                and d.product in (
                    "Mastermind Business System",
                    "Mastermind Business System 3 Pay"
                );
    
        """)
    )

    select cast(m.dt as date) as `Date`
        , sum(case when m.product = "Mastermind Business System" then 1 else 0 end) as `PIF Sales`
        , sum(case when m.product = "Mastermind Business System" then m.amount else 0 end) as `PIF Cash`
        , sum(case when m.product = "Mastermind Business System 3 Pay" then 1 else 0 end) as `3 Pay Sales`
        , sum(case when m.product = "Mastermind Business System 3 Pay" then m.amount else 0 end) as `3 Pay Cash`
        , count(*) as `Total Sales`
        , sum(amount) as `Total Cash`
    from mysql m
    where analytics.fnEmail_IsTest(m.email) = False
    group by all
    order by 1
    '''
    df = con.read(sql)
    df = df.set_index('Date')
    dfg_aggr = df.sum(axis=0, numeric_only=True)
    dfg_aggr = pd.DataFrame(dfg_aggr).T
    dfg_aggr.index = ['Total']
    df = pd.concat([df, dfg_aggr])
    df = df.reset_index(names=['Date'])
    styled_html = StyleDF(df)

    last_update = (dt.datetime.now() + dt.timedelta(hours=-7)).strftime('%m/%d/%Y, %H:%M:%S')
    return styled_html, last_update


#%% Streamlit App

st.set_page_config(layout="wide")


# @authenticate
def Dashboard():
    st_autorefresh(interval=refresh_mins * 60 * 1000, key="fizzbuzzcounter") # milliseconds

    st.title('Secrets to Scaling Sales')

    st.markdown('<br><br>', unsafe_allow_html=True)
    
    st.subheader('Mastermind Business System Sales')
    styled_html, last_update = GetData()
    st.write(styled_html, unsafe_allow_html=True)
    st.markdown(f'Last Update: {last_update}<br>Updates Every {refresh_mins} Minute(s) Automatically', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    st.components.v1.iframe('https://docs.google.com/spreadsheets/d/e/2PACX-1vQmzdJsXYWWa4GyZ3fCMYswAFYI-V1qrgxF1zUWYY4GcloVz8SbwBSFgS33i9n9hOdHFfWL7Pv0Vmkq/pubchart?oid=71379020&format=image', width=800, height=500)
    st.markdown(f'Updates Every Hour Automatically', unsafe_allow_html=True)

Dashboard()