def calculate_loan_payment(principal, rate, months):
    """
    Calculates monthly loan payment (Standard Amortization).
    Rate is annual percentage (e.g., 5.0 for 5%).
    """
    if rate <= 0:
        return principal / months
    
    monthly_rate = (rate / 100) / 12
    # Standard mortgage/auto loan formula
    payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    return payment

def calculate_lease_effective_cost(monthly_payment, down_payment, fees, months):
    """
    Calculates the effective monthly cost of a lease (Amortizing down payment + fees).
    """
    total_lease_cost = (monthly_payment * months) + down_payment + fees
    return total_lease_cost / months