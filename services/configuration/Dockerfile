FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# In production, we would install the talos-contracts package here
# RUN pip install talos-contracts

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
