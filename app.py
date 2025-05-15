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
CORS(app, resources={r"/*": {"origins": ["https://merilmoretolife.github.io"]}})

def generate_impact_analysis(department_input, change_description, product_name):
    prompt = f"""

### Instructions
You are a regulatory and quality expert analyzing the departmental impact of a change in a medical device company. Follow these steps to generate a structured impact analysis:
1. **Parse Change Description**: Identify the type of change (e.g., supplier, material, process, equipment), affected component/process, and relevant departments.
2. **Assess Impacts**: Evaluate impacts across all 5 departments (Design, Production, QC, QA, RA) using predefined impact areas.
3. **Match Documents**: Select relevant SOPs from the master document list based on keywords, document category, and department relevance.
4. **Generate Tables**: Create a table for each department with columns: Possible Impact Area, Impact, Documents Impacted, Justification.
5. **Provide Risk Assessment**: Summarize risks to quality, safety, or compliance, including mitigation steps.
6. **Classify Impact Type**: Classify as Critical, Major, or Minor with a brief justification.

### Inputs
- **Product**: {product_name}
- **Department Mentioned**: {department_input}
- **Change Description**: {change_description}
- **Section Logic**:
  - Section C Products: Staplers, Trocars (EMD), IUDs, SFE (Bulk Sutures) → Use `UTSOPC` documents.
  - AB Section: All other products → Use `UTSOP` documents.
  - If unclear, default to AB-section.

### Master Document List
{doc_masterlist_text}

### Document Matching Rules
- Extract keywords from the change description (e.g., "supplier" → "Supplier Control", "applicator" → "Assembly").
- Match document titles in the master list containing these keywords or synonyms (case-insensitive).
- Filter by department and category:
  - QMS: `PROC`, `RA`, 'QMM', 'SMF'
  - Production: `PRSOP`, `PFC`, 
  - Store: 'STSOP'
  - Utility: 'UTSOP'
  - Supply Chain/SCM: 'SCSOP'
  - QC: `QCSOP`, `QCSTP`, `PMTS`, 'RMTS', 'FGTS', 'QP'
  - QA: `QASOP`
  - Use section logic to select `UTSOPC` or `UTSOP` for relevant products. Same goes for techhnical specification e.g. 'FGTS' for AB section, 'FGTSEMD', 'RMTSSTA' for C section products.

- Cite documents as **[Document Number] - [Title]**. Use "—" if no documents match.
- Example: For "new supplier for Tyvek pouches," match documents like `QASOP-10 - Supplier Control`.

### Department Impact Tables
For each department, evaluate all listed impact areas. Use this format:

For each department that is relevant, generate a table with these columns:
1. Possible Impact Area (row title)
2. Impact → Yes or No
3. Documents Impacted → Document number - Title
4. Justification → Reason or "No impact"

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

### Justification Guidelines
- For impacted areas, explain how the change affects the area or document (e.g., "New supplier requires updated supplier control SOP").
- For non-impacted areas, use "No impact" with a brief reason if applicable (e.g., "No change to sterilization method").
- Examples:
  - Change: "New supplier for Tyvek pouches"
    - Document: **[QASOP-10] - Supplier Control**
    - Justification: "New supplier requires audit and quality agreement updates."
  - Change: "New applicator design"
    - Document: **[PRSOP-56] - Assembly Process**
    - Justification: "SOP to be revised for new applicator assembly."
    
---

### 🔍 Risk Assessment Summary

Based on the above impact analysis, assess the **risk level** of this change:
- Identify whether the change affects product quality, safety, regulatory compliance, or key QMS systems and provide identified risks and what mitigation steps will be taken.
- Consider if re-validation, re-qualification, or re-approval from notified bodies or authorities is likely required.
- Highlight any need for urgent updates to DMR, technical files, or labeling that would impact traceability or usability.

---

## Impact Type
- **Critical**: Affects patient safety, performance, or requires notified body approval.
- **Major**: Significant changes (e.g., material, design) requiring re-validation or DMR updates.
- **Minor**: Administrative, supplier, or equipment changes with no safety/performance impact.
- Default to Minor unless safety/regulatory impacts are identified.
- Provide 2–3 sentences justifying the classification.

### Example
**Input**:
- Product: Mirus Skin Stapler
- Department: Production
- Change: "Addition of new automatic pin loading machine."
**Output**:
Department: Design
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Device design, dimensions, and specification | No | — | No impact as machine does not alter design. |
| Assembly of Components | No | — | No impact. |
| Change in product Safety & Performance | Yes | — | IQ, OQ, PQ required for machine qualification. |
| Packaging Type & Sterilization Method | No | — | No impact. |
| Raw Material, Packaging material, or Components | No | — | No impact. |
| Others | Yes | — | Preventive maintenance schedule to be updated. |

Department: Production
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Manufacturing Processes - Flow chart, DHR, SOPs | Yes | [UTSOPC-16] - Pin Loading Process | SOP and BMR to be revised for new machine. |
| Machines and equipment | Yes | — | Machine qualification and calibration required. |
| Process Validation | Yes | — | Validation to be performed. |
| Production planning/Logistics | No | — | No impact. |
| Environmental and Premises | Yes | — | Area monitoring required. |
| Others | Yes | — | Training to be imparted. |

[... Other departments ...]

**Risk Assessment**: The new machine may affect pin loading consistency; requires IQ, OQ, PQ and operator training to mitigate risks.
**Impact Type**: Minor. The change enhances production capacity without affecting product safety or performance.

Change Description:
\"\"\"{change_description}\"\"\"

Respond in Markdown table format, one per department.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
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
