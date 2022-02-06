import os
import sys

from dotenv import dotenv_values

from src.utils import shard

# for testing Gradescope package currently under development
# in production, we will use the gradescope_api from https://cs161-staff/gradescope-api
# sys.path.append("/Users/shomil/Documents/github/cs161-staff/notebook/gradescope-api/src/")

print(dotenv_values(".env-test"))

for key, value in dotenv_values(".env-pytest").items():
    os.environ[shard + key] = value
