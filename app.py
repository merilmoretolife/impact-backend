from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import uuid
from openai import OpenAI

with open("Master List EndoSurgery.txt", "r", encoding="utf-8") as f:
    doc_masterlist_text = f.read()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

def generate_impact_analysis(department_input, change_description, product_name):
    prompt = f"""
You are a regulatory and quality expert helping assess the departmental impact of a change in a medical device company.

A user has described a change below. Based on that input, return department-wise impact analysis.

📂 Use the official document list below to identify exact impacted SOPs:
=== MASTER DOCUMENT LIST ===
{doc_masterlist_text}
=== END MASTER LIST ===

🔹 This list contains document numbers and titles. Match relevant documents using both title keywords and document type/number. Always cite documents in this format:
**[Document Number] - [Title]**

📦 Product affected: **{product_name}**
Section logic:
- Devices in section **C**: Staplers, Trocars (EMD), IUDs, SFE (Bulk Sutures)
- All others → AB section
Use this to decide document codes (e.g., `UTSOPC` for C-section products, `UTSOP` for AB-section).

🧭 Department mentioned: **{department_input}** — use it as a clue, but analyze ALL 5 departments:

For each department that is relevant, generate a table with these columns:
1. Possible Impact Area (row title)
2. Impact → Yes or No
3. Documents Impacted → Use actual document number and names from the list above if impacted, else write "—"
4. Justification → Short reason why the document is impacted, or "Not impacted"

Use this layout:
Department: [Department Name]
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| ...                  | ...    | ...                 | ...           |

The departments and their possible impact areas are:

### DESIGN
- Device design, dimensions and specification
- Assembly of Components
- Change in product Safety & Performance - Verification, validation, Clinical
- Packaging Type & Sterilization Method
- Raw Material, Packaging material or Components
- If Other, Please Specify

### PRODUCTION
- Manufacturing Processes - Flow chart, DHR, SOPs
- Machines and equipment
- Process Validation (IQ, OQ, PQ)
- Production planning/Logistics
- Environmental and Premises
- If Other, Please Specify

### QC
- Equipment and Instruments
- Technical Specifications
- Standard Testing Procedures
- Sampling Plan
- Quality Plan
- If Other, Please Specify

### QA
- QMS (e.g., equipment list, VMP)
- Finished Device Specifications & DMR
- Shelf Life
- Suppliers and Sub-contractors/Quality Agreements/Audits
- If Other, Please Specify

### RA
- Technical Documentation / Regulatory Files
- Indications / Intended Use / PMS / Clinical
- Labeling / Artwork
- Notification to NBs / Competent Authorities
- If Other, Please Specify

Always include all 5 departments (Design, Production, QC, QA, RA), even if they are not impacted. If not impacted, clearly write "No" in the Impact column, and "Not applicable" or "No impact" in the justification column.
Only list documents **actually** impacted from the master list. If none, write "—".

---

### 🔍 Risk Assessment Summary

Based on the above impact analysis, assess the **risk level** of this change:
- Identify whether the change affects product quality, safety, regulatory compliance, or key QMS systems and provide identified risks and what mitigation steps will be taken.
- Consider if re-validation, re-qualification, or re-approval from notified bodies or authorities is likely required.
- Highlight any need for urgent updates to DMR, technical files, or labeling that would impact traceability or usability.

---

### ⚠️ Impact Type Classification

Classify the change under one of the following impact types:

- **Critical** → Involves product approval, patient safety, regulatory compliance, or fundamental device performance.
- **Major** → Significant but does not compromise safety or regulatory approval (e.g., supplier change, DMR update, material).
- **Minor** → Administrative or editorial, no change to safety, performance, or approval status.

Clearly state the **Impact Type** and justification in 2–4 sentences based on your risk summary and impact tables.


Change Description:
\"\"\"{change_description}\"\"\"

Respond in Markdown table format, one per department.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content

@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    dept_input = data.get('department', '')
    change_input = data.get('change_description', '')
    product_input = data.get('product', '')
    report = generate_impact_analysis(dept_input, change_input, product_input)

    return jsonify({
        "report": report,
        "report_filename": f"impact_report_{uuid.uuid4()}.txt"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
