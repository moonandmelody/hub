# date_config.py
import datetime

# 1. Enter any specific dates your business will be closed (Format: "YYYY-MM-DD")
CUSTOM_BLOCKED_DATES = [
    "2026-08-15",  # Example: Independence Day Holiday
    "2026-10-02"  # Example: Gandhi Jayanti
]

def get_all_disabled_dates(start_days_ahead=30):
    """Generates an explicit list of all blocked dates for the calendar UI."""
    disabled_list = []
    today = datetime.date.today()
    
    # 2. Add your custom list of fixed blacklisted dates
    for date_str in CUSTOM_BLOCKED_DATES:
        try:
            disabled_list.append(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            pass

    # 3. Add all upcoming Mondays (0) and Tuesdays (1) for the next X days
    for i in range(-5, start_days_ahead + 60): # Scan broad window around current time
        check_date = today + datetime.timedelta(days=i)
        if check_date.weekday() in [0, 1]:  # 0 = Monday, 1 = Tuesday
            disabled_list.append(check_date)
            
    return list(set(disabled_list))  # Return unique date objects
