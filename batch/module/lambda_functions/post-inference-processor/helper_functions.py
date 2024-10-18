import sys
import json
import os
import boto3
from datetime import datetime
import re
import logging
from typing import Optional

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

logger = logging.getLogger()
logger.setLevel("INFO")

class Prompt():
    """
    A class to represent a prompt.

    Attributes
    ----------
    identifier : str
        The unique ID of the prompt on Amazon Bedrock Prompt Management.
    ver : str
        The version of the prompt on Amazon Bedrock Prompt Management.
    text : str
        The prompt body.

    """
    def __init__(self, identifier: Optional[str] = None, ver: Optional[str] = None, text: Optional[str] = None):
        self.identifier = identifier
        self.ver = ver
        self.text = text
        
def update_ddb_table(table_name: str, project_name: str, sqs_message_id: str, file_id: str, current_time: str, prompt: Prompt, system_prompt: Prompt, model_id: str, chunk_count: int, chunk_id: int, input_file_type: str, exception:str =None, model_response: dict =None):
    """
    Save the model response to a DynamoDB Table.

    Parameters:
    ----------
    table_name : str
        The destination DynamoDB Table name.

    project_name : str
        The internal project name.

    sqs_message_id : str
        The SQS message ID that triggers the Lambda function.

    file_id : str
        The unique file ID for the PDF.

    current_time : str
        The ingestion time for the file.

    prompt : Prompt
        An instance of the 'Prompt' class containing the prompt ID and prompt version from Bedrock Prompt Management.

    system_prompt : Prompt
        An instance of the 'Prompt' class containing the prompt ID and prompt version from Bedrock Prompt Management.

    model_id : str
        The ID of the model used in Bedrock.

    chunk_count : int
        The total number of chunk for the document.

    chunk_id : int
        The ID of the chunk (containing 20-page worth of data) that has been processed.

    input_file_type : str
        The input data (pdf or txt) for the document.

    exception : str, optional
        The exception message if the LLM call fails.

    model_response : dict, optional
        The response output from boto3 Bedrock converse API.

    Returns:
    ----------
    None
    """

    prompt_id = prompt.identifier
    prompt_ver = prompt.ver

    system_prompt_id = system_prompt.identifier
    system_prompt_ver = system_prompt.ver

    if model_response:
        flag_status = False

        response_text = model_response["content"][0]["text"]
        try:
            final_output = re.search(r'<final_output>(.*?)</final_output>', response_text, re.DOTALL).group(1).strip()
        except AttributeError:
            final_output = "[]"

        input_token = model_response["usage"]["input_tokens"]
        output_token = model_response["usage"]["output_tokens"]

        item = {
                "project_name": {"S": project_name},
                "chunk_count": {"N": str(chunk_count)},
                "chunk_id": {"N": str(chunk_id)},
                "sqs_message_id": {"S": sqs_message_id},
                "document_id": {"S": file_id},
                "ingestion_time": {"S": current_time},
                "model_response": {"S": final_output},
                "input_token": {"N": str(input_token)},
                "output_token": {"N": str(output_token)},
                "exception_FLAG": {"BOOL": flag_status},
                "prompt_id": {"S": prompt_id},
                "model_id": {"S": model_id},
                "input_file_type": {"S": input_file_type},
                "inference_mode": {"S": "batch"}
            }
    else:
        flag_status = True

        item = {
            "project_name": {"S": project_name},
            "chunk_count": {"N": str(chunk_count)},
            "chunk_id": {"N": str(chunk_id)},
            "sqs_message_id": {"S": sqs_message_id},
            "document_id": {"S": file_id},
            "ingestion_time": {"S": current_time},
            "exception": {"S": str(exception)},
            "exception_FLAG": {"BOOL": flag_status},
            "prompt_id": {"S": prompt_id},
            "model_id": {"S": model_id},
            "input_file_type": {"S": input_file_type},
            "inference_mode": {"S": "batch"}
        }

    if prompt_ver:
        item['prompt_ver'] = {"S": prompt_ver}
    if system_prompt_id:
        item['system_prompt_id'] = {"S": system_prompt_id}
        item['system_prompt_ver'] = {"S": system_prompt_ver}

    try:
        dynamodb.put_item(TableName=table_name, Item=item)
    except Exception as e:
        logging.error(f"Error saving record to DynamoDB table: {e}")

def parallel_enabled(array, metadata_dict, dynamodb_table_name, model_id):
    for j, f in enumerate(array):
        logging.info(f"Start processing model output:{j} - {f}")

        bucket_name = f.split('/')[2]
        key = f.split('/', 3)[3:][0]
        file_id = f.split('/')[-1].split('.')[0]

        ######### Retrieve msg attributes from metadata json ############
        try:
            sqs_message_id = metadata_dict[file_id]['sqs_message_id']
            prompt_id = metadata_dict[file_id]['prompt_id']
            prompt_ver = metadata_dict[file_id]['prompt_ver']
            system_prompt_id = metadata_dict[file_id]['system_prompt_id']
            system_prompt_ver = metadata_dict[file_id]['system_prompt_ver']
            chunk_count = metadata_dict[file_id]['chunk_count']
            project_name = metadata_dict[file_id]['project_name']
            input_file_type = metadata_dict[file_id]['input_file_type']

        except KeyError:
            logging.error(f"Error retrieving the sqs msg attributes for {file_id}. Please check the metadata.json to make sure all the required sqs msg attributes are present.")
            continue
        
        ######### Create prompt and system prompt objects ################
        prompt = Prompt(identifier=prompt_id, ver=prompt_ver)
        system_prompt = Prompt(identifier=system_prompt_id, ver=system_prompt_ver)

        ######### Download file from S3 ################
        try:
            logging.info(f"Downloading model output from {bucket_name}/{key}")
            response = s3.get_object(
                                Bucket=bucket_name,
                                Key=key,
                                )
        except Exception as we:
            logging.error(f"Error downloading model output from {bucket_name}/{key}: {e}")
            continue

        logging.info(f"Saving {file_id} model output to DynamoDB table.")
        content = response['Body'].iter_lines()
        ######### Process model output ################
        chunk_num = 0
        for line in content:
            ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            chunk_num+=1
            output_item = json.loads(line.decode('utf-8'))  # Decode and parse JSON object
            try:
                if 'modelOutput' in output_item:
                    update_ddb_table(dynamodb_table_name, project_name, sqs_message_id, file_id, ingestion_time, prompt, system_prompt, model_id, chunk_count, chunk_num, input_file_type, model_response=output_item['modelOutput'])
                else:
                    update_ddb_table(dynamodb_table_name, project_name, sqs_message_id, file_id, ingestion_time, prompt, system_prompt, model_id, chunk_count, chunk_num, input_file_type, exception=output_item['error'])
            except Exception as e:
                logging.error(f"Error saving the {file_id} chunk {chunk_num} model output to DynamoDB table: {e}")
                continue