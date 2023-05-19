# Duckmart Segmentation Query Generator

## Architecture
```
├── api
│   ├── logger.py
│   ├── requirements.txt
│   ├── schema_validator.py
│   ├── segmentation_query_generator.py ((MAIN CODE))
│   └── server.py ((MAIN/STARTER FILE))
├── data-gathering-loading
│   ├── eventsdata.csv
│   ├── getCSV.sh
│   ├── loadData.py ((MAIN/STARTER FILE))
│   ├── registrationdata.csv
│   └── requirements.txt
├── db
├── docs
│   ├── schema_doc.css
│   ├── schema_doc.min.js
│   └── schema.html ((DOCUMENTATION))
├── README.md
└── schema
    └── schema.json ((SCHEMA))

```

## Instructions To Run
**NOTE** `api` and `data-gathering-loading` directories need their virtual environments

- ### data-gathering-loading
	1. `cd data-gathering-loading`
	2. Setup venv
	3. `pip install -r requirements.txt`
	4. `python3 loadData.py`  
	**NOTE** `loadData.py` creates a db in db folder and loads data into it. Before running this file after the first time you'll need to delete the database first
- ### api
	1. `cd api`
	2. Setup venv
	3. `pip install -r requirements.txt`
	4. `uvicorn --reload server:app`
- ### docs
	Docs can be viewed by opening `schema.html`  
	
