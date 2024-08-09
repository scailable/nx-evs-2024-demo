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

        try:
            scores = input_object['Scores']
            print(f'Postprocessor -  Found scores: {scores}')

            # Step 1: Read number of score values
            # The scores are stored as a dictionary with the class index as key and the score as value
            values = list(scores.values())
            number_of_values = len(values)

            # Step 2: Find the class with the highest score
            max_class_index = values.index(max(values))

            # Step 3: Calculate the gauge value based on the class index
            step = 100 / number_of_values
            gauge_value = max_class_index * step + step / 2
            
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
