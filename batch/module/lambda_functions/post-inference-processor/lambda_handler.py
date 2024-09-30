from helper_functions import *
import sys
from multiprocessing import Process, Manager
import json
import os
import boto3
from datetime import datetime
import logging

# ENV VAR
dest_bucket = os.environ.get('BATCH_DATA_BUCKET')
dynamodb_table_name = os.environ.get('DDB_TABLE_NAME')

logger = logging.getLogger()
logger.setLevel("INFO")

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # batch inference job details
    logging.info(f"EVENT: {event}")
    try:
        logging.info("Reading batch job details from event.")
        job_arn = event["detail"]["batchJobArn"]
        job_id = job_arn.split("/")[-1]
        job_name = event["detail"]["batchJobName"]
        data_folder = job_name.split("-", 4)[-1]
        logging.info(f"JobID: {job_id}")
        logging.info(f"JobName: {job_name}")
    except KeyError as e:
        logging.error(f"Error reading batch job info from event: {e}")
    
    # read files from the model output folder
    try:
        logging.info(f"Searching S3 URIs for model outputs from {dest_bucket}/{data_folder}/model-output/")
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=dest_bucket, Prefix=f"{data_folder}/model-output/")
        model_output_arr = []
        for page in pages:
            try:
                for obj in page['Contents']:
                    key = obj['Key']
                    if len(key) > 0: 
                        model_output_arr.append(f's3://{dest_bucket}/{key}')
            except KeyError:
                logging.error("No files exist")
                exit(1)
        logging.info(f"Successfully searched all s3 URIs.")
        logging.info(f"s3_uris: {model_output_arr}")
    except Exception as e:
        logging.error(f"Error getting S3 URIs: {e}")
        raise
        
    # read sqs message attributes json
    try:
        response = s3_client.get_object(
            Bucket=dest_bucket,
            Key=f"{data_folder}/metadata/metadata.json"
        )
        msg_attributes = response["Body"].read().decode('utf-8')
        msg_attributes = json.loads(msg_attributes)

    except Exception as e:
        logging.error(f"Error reading the SQS message attributes json from S3: {e}")
        raise

    # Parallel processing for the model output
    logging.info("Starting post inference processing...")
    with Manager() as manager:
        try:
            msg_attributes_dict = manager.dict(msg_attributes)
            processes = []

            p = Process(target=parallel_enabled, args=(model_output_arr, msg_attributes_dict, dynamodb_table_name, ))
            processes.append(p)
            p.start()

            for p in processes:
                p.join()
            
            logging.info("Finish all inference processing.")

        except Exception as e:
            logging.error(f"Error processing batch inference output: {e}")