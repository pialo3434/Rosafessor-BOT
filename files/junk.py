# All the junk functions or functions purely visual like this one, just dump them here
# for the code to be more clean.

def print_status_messages(status_messages):
    # Calculate the maximum width based on the length of the longest status message
    box_width = max(len(msg) for msg in status_messages) + 4  # 2 characters padding on each side

    # Print the top of the box
    print("+" + "-" * (box_width - 2) + "+")

    # Print each status message with padding
    for message in status_messages:
        print("| " + message + " " * (box_width - len(message) - 3) + "|")

    # Print the bottom of the box
    print("+" + "-" * (box_width - 2) + "+")

# Ignore message
ignore_message = "\nI am aware of the Exception ignored in: <function _ProactorBasePipeTransport.__del__ at 0x000002A33BE0CB80>\n but there is nothing i can do to prevent it but it won't harm the code by any means so its safe to simply ignore it.\n"
