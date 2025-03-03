import pandas as pd
import json
import sys

def csv_to_json_schema(csv_file):
    """
    Convert publication CSV metadata specification to JSON schema
    with only the specified fields.
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        dict: JSON schema representation
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter the DataFrame to include only the target fields
    target_fields = [
        "Pubmed Id",
        "Publication Assay",
        "Publication Tumor Type",
        "Publication Tissue",
        "Publication Dataset Alias"
    ]
    
    filtered_df = df[df['Attribute'].isin(target_fields)]
    
    # Create the JSON schema structure
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Publication Metadata Schema",
        "description": "Schema for publication metadata with selected fields",
        "properties": {},
        "required": []
    }
    
    # Populate the schema with filtered fields
    for _, row in filtered_df.iterrows():
        # Convert attribute name to camelCase for property keys (removing spaces)
        property_key = row['Attribute'].replace(" ", "")
        
        # Check if the field allows multiple values (indicated by validation rule "list like")
        is_array = row['Validation Rules'] == "list like"
        
        # Create property definition
        if is_array:
            property_def = {
                "type": "array",
                "title": row['Attribute'],  # Original name with spaces
                "description": row['Description'],
                "items": {
                    "type": "string"
                }
            }
            
            # Add enum values if Valid Values exist
            if pd.notna(row['Valid Values']) and row['Valid Values'] is not None:
                # Handle comma-separated valid values
                valid_values = [v.strip() for v in row['Valid Values'].split(',')]
                property_def["items"]["enum"] = valid_values
        else:
            property_def = {
                "type": "string",
                "title": row['Attribute'],  # Original name with spaces
                "description": row['Description']
            }
            
            # Add enum values if Valid Values exist
            if pd.notna(row['Valid Values']) and row['Valid Values'] is not None:
                # Handle comma-separated valid values
                valid_values = [v.strip() for v in row['Valid Values'].split(',')]
                property_def["enum"] = valid_values
        
        # Add to properties
        schema["properties"][property_key] = property_def
        
        # Add to required fields if required
        if pd.notna(row['Required']) and row['Required'] == True:
            schema["required"].append(property_key)
    
    return schema

def generate_schema_file(csv_file, output_file):
    """
    Generate a JSON schema file from the CSV metadata
    
    Args:
        csv_file (str): Path to the CSV file
        output_file (str): Path to save the JSON schema
    """
    schema = csv_to_json_schema(csv_file)
    
    # Write the schema to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"JSON schema generated and saved to {output_file}")
    return schema


# Command line usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python publication_schema_generator.py input.csv output_schema.json")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Generate the schema
    schema = generate_schema_file(input_file, output_file)
    print("Schema generation complete.")