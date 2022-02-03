deploy-form-submit:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit --trigger-http --runtime python39

deploy-email-queue:
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_email_queue --trigger-http --runtime python39

all: deploy-form-submit deploy-email-queue