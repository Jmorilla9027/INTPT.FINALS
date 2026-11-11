import time
import random
import threading

from datetime import datetime
from collections import defaultdict, deque

from backend.logger import IDSLogger


class IDSEngine:

    def __init__(self):

        self.server_ip = "192.168.1.100"

        self.normal_ips = [
            "192.168.1.10",
            "192.168.1.15",
            "192.168.1.20",
            "192.168.1.25",
            "192.168.1.30"
        ]

        self.attacker_ip = "203.0.113.50"

        self.max_attempts = 5
        self.time_window = 60
        self.alert_cooldown = 30
        self.request_interval = 2

        self.failed_attempts = defaultdict(deque)
        self.last_alert = {}
        self.request_counts = defaultdict(int)
        self.source_last_seen = {}

        self.total_requests = 0
        self.total_failed = 0
        self.total_alerts = 0

        self.events = deque(maxlen=1000)
        self.next_event_id = 1

        self.lock = threading.RLock()
        self.lifecycle_lock = threading.Lock()

        self.logger = IDSLogger()

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.worker = None
        self.running = False

    # START MONITORING

    def start(self):

        with self.lifecycle_lock:

            with self.lock:
                old_worker = self.worker

            if old_worker and old_worker.is_alive():

                if self.stop_event.is_set():

                    old_worker.join(timeout=3)

                    if old_worker.is_alive():
                        raise RuntimeError(
                            "Previous IDS worker is still stopping"
                        )

                else:

                    with self.lock:
                        self.pause_event.set()
                        self.running = True

                    return

            with self.lock:

                self.stop_event.clear()
                self.pause_event.set()

                self.worker = threading.Thread(
                    target=self.run,
                    daemon=True,
                    name="IDS-Monitor"
                )

                self.running = True
                self.worker.start()

    # PAUSE MONITORING

    def pause(self):

        self.pause_event.clear()

        with self.lock:
            self.running = False

    # STOP MONITORING

    def stop(self):

        self.stop_event.set()
        self.pause_event.set()

        with self.lock:
            self.running = False

    # GENERATE SIMULATED TRAFFIC

    def generate_traffic(self):

        if random.random() < 0.70:

            src_ip = random.choice(self.normal_ips)

            request_type = random.choice([
                "HTTP_REQUEST",
                "DNS_REQUEST",
                "PASSWORD_AUTH"
            ])

            status = "SUCCESS"

            if request_type == "PASSWORD_AUTH":
                if random.random() < 0.10:
                    status = "FAILED"

        else:

            src_ip = self.attacker_ip
            request_type = "PASSWORD_AUTH"
            status = "FAILED"

        return (
            src_ip,
            self.server_ip,
            request_type,
            status
        )

    # BRUTE FORCE DETECTION

    def detect_brute_force(self, src_ip, dst_ip):

        now = time.monotonic()
        key = (src_ip, dst_ip)

        attempts = self.failed_attempts[key]

        while attempts and now - attempts[0] > self.time_window:
            attempts.popleft()

        if len(attempts) >= self.max_attempts:

            previous = self.last_alert.get(key, 0)

            if now - previous >= self.alert_cooldown:

                self.last_alert[key] = now
                self.total_alerts += 1

                return True

        return False

    # PUBLISH EVENT

    def publish_event(self, event):

        with self.lock:

            event["id"] = self.next_event_id
            self.next_event_id += 1

            self.events.append(event)

        self.logger.log_event(event)

    # PROCESS NETWORK REQUEST

    def process_request(self, src, dst, request_type, status):

        with self.lock:

            self.total_requests += 1
            self.request_counts[src] += 1

            self.source_last_seen[src] = time.monotonic()

            attempt = self.request_counts[src]

            alert = "NONE"

            if (
                request_type == "PASSWORD_AUTH"
                and status == "FAILED"
            ):

                self.total_failed += 1

                self.failed_attempts[(src, dst)].append(
                    time.monotonic()
                )

                if self.detect_brute_force(src, dst):
                    alert = "BRUTE FORCE DETECTED"

            event = {
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "src_ip": src,
                "dst_ip": dst,
                "request_type": request_type,
                "status": status,
                "attempt": attempt,
                "alert": alert
            }

        self.publish_event(event)

    # DASHBOARD STATISTICS

    def get_statistics(self):

        now = time.monotonic()

        with self.lock:

            active_sources = sum(
                1
                for last_seen in self.source_last_seen.values()
                if now - last_seen <= 60
            )

            failed_count = 0

            for attempts in self.failed_attempts.values():

                while attempts and now - attempts[0] > self.time_window:
                    attempts.popleft()

                failed_count += len(attempts)

            return {
                "active_sources": active_sources,
                "failed_attempts": failed_count,
                "total_alerts": self.total_alerts,
                "total_requests": self.total_requests,
                "running": self.running
            }

    # RETRIEVE EVENTS

    def get_events(self, after_id=0):

        with self.lock:

            return [
                event.copy()
                for event in self.events
                if event["id"] > after_id
            ]

    # MAIN MONITORING LOOP

    def run(self):

        try:

            while not self.stop_event.is_set():

                if not self.pause_event.wait(timeout=0.5):
                    continue

                if self.stop_event.is_set():
                    break

                traffic = self.generate_traffic()

                self.process_request(*traffic)

                self.stop_event.wait(self.request_interval)

        finally:

            with self.lock:
                self.running = False
