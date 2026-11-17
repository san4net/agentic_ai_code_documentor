import os

from google.genai import types

GOOGLE_API = ''
print('utils running\n')

def configure_api_key():
    print('utils configure api key\n')
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API


def retry_config():
    return types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,  # Initial delay before first retry (in seconds)
        http_status_codes=[429, 500, 503, 504]  # Retry on these HTTP errors
    )


