import json
import jsonschema



with open('../schema/schema.json', 'r') as schema_file:
        schema = json.load(schema_file)
# try:
jsonschema.Draft202012Validator.check_schema(schema)
# except Exception as e:
#     print(e.message)


