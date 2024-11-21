# Object store

Container containing AWS CLI through which users can interface with the Surf Object Store


# Useful commands

List buckets
```bash
docker compose run --rm \
    aws-cli s3api list-buckets
```


Add bucket lifecycle configuration:
``` bash
docker compose run --rm \
    aws-cli s3api put-bucket-lifecycle-configuration \
    --bucket mycostreams-raw-data \
    --lifecycle-configuration file://delete-prod-files.json
```


Get bucket lifecycle policy:
```bash
docker compose run --rm \
    aws-cli s3api get-bucket-lifecycle-configuration \
    --bucket mycostreams-raw-data
```
