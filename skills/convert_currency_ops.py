from core.registry import skill
import requests


@skill
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts an amount from one currency to another using real-time exchange rates.

    Args:
        amount (float): The amount of money to convert.
        from_currency (str): The source currency code (e.g., 'USD').
        to_currency (str): The target currency code (e.g., 'EUR').

    Returns:
        str: A human-readable string with the converted amount and exchange rate details,
             or an error message if the conversion fails.
    """
    try:
        if amount <= 0:
            return "Error: Amount must be greater than zero."

        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # Using exchangerate.host free API
        url = "https://api.exchangerate.host/convert"
        params = {
            "from": from_currency,
            "to": to_currency,
            "amount": amount
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", False):
            return f"Error: Unable to fetch exchange rate for {from_currency} to {to_currency}."

        rate = data.get("info", {}).get("rate")
        result = data.get("result")

        if rate is None or result is None:
            return "Error: Unexpected response from exchange rate service."

        converted_amount = round(float(result), 2)
        rate = float(rate)

        return (
            f"{amount:.2f} {from_currency} = {converted_amount:.2f} {to_currency}\n"
            f"Exchange Rate: 1 {from_currency} = {rate:.6f} {to_currency}"
        )

    except requests.exceptions.RequestException as e:
        return f"Network error while fetching exchange rates: {str(e)}"
    except ValueError:
        return "Error: Invalid numeric value provided."
    except Exception as e:
        return f"Unexpected error during currency conversion: {str(e)}"