# Changelog

<!--next-version-placeholder-->

## v1.2.2 (2024-11-20)

### Fix

* Replace 'self' with 'patch_py4' for better stability ([`6987942`](https://github.com/trialandsuccess/py4web-debug-tools/commit/6987942347b993cf767166b6f3dac90e75989130))

## v1.2.1 (2024-11-20)

### Fix

* Allow logger to be set to False in case you're using py4webs default logger (PY4WEB_ERRORLOG=:stderr) ([`43639f3`](https://github.com/trialandsuccess/py4web-debug-tools/commit/43639f377d92b2f8b96bbdb31f61251fde95f831))

## v1.2.0 (2023-11-06)
### Feature
* Allow custom `error_logger` for tools.enable ([`a8301bc`](https://github.com/trialandsuccess/py4web-debug-tools/commit/a8301bc1762984fc5af420075acdc09e97bcc378))

## v1.1.4 (2023-07-19)


## v1.1.3 (2023-07-19)
### Fix
* Error page renderer can also be False (in addition to None or a method) ([`41d33aa`](https://github.com/trialandsuccess/py4web-debug-tools/commit/41d33aae9e307034b2818641c041f1dd6c8364fc))

## v1.1.2 (2023-07-19)
### Fix
* Wrapper can also return an HTTP response! ([`4431d80`](https://github.com/trialandsuccess/py4web-debug-tools/commit/4431d8094162dc9100aab2798571b87e5a076ed4))

## v1.1.1 (2023-07-19)
### Fix
* Bump `configurable-json` to new typed version ([`52fa55a`](https://github.com/trialandsuccess/py4web-debug-tools/commit/52fa55a3eb0d8e95064ddb9ecae820a2fa229a9a))

### Documentation
* Updated changelog ([`15a9517`](https://github.com/trialandsuccess/py4web-debug-tools/commit/15a9517f149b9bff272306c64165e9e62845e8d0))

## v1.1.0 (2023-07-19)

Moved to hatch build system.

## v1.0.0 (2023-07-17)
### Feature
* **config:** Multiple minor changes: ([`bb14fec`](https://github.com/trialandsuccess/py4web-debug-tools/commit/bb14fec07780826eb7f550cb9c5d0ed24df1f8b3))
* **debugbar:** Added required files ([`afc690f`](https://github.com/trialandsuccess/py4web-debug-tools/commit/afc690fb96ec2c9d54547434caffe7c1469302b1))
* **p4w-debug:** Initial module setup ([`b36c53c`](https://github.com/trialandsuccess/py4web-debug-tools/commit/b36c53c30206189bfcfcbea1c7236f12ae8becab))

### Fix
* Expose `is_debug` from the top-level library ([`dd73055`](https://github.com/trialandsuccess/py4web-debug-tools/commit/dd7305596a90db3b5902dcaa7d4e5f5c22c693c6))
* Expose `is_debug` from the top-level library ([`ee835e8`](https://github.com/trialandsuccess/py4web-debug-tools/commit/ee835e84983e74aa03825b346074469563e58fe6))
* **tools:** 'db' is only required when debugbar is used (debugbar_enabled=True) ([`dba49b8`](https://github.com/trialandsuccess/py4web-debug-tools/commit/dba49b85149b8aa8cf5992529be6942cd9b08de4))

### Documentation
* **readme:** Updated for style and missing `wsgi` ([`9394747`](https://github.com/trialandsuccess/py4web-debug-tools/commit/9394747b2e48a30c1902f5852955f85f9524c6b3))
* **tools:** Include all parameters of .enable() ([`90ccffc`](https://github.com/trialandsuccess/py4web-debug-tools/commit/90ccffcf6342b68434ad64ad945aea4c7c516cf1))
* **README:** Updated explaination ([`3f3b6b3`](https://github.com/trialandsuccess/py4web-debug-tools/commit/3f3b6b3f2f2fca29f4ac15851082e2e49ae288f8))