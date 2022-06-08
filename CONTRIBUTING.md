## Environment Setup

- Create a `.env-pytest` file.
- Fill the contents of the `.env-pytest` file with appropriate environment variables for testing (note that some of the Gradescope-related tests need an account with access to the CS 161 Dev Gradescope.)
- To get the `APP_MASTER_SECRET`, sign into the CS 161 SPA and look for it in the [live cloud function.](https://console.cloud.google.com/functions/details/us-central1/handle_form_submit?env=gen1&authuser=1&project=cs-161-extensions&tab=variables)