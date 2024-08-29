# # awscc_bedrock_prompt.this:
# resource "awscc_bedrock_prompt" "this" {
#     default_variant = "variantOne"
#     name            = "aws-proserve-prompt-test"
#     # prompt_id       = "3DKW6HGLLD"
#     variants        = [
#         {
#             inference_configuration = {
#                 text = {}
#             }
#             name                    = "variantOne"
#             template_configuration  = {
#                 text = {
#                     text = <<-EOT
#                         Think step-by-step.
#                         Step 1. Retrieve all raw tract descriptions from the images provided to you, including all counties such as 'Irion County', 'Glasscock County', 'Menard County', and 'Nolan County', etc. 
#                         You will keep each tract together as an individual tract entity and combine the responses to the following questions into a JSON output, with each JSON object corresponding to a single tract entity. Return one JSON object per tract.
#                         Example of one tract: {'tract': 1, 'county': 'Travis', 'abstract': 'A-546', 'survey': 'T&P RR CO SURVEY', 'subdivision': 'Flatrock Creek Phase 1', 'lot': '1', 'subdivision_block': '1', 'section': '5', 'township': 'T-4-S', 'range_block': '5', 'quarter': 'N/2 of N/2', 'acreage': '126.3'} 
#                         If there are no specific tract descriptions, just return an empty JSON.
                        
#                         Step 2. For each distinct land description:
#                         <instruction>
#                         - Assign a sequential tract number.
#                         - Identify the counties. Get all values from the document. One tract can have multiple counties.
#                         - Identify all abstracts in the raw tract (format: A-#### or ####). One tract can have multiple abstracts.
#                         - Identify the survey name (sometimes called the original grantee).
#                         - Identify the subdivision. Subdivision is found when there is a stated "Subdivision", "Division" or "Addition".
#                         - Identify the lot number. The value "Three (3)" should be a numeric "3". Do not split lots if there are multiple.
#                         - Identify the subdivision block the tract of land located in in. Subdivision block value is found when there is a Subdivision.
#                         - Extract the section number. If more than one section numbers appear in a tract, then there are actually multiple tracts.
#                         - Identify the range block (often labeled as "Block"). Range block are found when a "Section" is described.
#                         - Identify the township. Township is found when the "Section" and "Range block" are described. Township value must follows the format: "T-<digit>-<direction>" and could be separated by a hyphen, such as 'T5S' and 'T-2-E'.
#                         - Extract all quarter descriptions exactly as written. Sometimes it starts with directional word such as 'South One-Fourth (S/4)'
#                         - Extract the acreage of the tract.
#                         - Note: Subdivision, lot, township, and acreage may not be present in all documents. Only include these if explicitly stated.
#                         </instruction>
                        
#                         Step 3. For surveys: Ensure the full survey name is captured, even if it spans multiple lines.
#                         Step 4. This step only applies to the quarter.
#                         - If multiple quarters are separated by "and", create separate JSON objects for each.
#                         - Example: "N/2 of N/2 and N/2 of S/2" should result in two tract entries.
#                         - Example: "Southeast Quarter (SE/4) and the Southeast Quarter fo the Northeast Quarter (SE/4 NE/4)" should result in two tract entries.
#                         Step 5. Simplify quarter descriptions:
#                         - Remove words, keeping only directional notations.
#                         - Example: "North One-Half (N/2)" becomes "N/2".
#                         Step 6. If multiple abstracts apply to a single tract, join them with a semicolon.
#                         Example: "abstract": "A-545; A-645" when document states 'A-545, Glasscock County, Texas, and A-645, Reagan County, Texas, containing 15 acres'.
                        
#                         Step 7. If multiple counties apply to a single tract, join them with a semicolon.
#                         Example: "county": "Glasscock; Reagan"
#                         Step 8. This step only applies to the section. If the both section and subdivision are present, then append the section to the end of subdivision. 
#                         Step 9. Format the final output as a list of JSON objects, each representing a single tract. Include the final output in XML <final_output> tags. Example:
#                         <final_output>
#                         [
#                           {
#                             "tract": 1,
#                             "county": "Glasscock; Reagan",
#                             "abstract": "A-545; A-645",
#                             "survey": "T&P RR Co Survey",
#                             "section": "37",
#                             "range_block": "35",
#                             "township": "TSS",
#                             "quarter": "S/2",
#                             "acreage": "115"
#                           },
#                           ...
#                         ]
#                         </final_output>
#                         Important:
#                         - Retrieve complete raw tract descriptions
#                         - Include only fields that are explicitly mentioned in the document.
#                         - Ensure all JSON objects are properly formatted and closed.
#                         - Double-check that all relevant information has been captured for each tract.
#                         - Verify that quarters have been properly split into separate tracts when necessary.
#                         - Verify that multiple abstracts, multiple counties, multiple surveys in a tract have been properly joined.
#                         - Verify the format of the township. Sometimes '5' and 'S' are easily mixed up. If the tonwship appears to be 'TSS', you know it is the wrong format and should output 'T5S' instead.
#                     EOT
#                 }
#             }
#             template_type           = "TEXT"
#         },
#     ]
#     # version         = "DRAFT"
# }



# # awscc_bedrock_prompt.this:
# resource "awscc_bedrock_prompt" "this" {
#     arn             = "arn:aws:bedrock:us-east-1:061039788063:prompt/3DKW6HGLLD"
#     created_at      = "2024-08-23T20:00:02.845721359Z"
#     default_variant = "variantOne"
#     id              = "arn:aws:bedrock:us-east-1:061039788063:prompt/3DKW6HGLLD"
#     name            = "aws-proserve-prompt-test"
#     prompt_id       = "3DKW6HGLLD"
#     tags            = {}
#     updated_at      = "2024-08-29T13:24:13.500091149Z"
#     variants        = [
#         {
#             inference_configuration = {
#                 text = {}
#             }
#             name                    = "variantOne"
#             template_configuration  = {
#                 text = {
#                     text = <<-EOT
#                         Think step-by-step.
#                         Step 1. Retrieve all raw tract descriptions from the images provided to you, including all counties such as 'Irion County', 'Glasscock County', 'Menard County', and 'Nolan County', etc. 
#                         You will keep each tract together as an individual tract entity and combine the responses to the following questions into a JSON output, with each JSON object corresponding to a single tract entity. Return one JSON object per tract.
#                         Example of one tract: {'tract': 1, 'county': 'Travis', 'abstract': 'A-546', 'survey': 'T&P RR CO SURVEY', 'subdivision': 'Flatrock Creek Phase 1', 'lot': '1', 'subdivision_block': '1', 'section': '5', 'township': 'T-4-S', 'range_block': '5', 'quarter': 'N/2 of N/2', 'acreage': '126.3'} 
#                         If there are no specific tract descriptions, just return an empty JSON.
                        
#                         Step 2. For each distinct land description:
#                         <instruction>
#                         - Assign a sequential tract number.
#                         - Identify the counties. Get all values from the document. One tract can have multiple counties.
#                         - Identify all abstracts in the raw tract (format: A-#### or ####). One tract can have multiple abstracts.
#                         - Identify the survey name (sometimes called the original grantee).
#                         - Identify the subdivision. Subdivision is found when there is a stated "Subdivision", "Division" or "Addition".
#                         - Identify the lot number. The value "Three (3)" should be a numeric "3". Do not split lots if there are multiple.
#                         - Identify the subdivision block the tract of land located in in. Subdivision block value is found when there is a Subdivision.
#                         - Extract the section number. If more than one section numbers appear in a tract, then there are actually multiple tracts.
#                         - Identify the range block (often labeled as "Block"). Range block are found when a "Section" is described.
#                         - Identify the township. Township is found when the "Section" and "Range block" are described. Township value must follows the format: "T-<digit>-<direction>" and could be separated by a hyphen, such as 'T5S' and 'T-2-E'.
#                         - Extract all quarter descriptions exactly as written. Sometimes it starts with directional word such as 'South One-Fourth (S/4)'
#                         - Extract the acreage of the tract.
#                         - Note: Subdivision, lot, township, and acreage may not be present in all documents. Only include these if explicitly stated.
#                         </instruction>
                        
#                         Step 3. For surveys: Ensure the full survey name is captured, even if it spans multiple lines.
#                         Step 4. This step only applies to the quarter.
#                         - If multiple quarters are separated by "and", create separate JSON objects for each.
#                         - Example: "N/2 of N/2 and N/2 of S/2" should result in two tract entries.
#                         - Example: "Southeast Quarter (SE/4) and the Southeast Quarter fo the Northeast Quarter (SE/4 NE/4)" should result in two tract entries.
#                         Step 5. Simplify quarter descriptions:
#                         - Remove words, keeping only directional notations.
#                         - Example: "North One-Half (N/2)" becomes "N/2".
#                         Step 6. If multiple abstracts apply to a single tract, join them with a semicolon.
#                         Example: "abstract": "A-545; A-645" when document states 'A-545, Glasscock County, Texas, and A-645, Reagan County, Texas, containing 15 acres'.
                        
#                         Step 7. If multiple counties apply to a single tract, join them with a semicolon.
#                         Example: "county": "Glasscock; Reagan"
#                         Step 8. This step only applies to the section. If the both section and subdivision are present, then append the section to the end of subdivision. 
#                         Step 9. Format the final output as a list of JSON objects, each representing a single tract. Include the final output in XML <final_output> tags. Example:
#                         <final_output>
#                         [
#                           {
#                             "tract": 1,
#                             "county": "Glasscock; Reagan",
#                             "abstract": "A-545; A-645",
#                             "survey": "T&P RR Co Survey",
#                             "section": "37",
#                             "range_block": "35",
#                             "township": "TSS",
#                             "quarter": "S/2",
#                             "acreage": "115"
#                           },
#                           ...
#                         ]
#                         </final_output>
#                         Important:
#                         - Retrieve complete raw tract descriptions
#                         - Include only fields that are explicitly mentioned in the document.
#                         - Ensure all JSON objects are properly formatted and closed.
#                         - Double-check that all relevant information has been captured for each tract.
#                         - Verify that quarters have been properly split into separate tracts when necessary.
#                         - Verify that multiple abstracts, multiple counties, multiple surveys in a tract have been properly joined.
#                         - Verify the format of the township. Sometimes '5' and 'S' are easily mixed up. If the tonwship appears to be 'TSS', you know it is the wrong format and should output 'T5S' instead.
#                     EOT
#                 }
#             }
#             template_type           = "TEXT"
#         },
#     ]
#     version         = "DRAFT"
# }


# resource "awscc_bedrock_prompt" "this" {
#   # provider                    = aws.acc
#   name        = "${var.prefix}-prompt"
#   description = "${var.prefix}-prompt"
#   # customer_encryption_key_arn = module.dev-use1.kms_key_arn
#   default_variant = "${var.prefix}-variant"

#   variants = [
#     {
#       name          = "${var.prefix}-variant"
#       template_type = "TEXT"
#       model_id      = "anthropic.claude-3-5-sonnet-20240620-v1:0"
#       inference_configuration = {
#         text = {
#           temperature = 1
#           top_p       = 0.9900000095367432
#           max_tokens  = 300
#           top_k       = 250
#         }
#       }
#       template_configuration = {
#         text = {
#           input_variables = [
#             {
#               name        = "topic"
#               description = "The subject or theme for the playlist"
#             },
#             {
#               name        = "number"
#               description = "The number of songs in the playlist"
#             },
#             {
#               name        = "genre"
#               description = "The genre of music for the playlist"
#             }
#           ]

#           text = "Create a {{genre}} playlist for {{topic}} consisting of {{number}} songs."
#         }
#       }
#     }

#   ]

# }


