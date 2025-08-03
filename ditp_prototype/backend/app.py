from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Define the path for the submissions log file relative to the app's root
SUBMISSIONS_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(app.root_path)), 'data', 'submissions.log')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(app.root_path)), 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return "DITP Backend is running!"

@app.route('/submit', methods=['POST'])
def handle_submission():
    description = request.form.get('description')
    file = request.files.get('file')

    if not description and not file:
        return jsonify({"error": "No description or file provided"}), 400

    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"""---\nTimestamp: {timestamp}\n"""

    if description:
        log_entry += f"Description: {description}\n"

    if file:
        filename = f"{timestamp.replace(':', '-')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        log_entry += f"File: {file.path}\n"
    
    log_entry += "---\n"

    try:
        with open(SUBMISSIONS_LOG_FILE, 'a') as f:
            f.write(log_entry)
        return jsonify({"message": "Submission successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def scrape_procurement_data(html_content):
    nodes = []
    links = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the div containing the solicitations
    solicitation_list_div = soup.find('div', id='solicitationList-resultList')

    if solicitation_list_div:
        # Find the table within the solicitation list div
        solicitation_table = solicitation_list_div.find('table', class_='sol-table')

        if solicitation_table:
            rows = solicitation_table.find('tbody').find_all('tr', class_='mets-table-row')
            for row in rows:
                anomalies = []

                # Extract Solicitation Number
                sol_num_div = row.find('div', class_='sol-num')
                sol_num = sol_num_div.text.strip() if sol_num_div else "N/A"

                # Extract Solicitation Title and Link
                sol_title_link = row.find('a', class_='solicitation-link')
                sol_title = sol_title_link.text.strip() if sol_title_link else "N/A"
                sol_link = sol_title_link['href'] if sol_title_link and 'href' in sol_title_link.attrs else "N/A"

                # Extract Dates
                published_date_span = row.find('span', class_='sol-publication-date')
                published_date = published_date_span.find('span', class_='date-value').text.strip() if published_date_span and published_date_span.find('span', class_='date-value') else "N/A"

                closed_date_span = row.find('span', class_='sol-closing-date')
                closed_date = closed_date_span.find('span', class_='date-value').text.strip() if closed_date_span and closed_date_span.find('span', class_='date-value') else "N/A"

                awarded_date_span = row.find('span', class_='sol-award-date')
                awarded_date = awarded_date_span.find('span', class_='date-value').text.strip() if awarded_date_span and awarded_date_span.find('span', class_='date-value') else "N/A"

                # Anomaly Detection
                if published_date == "N/A":
                    anomalies.append("Missing Published Date")
                if closed_date == "N/A":
                    anomalies.append("Missing Closed Date")
                if awarded_date != "N/A" and closed_date == "N/A":
                    anomalies.append("Awarded Date present without Closed Date")

                # Keyword-based anomaly detection
                keywords_of_interest = ["emergency", "no bid", "single source", "sole source", "urgent", "expedited"]
                for keyword in keywords_of_interest:
                    if keyword in sol_title.lower():
                        anomalies.append(f"Keyword '{keyword}' found in title")

                node_id = sol_link # Use link as ID for consistency with frontend
                details = f"Title: {sol_title}\nNumber: {sol_num}\nPublished: {published_date}\nClosed: {closed_date}\nAwarded: {awarded_date}\nLink: {sol_link}"

                node_data = {"id": node_id, "group": "procurement", "details": details}
                if anomalies:
                    node_data["anomalies"] = anomalies
                    node_data["group"] = "anomaly" # Change group to anomaly if anomalies are found

                nodes.append(node_data)
                links.append({"source": node_id, "target": sol_link, "type": "procurement_link"})
        else:
            nodes.append({"id": "No Procurement Table Found", "group": "error", "details": "Could not find the procurement table within the solicitation list."})
    else:
        nodes.append({"id": "No Procurement Data Found", "group": "error", "details": "Could not find the solicitation list div."})

    return {"nodes": nodes, "links": links}

def analyze_audit_reports(report_filenames):
    nodes = []
    links = []
    anomaly_keywords = ["unaudited", "irregular", "fraud", "mismanagement"]

    for filename in report_filenames:
        anomalies = []
        file_id = os.path.basename(filename)
        
        # Check for keywords in the filename
        for keyword in anomaly_keywords:
            if keyword in filename.lower():
                anomalies.append(f"Keyword '{keyword}' found in filename")
        
        node_data = {"id": file_id, "group": "audit_report", "details": f"Audit Report: {file_id}"}
        if anomalies:
            node_data["anomalies"] = anomalies
            node_data["group"] = "anomaly" # Mark as anomaly if keywords are found
        
        nodes.append(node_data)
    return {"nodes": nodes, "links": links}

@app.route('/api/procurement_anomalies')
def get_procurement_anomalies():
    all_nodes = []
    all_links = []

    # Process procurement data
    html_file_path = "C:\\Users\\emili\\Downloads\\Digital_Integrity_Transparency_Platform\\Web_Page_Data\\City of Victoria - Bid Opportunities and RFPs _ BidNet Direct.html"
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        procurement_data = scrape_procurement_data(html_content)
        all_nodes.extend(procurement_data["nodes"])
        all_links.extend(procurement_data["links"])
    except FileNotFoundError:
        all_nodes.append({"id": "Error: Procurement HTML file not found", "group": "error", "details": f"The file {html_file_path} was not found."})
    except Exception as e:
        all_nodes.append({"id": "Error processing Procurement HTML", "group": "error", "details": f"An error occurred: {str(e)}"})

    # Process audit reports
    audit_report_dir = "C:\\Users\\emili\\Downloads\\Digital_Integrity_Transparency_Platform\\data\\Victoria_Texas_Audit_Reports"
    try:
        report_filenames = [os.path.join(audit_report_dir, f) for f in os.listdir(audit_report_dir) if f.endswith('.pdf')]
        audit_data = analyze_audit_reports(report_filenames)
        all_nodes.extend(audit_data["nodes"])
        all_links.extend(audit_data["links"])
    except FileNotFoundError:
        all_nodes.append({"id": "Error: Audit Reports directory not found", "group": "error", "details": f"The directory {audit_report_dir} was not found."})
    except Exception as e:
        all_nodes.append({"id": "Error processing Audit Reports", "group": "error", "details": f"An error occurred: {str(e)}"})

    return jsonify({"nodes": all_nodes, "links": all_links})


if __name__ == '__main__':
    app.run(debug=True, port=5001) # Running on a different port to avoid conflict with React

