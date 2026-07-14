<div align="center" width="100%">
    <h1>Authentik-Enum</h1>
    <img width="350" alt="authentik" src="https://github.com/user-attachments/assets/4ae935c5-0648-46d3-9528-488855934200" />
    <p>Enumerate the exact version of a live Authentik instance through unauthenticated static asset probing</p>
    <p>
        <a target="_blank" href="https://github.com/l4rm4nd"><img src="https://img.shields.io/badge/maintainer-LRVT-orange" /></a>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/graphs/contributors/"><img src="https://img.shields.io/github/contributors/l4rm4nd/Authentik-Enum.svg" /></a>
        <a target="_blank" href="https://github.com/PyCQA/bandit"><img src="https://img.shields.io/badge/security-bandit-yellow.svg" /></a><br>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/commits/"><img src="https://img.shields.io/github/last-commit/l4rm4nd/Authentik-Enum.svg" /></a>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/issues/"><img src="https://img.shields.io/github/issues/l4rm4nd/Authentik-Enum.svg" /></a>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/issues?q=is%3Aissue+is%3Aclosed"><img src="https://img.shields.io/github/issues-closed/l4rm4nd/Authentik-Enum.svg" /></a><br>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/stargazers"><img src="https://img.shields.io/github/stars/l4rm4nd/Authentik-Enum.svg?style=social&label=Star" /></a>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/network/members"><img src="https://img.shields.io/github/forks/l4rm4nd/Authentik-Enum.svg?style=social&label=Fork" /></a>
        <a target="_blank" href="https://github.com/l4rm4nd/Authentik-Enum/watchers"><img src="https://img.shields.io/github/watchers/l4rm4nd/Authentik-Enum.svg?style=social&label=Watch" /></a>
    </p>
    <p>
        <a href="https://www.buymeacoffee.com/LRVT" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;"></a>
    </p>
</div>

## Description

Authentik-Enum is a Python3 script that attempts to identify the exact version of a publicly accessible Authentik instance.

> [!NOTE]
> No credentials are required. Script only accesses publicly served static assets.

## How It Works

Authentik uses versioned script includes in its administrative interface template.

An example of the relevant upstream implementation can be found [in the Authentik repository](https://github.com/goauthentik/authentik/blob/bc24815ae6c8181216b88daeb0e8825aa7b17f7b/authentik/core/templates/if/admin.html#L6).

```html
<script src="/static/dist/AdminInterface-{version}.js"></script>
```

Authentik-Enum retrieves release versions from GitHub and checks whether the corresponding versioned file exists on the target. 

The flow goes like this:

1. Retrieve the available Authentik release versions from GitHub
2. Construct the expected `AdminInterface-{version}.js` URL for every release
3. Send an HTTP request for each versioned JavaScript file
4. Use byte-range requests to avoid downloading the complete asset where supported
5. Print the HTTP status and MD5 hash of matching responses
6. Stop at the first discovered version unless `--all` is specified

A successful response indicates that the tested asset exists:

| HTTP status           | Meaning                                                                      |
| --------------------- | ---------------------------------------------------------------------------- |
| `200 OK`              | The versioned JavaScript file exists and was returned                        |
| `206 Partial Content` | The file exists and the server honored the byte-range request                |
| `404 Not Found`       | The tested versioned JavaScript file does not exist                          |
| Other status          | The request may have been redirected, blocked, or handled by an intermediary |

> [!TIP]
> A `206 Partial Content` response is expected when the target supports byte-range requests. This confirms that the asset exists without downloading the complete JavaScript file, which may be 50 KB or larger.

## Requirements

* Python 3
* Network access to the target Authentik instance
* Network access to the GitHub API for retrieving Authentik releases

## Usage

### Clone the Repository

```bash
git clone https://github.com/l4rm4nd/Authentik-Enum
cd Authentik-Enum

python3 authentik-enum.py --base-url https://sso.example.com
```

## Limitations

* **Custom frontend builds:** Modified or custom Authentik frontend bundles may use different filenames or paths.
* **Reverse proxies:** A proxy, CDN, web application firewall, or authentication gateway may alter status codes or block the requests.
* **Stale assets:** Old JavaScript files may remain accessible after an Authentik upgrade, resulting in multiple matches.
* **Changed asset structure:** Future Authentik releases may change the filename or static asset path.
* **GitHub API access:** Release discovery may fail if GitHub is unavailable, rate-limited, or blocked from the testing system.
* **False-positive responses:** Some servers return custom pages with status `200` for nonexistent files. Compare response hashes, content types, and response sizes when validating unexpected results.
