# MessageGateway

Deploy the function to serve HTTP requests:

```
gcloud functions deploy handle_http --trigger-http --runtime=python312 --entry-point=handle_http --memory=1024MB --timeout=300s
```

Deploy the function to serve pub/sub requests:

```
 gcloud functions deploy handle_pubsub --gen2 --region=us-central1 --trigger-topic=messages --runtime=python312 --entry-point=handle_pubsub --memory=1024MB --timeout=300s
```

# Other useful gcloud functions commands
- `gcloud auth login` - Login to Google Cloud.
- `gcloud projects list` - List the projects you have access to.
- `gcloud config list` - List the current configuration.
- `gcloud config set project PROJECT_ID` - Set the project to use.
- `gcloud functions list` - List Google Cloud Functions.
- `gcloud functions describe FUNCTION_NAME` - Display details of a Google Cloud Function.
- `gcloud functions logs read --limit 50` - Show the last 50 log entries.
- `gcloud functions delete FUNCTION_NAME` - Because sometime (always?) `deploy` silently fails to replace the existing function. 
