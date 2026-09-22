# Property Moduler

Property Moduler is a Python-based property data consolidation and review application designed to collect property information from multiple documents, compare records, identify conflicts or duplicates, and present the consolidated information through a clear user interface.

The main purpose of the project is to help users organize property-related information when the same property may appear in different documents with incomplete, duplicated, or conflicting values.

---

## 1. Problem It Solves

Property information is often spread across multiple files and documents.

The same property may have:

- Different addresses written in slightly different formats
- Missing information
- Duplicate records
- Conflicting values
- Multiple documents referring to the same property
- Similar-looking records that actually belong to different properties
- Different document types with different levels of reliability

Manually comparing all of these records can be slow and error-prone.

Property Moduler helps organize this process by keeping property values together with their source documents and document types, allowing records to be compared and reviewed before they are treated as consolidated information.

The system is intended to distinguish between:

- Records that can reasonably be consolidated
- Records that should remain separate
- Conflicting information
- Records that require human review

The reviewed repository already represents values together with their source documents and document types, which is an important part of the consolidation workflow. :chatgpt-content-reference{index="0"}

---

## 2. Core Features

### Property Data Collection

The system accepts property-related information and organizes it into structured records.

### Source Tracking

Each important value can be associated with:

- Source document
- Document type
- Property record

This makes it possible to understand where a particular value came from.

### Property Record Consolidation

The application can compare property information and help determine whether multiple records may represent the same property.

### Conflict Detection

When different documents contain conflicting values, the system can identify that the information is not fully consistent.

### Confidence / Priority Rules

The current project includes configured confidence or priority values associated with document categories.

These values should be understood as configured rules rather than automatically proven probabilities of correctness. :chatgpt-content-reference{index="1"}

### Human Review

Cases that cannot be safely resolved automatically can be left for manual review instead of forcing an incorrect merge.

Examples include:

- Similar addresses belonging to different units
- Missing identifying information
- Conflicting values
- Duplicate uploads
- Uncertain property matches

### Data Presentation

The application provides a user-facing interface for viewing and reviewing property information.

### Database Interaction

Property data can be stored and retrieved through the application's database layer.

---

## 3. Tech Stack

The project is built around the following technologies:

- **Python** — core application and business logic
- **Streamlit** — user interface and data presentation
- **Database layer** — storing and retrieving property records
- **File / document processing** — handling property-related documents
- **Python data-processing logic** — comparing and consolidating records
- **pytest** — recommended for automated testing and regression testing

If the current version of the repository uses SQLite, PostgreSQL, OCR, or another specific document-processing library, those technologies should be listed here according to the actual implementation.

---

## 4. Setup and Installation

### Clone the Repository

```bash
git clone https://github.com/amnahadia34-dotcom/Property-moduler.git
Move into the project:
cd Property-moduler
Open the application folder:
cd "jerry project folder"
Create a Virtual Environment
Windows:
python -m venv venv
venv\Scripts\activate
macOS / Linux:
python3 -m venv venv
source venv/bin/activate
Install Dependencies
If the project contains a requirements.txt file:
pip install -r requirements.txt
Run the Application
If the main application is a Streamlit application:
streamlit run app.py
If the main file has another name, replace app.py with the actual entry-point filename.
5. Demo and Testing
The project should be demonstrated using a small set of property records containing both normal and difficult cases.
Normal Test
Upload or enter two records that clearly belong to the same property.
Expected result:
Records recognized as belonging to the same property
        ↓
Relevant values compared
        ↓
Sources preserved
        ↓
Consolidated information displayed
Different Property Test
Use similar-looking addresses that belong to different apartments or units.
Expected result:
Records remain separate
Conflicting Data Test
Provide two documents containing different values for the same property field.
Expected result:
Conflict identified
        ↓
Source of each value preserved
        ↓
Case reviewed according to defined rules
Duplicate Upload Test
Upload the same document more than once.
Expected behavior should be defined and tested so duplicate information does not silently distort the final result.
Missing Data Test
Use a record with missing address or identifying information.
Expected result:
Insufficient information
        ↓
Needs review
Automated Testing
A strong automated test should compare:
Expected Result
        VS
Actual Result
The earlier repository version mainly printed database-operation results rather than asserting that the results matched expected outcomes, so converting these into real automated assertions is an important improvement.     Amna_Aurangzaib_Technical_and_C…
Recommended test command:
pytest
Important cases to test include:
- Missing addresses
- Similar addresses for different units
- Duplicate uploads
- Conflicting values
- Malformed files
- Missing identifying information
- Incorrect consolidation
- Previously discovered bugs
These are also the kinds of cases recommended in the technical assessment of the project.     Amna_Aurangzaib_Technical_and_C…
6. Current Limitations
The project is a practical development project and should not yet be treated as a fully verified production property-management system.
Current areas that require further strengthening include:
Confidence Meaning
Configured confidence values should not automatically be presented as statistical probabilities unless they have been independently measured and validated.
Date-Aware Conflict Resolution
The reviewed version could prefer a value processed later without necessarily checking whether the underlying document itself was newer.
A document processed later is not always the most recent document.     Amna_Aurangzaib_Technical_and_C…
Automated Tests
More assertion-based automated tests are required.
Difficult Matching Cases
Property matching rules need to be tested carefully for:
- Apartment/unit differences
- Similar addresses
- Incomplete records
- Conflicting documents
Documentation
Setup instructions, supported entry points, configuration, testing commands, and known limitations should remain documented so another developer can reproduce the project.     Amna_Aurangzaib_Technical_and_C…
Production Readiness
Before real production deployment, additional work may be required around:
- Authentication
- Security
- Error handling
- Logging
- Database reliability
- Backup and recovery
- Access control
- Testing
- Deployment
- Monitoring
7. Contribution and Ownership
This project may contain collaborative work, so individual contributions should be stated clearly.
