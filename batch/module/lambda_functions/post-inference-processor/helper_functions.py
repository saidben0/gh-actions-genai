import sys
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.client('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3')

def process_model_output(array):
    for j in range(0, len(array)):
        f = array[j]
        print(f"Processing file:{j} - {f}")

        ##### Download outputs from s3
        bucket = f.split('/')[2]
        key = f.split('/',3)[3:][0]
        file_id = f.split('/')[-1].split('.')[0]

        print(f'file id: {file_id}')
        response = s3.get_object(
                            Bucket=bucket,
                            Key=key,
                            )
        content = response['Body'].iter_lines()
        # print(f'content: {content}')

        chunk_count = 0
        for line in content:
            ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chunk_count+=1
            print(chunk_count)
            output_item = json.loads(line.decode('utf-8'))  # Decode and parse JSON object
            # print(output_item)
            # print(f'output_item: {output_item}')
            response_text=output_item['modelOutput']['content'][0]['text']
            print(f"Response for chunk {chunk_count}: {response_text}")

            flag_status = False

            try:
                final_output = re.search(r'<final_output>(.*?)</final_output>', response_text, re.DOTALL).group(1).strip()
            except AttributeError:
                final_output = "[]"
            # print(f"final_output: {final_output}")
            input_token = output_item["modelOutput"]["usage"]["input_tokens"]
            output_token = output_item["modelOutput"]["usage"]["output_tokens"]
            ##### Save to DDB table
            item = {
                "project_name": {"S": 'landman'},
                # "chunk_count": {"N": str(len(model_outputs))},
                "chunk_id": {"N": str(chunk_count)},
                # "sqs_message_id": {"S": sqs_message_id},
                "document_id": {"S": file_id.split('.')[0]},
                "ingestion_time": {"S": ingestion_time},
                "model_response": {"S": final_output},
                # "latency": {"N": str(latency)},
                "input_token": {"N": str(input_token)},
                "output_token": {"N": str(output_token)},
                "exception_FLAG": {"BOOL": flag_status},
                "inference_mode": {"S": 'batch'},
                # "prompt_id": {"S": prompt_id},
                # "prompt_ver": {"S": prompt_ver},
                "model_id": {"S": 'anthropic.claude-3-5-sonnet-20240620-v1:0'}
            }
            # ddb_response = dynamodb.put_item(TableName='aws-proserve-land-doc', Item=item)
            # print(f"ddb_response: {ddb_response}")
        print(f"Finish processing file: {f}")

def update_ddb_table(table_name: str, project_name: str, sqs_message_id: str, file_id: str, current_time: str, prompt: Prompt, system_prompt: Prompt, chunk_count: int, chunk_id: int, exception:str =None, model_response: dict =None):
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

    chunk_count : int
        The total number of chunk for the document.

    chunk_id : int
        The ID of the chunk (containing 20-page worth of data) that has been processed.

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

        model_id = model_response["model"]
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
                "inference_mode": {"S": 'batch'}
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
            "model_id": {"S": model_id}
        }

    if prompt_ver:
        item['prompt_ver'] = {"S": prompt_ver}
    if system_prompt_id:
        item['system_prompt_id'] = {"S": system_prompt_id}
        item['system_prompt_ver'] = {"S": system_prompt_ver}

    try:
        response = dynamodb.put_item(TableName=table_name, Item=item)
    except Exception as e:
        logging.error(f"Error saving record to DynamoDB table: {e}")

def parallel_enabled(array, metadata_dict, dynamodb_table_name):
    for j in range(0, len(array)):
        f = array[j]
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

        except KeyError:
            logging.error(f"Error retrieving the sqs msg attributes for {file_id}")
            continue
        
        ######### Create prompt and system prompt objects ################
        prompt = Prompt(identifier=prompt_id, ver=prompt_ver)
        system_prompt = Prompt(identifier=system_prompt_id, ver=system_prompt_ver)

        ######### Download file from S3 ################
        try:
            logging.info(f"Downloading model output from {bucket_name}/{s3_key}")
            response = s3.get_object(
                                Bucket=bucket,
                                Key=key,
                                )
        except Exception as we:
            logging.error(f"Error downloading model output from {bucket_name}/{s3_key}: {e}")
            raise

        try:
            logging.info(f"Saving model output to DynamoDB table.")          
            content = response['Body'].iter_lines()
            ######### Process model output ################
            chunk_num = 0
            for line in content:
                ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chunk_num+=1
                logging.info(f"Processing chunk {chunk_num}...")
                output_item = json.loads(line.decode('utf-8'))  # Decode and parse JSON object

                if 'modelOutput' in output_item:
                    update_ddb_table(dynamodb_table_name, project_name, sqs_message_id, file_id, ingestion_time, prompt, system_prompt, chunk_count, chunk_num, model_response=output_item['modelOutput'])
                else:
                    update_ddb_table(dynamodb_table_name, project_name, sqs_message_id, file_id, ingestion_time, prompt, system_prompt, chunk_count, chunk_num, exception=output_item['error'])
        except Exception as e:
            logging.error(f"Error saving the model output to DynamoDB table: {e}")          


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