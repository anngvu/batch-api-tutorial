from openai import OpenAI
import json

client = OpenAI() # Make sure OPENAI_API_KEY is in env

batch_input_file = client.files.create(
    file=open("datasets/publication_dataset.jsonl", "rb"),
    purpose="batch"
)

print(batch_input_file)

batch_input_file_id = batch_input_file.id
created_batch = client.batches.create(
    input_file_id=batch_input_file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "description": "Publication curation"
    }
)

batch = client.batches.retrieve(created_batch.id)
with open(f"{batch.id}.json", "w") as f:
    json.dump(created_batch.to_dict(), f)

# Also preview batch obj
print(batch)
