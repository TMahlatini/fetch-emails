commands to deploy to heroku:

1. git add .
2. git commit -m "deploy"
3. git push heroku main
4. heroku ps:scale web=1

commands to encode the token.json and credentials.json files:

    base64 -i token.json -o  token_base64.txt to encode the token.json file

    base64 -i credentials.json -o  credentials_base64.txt to encode the credentials.json file

commands to update env variables in heroku:

    heroku config:set TOKEN_JSON_BASE64=<encoded_token_base64>
    heroku config:set CREDENTIALS_JSON_BASE64=<encoded_credentials_base64>


