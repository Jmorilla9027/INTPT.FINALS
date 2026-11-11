
import csv
import os
import threading


class IDSLogger:

    def __init__(self, filename="logs/ids_logs.csv"):

        self.filename = filename

        self.lock = threading.Lock()

        # Create logs directory if it does not exist
        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        # Create CSV file and headers
        if not os.path.exists(filename):

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Event ID",
                    "Timestamp",
                    "Source IP",
                    "Destination IP",
                    "Request Type",
                    "Status",
                    "Attempt Number",
                    "Alert"
                ])

    # =================================
    # LOG NETWORK EVENT
    # =================================

    def log_event(self, event):

        with self.lock:

            with open(
                self.filename,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    event["id"],
                    event["timestamp"],
                    event["src_ip"],
                    event["dst_ip"],
                    event["request_type"],
                    event["status"],
                    event["attempt"],
                    event["alert"]
                ])
