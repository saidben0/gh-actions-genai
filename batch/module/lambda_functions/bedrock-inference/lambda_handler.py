from helper_functions import *
import sys
from multiprocessing import Process, Manager
import json
import os
import boto3
from datetime import datetime
import logging

# Logger information
logger = logging.getLogger()
logger.setLevel("INFO")

# Read environment variables
queue_url = os.environ.get('QUEUE_URL')
dest_bucket = os.environ.get('BATCH_DATA_BUCKET')
role_arn = os.environ.get('LLANDMAN_DEV_LAMBDA_ROLE_ARN')

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')

    data_folder = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

    EXPECTED = 1000
    queue_arr = []
    doc_arr = []
    # create array of SQS queue message with ReceiptHandle
    # quit if the ApproximateNumberOfMessages of the first record is less than 1000
    try:
    # checking if there are required messages
        logging.info("Checking # of message in the queue...")   
        response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=[ 'All' ],
        )
        attrib = response['Attributes']['ApproximateNumberOfMessages']
        logging.info(f"ApproximateNumberOfMessages: {attrib}")
        if ( int(attrib) < EXPECTED):
            logging.info("Not enough messages for batch inference")   
            sys.exit(0)

        logging.info("Receiving SQS message from queue...")   
        msg_count = 0
        
        msg_attributes = {}     # to save message attributes for each doc

        # for model polling
        model_count = {}
        
        # for storing prompts
        prompts = {}

        # one receive_message call can receive up to 10 messages a time 
        # so we will contine to call if we haven't received the EXPECTED number yet
        # note we could receive a few more messages depending on how many messages in the last call
        while (msg_count < EXPECTED):
            logging.info(f"Messages received so far = {msg_count}, calling receive_message again -")
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                MessageAttributeNames=['All']
            )

            # add up to 10 messages to the array
            try:
                messages = response['Messages']
                num_messages = len(messages)
            except KeyError:
                logging.info("No more records, exit loop")
                # num_messages = 0
            for j in range(0, num_messages):
                try:
                    message = messages[j]
                except KeyError:
                    logging.error("Error in receive message, exit normally")
                    raise
                else:
                    try:
                        receipt_handle = message['ReceiptHandle']
                        if receipt_handle in queue_arr:
                            logging.info(f"Message already received before. Reading the next message.")
                            continue
                        else:
                            msg_count = msg_count + 1
                            sqs_message_id = message['MessageId']
                            logging.info(f"sqs_message_id: {j} - {sqs_message_id}")
                            message_attributes = message['MessageAttributes']
                            project_name = message_attributes['application']['StringValue']
                            s3_loc = message_attributes['s3_location']['StringValue']
                            file_id = s3_loc.split('/')[-1].split('.')[0]
                            model_id = message_attributes['model_id']['StringValue']
                            prompt_id = message_attributes['prompt_id']['StringValue']
                            prompt_ver = message_attributes.get('prompt_version', {}).get('StringValue', None)
                            system_prompt_id = message_attributes.get('system_prompt_id', {}).get('StringValue', None)
                            system_prompt_ver = message_attributes.get('system_prompt_version', {}).get('StringValue', None)

                            msg_attributes[file_id] = {
                                "sqs_message_id": sqs_message_id,
                                "prompt_id": prompt_id,
                                "prompt_ver": prompt_ver,
                                "system_prompt_id": system_prompt_id,
                                "system_prompt_ver": system_prompt_ver,
                                "project_name": project_name
                                }

                            model_count[model_id] = model_count.get(model_id, 0) + 1

                            doc_arr.append(s3_loc)
                            queue_arr.append(receipt_handle)

                    except KeyError as e:
                        logging.info(f"Error parsing SQS message # {msg_count}: {e}")
                        continue

                    try:
                        # check if the text already exists in prompts
                        # if not, add the text to the dictionary
                        prompts = add_prompt_if_missing(prompts, prompt_id, prompt_ver)
                        prompts = add_prompt_if_missing(prompts, system_prompt_id, system_prompt_ver)
                    except Exception as e:
                        logging.info(f"Error checking the prompts: {e}")
  
    except Exception as e:
        logging.error(f"Error receiving SQS message from queue: {e}")
        sys.exit(0)
    
    logging.info("Determining the model to use.")
    try:
        if model_count:
            max_model_id = max(model_count, key=model_count.get)
            max_count = model_count[max_model_id]
            logging.info(f"{max_count} out of {msg_count} messages use {max_model_id}. Using {max_model_id} for the batch inference.")
    except Exception as e:
        logging.error(f"Error determining the model to use: {e}")
        raise
    
    logging.info("Finish reading SQS messages.")
    
    logging.info("Start processing data.")
    
    # Divide the doc_arr into chunks of 200 so that multiprocessing would not create too many connections
    chunk_size = 100
    doc_arr_chunks = [doc_arr[i:i + chunk_size] for i in range(0, len(doc_arr), chunk_size)]
    logging.info(f"There are {len(doc_arr)} PDFs to process. Dividing them into {len(doc_arr_chunks)} chunks for parallel processing.")

    with Manager() as manager:
        try:
            metadata_dict = manager.dict(msg_attributes)
            processes = []
            
            for doc_arr_chunk in doc_arr_chunks:
                p = Process(target=parallel_enabled, args=(doc_arr_chunk, metadata_dict, prompts, dest_bucket, data_folder, ))
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            metadata = dict(metadata_dict)

        except Exception as e:
            logging.error(f"Error processing data: {e}")
            raise

        try:
            logging.info(f"Uploading metadata.json to {dest_bucket}")
            upload_to_s3(dest_bucket, f'{data_folder}/metadata/metadata.json', json.dumps(metadata))

        except Exception as e:
            logging.error(f"Error uploading metadata.json: {e}")
            raise
    
    logging.info("Finish processing data.")
    logging.info("Creating Bedrock batch inference job.")
    
    inputDataConfig=({
    "s3InputDataConfig": {
        "s3Uri": f"s3://{dest_bucket}/{data_folder}/model-input/"
    }
    })

    outputDataConfig=({
    "s3OutputDataConfig": {
        "s3Uri": f"s3://{dest_bucket}/{data_folder}/model-output/"
        }
    })
    
    bedrock = boto3.client(service_name="bedrock", region_name="us-east-1")
    job_name = f"{project_name}-batch-inference-{data_folder}"
    try:
        response=bedrock.create_model_invocation_job(
                                                    roleArn=role_arn,
                                                    modelId=max_model_id,
                                                    jobName=job_name,
                                                    inputDataConfig=inputDataConfig,
                                                    outputDataConfig=outputDataConfig,
                                                    timeoutDurationInHours=72,
                                                    tags=[
                                                        {"key":"Team", "value":"Tech-Land-Manufacturing@enverus.com"},
                                                        {"key":"Dataset", "value":"land"},
                                                        {"key":"SourceCode", "value":"https://github.com/enverus-ea/land.llandman"},
                                                        {"key":"Component", "value":"llandman"},
                                                        {"key":"BusinessUnit", "value":"ea"},
                                                        {"key":"Product", "value":"courthouse"},
                                                        {"key":"Environment", "value":"dev"}
                                                        ]
                                                    )
        logging.info(f"Bedrock batch inference job successfully created. Job name: {job_name}")

        job_arn = response.get('jobArn')
        job_response = bedrock.get_model_invocation_job(jobIdentifier=job_arn)
        status = job_response['status']
        if status != 'Failed':
            logging.info(f"The Bedrock batch inference job is {status}. Deleting SQS messages...")
            # delete messages from SQS using queue_arr 
            delete_queue_messages(sqs, queue_url, queue_arr)
            logging.info("Deleted SQS messages.")
        else:
            logging.info("The Bedrock batch inference job has failed. Please check Bedrock for more info.")
            logging.info("The SQS messages are not deleted.")

    except Exception as e:
        logging.error(f"Error creating Bedrock batch inference job: {e}")
