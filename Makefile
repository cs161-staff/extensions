prod:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit --trigger-http --runtime python39
	gcloud functions deploy handle_email_queue --trigger-http --runtime python39
	gcloud functions deploy handle_flush_gradescope --trigger-http --runtime python39

stage:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit_stage --entry-point handle_form_submit --trigger-http --runtime python39
	gcloud functions deploy handle_email_queue_stage --entry-point handle_email_queue --trigger-http --runtime python39
	gcloud functions deploy handle_flush_gradescope_stage --entry-point handle_flush_gradescope --trigger-http --runtime python39

test: 
	pytest