import time
# from functools import wraps
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from typing import Dict
from blueprint.logger import log

MAX_CALLS = 20

# Rate limiter
class RateLimiter(BaseHTTPMiddleware):
  def __init__(self, app):
    super().__init__(app)
    self.rate_limit_records: Dict[str, int] = defaultdict(int)

  async def dispatch(self, request: Request, call_next):
    client_ip = str(request.client)

    if self.rate_limit_records[client_ip] >= MAX_CALLS:
      time.sleep(1)
      self.rate_limit_records[client_ip] = 0
      print("slept for 1 sec")

    self.rate_limit_records[client_ip] += 1

    # Process the request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    path = request.url.path

    log.info(f"{request.method} request to {path} took {process_time} seconds")

    return response
