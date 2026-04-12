import pdfplumber
import docx
import json
import sys
import re
# import spacy

##### Extract Text Functions ########

# extract text from input resume format pdf
def extract_text_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text 

# extract text from input resume format word document
def extract_text_word(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


###### Extract Section Information #######

# extract resume sections such as education experience projects skills certificates etc. 
def extract_sections(text):
    sections = {"education": "", "experience": [], "projects": [], "skills": "", "certifications": ""}
    current_section = None

    for line in text.split("\n"):
        clean_line = line.strip().lower()
        if "education" in clean_line:
            current_section = "education"
        elif "project" in clean_line:
            current_section = "projects"
        elif "experience" in clean_line:
            current_section = "experience"
        elif "skill" in clean_line:
            current_section = "skills"
        elif "certificat" in clean_line:
            current_section = "certifications"
        elif current_section:
            if current_section in ["experience", "projects"]:
                sections[current_section].append(line)
            else:
                sections[current_section] += line + "\n"

    # convert experience/projects into structured json structures 
    for key in ["experience", "projects"]:
        combined_text = "\n".join(sections[key])
        sections[key] = split_entries(combined_text)

    #  remove newlines for sections
    for key in ["education", "skills", "certifications"]:
        sections[key] = sections[key].strip()

    return sections


def parse_title_line(title_line):
    date_match = re.search(
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present)\s?\d{0,4}|Present)$',
        title_line, re.IGNORECASE)
    dates = date_match.group(1).strip() if date_match else ""
    line_no_dates = title_line.replace(dates, "").strip()
    if " - " in line_no_dates:
        parts = line_no_dates.split(" - ", 1)
    elif "-" in line_no_dates:
        parts = line_no_dates.split("-", 1)
    else:
        parts = [line_no_dates, ""]
    position = parts[0].strip()
    company = parts[1].strip() if len(parts) > 1 else ""
    return {"position": position, "company": company, "dates": dates}

# extract resume info email
def extract_email(text):
    match = re.search(r'\b[\w.-]+@[\w.-]+\.\w{2,4}\b', text)
    return match.group(0) if match else None

# extract resume info phone number
def extract_phone(text):
    phone_pattern = re.compile(
        r'(\+?\d{1,2}[\s\-\.]?)?'        # optional country code
        r'(\(?\d{3}\)?[\s\-\.]?)'        # area code with optional parentheses
        r'\d{3}[\s\-\.]?\d{4}'           # 7-digit number
    )
    match = phone_pattern.search(text)
    return match.group(0) if match else None

# extract resume info full name 
def extract_name(text):
    return text.strip().split("\n")[0]


###### Parse/ Format text #######
def normalize_text(text):
    # Normalize dash types
    text = text.replace("–", "-").replace("—", "-")
    
    # Normalize bullet types
    text = text.replace("•", "\u25cf")
    
    return text

def split_entries(text):
    text = normalize_text(text)
    entries = []
    possible_entries = re.split(r'\n(?=\u25cf|\w)', text.strip())
    
    current_entry = None
    for line in possible_entries:
        line = line.strip()
        if not line:
            continue
        if line.startswith("\u25cf") and current_entry:
            current_entry["details"].append(line[1:].strip())
        else:
            if current_entry:
                entries.append(current_entry)
            # Parse position/company/dates
            parsed = parse_title_line(line)
            parsed["details"] = []
            current_entry = parsed

    if current_entry:
        entries.append(current_entry)
    
    return entries

# main resume structure parser
def parse_resume(file_path):
    if file_path.lower().endswith(".pdf"):
        text = extract_text_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        text = extract_text_word(file_path)
    else:
        raise ValueError("Unsuported Resume File Type")
    
    data = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "sections": extract_sections(text)
    }
    return data
 
if __name__ == "__main__":
    # nlp = spacy.load("en_core_web_sm")
    file_path = sys.argv[1]
    parsed_text = parse_resume(file_path)
    print(parsed_text)
    json_str = json.dumps(parsed_text, indent=4)
    with open("sample.json", "w") as f:
        f.write(json_str)

