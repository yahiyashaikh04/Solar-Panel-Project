from app import db, SolarData
from datetime import datetime, timedelta
import random

# ---- 1 YEAR DATA GENERATION ----
def generate_year_data():
    print("⏳ Generating 1 year of dummy solar data...")

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 11, 1)
    current_date = start_date
    panels = 8  # Number of solar panels

    while current_date <= end_date:
        for panel_no in range(1, panels + 1):
            # Random realistic values
            voltage = round(random.uniform(70, 100), 2)
            current = round(random.uniform(2.5, 6.5), 2)
            power = round(voltage * current / 10, 2)
            efficiency = round(random.uniform(70, 98), 2)

            # Solar condition logic
            if voltage < 75:
                status = "FAULTY"
            elif 75 <= voltage < 85:
                status = "OK (Low Sunlight)"
            else:
                status = "OK"

            new_data = SolarData(
                panel_no=panel_no,
                voltage=voltage,
                current=current,
                power=power,
                efficiency=efficiency,
                status=status,
                timestamp=current_date
            )
            db.session.add(new_data)

        current_date += timedelta(days=1)

    db.session.commit()
    print("✅ Successfully added 1 year of solar data!")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        generate_year_data()
