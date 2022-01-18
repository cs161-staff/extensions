deploy-form-submit:
	gcloud config configurations activate cs161
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_form_submit --trigger-http --runtime python39

deploy-email-queue:
	gcloud config configurations activate cs161
	gcloud config set project cs-161-extensions
	gcloud functions deploy handle_email_queue --trigger-http --runtime python39

all: deploy-email-queue deploy-form-submit