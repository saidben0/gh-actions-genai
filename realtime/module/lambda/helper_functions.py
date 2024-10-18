import logging
import multiprocessing 
from joblib import Parallel, delayed
import botocore
import boto3
from decimal import Decimal
import math
import pymupdf
from datetime import datetime
import re
from botocore.config import Config
from botocore.response import StreamingBody
from typing import Optional

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
		
def retrieveS3File(bucket: str , s3_key: str) -> tuple[str, StreamingBody]:
    """
    Retrieve data of a file from an S3 bucket.

    Parameters:
    ----------
    bucket : str
        The name of the S3 bucket.

    s3_key : str
        The file path to the file.

    Returns:
    ----------
    tuple[str, StreamingBody]
        A tuple containing:
        - mime (str): A standard MIME type describing the format of the file data.
        - body (StreamingBody): The file data.

    """
    s3 = boto3.client('s3')

    response = s3.get_object(Bucket=bucket, Key=s3_key)
    mime = response["ContentType"]
    body = response["Body"]

    return mime, body

def convertS3Pdf(mime: str, body: StreamingBody) -> list[bytes]:
    """
    Convert the file data to bytes.

    Parameters:
    ----------
    mime : str
        The standard MIME type describing the format of the file data.

    body : str
        The file data.

    Returns:
    ----------
    list[bytes]
        A list of bytes for the PDF data. The length of the list equals to the number of pages of the PDF.
    """
    bytes_outputs = []

    doc = pymupdf.open(mime, body.read())  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(dpi=100)  # render page to an image
        pdfbytes=pix.tobytes()
        bytes_outputs.append(pdfbytes)
    return bytes_outputs

def convertPdf(file_path: str) -> list[bytes]:
    """
    Convert the PDF file to bytes.

    Parameters:
    ----------
    file_path : str
        The loca path to the PDF.

    Returns:
    ----------
    list[bytes]
        A list of bytes for the PDF data. The length of the list equals to the number of pages of the PDF.
    """
    bytes_outputs = []

    doc = pymupdf.open(file_path)
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(dpi=100)  # render page to an image
        pdfbytes=pix.tobytes(output='png')
        bytes_outputs.append(pdfbytes)
    return bytes_outputs

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
    dynamodb = boto3.client('dynamodb')

    prompt_id = prompt.identifier
    prompt_ver = prompt.ver

    system_prompt_id = system_prompt.identifier
    system_prompt_ver = system_prompt.ver

    if model_response:
        flag_status = False

        response_text = model_response["output"]["message"]["content"][0]["text"]
        try:
            final_output = re.search(r'<final_output>(.*?)</final_output>', response_text, re.DOTALL).group(1).strip()
        except AttributeError:
            final_output = "[]"

        latency = model_response["metrics"]["latencyMs"]
        input_token = model_response["usage"]["inputTokens"]
        output_token = model_response["usage"]["outputTokens"]

        item = {
                "project_name": {"S": project_name},
                "chunk_count": {"N": str(chunk_count)},
                "chunk_id": {"N": str(chunk_id)},
                "sqs_message_id": {"S": sqs_message_id},
                "document_id": {"S": file_id.split('.')[0]},
                "ingestion_time": {"S": current_time},
                "model_response": {"S": final_output},
                "latency": {"N": str(latency)},
                "input_token": {"N": str(input_token)},
                "output_token": {"N": str(output_token)},
                "exception_FLAG": {"BOOL": flag_status},
                "prompt_id": {"S": prompt_id},
                "model_id": {"S": model_id},
                "input_file_type": {"S": input_file_type},
                "inference_mode": {"S": 'on demand'}
            }
    else:
        flag_status = True
        item = {
            "project_name": {"S": project_name},
            "chunk_count": {"N": str(chunk_count)},
            "chunk_id": {"N": str(chunk_id)},
            "sqs_message_id": {"S": sqs_message_id},
            "document_id": {"S": file_id.split('.')[0]},
            "ingestion_time": {"S": current_time},
            "exception": {"S": str(exception)},
            "exception_FLAG": {"BOOL": flag_status},
            "prompt_id": {"S": prompt_id},
            "model_id": {"S": model_id},
            "input_file_type": {"S": input_file_type},
            "inference_mode": {"S": 'on demand'}
        }

    if prompt_ver:
        item['prompt_ver'] = {"S": prompt_ver}
    if system_prompt_id:
        item['system_prompt_id'] = {"S": system_prompt_id}
        item['system_prompt_ver'] = {"S": system_prompt_ver}

    dynamodb.put_item(TableName=table_name, Item=item)

def retrieve_bedrock_prompt(prompt_id: str, prompt_ver: str):
    """
    Retrieve a prompt from Amazon Bedrock Prompt Management.

    Parameters:
    ----------
    prompt_id : str
        The unique identifier or ARN of the prompt

    prompt_ver : str
        The version of the prompt

    Returns:
    ----------
    str
        The prompt.
    str
        The prompt version.
    """
    client = boto3.client('bedrock-agent')
    # logging.info(f"Returning version {prompt_ver} of the prompt {prompt_id}.")
    response = client.get_prompt(promptIdentifier=prompt_id,
								promptVersion=prompt_ver)

    prompt = response['variants'][0]['templateConfiguration']['text']['text']

    return prompt, prompt_ver

def call_llm(bytes_inputs: list[bytes], input_file_type: str, model_id: str, prompt: Prompt, system_prompt: Prompt =None) -> dict:
    """
    Construct an input to call the LLM using the boto3 Bedrock runtime converse API.

    Parameters:
    ----------
    bytes_inputs : list[bytes]
        A list of bytes containing data for each page in the PDF document. Or if it is from a txt file, a list containing all the text in a string.

    input_file_type : str
        The input data (pdf or txt) for the document.
    
    model_id : str
        The ID of the model to be used in Bedrock.

    prompt : Prompt
        An instance of the 'Prompt' class containing the prompt ID and prompt version from Bedrock Prompt Management.

    system_prompt : Prompt [optional, default = None]
        An instance of the 'Prompt' class containing the prompt ID and prompt version from Bedrock Prompt Management.

    Returns:
    ----------
    dict
        The output of the Bedrock runtime converse API.
    """
    config = Config(read_timeout=1000)
    bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1", config=config)

    temperature = 0
    top_p = 0.1

    content_input = []

    if input_file_type == 'pdf':
        for bytes_input in bytes_inputs:
            content_input.append({"image": {"format": "png", "source": {"bytes": bytes_input}}})

        content_input.append({"text": prompt.text})

        messages = [
            {
                "role": "user",
                "content": content_input,
            }
        ]
    else:
        final_text = f"{prompt.text} <document> {bytes_inputs[0]}</document>"
        content_input.append({"text": final_text})

        messages = [
            {
                "role": "user",
                "content": content_input,
            }
        ]

    if system_prompt.identifier:
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
            system=[
                    {"text": system_prompt.text
                    }],
            inferenceConfig={
                'temperature': temperature,
                'topP': top_p
            }
        )
    else:
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                'temperature': temperature,
                'topP': top_p
            }
        )
    return response
