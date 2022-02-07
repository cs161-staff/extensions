import os

from dotenv import dotenv_values

from src.utils import PREFIX

# for testing Gradescope package currently under development
# in production, we will use the gradescope_api from https://cs161-staff/gradescope-api
# sys.path.append("/Users/shomil/Documents/github/cs161-staff/notebook/gradescope-api/src/")

for key, value in dotenv_values(".env-pytest").items():
    os.environ[PREFIX + key] = value
