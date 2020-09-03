from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# Set up Assistant service.
authenticator = IAMAuthenticator('************API-KEY*******************') # replace with API key
service = AssistantV2(
    version = '2020-04-01',
    authenticator = authenticator
)
service.set_service_url('**********SERVICE-URL*******************') # replace with service URL
assistant_id = '******ASSISTANT-ID************' # replace with assistant ID

# Create session.
session_id = service.create_session(
    assistant_id = assistant_id
).get_result()['session_id']

# Initialize with empty values to start the conversation.
message_input = {'text': ''}
current_action = ''


# Main input/output loop
while current_action != 'end_conversation':
    # Clear any action flag set by the previous response.
    current_action = ''

    # Send message to assistant.
    response = service.message(
        assistant_id,
        session_id,
        input = message_input
    ).get_result()

    # Print the output from dialog, if any. Supports only a single
    # text response.
    if response['output']['generic']:
        if response['output']['generic'][0]['response_type'] == 'text':
            print(response['output']['generic'][0]['text'])

    # Check for client actions requested by the assistant.
    if 'actions' in response['output']:
        if response['output']['actions'][0]['type'] == 'client':
            current_action = response['output']['actions'][0]['name']

    # If we're not done, prompt for next round of input.
    if current_action != 'end_conversation':
        user_input = input('>> ')
        message_input = {
            'text': user_input
        }

# We're done, so we delete the session.
service.delete_session(
    assistant_id = assistant_id,
    session_id = session_id
)
