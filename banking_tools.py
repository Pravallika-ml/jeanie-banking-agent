"""
Mock banking backend + tools the agent can call.
"""
from langchain_core.tools import tool
from langgraph.types import interrupt

CUSTOMER = {
    "name": "Alex Morgan",
    "accounts": {
        "checking": {"balance": 2450.36},
        "savings": {"balance": 8120.00},
    },
    "cards": {
        "4412": {"status": "active", "type": "debit"},
        "7788": {"status": "active", "type": "credit"},
    },
    "transactions": [
        {"id": "TXN1001", "account": "checking", "merchant": "Kroger", "amount": -84.12, "date": "2026-06-28"},
        {"id": "TXN1002", "account": "checking", "merchant": "Shell Gas", "amount": -42.50, "date": "2026-06-27"},
        {"id": "TXN1003", "account": "checking", "merchant": "Direct Deposit - Payroll", "amount": 2100.00, "date": "2026-06-25"},
        {"id": "TXN1004", "account": "checking", "merchant": "Netflix", "amount": -15.49, "date": "2026-06-20"},
        {"id": "TXN1005", "account": "savings", "merchant": "Transfer from Checking", "amount": 500.00, "date": "2026-06-15"},
    ],
    "disputes": [],
}


@tool
def get_balance(account_type: str) -> str:
    """Get the current balance for the customer's checking or savings account.

    Args:
        account_type: Either 'checking' or 'savings'.
    """
    account_type = account_type.lower().strip()
    if account_type not in CUSTOMER["accounts"]:
        return f"I don't see a '{account_type}' account. Available accounts: checking, savings."
    balance = CUSTOMER["accounts"][account_type]["balance"]
    return f"Your {account_type} account balance is ${balance:,.2f}."


@tool
def get_recent_transactions(account_type: str, limit: int = 5) -> str:
    """Get the most recent transactions for a given account.

    Args:
        account_type: Either 'checking' or 'savings'.
        limit: Maximum number of transactions to return (default 5).
    """
    account_type = account_type.lower().strip()
    matches = [t for t in CUSTOMER["transactions"] if t["account"] == account_type]
    if not matches:
        return f"No transactions found for the {account_type} account."
    matches = sorted(matches, key=lambda t: t["date"], reverse=True)[:limit]
    lines = [f"{t['date']}  {t['merchant']:<28} {t['amount']:+.2f}  ({t['id']})" for t in matches]
    return "\n".join(lines)


@tool
def transfer_funds(from_account: str, to_account: str, amount: float) -> str:
    """Transfer money between the customer's own checking and savings accounts.
    This is a sensitive action and requires the customer to confirm before it executes.

    Args:
        from_account: Account to move money out of ('checking' or 'savings').
        to_account: Account to move money into ('checking' or 'savings').
        amount: Dollar amount to transfer.
    """
    from_account, to_account = from_account.lower().strip(), to_account.lower().strip()

    if from_account not in CUSTOMER["accounts"] or to_account not in CUSTOMER["accounts"]:
        return "One of those accounts doesn't exist. Use 'checking' or 'savings'."
    if CUSTOMER["accounts"][from_account]["balance"] < amount:
        return f"Transfer declined: insufficient funds in {from_account}."

    approved = interrupt({
        "action": "transfer_funds",
        "message": f"Confirm: transfer ${amount:,.2f} from {from_account} to {to_account}?",
        "details": {"from_account": from_account, "to_account": to_account, "amount": amount},
    })

    if not approved:
        return "Transfer cancelled -- the customer did not confirm it."

    CUSTOMER["accounts"][from_account]["balance"] -= amount
    CUSTOMER["accounts"][to_account]["balance"] += amount
    return (f"Transferred ${amount:,.2f} from {from_account} to {to_account}. "
            f"New {from_account} balance: ${CUSTOMER['accounts'][from_account]['balance']:,.2f}. "
            f"New {to_account} balance: ${CUSTOMER['accounts'][to_account]['balance']:,.2f}.")


@tool
def activate_card(last_four: str) -> str:
    """Activate a debit or credit card using its last 4 digits.

    Args:
        last_four: The last 4 digits printed on the card.
    """
    card = CUSTOMER["cards"].get(last_four)
    if not card:
        return f"I couldn't find a card ending in {last_four} on this account."
    card["status"] = "active"
    return f"Your {card['type']} card ending in {last_four} is now active."


@tool
def report_lost_card(last_four: str) -> str:
    """Report a card lost or stolen and deactivate it. This is a sensitive
    action and requires the customer to confirm before it executes.

    Args:
        last_four: The last 4 digits printed on the card.
    """
    card = CUSTOMER["cards"].get(last_four)
    if not card:
        return f"I couldn't find a card ending in {last_four} on this account."

    approved = interrupt({
        "action": "report_lost_card",
        "message": f"Confirm: report the card ending in {last_four} as lost and deactivate it?",
        "details": {"last_four": last_four},
    })

    if not approved:
        return "No action taken -- the customer did not confirm the report."

    card["status"] = "deactivated"
    return f"Card ending in {last_four} has been deactivated and a replacement has been requested."


@tool
def file_dispute(transaction_id: str, reason: str) -> str:
    """File a dispute on a past transaction.

    Args:
        transaction_id: The transaction ID to dispute (e.g. 'TXN1002').
        reason: Why the customer is disputing this charge.
    """
    match = next((t for t in CUSTOMER["transactions"] if t["id"] == transaction_id), None)
    if not match:
        return f"I couldn't find transaction {transaction_id}."
    CUSTOMER["disputes"].append({"transaction_id": transaction_id, "reason": reason})
    return (f"Dispute filed for {transaction_id} ({match['merchant']}, ${match['amount']:.2f}). "
            f"Reason logged: \"{reason}\". You'll hear back within 5-7 business days.")


ALL_TOOLS = [get_balance, get_recent_transactions, transfer_funds, activate_card,
             report_lost_card, file_dispute]
SENSITIVE_ACTIONS = {"transfer_funds", "report_lost_card"}
