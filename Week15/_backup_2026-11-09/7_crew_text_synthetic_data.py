# Legal Document Generator POC with CrewAI + Serper
#
# This script generates synthetic legal documents using CrewAI with web research capabilities via Serper API.
# Documents are saved as individual TXT files for easy model training.
# Note: All generated documents are synthetic and for training purposes only.

## Installation and Setup
# Install required packages
# ! pip install crewai crewai-tools langchain-openai python-dotenv faker

import os
import json
import requests
import shutil
from datetime import datetime, timedelta
from faker import Faker
import random
from dotenv import load_dotenv
from pathlib import Path

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, FileReadTool
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize tools
fake = Faker()
search_tool = SerperDevTool()
file_read_tool = FileReadTool()

os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_ROUTER_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
# os.environ['HUGGINGFACEHUB_API_TOKEN'] = os.getenv('HF_TOKEN')
# os.environ['LITELLM_LOG'] = 'DEBUG'
os.environ['OPENAI_API_BASE'] = 'https://openrouter.ai/api/v1'
os.environ['OPENAI_BASE_URL'] = 'https://openrouter.ai/api/v1'


# Configure LLM
llm = ChatOpenAI(
    model="openai/gpt-4o",
    temperature=0.7
)

# Verify API keys

# os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
# os.environ["SERPER_API_KEY"] = os.environ.get("SERPER_API_KEY")
# llm = LLM(model='openai/gpt-4o',api_key=os.environ.get("OPENAI_API_KEY"))


print("✓ Setup complete!")


## File Management Utilities

class LegalDocumentFileManager:
    """
    Manages file operations for legal document generation
    """

    def __init__(self, base_dir="legal_documents"):
        self.base_dir = Path(base_dir)
        self.setup_directories()

    def setup_directories(self):
        """Create directory structure for legal documents"""
        directories = [
            'complaints',
            'motions',
            'contracts',
            'memos',
            'briefs',
            'agreements',
            'templates',
            'metadata'
        ]

        for dir_name in directories:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        print(f"✓ Directory structure created in: {self.base_dir}")

    def save_document_txt(self, content, doc_type, metadata=None):
        """Save document as TXT file with metadata"""

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = metadata.get('case_number', f"DOC_{random.randint(1000, 9999)}") if metadata else f"DOC_{random.randint(1000, 9999)}"
        safe_case_id = case_id.replace('-', '_').replace(' ', '_')

        filename = f"{safe_case_id}_{timestamp}.txt"
        file_path = self.base_dir / doc_type / filename

        # Prepare content with header
        header = f"""
========================================
SYNTHETIC LEGAL DOCUMENT - FOR TRAINING ONLY
========================================
Document Type: {doc_type.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Document ID: {case_id}
========================================

"""

        footer = f"""

========================================
END OF SYNTHETIC DOCUMENT
This document was generated for AI training purposes.
Do not use for actual legal proceedings.
========================================
"""

        full_content = header + content + footer

        # Save document
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        # Save metadata separately
        if metadata:
            metadata_filename = f"{safe_case_id}_{timestamp}_metadata.json"
            metadata_path = self.base_dir / 'metadata' / metadata_filename

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)

        print(f"✓ Saved: {file_path}")
        return str(file_path)

    def get_document_count(self):
        """Get count of generated documents by type"""
        counts = {}

        for subdir in self.base_dir.iterdir():
            if subdir.is_dir() and subdir.name != 'metadata':
                txt_files = list(subdir.glob('*.txt'))
                counts[subdir.name] = len(txt_files)

        return counts

    def clean_documents(self, doc_type=None):
        """Clean generated documents"""
        if doc_type:
            target_dir = self.base_dir / doc_type
            if target_dir.exists():
                shutil.rmtree(target_dir)
                target_dir.mkdir()
                print(f"✓ Cleaned {doc_type} documents")
        else:
            shutil.rmtree(self.base_dir)
            self.setup_directories()
            print("✓ Cleaned all documents")

# Initialize file manager
file_manager = LegalDocumentFileManager()


## Web Research for Legal Templates

def research_legal_templates(document_type):
    """
    Research legal document templates and examples using Serper
    """

    search_queries = {
        'complaint': [
            "civil complaint template format legal document",
            "federal court complaint example structure",
            "civil litigation complaint format sections"
        ],
        'motion': [
            "motion to dismiss template legal format",
            "summary judgment motion example structure",
            "federal rules civil procedure motion format"
        ],
        'contract': [
            "commercial contract template clauses",
            "service agreement legal format example",
            "business contract standard provisions"
        ],
        'memo': [
            "legal memorandum format template structure",
            "law firm internal memo example",
            "legal analysis memorandum format"
        ]
    }

    research_results = []

    if document_type in search_queries:
        for query in search_queries[document_type]:
            try:
                # Using search_tool to find relevant information
                result = search_tool.run(query)
                research_results.append({
                    'query': query,
                    'results': result
                })
                print(f"✓ Researched: {query}")
            except Exception as e:
                print(f"⚠️ Search failed for '{query}': {e}")

    return research_results

def extract_template_insights(research_results):
    """
    Extract key insights from research results
    """

    insights = {
        'common_sections': [],
        'formatting_notes': [],
        'legal_language_patterns': []
    }

    # Process research results to extract patterns
    for result in research_results:
        if isinstance(result.get('results'), str):
            content = result['results'].lower()

            # Look for common legal document sections
            section_keywords = [
                'caption', 'jurisdiction', 'venue', 'parties', 'facts',
                'causes of action', 'prayer for relief', 'signature',
                'whereas', 'recitals', 'definitions', 'termination'
            ]

            for keyword in section_keywords:
                if keyword in content:
                    insights['common_sections'].append(keyword)

    # Remove duplicates
    insights['common_sections'] = list(set(insights['common_sections']))

    return insights


## Enhanced Data Generation with Research

def generate_enhanced_case_data():
    """Generate enhanced synthetic case data"""

    case_types = [
        "Contract Dispute", "Personal Injury", "Employment Discrimination",
        "Real Estate Litigation", "Business Tort", "Breach of Fiduciary Duty",
        "Intellectual Property Infringement", "Securities Fraud", "Insurance Bad Faith",
        "Product Liability", "Professional Malpractice", "Construction Defect"
    ]

    courts = [
        f"{fake.city()} County Superior Court",
        f"United States District Court for the {fake.state()} District",
        f"{fake.state()} Court of Appeals",
        f"{fake.city()} Municipal Court"
    ]

    return {
        "case_number": f"CV-{random.randint(2020, 2024)}-{random.randint(10000, 99999)}",
        "case_type": random.choice(case_types),
        "plaintiff": fake.company() if random.choice([True, False]) else fake.name(),
        "defendant": fake.company() if random.choice([True, False]) else fake.name(),
        "plaintiff_attorney": fake.name(),
        "defendant_attorney": fake.name(),
        "court": random.choice(courts),
        "judge": f"Hon. {fake.name()}",
        "filing_date": fake.date_between(start_date='-2y', end_date='today'),
        "amount_in_controversy": random.randint(25000, 10000000),
        "law_firm_plaintiff": f"{fake.last_name()}, {fake.last_name()} & Associates LLP",
        "law_firm_defendant": f"{fake.last_name()} Law Group PC",
        "address_plaintiff": fake.address(),
        "address_defendant": fake.address(),
        "jurisdiction": fake.state(),
        "cause_of_action": random.choice([
            "Breach of Contract", "Negligence", "Fraud", "Unjust Enrichment",
            "Conversion", "Defamation", "Intentional Infliction of Emotional Distress"
        ])
    }

def generate_enhanced_contract_data():
    """Generate enhanced synthetic contract data"""

    contract_types = [
        "Software License Agreement", "Master Service Agreement", "Non-Disclosure Agreement",
        "Asset Purchase Agreement", "Commercial Lease Agreement", "Joint Venture Agreement",
        "Distribution Agreement", "Employment Agreement", "Consulting Agreement",
        "Supply Agreement", "Franchise Agreement", "Technology Transfer Agreement"
    ]

    return {
        "contract_type": random.choice(contract_types),
        "party_a": fake.company(),
        "party_b": fake.company() if random.choice([True, False]) else fake.name(),
        "effective_date": fake.date_between(start_date='-6m', end_date='+1m'),
        "termination_date": fake.date_between(start_date='+1y', end_date='+5y'),
        "contract_value": random.randint(10000, 5000000),
        "governing_law": fake.state(),
        "jurisdiction": f"{fake.city()}, {fake.state()}",
        "payment_terms": random.choice([
            "Net 30 days", "Net 60 days", "Payment upon delivery",
            "Monthly installments", "Quarterly payments"
        ]),
        "renewal_terms": random.choice([
            "Automatic renewal", "Mutual consent", "30-day notice required"
        ])
    }


## Enhanced CrewAI Agents with Research Capabilities

# Enhanced agents with research capabilities

research_agent = Agent(
    role="Legal Research Specialist",
    goal="Research legal document templates and best practices using web search",
    backstory="""You are a legal research specialist who uses web search to find
    current legal document templates, formatting standards, and best practices.
    You analyze multiple sources to understand proper legal document structure.""",
    tools=[search_tool],
    llm=llm,
    verbose=True
)

litigation_attorney = Agent(
    role="Senior Litigation Attorney",
    goal="Generate comprehensive and realistic litigation documents based on research findings",
    backstory="""You are a senior litigation attorney with 20+ years of experience
    in federal and state courts. You create documents that follow current legal
    standards and incorporate best practices from recent case examples.""",
    llm=llm,
    verbose=True
)

contract_specialist = Agent(
    role="Corporate Contract Specialist",
    goal="Create detailed and legally sound contract documents with modern commercial terms",
    backstory="""You are a corporate contract specialist with expertise in
    commercial transactions. You draft contracts that reflect current market
    practices and include comprehensive risk management provisions.""",
    llm=llm,
    verbose=True
)

document_reviewer = Agent(
    role="Legal Document Quality Reviewer",
    goal="Review and enhance legal documents for accuracy, completeness, and professional standards",
    backstory="""You are a meticulous legal document reviewer who ensures all
    documents meet the highest professional standards, include proper legal
    citations, and follow jurisdictional requirements.""",
    llm=llm,
    verbose=True
)

file_manager_agent = Agent(
    role="Document Management Specialist",
    goal="Format and save legal documents as properly structured text files",
    backstory="""You are a document management specialist who ensures all
    generated legal documents are properly formatted, saved with appropriate
    metadata, and organized for training purposes.""",
    tools=[file_read_tool],
    llm=llm,
    verbose=True
)


## Enhanced Document Generation Tasks

def create_research_task(document_type):
    """Create a research task for legal document templates"""

    return Task(
        description=f"""
        Research current legal document templates and formatting standards for {document_type} documents.

        Find information about:
        1. Standard document structure and sections
        2. Required legal formatting and citation styles
        3. Current best practices and conventions
        4. Jurisdictional requirements and variations
        5. Common clauses and legal language patterns

        Search for examples from reputable legal sources, court websites,
        and legal practice guides. Focus on finding templates that show
        proper structure and professional formatting.

        Provide a comprehensive summary of findings that can guide document generation.
        """,
        agent=research_agent,
        expected_output=f"Comprehensive research summary on {document_type} document standards and templates"
    )

def create_enhanced_complaint_task(case_data, research_context=""):
    return Task(
        description=f"""
        Draft a comprehensive civil complaint incorporating research findings and best practices.

        Case Details:
        - Case Number: {case_data['case_number']}
        - Case Type: {case_data['case_type']}
        - Plaintiff: {case_data['plaintiff']}
        - Defendant: {case_data['defendant']}
        - Court: {case_data['court']}
        - Amount in Controversy: ${case_data['amount_in_controversy']:,}
        - Cause of Action: {case_data['cause_of_action']}

        Research Context: {research_context}

        Create a complete complaint with:
        1. Proper caption with case styling
        2. Parties section with detailed identification
        3. Jurisdiction and venue allegations
        4. Factual background (numbered paragraphs)
        5. Multiple causes of action with elements
        6. Damages allegations
        7. Prayer for relief with specific requests
        8. Jury demand
        9. Verification clause
        10. Attorney signature block with bar number

        Include realistic legal citations and follow current formatting standards.
        Make content detailed and professional while keeping it clearly synthetic.
        """,
        agent=litigation_attorney,
        expected_output="A complete, professionally formatted civil complaint ready for filing"
    )

def create_enhanced_contract_task(contract_data, research_context=""):
    return Task(
        description=f"""
        Draft a comprehensive {contract_data['contract_type']} incorporating modern commercial practices.

        Contract Details:
        - Contract Type: {contract_data['contract_type']}
        - Party A: {contract_data['party_a']}
        - Party B: {contract_data['party_b']}
        - Contract Value: ${contract_data['contract_value']:,}
        - Effective Date: {contract_data['effective_date']}
        - Term: {contract_data['termination_date']}
        - Governing Law: {contract_data['governing_law']}
        - Payment Terms: {contract_data['payment_terms']}

        Research Context: {research_context}

        Include comprehensive sections:
        1. Cover page with contract title and parties
        2. Table of contents (for longer contracts)
        3. Preamble with party identification
        4. Recitals explaining transaction background
        5. Definitions section with key terms
        6. Main operative provisions and obligations
        7. Payment and financial terms
        8. Performance standards and deliverables
        9. Intellectual property provisions
        10. Confidentiality and non-disclosure
        11. Termination and breach provisions
        12. Dispute resolution mechanisms
        13. Force majeure and risk allocation
        14. Governing law and jurisdiction
        15. General provisions (integration, amendments, etc.)
        16. Signature pages with execution details

        Make the contract comprehensive and commercially realistic.
        """,
        agent=contract_specialist,
        expected_output=f"A complete, professionally drafted {contract_data['contract_type']}"
    )

def create_review_task():
    return Task(
        description="""
        Review the generated legal document for:

        1. Legal accuracy and completeness
        2. Professional formatting and structure
        3. Proper legal citations and references
        4. Consistency in terminology and style
        5. Inclusion of all required legal elements
        6. Appropriate disclaimers and notices
        7. Compliance with document type standards

        Enhance the document by:
        - Adding any missing standard provisions
        - Improving legal language and precision
        - Ensuring proper paragraph numbering
        - Verifying citation formats
        - Adding synthetic case law references where appropriate

        Provide a final, polished version ready for file output.
        """,
        agent=document_reviewer,
        expected_output="A polished, professional legal document ready for training use"
    )


## Enhanced Document Generation Function

def generate_legal_document_with_research(document_type, num_documents=1, use_research=True):
    """
    Generate legal documents with web research and save as TXT files

    Args:
        document_type: Type of document ('complaint', 'motion', 'contract', 'memo')
        num_documents: Number of documents to generate
        use_research: Whether to perform web research first

    Returns:
        List of generated file paths
    """

    generated_files = []
    research_context = ""

    # Perform research if requested
    if use_research:
        print(f"🔍 Researching {document_type} templates and standards...")

        research_task = create_research_task(document_type)
        research_crew = Crew(
            agents=[research_agent],
            tasks=[research_task],
            process=Process.sequential,
            verbose=False
        )

        try:
            research_result = research_crew.kickoff()
            research_context = str(research_result)[:2000]  # Limit context length
            print("✓ Research completed")
        except Exception as e:
            print(f"⚠️ Research failed: {e}")
            research_context = "No research context available"

    # Generate documents
    for i in range(num_documents):
        print(f"\n📝 Generating {document_type} {i+1}/{num_documents}...")

        try:
            # Generate case or contract data
            if document_type in ['complaint', 'motion', 'memo']:
                case_data = generate_enhanced_case_data()
                metadata = case_data

                if document_type == 'complaint':
                    main_task = create_enhanced_complaint_task(case_data, research_context)
                elif document_type == 'motion':
                    # You can add enhanced motion task here similar to complaint
                    main_task = create_enhanced_complaint_task(case_data, research_context)  # Placeholder
                elif document_type == 'memo':
                    # You can add enhanced memo task here
                    main_task = create_enhanced_complaint_task(case_data, research_context)  # Placeholder

            elif document_type == 'contract':
                contract_data = generate_enhanced_contract_data()
                metadata = contract_data
                main_task = create_enhanced_contract_task(contract_data, research_context)

            # Create review task
            review_task = create_review_task()

            # Create and execute crew
            crew = Crew(
                agents=[litigation_attorney, contract_specialist, document_reviewer],
                tasks=[main_task, review_task],
                process=Process.sequential,
                verbose=False
            )

            # Generate document
            result = crew.kickoff()

            # Save as TXT file
            file_path = file_manager.save_document_txt(
                content=str(result),
                doc_type=document_type + 's',  # Pluralize for directory name
                metadata=metadata
            )

            generated_files.append(file_path)
            print(f"✓ {document_type.capitalize()} {i+1} generated and saved")

        except Exception as e:
            print(f"❌ Error generating {document_type} {i+1}: {e}")
            continue

    return generated_files

def generate_document_dataset(output_dir="legal_documents", counts=None):
    """
    Generate a comprehensive dataset of legal documents as TXT files
    """

    if counts is None:
        counts = {
            'complaint': 3,
            'contract': 3,
            'motion': 2,
            'memo': 2
        }

    # Update file manager base directory
    global file_manager
    file_manager = LegalDocumentFileManager(output_dir)

    all_files = []

    for doc_type, count in counts.items():
        print(f"\n{'='*60}")
        print(f"Generating {count} {doc_type}(s)...")
        print(f"{'='*60}")

        files = generate_legal_document_with_research(doc_type, count, use_research=True)
        all_files.extend(files)

    # Print summary
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Total files generated: {len(all_files)}")
    print(f"✓ Saved in directory: {output_dir}")

    # Show file counts
    counts = file_manager.get_document_count()
    for doc_type, count in counts.items():
        print(f"  {doc_type}: {count} files")

    return all_files


## Generate Sample Documents

# Test the system with a single document
print("Testing document generation...")
print("Current directory structure:")
print(file_manager.get_document_count())

# Generate one complaint as a test
print("\nGenerating test complaint...")
test_files = generate_legal_document_with_research('complaint', 1, use_research=True)

if test_files:
    print(f"\n✓ Test file generated: {test_files[0]}")

    # Read and display first 1000 characters
    with open(test_files[0], 'r', encoding='utf-8') as f:
        content = f.read()
        print("\nFirst 1000 characters of generated document:")
        print("-" * 50)
        print(content[:1000] + "..." if len(content) > 1000 else content)
else:
    print("❌ Test generation failed")


# Generate a contract example
print("Generating test contract...")
contract_files = generate_legal_document_with_research('contract', 1, use_research=True)

if contract_files:
    print(f"\n✓ Contract file generated: {contract_files[0]}")

    # Show file structure
    print("\nCurrent file structure:")
    counts = file_manager.get_document_count()
    for doc_type, count in counts.items():
        print(f"  {doc_type}: {count} files")


## Generate Complete Dataset

# Generate a full dataset
# Adjust counts as needed for your training requirements

dataset_config = {
    'complaint': 3,    # 3 civil complaints
    'contract': 3,     # 3 various contracts
    'motion': 3,        # 3 legal motions
    'memo': 3           # 3 legal memos
}

print("Starting full dataset generation...")
print(f"Total documents to generate: {sum(dataset_config.values())}")
print("⚠️ This will take 15-30 minutes and use significant API credits")

# Uncomment the next line to start full generation
all_generated_files = generate_document_dataset("legal_training_data", dataset_config)

print("\nTo generate the complete dataset, uncomment the line above.")
print("This will create 30 legal documents with web research for training.")


## Document Analysis and Validation

def analyze_generated_files(base_dir="legal_documents"):
    """
    Analyze the generated TXT files for training readiness
    """

    base_path = Path(base_dir)
    analysis = {
        'total_files': 0,
        'total_size_mb': 0,
        'by_type': {},
        'avg_length': {},
        'file_list': []
    }

    if not base_path.exists():
        print(f"Directory {base_dir} does not exist")
        return analysis

    for subdir in base_path.iterdir():
        if subdir.is_dir() and subdir.name not in ['metadata', 'templates']:
            doc_type = subdir.name
            txt_files = list(subdir.glob('*.txt'))

            if txt_files:
                total_length = 0
                for txt_file in txt_files:
                    file_size = txt_file.stat().st_size
                    analysis['total_size_mb'] += file_size / (1024 * 1024)

                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_length += len(content)

                    analysis['file_list'].append(str(txt_file))

                analysis['by_type'][doc_type] = len(txt_files)
                analysis['avg_length'][doc_type] = total_length // len(txt_files) if txt_files else 0
                analysis['total_files'] += len(txt_files)

    # Print analysis
    print(f"\n{'='*60}")
    print("DATASET ANALYSIS")
    print(f"{'='*60}")
    print(f"Total files: {analysis['total_files']}")
    print(f"Total size: {analysis['total_size_mb']:.2f} MB")

    print("\nDocument types:")
    for doc_type, count in analysis['by_type'].items():
        avg_chars = analysis['avg_length'].get(doc_type, 0)
        print(f"  {doc_type}: {count} files, avg {avg_chars:,} characters")

    print("\nFirst 5 generated files:")
    for i, file_path in enumerate(analysis['file_list'][:5]):
        print(f"  {i+1}. {Path(file_path).name}")

    return analysis

# Analyze current files
current_analysis = analyze_generated_files()


## Training Data Export Functions

def create_training_manifest(base_dir="legal_documents"):
    """
    Create a manifest file for training data
    """

    base_path = Path(base_dir)
    manifest = []

    for subdir in base_path.iterdir():
        if subdir.is_dir() and subdir.name not in ['metadata', 'templates']:
            doc_type = subdir.name

            for txt_file in subdir.glob('*.txt'):
                # Find corresponding metadata
                metadata_file = base_path / 'metadata' / f"{txt_file.stem}_metadata.json"

                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                manifest.append({
                    'file_path': str(txt_file.relative_to(base_path)),
                    'document_type': doc_type.rstrip('s'),  # Remove plural
                    'file_size': txt_file.stat().st_size,
                    'metadata_file': str(metadata_file.relative_to(base_path)) if metadata_file.exists() else None,
                    'metadata': metadata
                })

    # Save manifest
    manifest_path = base_path / 'training_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"✓ Training manifest created: {manifest_path}")
    print(f"  Total entries: {len(manifest)}")

    return manifest

def prepare_for_model_training(base_dir="legal_documents"):
    """
    Prepare the complete dataset for model training
    """

    print("Preparing dataset for model training...")

    # Create manifest
    manifest = create_training_manifest(base_dir)

    # Create summary statistics
    analysis = analyze_generated_files(base_dir)

    # Create README for the dataset
    readme_content = f"""# Legal Document Training Dataset

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Overview
- Total files: {analysis['total_files']}
- Total size: {analysis['total_size_mb']:.2f} MB
- Document types: {', '.join(analysis['by_type'].keys())}

## File Structure
```
{base_dir}/
├── complaints/     # Civil complaint documents
├── contracts/      # Various contract types
├── motions/        # Legal motions and briefs
├── memos/          # Legal memoranda
├── metadata/       # JSON metadata for each document
└── training_manifest.json  # Complete file manifest
```

## Document Types and Counts
""" + "\n".join([f"- {doc_type}: {count} files" for doc_type, count in analysis['by_type'].items()]) + f"""

## Usage Notes
- All documents are synthetic and generated for training purposes
- Each document includes disclaimers indicating synthetic nature
- Metadata files contain case/contract details used for generation
- Documents follow realistic legal formatting and structure

## Model Training Recommendations
1. Use document type classification as initial task
2. Implement named entity recognition for legal entities
3. Train on legal language patterns and clause identification
4. Consider fine-tuning for specific legal document generation

## Disclaimer
These documents are entirely synthetic and created for AI training purposes.
They should not be used for actual legal proceedings or advice.
"""

    readme_path = Path(base_dir) / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"✓ README created: {readme_path}")
    print(f"\n🎉 Dataset ready for model training in: {base_dir}")

    return {
        'manifest': manifest,
        'analysis': analysis,
        'base_dir': base_dir
    }

# Prepare current dataset
if file_manager.get_document_count():
    training_data = prepare_for_model_training()
    print("\n✅ Your legal document dataset is ready for model training!")
else:
    print("\n📝 Generate some documents first to create the training dataset.")


## Usage Instructions
#
# ### Setup Requirements:
# 1. OpenAI API Key: Set `OPENAI_API_KEY` in your environment
# 2. Serper API Key: Get free key at https://serper.dev/ and set `SERPER_API_KEY`
# 3. Install packages: Run the pip install command above
#
# ### Key Features:
# 1. Web Research: Uses Serper to find current legal document templates
# 2. TXT Output: Saves documents as individual text files with metadata
# 3. File Management: Organized directory structure for different document types
# 4. Training Ready: Includes manifest and analysis for ML training
#
# ### Generated File Structure:
# legal_documents/
# ├── complaints/          # Civil complaints
# ├── contracts/           # Various contracts
# ├── motions/            # Legal motions
# ├── memos/              # Legal memoranda
# ├── metadata/           # JSON metadata files
# ├── training_manifest.json
# └── README.md
#
# ### For Your Model Training:
# 1. Each document is a separate TXT file
# 2. Metadata available in JSON format
# 3. Manifest file lists all documents with metadata
# 4. Documents include proper legal formatting
# 5. Clear synthetic disclaimers included
#
# ### Customization:
# - Modify `dataset_config` to change document counts
# - Adjust `case_types` and `contract_types` for specific domains
# - Update research queries for different legal areas
# - Change file organization in `LegalDocumentFileManager`
