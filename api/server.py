from segmentation_query_generator import DuckmartQueryGenerator
from fastapi import FastAPI, Request, HTTPException
import duckdb, json, jsonschema
from logger import configure_logger, logger

app = FastAPI()
configure_logger()

conn = duckdb.connect("../db/duckmart.db")

qg = DuckmartQueryGenerator(conn)

with open('../schema/schema.json', 'r') as schema_file:
    schema = json.load(schema_file)


@app.post("/")
async def segment(request: Request):
    try:
        json_body = await request.json()
        jsonschema.Draft202012Validator(schema).validate(dict(json_body))
        sql = qg.generate(dict(json_body))
        query = conn.query(sql)
        response_data=query.to_df().to_dict(orient='list')

    except Exception as e:
        if type(e) is jsonschema.ValidationError:
            logger.error(e)
            raise HTTPException(status_code=400, detail=e.message)

        elif type(e) is json.decoder.JSONDecodeError:
            logger.error(e)
            raise HTTPException(status_code=400, detail=str(e))

        logger.error(e)
        raise HTTPException(status_code=500, detail="Something went wrong")

    logger.info(sql)
    logger.info(query)

    return {"data": response_data}


