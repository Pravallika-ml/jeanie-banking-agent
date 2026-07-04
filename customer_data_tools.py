"""
Tools for looking up individual customers (by ID or by name) and running
aggregate/analytics queries across the full 250-customer dataset.
"""
import pandas as pd
from langchain_core.tools import tool

CUSTOMERS_DF = pd.read_excel("customer_banking_data.xlsx", sheet_name="Customers", dtype={"customer_id": str})

VALID_COLUMNS = ("checking_balance", "savings_balance")
OPERATORS = {"<": lambda s, v: s < v, "<=": lambda s, v: s <= v,
             ">": lambda s, v: s > v, ">=": lambda s, v: s >= v,
             "==": lambda s, v: s == v}


@tool
def get_customer_details(identifier: str) -> str:
    """Look up full account details for a single customer, using EITHER
    their customer ID (e.g. 'CUST0001') OR their first or last name
    (e.g. 'Pravallika' or 'Dasari'). Always try this tool directly with
    whatever the customer gave you -- name or ID both work.

    Args:
        identifier: A customer ID like CUST0001, or a first/last name.
    """
    identifier = identifier.strip()
    row = CUSTOMERS_DF[CUSTOMERS_DF["customer_id"].str.upper() == identifier.upper()]

    if row.empty:
        query = identifier.lower()
        matches = CUSTOMERS_DF[
            CUSTOMERS_DF["first_name"].str.lower().str.contains(query, na=False)
            | CUSTOMERS_DF["last_name"].str.lower().str.contains(query, na=False)
        ]
        if matches.empty:
            return f"No customer found matching '{identifier}'."
        if len(matches) > 1:
            options = ", ".join(f"{r['customer_id']} ({r['first_name']} {r['last_name']})"
                                 for _, r in matches.iterrows())
            return f"Multiple customers match '{identifier}': {options}. Please specify the customer ID."
        row = matches

    r = row.iloc[0]
    return (f"{r['first_name']} {r['last_name']} ({r['customer_id']}), {r['city']}, {r['state']}. "
            f"Checking balance: ${r['checking_balance']:,.2f}. Savings balance: ${r['savings_balance']:,.2f}. "
            f"Debit card ...{r['debit_card_last4']} ({r['debit_card_status']}). "
            f"Credit card ...{r['credit_card_last4']} ({r['credit_card_status']}). "
            f"Account opened: {r['account_open_date']}.")


@tool
def count_customers(column: str, operator: str, value: float) -> str:
    """Count how many of the 250 customers meet a numeric condition.

    Args:
        column: One of 'checking_balance' or 'savings_balance'.
        operator: One of '<', '<=', '>', '>=', '=='.
        value: The number to compare against.
    """
    if column not in VALID_COLUMNS or operator not in OPERATORS:
        return "column must be checking_balance/savings_balance; operator must be <, <=, >, >=, or ==."
    count = OPERATORS[operator](CUSTOMERS_DF[column], value).sum()
    return f"{count} out of {len(CUSTOMERS_DF)} customers have {column} {operator} {value}."


@tool
def average_balance(column: str) -> str:
    """Get the average balance across all 250 customers.

    Args:
        column: One of 'checking_balance' or 'savings_balance'.
    """
    if column not in VALID_COLUMNS:
        return "column must be 'checking_balance' or 'savings_balance'."
    avg = CUSTOMERS_DF[column].mean()
    return f"The average {column.replace('_', ' ')} across {len(CUSTOMERS_DF)} customers is ${avg:,.2f}."


@tool
def list_customers(column: str, operator: str, value: float, limit: int = 10) -> str:
    """List customers meeting a numeric condition, up to a limit.

    Args:
        column: One of 'checking_balance' or 'savings_balance'.
        operator: One of '<', '<=', '>', '>=', '=='.
        value: The number to compare against.
        limit: Max number of customers to list (default 10).
    """
    if column not in VALID_COLUMNS or operator not in OPERATORS:
        return "column must be checking_balance/savings_balance; operator must be <, <=, >, >=, or ==."
    matches = CUSTOMERS_DF[OPERATORS[operator](CUSTOMERS_DF[column], value)].head(limit)
    if matches.empty:
        return "No customers match that condition."
    lines = [f"{r['customer_id']}: {r['first_name']} {r['last_name']} - {column} ${r[column]:,.2f}"
             for _, r in matches.iterrows()]
    return "\n".join(lines)


CUSTOMER_DATA_TOOLS = [get_customer_details, count_customers, average_balance, list_customers]
