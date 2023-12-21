# Use an official Python runtime as a parent image
FROM python:3.6

# Set the working directory in the container
WORKDIR .

# Copy the current directory contents into the container at .
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# The CMD instruction does not run a script by default
CMD ["echo", "Specify a script to run with docker run <image-name> python <script-name>"]

