FROM python:3.10-slim 

WORKDIR /app 

#Install system dependencies 
Run apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

#Copy requirements 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy application files 
COPY main.py ./
COPY data/ ./data/ 

#Create a startup script that properly handles Taipy gui 
RUN echo '#!/bin/bash\n\
export TAIPY_GUI_PORT=5000\n\
export TAIPY_GUI_HOST="0.0.0.0"\n\
taipy run main.py --port 5000 --host "0.0.0.0"' > /app/start.sh && \
chmod +x /app/start.sh 

#Expose ports 
EXPOSE 5000

#Set environment variables for container networking 
ENV HOST="0.0.0.0"
ENV TAIPY_GUI_PORT=5000
ENV TAIPY_GUI_HOST="0.0.0.0"

# Run the startup script
CMD ["/app/start.sh"]