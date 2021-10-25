# Primoco Selenium Export

Primoco Selenium Export is a small tool to download a [Primoco](https://primoco.me/en/) CSV export with the help of Selenium.

## Requirements
- Google Chrome either locally or in a docker selenium container

## Installation

1. Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all necessary packages.

```bash
pip3 install -U selenium
pip3 install -U python-dotenv
```

2. Make sure to rename the file `example.env` to `.env` and update the variables accordingly.


## Usage

### Docker
1. Make sure your docker instance is running and on port `4444`. To quickly spin it up, run:
```bash
docker run -d -p 4444:4444 -p 5900:5900 --shm-size="2g" -v ~/selenium-downloads:/home/seluser/Downloads selenium/standalone-chrome:latest
```
Hnt: Port `5900` is to access the instance with a VNC viewer.

2. make sure that you can connect to your docker instance. To test it run:
```bash
python3 webdriver-test.py
```
3. Run the script
```bash
python3 download-export.py
```


### Local Browser

1. In order to use your installed Chrome browser you might need to install chromedrivers:
```bash
pip3 install chromedriver-py
```
2. Make sure to set the `RUN_LOCALLY` constant in the `PrimocoExportDownloader` class to `True`.
3. Run
```bash
python3 download-export.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT License](https://choosealicense.com/licenses/mit/)

Copyright (c) 2021 Simon Mayerhofer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.