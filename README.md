# Pocket48 API

A Python wrapper for Pocket48 API.

![Python 3.7](https://img.shields.io/badge/Python-3.7-3776ab.svg?maxAge=2592000)

## Install

* Install with pip:
  ```
  pip install git+https://git@github.com:wdwind/pocket48_api.git
  ```

* To update:
  ```
  pip install git+https://git@github.com:wdwind/pocket48_api.git --upgrade
  ```

* To update with latest repo code:
  ```
  pip install git+https://git@github.com:wdwind/pocket48_api.git --upgrade --force-reinstall
  ```
  
## Notes

1. `pa`  
   A sample `pa` is provided in the api code, however, it can be only used by one account for at least 10 minutes (meaning after 10 minutes it can be reused by other accounts). It is better to have your own `pa`.
1. Avoiding Re-login  
   The recommendation is to save the requests sessions to avoid login every time when initiating the class. Too many logins may result in an account/ip ban. 

## Examples

Check [``examples/``](examples/).

## License

MIT

## Disclaimer

Pocket48 services are changing constantly. Use it at your own risk.
