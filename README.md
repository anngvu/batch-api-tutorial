# Exxample to create dataset and use OpenAI batch API

1. Convert publication metadata CSV into JSON schema format. Currently extracts only specified fields: Pubmed Id, Publication Assay, Publication Tumor Type, Publication Tissue, and Publication Dataset Alias.

```
 python csv_to_jsonschema.py publication.csv
```

2. `create_batch.py`


