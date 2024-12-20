#!/bin/bash

source ./parser/.env

# Создание функции activity_tabel

cd crons/activity_table
zip code.zip ./*

yc serverless function create --name=activity-tabel


yc serverless function version create \
  --function-name=activity-tabel \
  --runtime python311 \
  --entrypoint update_activity.update_activity \
  --memory 128m \
  --execution-timeout 3s \
  --source-path ./code.zip \
  --environment DB_HOST="$DB_HOST",DB_PORT=$DB_PORT,DB_PASSWORD="$DB_PASSWORD",DB_USER="$DB_USER",DB_NAME="$DB_NAME"

yc serverless trigger create timer \
  --name activity-tabel-trigger \
  --cron-expression '0 * ? * * *' \
  --invoke-function-name activity-tabel \
  --invoke-function-service-account-id $SERVICE_ACCOUNT_ID


rm code.zip
cd ../..

# Создание функции top100_table

cd crons/top100_table
zip code.zip ./*

yc serverless function create --name=top100-tabel


yc serverless function version create \
  --function-name=top100-tabel \
  --runtime python311 \
  --entrypoint update_top_100.update_top100 \
  --memory 128m \
  --execution-timeout 3s \
  --source-path ./code.zip \
  --environment "DB_HOST"="$DB_HOST","DB_PORT"=$DB_PORT,"DB_PASSWORD"="$DB_PASSWORD","DB_USER"="$DB_USER","DB_NAME"="$DB_NAME"

yc serverless trigger create timer \
  --name top100-tabel-trigger \
  --cron-expression '*/5 * ? * * *' \
  --invoke-function-name top100-tabel \
  --invoke-function-service-account-id $SERVICE_ACCOUNT_ID

rm code.zip