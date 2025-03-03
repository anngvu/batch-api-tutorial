import requests
import csv
import json
import time
import tiktoken
import pandas as pd
import os
from io import StringIO
from xml.etree import ElementTree as ET

def fetch_pmcid_from_pmid(pmid):
    """Fetch PMCID from PMID using NCBI's ID Converter API"""
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=my_tool&email=nf-osi@sagebionetworks.org&ids={pmid}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        records = data.get('records', [])
        if records and 'pmcid' in records[0]:
            return records[0]['pmcid']
    return None

def fetch_article_text(pmcid):
    """Fetch article text content using PMC's BioC API and save XML to local folder"""
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
    response = requests.get(url)
    
    if response.status_code == 200:
        # Create directory for XML files if it doesn't exist
        import os
        os.makedirs("xml_content", exist_ok=True)
        
        # Save the XML content to a file
        xml_file_path = f"xml_content/{pmcid}.xml"
        with open(xml_file_path, "wb") as xml_file:
            xml_file.write(response.content)
        
        try:
            # Parse XML content
            root = ET.fromstring(response.content)
            # Extract all text passages
            passages = root.findall(".//passage/text")
            text_content = " ".join([p.text for p in passages if p.text])
            return text_content
        except ET.ParseError:
            print(f"XML parsing error for PMCID {pmcid}")
            return None
    return None

def count_tokens(text, model="gpt-4"):
    """Count tokens in text using tiktoken"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def main():
    # Load CSV data
    csv_file = "20250106_publicationsmanifestfinal.csv"
    df = pd.read_csv(csv_file)
    
    # Load schema data
    with open("pub_subschema.json", "r") as f:
        schema = json.load(f)
    
    # Filter for open access publications only
    open_access_df = df[df["Publication Accessibility"] == "Open Access"]
    
    # Prepare JSON Lines output file
    jsonl_output = "datasets/publication_dataset.jsonl"
    
    # Prepare log file for PMCIDs and token counts
    log_file = "pmcid_token_log.csv"
    
    # Initialize log file with headers
    with open(log_file, "w") as logfile:
        logfile.write("PMID,PMCID,TokenCount,Included\n")
    
    with open(jsonl_output, "w") as outfile, open("pmcid_token_log.csv", "a") as logfile:
        for i, row in open_access_df.iterrows():
            pmid = str(row["Pubmed Id"])
            print(f"Processing PMID: {pmid}")
            
            # Get PMCID from PMID
            pmcid = fetch_pmcid_from_pmid(pmid)
            
            if pmcid:
                print(f"Found PMCID: {pmcid}")
                
                # Fetch article text
                article_text = fetch_article_text(pmcid)
                
                if article_text:
                    # Count tokens
                    token_count = count_tokens(article_text)
                    print(f"Token count: {token_count}")
                    
                    included = "No"
                    if token_count < 200000:
                        # Create a more detailed system prompt
                        system_content = """You are an expert curation assistant who reviews biomedical publications to extract and classify key metadata attributes. 

Your task is to:
1. Carefully read the publication content
2. Identify all relevant metadata elements defined in the schema
3. Select ONLY values from the provided controlled vocabularies in the schema
4. Format your response as valid JSON matching the required schema
5. For fields that allow multiple values, use comma-separated format if multiple values apply
6. If you're uncertain about a value, select the most appropriate option based on available evidence

Respond only with the completed JSON metadata, properly formatted according to the schema."""
                        
                        # Format schema and content for user message
                        schema_str = json.dumps(schema)
                        
                        # Extract publication metadata from the row
                        pub_title = row.get("Publication Title", "")
                        pub_journal = row.get("Publication Journal", "")
                        pub_year = str(row.get("Publication Year", ""))
                        pub_authors = row.get("Publication Authors", "")
                        pub_abstract = row.get("Publication Abstract", "")
                        
                        # Structure the user content in a more instructive way
                        user_content = f"""# Publication Metadata Extraction Task

## Instructions
Please review the publication content and extract the following metadata according to the provided schema:
1. Publication Assay - Select all applicable assays used in the research
2. Publication Tumor Type - Select all applicable tumor types studied
3. Publication Tissue - Select all applicable tissue types examined
4. Publication Dataset Alias - Extract any mentioned dataset identifiers (e.g., GSE12345, DOI)

## Schema
{schema_str}

## Publication Information
- Title: {pub_title}
- Journal: {pub_journal}
- Year: {pub_year}
- Authors: {pub_authors}
- PMID: {pmid}
- PMCID: {pmcid}

## Abstract
{pub_abstract}

## Full Publication Content
{article_text}
"""
                        
                        # Create entry for JSONL file
                        entry = {
                            "custom_id": f"pub-{pmid}",
                            "method": "POST",
                            "url": "/v1/chat/completions",
                            "body": {
                                "model": "gpt-4o-mini",
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": system_content
                                    },
                                    {
                                        "role": "user",
                                        "content": user_content
                                    }
                                ]
                            }
                        }
                        
                        # Write to JSON Lines file
                        outfile.write(json.dumps(entry) + "\n")
                        print(f"Added PMID {pmid} to dataset")
                        included = "Yes"
                    else:
                        print(f"Skipping PMID {pmid}: Too many tokens ({token_count})")
                    
                    # Log PMCID and token count
                    logfile.write(f"{pmid},{pmcid},{token_count},{included}\n")
                else:
                    print(f"Failed to fetch article text for PMCID {pmcid}")
                    logfile.write(f"{pmid},{pmcid},0,Error-NoText-or-XMLParseError\n")
            else:
                print(f"No PMCID found for PMID {pmid}")
                logfile.write(f"{pmid},None,0,Error-NoPMCID\n")
            
            # Add a small delay to avoid overloading the API
            time.sleep(1)

if __name__ == "__main__":
    main()
