import os
import signal
import socket
import sys

import requests
import re


def send_post_request(gauge_value):
    print('Postprocessor -  Sending post request with gauge value:', gauge_value)
    # This function assumes that the API is up and running
    endpoint = f"http://localhost:8888/value?value={gauge_value}"  # Replace with your actual API endpoint
    try:
        response = requests.post(endpoint)
        response.raise_for_status()  # Raises a HTTPError if the response was unsuccessful
    except requests.exceptions.RequestException as err:
        print(f"Postprocessor -  An error occurred: {err}")


# Add the sclbl-utilities python utilities
script_location = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_location, "../sclbl-utilities/python-utilities"))
import communication_utils

# The name of the postprocessor.
# This is used to match the definition of the postprocessor with routing.
Postprocessor_Name = "Python-Example-Postprocessor"

# The socket this postprocessor will listen on.
# This is always given as the first argument when the process is started
# But it can be manually defined as well, as long as it is the same as the socket path in the runtime settings
Postprocessor_Socket_Path = "/tmp/python-example-postprocessor.sock"


# Data Types
# 1:  //FLOAT
# 2:  //UINT8
# 3:  //INT8
# 4:  //UINT16
# 5:  //INT16
# 6:  //INT32
# 7:  //INT64
# 8:  //STRING
# 9:  //BOOL
# 11: //DOUBLE
# 12: //UINT32
# 13: //UINT64


def main():
    # Start socket listener to receive messages from NXAI runtime
    server = communication_utils.startUnixSocketServer(Postprocessor_Socket_Path)
    count = 0
    # Wait for messages in a loop
    while True:
        count = count + 1
        # Wait for input message from runtime
        try:
            input_message, connection = communication_utils.waitForSocketMessage(server)
        except socket.timeout:
            # Request timed out. Continue waiting
            continue

        # Parse input message
        input_object = communication_utils.parseInferenceResults(input_message)

        # Add extra bbox

        try:
            scores = input_object['Scores']
            print(f'Postprocessor -  Found scores: {scores}')

            # Step 1: Parse the string to extract the class names and their scores
            #scores = "{'Class 1': 0.0003794431977439672, 'Class 2': 1.0930746157100657e-06, 'Class 3': 2.760653785571776e-07, 'Class 4': 0.9996192455291748}"
            pattern = re.compile(r"'Class (\d+)': ([\d.e-]+)")
            matches = pattern.findall(str(scores))

            # Step 2: Find the class with the highest score
            max_class_index = None
            max_score = float('-inf')

            for match in matches:
                class_index = int(match[0])
                score = float(match[1])
                if score > max_score:
                    max_score = score
                    max_class_index = class_index

            gauge_value = (max_class_index -1) * 25 + 12.5 # 12.5, 37.5, 62.5, 87.5
            
            send_post_request(gauge_value)
        except Exception as e:
            print("Postprocessor -  Error: " + str(e))

        # Write object back to string
        output_message = communication_utils.writeInferenceResults(input_object)

        # Send message back to runtime
        communication_utils.sendMessageOverConnection(connection, output_message)


def signalHandler(sig, _):
    print("Postprocessor -  EXAMPLE PLUGIN: Received interrupt signal: ", sig)
    sys.exit(0)


if __name__ == "__main__":
    print("Postprocessor -  EXAMPLE PLUGIN: Input parameters: ", sys.argv)

    # Parse input arguments
    if len(sys.argv) > 1:
        Postprocessor_Socket_Path = sys.argv[1]
    # Handle interrupt signals
    signal.signal(signal.SIGINT, signalHandler)
    # Start program
    main()
