# W3ID Smoke Tester

Test the Perma-id (w3id.org) routing for https://github.com/lmodel.

These scripts exercise the content-negotiation and redirect rules in
`./lmodel/.htaccess` so you can catch breakage before deploying to
[w3id.org](https://w3id.org).

## Requirements

- Python 3.7+ (stdlib only).
- For `podman_smoke.sh`: `podman` (or `docker`), `curl`, `bash`.

## Test a local `.htaccess`

Spins up a throwaway Apache container with your `.htaccess` mounted, runs the suite against it, and cleans up on exit:

```bash
./podman_smoke.sh path/to/lmodel/.htaccess
```

The path defaults to `../git/hub/w3id.org/lmodel/.htaccess`. Override with env vars: `ENGINE` (default `podman`), `PORT` (`18080`), `IMAGE`, `NAME`, `PYTHON`.

## Test any base URL

`w3id_smoke_test.py` requests each case, checks the status and `Location`, then follows the redirect upstream to verify it returns `200`.

```bash
python3 w3id_smoke_test.py                              # local Apache (default)
BASE=https://w3id.org/lmodel python3 w3id_smoke_test.py # production
ONLY=turtle python3 w3id_smoke_test.py                  # one case (substring)
NO_UPSTREAM=1 python3 w3id_smoke_test.py                # skip upstream check
```

| Variable      | Default                         | Description                          |
|---------------|---------------------------------|--------------------------------------|
| `BASE`        | `http://localhost:18080/lmodel` | Base URL to test against.            |
| `TIMEOUT`     | `10`                            | Per-request timeout (seconds).       |
| `NO_UPSTREAM` | _(unset)_                       | Set to `1` to skip the upstream check.|
| `ONLY`        | _(unset)_                       | Run only cases matching this substring.|

Exit code is `0` if all cases pass, `1` otherwise.

### Running with uv

Since the tester is stdlib-only, [uv](https://docs.astral.sh/uv/) can run it without any project setup, provisioning a suitable Python automatically:

```bash
uv run w3id_smoke_test.py                                # local Apache (default)
uv run --python 3.11 w3id_smoke_test.py                  # pin interpreter version
BASE=https://w3id.org/lmodel uv run w3id_smoke_test.py   # production
```
