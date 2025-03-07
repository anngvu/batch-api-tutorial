# Example to use OpenAI batch API for batch labeling or other batch tasks

1. Convert publication metadata CSV into JSON schema format. Currently extracts only specified fields: Pubmed Id, Publication Assay, Publication Tumor Type, Publication Tissue, and Publication Dataset Alias.

```
 python csv_to_jsonschema.py publication.csv
```

2. `create_batch.py`


