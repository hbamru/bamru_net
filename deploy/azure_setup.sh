#!/bin/bash
set -e
set -x

NAME=$1
RESOURCEGROUP_NAME=${NAME}-rg
POSTGRES_NAME=${NAME}-db
SERVICEPLAN_NAME=${NAME}-sp
WEBAPP_NAME=${NAME}-app
STORAGE_NAME=${NAME}
SLOT=staging
HOSTNAME=$2

POSTGRES_DB=${NAME}
POSTGRES_USER=${NAME}_admin
POSTGRES_PASSWORD=$3

LOCATION=westus2
SERVICEPLAN_SKU=S1
POSTGRES_SKU=B_Gen5_1

RUNTIME="python:3.6"

: "${SETUP_AZ:=false}"
: "${SETUP_STORE:=false}"
: "${SETUP_DB:=false}"
: "${SETUP_CONFIG:=false}"

if [  $# -lt 3 ]; then
  echo "Usage: \$0 NAME HOSTNAME POSTGRES_PASSWORD"
  exit 1;
fi

# If there are any errors on DB creation, you may need:
#   az extension add --name db-up

if $SETUP_AZ; then
  az group create --name $RESOURCEGROUP_NAME --location $LOCATION

  az postgres up --resource-group $RESOURCEGROUP_NAME --location $LOCATION --sku-name $POSTGRES_SKU --server-name $POSTGRES_NAME --database-name $POSTGRES_DB --admin-user $POSTGRES_USER --admin-password $POSTGRES_PASSWORD --ssl-enforcement Enabled

  az appservice plan create --name $SERVICEPLAN_NAME --resource-group $RESOURCEGROUP_NAME --sku $SERVICEPLAN_SKU --is-linux

  az webapp create --name $WEBAPP_NAME --resource-group $RESOURCEGROUP_NAME --plan $SERVICEPLAN_NAME --runtime $RUNTIME

  az webapp update -g $RESOURCEGROUP_NAME -n $WEBAPP_NAME --https-only true
  az webapp config set --ftps-state Disabled --resource-group $RESOURCEGROUP_NAME -n $WEBAPP_NAME

  # az webapp config appsettings set --resource-group $RESOURCEGROUP_NAME -n $WEBAPP_NAME --settings #Name=Value
  az webapp config appsettings set --resource-group $RESOURCEGROUP_NAME -n $WEBAPP_NAME --settings @azure_settings.json

  az webapp deployment slot create --name $WEBAPP_NAME --resource-group $RESOURCEGROUP_NAME --slot $SLOT --configuration-source $WEBAPP_NAME
  az webapp update -g $RESOURCEGROUP_NAME -n $WEBAPP_NAME --https-only true -s $SLOT

  # Create and bind a free certificate
  #az webapp config hostname add --webapp-name $WEBAPP_NAME --resource-group $RESOURCEGROUP_NAME --hostname $HOSTNAME
  #thumbprint=$(az webapp config ssl create  --name $WEBAPP_NAME --resource-group $RESOURCEGROUP_NAME --hostname $HOSTNAME  --output tsv --query thumbprint)
  #az webapp config ssl bind --name $WEBAPP_NAME --resource-group $RESOURCEGROUP_NAME --certificate-thumbprint $thumbprint --ssl-type SNI
fi

if $SETUP_STORE; then
  az storage account create --name $STORAGE_NAME --resource-group $RESOURCEGROUP_NAME --access-tier Hot --kind StorageV2  --location $LOCATION --min-tls-version TLS1_2 --sku Standard_RAGRS
  az storage account blob-service-properties update --resource-group $RESOURCEGROUP_NAME --account-name $STORAGE_NAME \
    --enable-delete-retention true \
    --delete-retention-days 14 \
    --enable-versioning true \
    --enable-change-feed true \
    --enable-restore-policy true \
    --restore-days 7 \
    --enable-container-delete-retention true \
    --container-delete-retention-days 7
  az storage container create --name media --account-name $STORAGE_NAME --resource-group $RESOURCEGROUP_NAME --public-access off
  az storage container create --name static --account-name $STORAGE_NAME --resource-group $RESOURCEGROUP_NAME --public-access container
  az storage cors add --methods GET --service b --origins "https://${WEBAPP_NAME}-${SLOT}.azurewebsites.net" --account-name $STORAGE_NAME
  az storage cors add --methods GET --service b --origins "https://${WEBAPP_NAME}.azurewebsites.net" --account-name $STORAGE_NAME
  az storage cors add --methods GET --service b --origins "https://${HOSTNAME}" --account-name $STORAGE_NAME
fi

if $SETUP_DB; then
  # mv gunzip db-2021-05-24--18-17.sql.gz db.sql.gz
  gunzip -k db.sql.gz
  sed -i s/bnet_db/${POSTGRES_USER}/ db.sql
  PGPASSWORD=$POSTGRES_PASSWORD psql --host=${POSTGRES_NAME}.postgres.database.azure.com --port=5432 --username=${POSTGRES_USER}@${POSTGRES_NAME} --dbname=$POSTGRES_DB < db.sql
  rm db.sql
fi


AZURE_STORAGE_KEY=$(az storage account keys list  --account-name $STORAGE_NAME --resource-group $RESOURCEGROUP_NAME --query [0].value -o tsv)


if $SETUP_CONFIG; then
  sed -e "s#X_AZURE_STORAGE_KEY#$AZURE_STORAGE_KEY#g" \
      -e "s/X_AZURE_STORAGE_ACCOUNT_NAME/$STORAGE_NAME/g" \
      -e "s/X_HOSTNAME/${WEBAPP_NAME}-${SLOT}.azurewebsites.net/g" \
      -e "s/X_POSTGRES_HOST/${POSTGRES_NAME}.postgres.database.azure.com/g" \
      -e "s/X_POSTGRES_DB/$POSTGRES_DB/g" \
      -e "s/X_POSTGRES_PASS/$POSTGRES_PASSWORD/g " \
      -e "s/X_POSTGRES_USER/${POSTGRES_USER}@${POSTGRES_NAME}/g" \
      azure_settings.json > processed.json

  az webapp config appsettings set --resource-group $RESOURCEGROUP_NAME -n ${WEBAPP_NAME} --slot ${SLOT} --settings @processed.json

  sed -i -e "s/${WEBAPP_NAME}-${SLOT}/${WEBAPP_NAME}/g" processed.json

  az webapp config appsettings set --resource-group $RESOURCEGROUP_NAME -n ${WEBAPP_NAME} --settings @processed.json

  rm processed.json
fi

#az webapp deployment github-actions add --repo "kduncklee/bamru_net_azure" --branch azure --resource-group $RESOURCEGROUP_NAME -n ${WEBAPP_NAME} --slot ${SLOT}

echo Storage command:
echo az storage blob upload-batch -d media -s . --account-name $STORAGE_NAME --account-key \'$AZURE_STORAGE_KEY\'
