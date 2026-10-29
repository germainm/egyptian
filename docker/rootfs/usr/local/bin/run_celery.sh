#!/bin/sh

echo "Executing \`run_celery\`."

# Use -A and not --app. Both are the same but behave differently
# -A can be located before the command while --app cannot.
exec "${MAYAN_PYTHON_BIN_DIR}celery" -A mayan "${@}"
