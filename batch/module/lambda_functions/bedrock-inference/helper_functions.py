import sys
import json
import os
import boto3
from datetime import datetime
from botocore.response import StreamingBody
import pymupdf
import base64
from typing import Optional
import logging

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

def prepare_model_inputs(bytes_inputs: list[bytes], prompt: Prompt, system_prompt: Prompt) -> tuple[list, int]:
    """
    Prepare the data to the required format for Bedrock batch inference.

    Parameters:
    ----------
    bytes_inputs : list[bytes]
        A list containing the data, in bytes, for each page of the PDF.

    prompt : Prompt
        An instance of the Prompt class that contains the user prompt to be used in the record.
    
    system_prompt : Prompt
        An instance of the Prompt class that contains the system prompt to be used in the record.

    Returns:
    ----------
    tuple[list, int]
        A tuple containing:
        - A list of formatted dictionaries to send to Bedrock batch inference job
        - An integer of the total number of formatted dictionaries. This is used as the total number of chunks in a PDF.
    """
    temperature = 0
    top_p = 0.1
    max_tokens = 4096
    anthropic_version = "bedrock-2023-05-31"

    ### Retrieve prompts from Bedrock
    prompt.text, prompt.ver = retrieve_bedrock_prompt(prompt.identifier, prompt.ver)
  
    if system_prompt.identifier:
        system_prompt.text, system_prompt.ver = retrieve_bedrock_prompt(system_prompt.identifier, system_prompt.ver)

    ### Split the data into chunks of 20 pages
    grouped_bytes_input = [bytes_inputs[i:i+20] for i in range(0, len(bytes_inputs), 20)]

    chunk_count = len(grouped_bytes_input)

    model_inputs = []

    for i, bytes_input in enumerate(grouped_bytes_input):
        page_count = 1
        content_input = []
        for one_page_data in bytes_input:
            content_input.append({"type": "text", "text": f"Image {page_count}"})
            content_input.append({"type": "image",
                                 "source": {"type": "base64",
                                           "media_type": "image/png",
                                           "data": one_page_data}})
            page_count += 1

        content_input.append({"type": "text", "text": prompt.text})

        model_input = {
            "anthropic_version": anthropic_version,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": content_input,
                }
            ]}

        if system_prompt.identifier:
            model_input["system"] = system_prompt.text

        final_json = {"recordId": f"{i+1}".zfill(11),
                      "modelInput": model_input}

        model_inputs.append(final_json)

    return model_inputs, chunk_count

def write_jsonl(data):
    jsonl_content = ''
    for item in data:
        jsonl_content += json.dumps(item) + '\n'
    return jsonl_content

def upload_to_s3(bucket_name, key, body):
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=body,
        ContentType='application/json'
    )
    
def parallel_enabled(array, metadata_dict, dest_bucket, data_folder):
    for j in range(0, len(array)):
        f = array[j]
        logging.info(f"Start processing file:{j} - {f}")

        bucket_name = f.split('/')[2]
        s3_key = f.split('/', 3)[3:][0]
        file_id = f.split('/')[-1].split('.')[0]

        try:
            mime, body = retrievePdf(bucket_name, s3_key)
        except Exception as e:
            logging.info(f"Error retrieving document thus skipping: {s3_key} - {e}")
            continue
    
        try:
            bytes_inputs = convertS3Pdf(mime, body)
        except Exception as e:
            logging.info(f"Error conversting document thus skipping: {s3_key} - {e}")
            continue
        # bytes_inputs = convertPdf(f)

        prompt = Prompt(
            identifier = metadata_dict[file_id]["prompt_id"],
            ver = metadata_dict[file_id]["prompt_ver"]
        )

        system_prompt = Prompt(
            identifier = metadata_dict[file_id]["system_prompt_id"],
            ver = metadata_dict[file_id]["system_prompt_ver"]
        )

        logging.info(f"Start processing data for {j} - {f}")
        try:
            model_input_jsonl, chunk_count = prepare_model_inputs(bytes_inputs, prompt, system_prompt)

        except Exception as e:
            logging.error(f"Error creating model input: {e}")
            continue

        logging.info(f"Writing model_input JSON for {j} - {f}")
        try:
            jsonl_content = write_jsonl(model_input_jsonl)
        except Exception as e:
            logging.error(f"Error creating model input: {e}")
            continue
        
        try:
            logging.info(f"Saving JSONL for {j} - {f} ")
            upload_to_s3(dest_bucket, f'{data_folder}/model-input/{file_id}.jsonl', jsonl_content)
        except Exception as e:
            logging.error(f"Error saving JSONL: {e}")
            raise

        metadata_dict[file_id]["chunk_count"] = chunk_count

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
    try:
        doc = pymupdf.open(mime, body.read())  # open document
        for page in doc:  # iterate through the pages
            pix = page.get_pixmap(dpi=90)  # render page to an image
            pdfbytes=pix.tobytes()
            b64 = base64.b64encode(pdfbytes).decode('utf8')
            bytes_outputs.append(b64)
    except Exception as e:
        logging.error(f"Error converting document: {e}")
        raise e
    return bytes_outputs

def retrieve_bedrock_prompt(prompt_id: str, prompt_ver: str) -> tuple[str, str]:
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
    tuple[str, str]
        A tuple containing:
        - prompt (str): The text of the prompt returned by Amazon Bedrock Prompt Management.
        - prompt_ver (str): The version of the prompt returned.
    """
    client = boto3.client('bedrock-agent')
    # logging.info(f"Returning version {prompt_ver} of the prompt {prompt_id}.")
    response = client.get_prompt(promptIdentifier=prompt_id,
								promptVersion=prompt_ver)

    prompt = response['variants'][0]['templateConfiguration']['text']['text']

    return prompt, prompt_ver

def retrievePdf(bucket: str , s3_key: str) -> tuple[str, StreamingBody]:
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

    try:
        response = s3.get_object(Bucket=bucket, Key=s3_key)
    except Exception as e:
        logging.error(f"Error retrieving document from S3: {s3_key} - {e}")
        raise e
    mime = response["ContentType"]
    body = response["Body"]

    return mime, body

def delete_queue_messages(sqs, queue_url, queue_arr):
    logging.info(f"Deleting all SQS messages ")
    for i in range(0, len(queue_arr)):
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=queue_arr[i])
    logging.info(f"sqs message deleted: - {i}")

