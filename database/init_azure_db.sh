#!/bin/bash
# database/init_azure_db.sh
# Script para inicializar la base de datos PostgreSQL en Azure

set -euo pipefail

echo " Inicializando base de datos RecWay en Azure PostgreSQL..."

# Variables (configurar según tu deployment)
DB_HOST=${DB_HOST:-recway-db-new.postgres.database.azure.com}
DB_NAME=${DB_NAME:-recWay_db}
DB_USER=${DB_USER:-adminuser}
DB_PORT=${DB_PORT:-5432}

echo " Conectando a: $DB_HOST:$DB_PORT/$DB_NAME"

# Verificar conectividad
echo " Verificando conectividad..."
psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/postgres?sslmode=require" -c "SELECT version();"

# Crear base de datos si no existe
echo " Creando base de datos si no existe..."
psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/postgres?sslmode=require" -c "CREATE DATABASE \"$DB_NAME\" OWNER $DB_USER;" || echo "BD ya existe, continuando..."

# Ejecutar schema
echo " Ejecutando schema..."
psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -f database/schema.sql

echo " Base de datos inicializada correctamente!"
echo " URL de conexión: postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require"
