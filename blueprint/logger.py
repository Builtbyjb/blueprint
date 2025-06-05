import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# file_handler = logging.FileHandler("log_file.log")
# file_handler.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stdout_handler.setFormatter(formatter)
# file_handler.setFormatter(formatter)
# log.addHandler(file_handler)
log.addHandler(stdout_handler)
