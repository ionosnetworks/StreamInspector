from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from inspector import StreamStates
from dotenv import load_dotenv
import os

load_dotenv()

SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
SLACK_TOKEN = os.environ.get("SLACK_OAUTH_TOKEN")


def stream_state_to_emoji(state_array):
    states_to_emoji = {
        StreamStates.LOADED: " ✅ ",
        StreamStates.NO_SIGNAL: " 🚫 ",
        StreamStates.TOO_LONG_TO_LOAD: " 💤 ",
        StreamStates.INTERNAL_SERVICE_ERROR: " ⚠️ "
    }
    result_emoji_text = " ".join(states_to_emoji[state] for state in state_array)
    return result_emoji_text


def post_status_to_slack(stream_states):
    try:
    
        if len(stream_states) == 0:
            print("Nothing to send here")
            return
        else:
            blocks = []
            for index,org_data in enumerate(stream_states):
                if index > 0:
                    divider = {"type": "divider"}
                    blocks.append(divider)
                org_header = {
                    "type": "header",
                    "text": {"type": "plain_text", "text": org_data['org_name']},
                }
                blocks.append(org_header)
                message_core_body = ""
                for location_dict in org_data["locations"]:
                    loaded_count = location_dict["stream_states"].count(StreamStates.LOADED)
                    message_core_body += f"{location_dict['location_name']} - ({loaded_count}/{len(location_dict['stream_states'])}) {stream_state_to_emoji(location_dict['stream_states'])} \n"
                org_content = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_core_body,
                    },
                }
                blocks.append(org_content)
            client = WebClient(token=SLACK_TOKEN)
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL, 
                text="Live Stream Check", 
                blocks=blocks
            )
    except SlackApiError as err:
        print(f"Error posting message to Slack: {e}")
    except Exception as e:
        print("Some unknoen error occured sending message : ",e)    
    
