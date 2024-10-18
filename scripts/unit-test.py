import json
import re
import pymupdf
import boto3
from botocore.config import Config
import unittest

# Read the prompt and system prompts 
with  open('../realtime/module/templates/prompt_template.txt', 'r') as f:
    PROMPT = f.read()
with  open('../realtime/module/templates/system_prompt_template.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()

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

def get_llm_output(prompt, system_prompt=None):
	##### Model parameters #####
	temperature = 0
	top_p = 0.1
	model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

	config = Config(read_timeout=1000)
	bedrock_runtime = boto3.client(service_name='bedrock-runtime', 
								region_name='us-east-1',
								config=config)
	s3 = boto3.client('s3')

	bucket_name = 'xxxxxxxx'	# TODO: specify bucket that contains the test PDF
	s3_key = 'xxxxxxxx'		# TODO: specify the key to the test PDF

	mime, body = retrieveS3File(bucket_name, s3_key)
	bytes_inputs = convertS3Pdf(mime, body)

	##### Construct message #####
	grouped_bytes_input = [bytes_inputs[i:i+20] for i in range(0, len(bytes_inputs), 20)]

	content_input = []
	for i, bytes_inputs in enumerate(grouped_bytes_input):
		for bytes_input in bytes_inputs:
			content_input.append({"text": f"Image {i+1}"})
			content_input.append({"image": {"format": "png", "source": {"bytes": bytes_input}}})

	content_input.append({"text": prompt})

	messages = [
		{
			"role": "user",
			"content": content_input,
		}
	]

	##### Call Model #####
	if system_prompt:
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
            system=[
                    {"text": system_prompt
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

	##### Parse model output #####
	model_output = response["output"]["message"]["content"][0]["text"]
	try:
		land_desc = re.search(r'<final_output>(.*?)</final_output>', model_output, re.DOTALL).group(1).strip()
	except AttributeError:
		land_desc = "[]"

	return land_desc


class TestJSONOutput(unittest.TestCase):
	def test_valid_json_output(self):
		output = get_llm_output(PROMPT, SYSTEM_PROMPT)
        
		try:
			# Try to load the output as JSON
			parsed_output = json.loads(output)

			# Check if the parsed output is a dictionary or list (valid JSON structures)
			self.assertTrue(isinstance(parsed_output, (dict, list)), "Output is not a valid JSON object or array")

			# Check if the output contains double quotes
			self.assertIn('"', output, "Output JSON does not contain double quotes")

		except json.JSONDecodeError:
			self.fail("Output is not valid JSON")

if __name__ == '__main__':
    unittest.main(argv=[''], verbosity=3, exit=False)