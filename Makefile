deploy-form-submit:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit --trigger-http --runtime python39

deploy-email-queue:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_email_queue --trigger-http --runtime python39

deploy-form-submit-stage:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit_stage --trigger-http --runtime python39

deploy-email-queue-stage:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_email_queue_stage --trigger-http --runtime python39

test: 
	pytest
	
stage: deploy-form-submit-stage deploy-email-queue-stage
prod: deploy-form-submit deploy-email-queue
