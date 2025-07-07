First time when start developing an serverless API, execute the following to setup project structure with sample code. don't forget to ask/set the app name and replace `sam-app` accordingly.
```bash
sam init —app-template hello-world-powertools-python —name sam-app \
—package-type Zip —runtime python3.12 \
—tracing —application-insights —structured-logging
```
use MCP tools provided whenever necessary to further modify/develop features, especially around lambda powertools.

When asked to deploy, run `sam deploy --no-confirm-changeset`. If you run with `--guided`, it will stuck. DONT use that flag.