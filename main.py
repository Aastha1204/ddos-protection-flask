from flask import Flask, render_template, jsonify, request, redirect
import threading, time
from detector import start_monitoring, traffic_data
from database import get_all_logs, init_db, save_user_email, get_user_email
import io, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from notifier import send_email_alert


app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/email-setup")
def email_page():
    return render_template("email_alert.html")

@app.route("/save-email", methods=["POST"])
def save_email():
    email = request.form.get("email")
    if email:
        save_user_email(email)
    return redirect("/email-setup")

@app.route("/api/traffic")
def api_traffic():
    # Return summary traffic and recent request counts
    return jsonify({
        "requests": traffic_data.get("requests", {}),
        "alerts": traffic_data.get("alerts", [])
    })
@app.route("/test-email")
def test_email():
    send_email_alert("🔥 Test email from Render!")
    return "Email function triggered"


@app.route("/api/alerts")
def api_alerts():
    # return persisted alerts
    logs = get_all_logs()
    return jsonify(logs)

@app.route("/download-pdf")
def download_pdf():
    """
    Generate a light-themed PDF report containing alerts, traffic stats, and configured email.
    Uses reportlab to build the PDF in-memory and returns it as a download.
    """
    # gather data
    alerts = get_all_logs(500)
    traffic = traffic_data.get("requests", {})
    top_ips = sorted(traffic.items(), key=lambda x: x[1], reverse=True)[:10]
    user_email = get_user_email()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36,leftMargin=36, topMargin=36,bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph("DDoS Protection Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    meta = Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    story.append(meta)
    story.append(Spacer(1, 12))

    # Email info
    story.append(Paragraph("<b>Configured Alert Email:</b> " + (user_email or "Not configured"), styles['Normal']))
    story.append(Spacer(1, 12))

    # Traffic summary table
    story.append(Paragraph("<b>Top IPs (current snapshot)</b>", styles['Heading3']))
    if top_ips:
        tdata = [["IP", "Requests"]]
        for ip, cnt in top_ips:
            tdata.append([ip, str(cnt)])
        tbl = Table(tdata, hAlign='LEFT')
        tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightblue),
                                 ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                                 ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                                 ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        story.append(tbl)
    else:
        story.append(Paragraph("No traffic data available.", styles['Normal']))
    story.append(Spacer(1, 12))

    # Alerts table
    story.append(Paragraph("<b>Recent Alerts</b>", styles['Heading3']))
    if alerts:
        atable = [["ID","IP","Timestamp","Message"]]
        for a in alerts:
            # truncate long messages for table readability
            msg = a.get("message","")
            if len(msg) > 120:
                msg = msg[:117] + "..."
            atable.append([str(a.get("id")), a.get("ip",""), a.get("timestamp",""), msg])
        t = Table(atable, colWidths=[40,100,120,240], hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightblue),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                               ('GRID',(0,0),(-1,-1),0.25,colors.grey),
                               ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        story.append(t)
    else:
        story.append(Paragraph("No alerts found in the database.", styles['Normal']))

    # Footer spacer
    story.append(Spacer(1, 20))
    story.append(Paragraph("End of report", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return (buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="ddos_report.pdf"'
    })

if __name__ == "__main__":
    init_db()
    # start detector in background thread
    t = threading.Thread(target=start_monitoring, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
