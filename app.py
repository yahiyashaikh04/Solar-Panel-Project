from flask import Flask,render_template,redirect,url_for,flash,make_response,request,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv,io,random
from flask_mail import Mail,Message
from collections import defaultdict
from sqlalchemy import extract

app =Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///solardata.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.secret_key = "mohsin_senior"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yahiyasgamin@gmail.com'       # Apna Gmail
app.config['MAIL_PASSWORD'] = 'wmww vuep negr pxiv'          # Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'yahiyas917@gmail.com'

mail= Mail(app)

class SolarData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_no = db.Column(db.String(20), nullable=False)
    voltage = db.Column(db.Float, nullable=False)
    current = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    efficiency = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default="OK")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def send_faulty_email():
    faulty_panels = SolarData.query.filter_by(status='Faulty').all()
    if faulty_panels:
        body = "⚠️ Faulty Panels Detected:\n\n"
        for p in faulty_panels:
            body += f"Panel {p.panel_no} at {p.timestamp} - Power: {p.power} W\n"

        msg = Message(subject="⚠️ Solar Panel Alert", recipients=["recipient_email@gmail.com"], body=body)
        mail.send(msg)

@app.route('/')
def start():

    return render_template("login.html")

@app.route('/login',methods =["GET","POST"])
def login():
    email = "admin@123"
    password = "1234"

    if request.method == "POST":
        name = request.form["email"]
        puss = request.form["password"]

        if name == email and puss == password:
            flash("Login Successful!!....")
            return redirect(url_for('main'))
        else:
            flash("Login Failed. Please Try Again....")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/main')
def main():
    data = SolarData.query.order_by(SolarData.timestamp.asc()).all()

    total_panels = len(set([d.panel_no for d in data]))
    faulty_count = sum(1 for d in data if d.status == "Faulty")
    active_count = sum(1 for d in data if d.status == "OK")
    total_power = sum(d.power for d in data)
    
    balance_power = sum(d.power if d.status == "OK" else -d.power for d in data)

    subquery = db.session.query(
        SolarData.panel_no,
        db.func.max(SolarData.timestamp).label('max_ts')
    ).group_by(SolarData.panel_no).subquery()

    latest_panels = db.session.query(SolarData).join(
        subquery,
        (SolarData.panel_no == subquery.c.panel_no) & 
        (SolarData.timestamp == subquery.c.max_ts)
    ).order_by(SolarData.panel_no).all()

    # Full history for table
    all_data = SolarData.query.order_by(SolarData.timestamp).all()

    graph_data = [
        {
        "panel_no": d.panel_no,
        "power": d.power,
        "voltage": d.voltage,
        "current": d.current,
        "efficiency": d.efficiency,
        "status": d.status,
        "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for d in SolarData.query.all()
    ]

    year = request.args.get("year", datetime.now().year, type=int)
    years = [y[0] for y in db.session.query(extract('year', SolarData.timestamp)).distinct()]

    seta = SolarData.query.filter(extract('year', SolarData.timestamp) == year).all()
    grouped = defaultdict(lambda: defaultdict(list))
    monthly_totals = {}
    yearly = {"voltage":0, "current":0, "power":0, "efficiency":0, "count":0}

    for s in seta:
        month = s.timestamp.strftime("%B")
        day = s.timestamp.strftime("%Y-%m-%d")
        grouped[month][day].append(s)

    # Monthly totals
    for month, days in grouped.items():
        total_v = sum(p.voltage for panels in days.values() for p in panels)
        total_c = sum(p.current for panels in days.values() for p in panels)
        total_p = sum(p.power for panels in days.values() for p in panels)
        total_e = sum(p.efficiency for panels in days.values() for p in panels) / sum(len(panels) for panels in days.values())
        count = sum(len(panels) for panels in days.values())
        monthly_totals[month] = dict(voltage=total_v, current=total_c, power=total_p, efficiency=total_e, count=count, status="OK")

        yearly["voltage"] += total_v
        yearly["current"] += total_c
        yearly["power"] += total_p
        yearly["efficiency"] += total_e
        yearly["count"] += count


    return render_template("index.html", data=data, total_panels=total_panels, faulty_count=faulty_count, active_count=active_count, total_power=round(total_power, 2), balance_power=round(balance_power, 2), geta=latest_panels, table_data=all_data, graph_data=graph_data, grouped=grouped, monthly_totals=monthly_totals, yearly_totals=yearly, years=years, selected_year=year)


@app.route('/update')
def update_data():
    for panel_no in range(1, 9):
        voltage = round(random.uniform(15, 20), 2)
        current = round(random.uniform(0.8, 1.5), 2)
        power = round(voltage * current, 2)
        efficiency = round(random.uniform(70, 100), 2)
        
        if efficiency < 70:
            send_faulty_email()
            print("Message Sent...")
            status = "FAULTY"
        elif efficiency < 80:
            status = "OK (No Sunlight)"
        else:
            status = "OK"
        # Insert new record for history table
        new_data = SolarData(
            panel_no=f"PANEL-{panel_no}",
            voltage=voltage,
            current=current,
            power=power,
            efficiency=efficiency,
            status=status
        )
        db.session.add(new_data)
    
    db.session.commit()
    return redirect(url_for("main"))

@app.route('/delete')
def delete():
    db.session.query(SolarData).delete()
    db.session.commit()
    flash(" All data deleted successfully!", "danger")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect('/')

@app.route('/export')
def export_csv():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["id","panel_no","voltage","current","power","efficiency","status","timestamp"])
    for r in SolarData.query.order_by(SolarData.id.asc()).all():
        cw.writerow([r.id, r.panel_no, r.voltage, r.current, r.power, r.efficiency, r.status, r.timestamp])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=solardata.csv"
    output.headers["Content-type"] = "text/csv"
    return output


if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
