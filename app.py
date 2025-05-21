from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import uuid
from html import escape
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://merilmoretolife.github.io"]}})

def generate_impact_analysis(department_input, change_description, product_name):
  # Full list of document series and their meanings
    document_series = [
        "EOD - External Origin Documents (Standards module)",
        "Artwork - Labeling and Instructions for Use (IFU)",
        "Calibration ID - Calibration Matrix for instruments and equipments",
        "Product Master - Product profile containing Brand Name, Generic Name, UDI-DI, EMDN, Classification, Certifications (EU MDR/MDD, DCGI, USFDA), Device Description, Intended Purpose, Indications, Variants, Sizes, and IFU",
        "AHU ID - Environmental Monitoring and Validations",
        "PRSOP - Production SOP related to Sutures, Meshes, Adhesives, Bonewax",
        "PRSOPEMD - Production SOP related to Endomechanical devices (Stapler, Trocar)",
        "PRSOPIUD - Production SOP related to IUD",
        "PRSOPSFE - Production SOP related to Bulk Suture",
        "PRSOPAGS - Production SOP related to Gelatin Sponge",
        "PFC - Production Flow Charts of all products",
        "STSOP - Store SOPs",
        "SCSOP - Supply Chain SOPs",
        "UTSOP - Utility SOPs AB section",
        "UTSOPC - Utility SOPs C section",
        "RMTS - Raw Material Technical Specifications AB section",
        "PMTS - Packaging Material Technical Specifications AB section",
        "FGTS - Finished Goods Technical Specifications AB section",
        "QCSOP - Quality Control SOP",
        "QCSTP - Quality Control Standard Testing Procedure",
        "MICSOP - Microbiology QC SOP",
        "MICSTP - Microbiology QC STP",
        "QASOP - Quality Assurance SOPs",
        "QCSOPEMD - Quality Control SOP Endomechanical devices",
        "QASOPC - Quality Assurance SOP C section",
        "QCSTPEMD - Quality Control Standard Testing Procedure Endomechanical devices",
        "RMTSSTA - Raw Material Technical Specifications Stapler",
        "PMTSEMD - Packaging Material Technical Specifications Endomechanical devices",
        "FGTSEMD - Finished Goods Technical Specifications Endomechanical devices",
        "QPEMD - Quality Plan Endomechanical devices",
        "QCSTPIUD - Quality Control Standard Testing Procedure IUD",
        "RMTSIUD - Raw Material Technical Specifications IUD",
        "PMTSIUD - Packaging Material Technical Specifications IUD",
        "FGTSIUD - Finished Goods Technical Specifications IUD",
        "QPIUD - Quality Plan IUD",
        "QCSTPSFE - Quality Control Standard Testing Procedure Bulk Suture",
        "RMTSSFE - Raw Material Technical Specifications Bulk Suture",
        "PMTSSFE - Packaging Material Technical Specifications Bulk Suture",
        "FGTSSFE - Finished Goods Technical Specifications Bulk Suture",
        "QPSFE - Quality Plan Bulk Suture",
        "QCSTPAGS - Quality Control Standard Testing Procedure Gelatin Sponge",
        "RMTSAGS - Raw Material Technical Specifications Gelatin Sponge",
        "PMTSAGS - Packaging Material Technical Specifications Gelatin Sponge",
        "FGTSAGS - Finished Goods Technical Specifications Gelatin Sponge",
        "QPAGS - Quality Plan Gelatin Sponge",
        "QMM - Quality Manual",
        "SMF - Site Master File",
        "RA - Manufacturing License details, list of products, standards, Organization Chart, QMS process interactions",
        "PROC - Quality Procedures (as per ISO 13485)",
        "Validation of Equipments - IQ, OQ, PQ, VMP Validation Master Plan",
        "Validation of Microbiology tests - Bioburden, Sterilization test, etc.",
        "Stability Study plan - Stability Study Plan and Reports of all products",
        "SC - Supplier Control (Supplier Profile containing supplier details, agreement, certification)",
        "ASL - Approved Supplier List"
    ]

    # Determine product section
    section_c_products = ["stapler", "trocar", "iud", "sfe", "bulk suture", "gelatin sponge"]
    section_ab_products = ["suture", "mesh", "bonewax", "adhesive"]
    product_lower = product_name.lower()
    product_section = "Section C" if any(p in product_lower for p in section_c_products) else "AB Section"
        
    prompt = f"""

### Instructions
You are a regulatory and quality expert analyzing the impact of a change in a medical device company. Follow these steps to generate a structured impact analysis:
1. **Analyze Change Description**: Intelligently interpret the change description, product, and department to identify the nature of the change (e.g., new supplier, packaging update) and affected processes (e.g., sealing, supplier audits).
2. **Determine Impacted Documents**: Using the provided document series, select documents that need to be created or updated based on the change's impact. Consider the product type and section (C or AB) to choose appropriate variants (e.g., PMTSEMD for Staplers, PMTS for AB section).
3. **Assess Impacts**: Evaluate impacts across predefined areas for each department (Design, Production, QC, QA, RA), assigning relevant documents and justifications.
4. **Generate Tables**: Create a table for each department with columns: Possible Impact Area, Impact, Documents Impacted, Justification.
5. **Provide Risk Assessment**: Summarize risks to quality, safety, or compliance, including mitigation steps.
6. **Classify Impact Type**: Classify as Critical, Major, or Minor with a brief justification.

### Inputs
- **Product**: {product_name}
- **Department Mentioned**: {department_input}
- **Change Description**: {change_description}
- **Product Section**: {product_section}
### Document Series
The following is the complete list of document series available for creation or update:
{'; '.join(document_series)}

### Document Selection Guidelines
- Analyze the change description to identify affected processes, components, or systems (e.g., supplier addition, packaging material, sterilization).
- Select documents from the provided list that are directly relevant to the change. For example:
  - A new supplier may require `SC`, `ASL`, `QASOP` (supplier profile, list, audits) and TMF update.
  - A packaging change may require `PMTS` or section-specific variants (e.g., `PMTSEMD` for Staplers).
  - A new product variant may require `Product Master`.
- Use section-specific variants for Section C products:
  - Stapler/Trocar: `RMTSSTA`, `PMTSEMD`, `FGTSEMD`, `PRSOPEMD`, `QCSTPEMD`, `QPEMD`.
  - IUD: `RMTSIUD`, `PMTSIUD`, `FGTSIUD`, `PRSOPIUD`, `QCSTPIUD`, `QPIUD`.
  - Bulk Suture (SFE): `RMTSSFE`, `PMTSSFE`, `FGTSSFE`, `PRSOPSFE`, `QCSTPSFE`, `QPSFE`.
  - AB Section: Use `RMTS`, `PMTS`, `FGTS`, etc., unless Gelatin Sponge (`RMTSAGS`, `PMTSAGS`).
- Avoid irrelevant documents (e.g., do not select `EOD` unless standards are explicitly mentioned).
- Format documents as `[Series] - [Description]` (e.g., `[PMTS] - Packaging Material Specification`).

### Department Impact Tables
For each department (Design, Production, QC, QA, RA), evaluate and show all listed impact areas. Use "—" if no documents are impacted for an area.
Use this format:
```
Department: [Department Name]
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| [Area]               | Yes/No | [Series] - [Description] or — | [Reason or "No impact"] |
```

### Departments and Impact Areas
- **Design**:
  - Device design, dimensions, and specification
  - Assembly of Components
  - Change in product Safety & Performance
  - Packaging Type & Sterilization Method
  - Raw Material, Packaging material, or Components
  - Others
- **Production**:
  - Manufacturing Processes - Flow chart, DHR, SOPs
  - Machines and equipment
  - Process Validation (IQ, OQ, PQ)
  - Production planning/Logistics
  - Environmental and Premises
  - Others
- **QC**:
  - Equipment and Instruments
  - Technical Specifications
  - Standard Testing Procedures
  - Sampling Plan
  - Quality Plan
  - Others
- **QA**:
  - QMS
  - Finished Device Specifications & DMR
  - Shelf life
  - Suppliers and Sub-contractors/Quality Agreements/Audits
  - Others
- **RA**:
  - Technical Documentation/Regulatory Files
  - Indications/Intended Use/PMS/Clinical
  - Labeling/Artwork
  - Notification to NBs/Competent Authorities
  - Others

### Justification Guidelines
- For impacted areas, provide a specific reason linking the change to the area or document (e.g., “New supplier requires updated supplier profile”).
- For non-impacted areas, use “No impact” with a brief reason (e.g., “No change to manufacturing processes”).
- Examples:
  - Change: "New supplier for Tyvek pouches"
    - Area: Suppliers (QA)
    - Document: `[SC] - Supplier Control`
    - Justification: “New supplier requires profile and quality agreement.”
    - Area: Technical Specifications (QC)
    - Document: `[PMTS] - Packaging Material Specification`
    - Justification: “New specification for Tyvek pouch to be prepared.”

### Risk Assessment
- Identify risks to quality, safety, or compliance (e.g., “New supplier may affect sealing performance”).
- Suggest specific mitigation steps (e.g., “Conduct supplier audit, validate sealing process”).
- Example: “New supplier for Tyvek pouches may affect material quality; requires supplier QMS certificate and sealing validation.”

### Impact Type
- **Critical**: Affects patient safety, performance, or requires notified body approval.
- **Major**: Significant changes (e.g., material, design) requiring re-validation or DMR updates.
- **Minor**: Administrative, supplier, or equipment changes with no safety/performance impact.
- Default to Minor unless safety/regulatory impacts are identified.
- Provide 2–3 sentences justifying the classification.

### Example
**Input**:
- Product: Tyvek Pouch
- Department: QA
- Change: "M/s Jostick Adhesive is to be introduced as a new supplier for 1073B uncoated Tyvek pouches."
- Product Section: AB Section
**Output**:
Department: Design
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Device design, dimensions, and specification | No | — | No change to product design. |
| Assembly of Components | No | — | No impact on assembly. |
| Change in product Safety & Performance | Yes | — | Pre/post-ETO sterilization performance and sealing verification required. |
| Packaging Type & Sterilization Method | No | — | No change to sterilization method. |
| Raw Material, Packaging material, or Components | Yes | [PMTS] - Packaging Material Specification | New PMTS to be prepared for Tyvek pouch. |
| Others | No | — | No other impacts. |

Department: Production
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Manufacturing Processes - Flow chart, DHR, SOPs | No | — | No change to manufacturing processes. |
| Machines and equipment | Yes | — | Sealing performance check required for new packaging material. |
| Process Validation (IQ, OQ, PQ) | No | — | No validation required. |
| Production planning/Logistics | No | — | No impact on logistics. |
| Environmental and Premises | No | — | No impact on premises. |
| Others | No | — | No other impacts. |

Department: QC
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Equipment and Instruments | No | — | No impact on equipment. |
| Technical Specifications | Yes | [PMTS] - Packaging Material Specification | New specification for Tyvek pouch to be prepared. |
| Standard Testing Procedures | No | — | No change to testing procedures. |
| Sampling Plan | No | — | No change to sampling plan. |
| Quality Plan | No | — | No impact on quality plan. |
| Others | Yes | — | Training required for new material handling. |

Department: QA
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| QMS | Yes | [QASOP] - Quality Assurance SOP | QMS certificate from supplier to be collected. |
| Finished Device Specifications & DMR | No | — | No impact on DMR. |
| Shelf life | No | — | No impact on shelf life. |
| Suppliers and Sub-contractors/Quality Agreements/Audits | Yes | [SC] - Supplier Control, [ASL] - Approved Supplier List | New supplier requires profile, quality agreement, and supplier list update. |
| Others | No | — | No other impacts. |

Department: RA
| Possible Impact Area | Impact | Documents Impacted | Justification |
|----------------------|--------|---------------------|---------------|
| Technical Documentation/Regulatory Files | Yes | [RA] - Manufacturing License and QMS Details | Supplier details to be added to TMF. |
| Indications/Intended Use/PMS/Clinical | No | — | No impact on intended use. |
| Labeling/Artwork | No | — | No change to labeling. |
| Notification to NBs/Competent Authorities | No | — | No notification required. |
| Others | No | — | No other impacts. |

**Risk Assessment**: The new supplier may affect pouch quality or sealing performance; requires supplier QMS certificate, material testing, and sealing validation to mitigate risks.
**Impact Type**: Minor. The change is administrative, involving a new supplier with no impact on product safety or performance, managed through standard quality processes.
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
