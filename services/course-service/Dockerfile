FROM public.ecr.aws/lambda/python:3.12

# Set working directory to Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first (better layer cache)
COPY requirements.txt .

# Install Python dependencies into the Lambda image
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# Ensure src is on PYTHONPATH
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/src:${PYTHONPATH}"

# AWS Lambda entrypoint (Mangum handler defined in src/main.py)
CMD ["src.main.handler"]