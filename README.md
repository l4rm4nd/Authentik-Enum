# Authentik-Enum
Simple Python3 Script to Enumerate Authentik Version

## How it works

Authentik uses versioned script includes (see [here](https://github.com/goauthentik/authentik/blob/bc24815ae6c8181216b88daeb0e8825aa7b17f7b/authentik/core/templates/if/admin.html#L6)).

<img width="1938" height="603" alt="image" src="https://github.com/user-attachments/assets/834628f1-1cdc-465b-94b8-af1a92d5b06b" />

This allows for unauthenticated version enumerations by file existence testing. Basically get all release versions from Github, then try to fetch each versioned JS file and display the result. If an exact versioned script was found (200 OK), you have enumerated the exact Authentik version in use.

## How to run

````bash
python3 authentik-enum.py --verbose
````
