import yfinance as yf
import pandas as pd
# Create a ticker object (example using Apple - AAPL)
ticker = yf.Ticker("0941.HK")
income_stmt = ticker.income_stmt
cash_flow = ticker.cashflow
financial_data = []
if income_stmt is not None and not income_stmt.empty:
    dates = income_stmt.columns
    for date in dates:
        print(date)
for date in dates:
    year_data = {
                            'fiscal_year': date.year,
                            'period_label': 'Q4',
                            'period_end_date': date.strftime('%Y-%m-%d')
                        }
if cash_flow is not None and not cash_flow.empty:
                    for data in financial_data:
                        
                       
                            # Operating Cash Flow (cf_cash_from_oper)
                        if 'Operating Cash Flow' in cash_flow.index:
                                cf = float(cash_flow.loc['Operating Cash Flow'])
                                data['cf_cash_from_oper'] = cf
# Get cash flow data
print(data)


# Operating cash flow is already a row in the cashflow dataframe
# operating_cash_flow = cash_flow_data.loc["Operating Cash Flow"]

