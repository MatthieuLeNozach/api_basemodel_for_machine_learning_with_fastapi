# CAUTION: ADD THE .environment FOLDER TO A .dockerignore  FILE
# TO ENSURE THAT THE ENVIRONMENT VARIABLES ARENT COPIED IN THE IMAGE

FROM python:3.11.7

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 
ENV $(cat .env.dev | xargs)
ENV $(cat .env.test | xargs)


ENV $(cat .env.shared | xargs)

COPY . .

CMD ["./run.sh", "dev", "superuser"]