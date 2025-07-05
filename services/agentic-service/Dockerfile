FROM public.ecr.aws/lambda/python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

ENV PYTHONPATH="/app/src"

# Command to run the application
CMD ["main.handler"]