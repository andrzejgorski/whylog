# Whylog

Whylog is a tool for root cause analysis of log entries. It allows the users to capture information about important cause-effect relations between log statements. Whylog then allows to use that knowledge to quickly determine the cause during an investigation of logs.

| CI type  | Status |
| :------------ | :------------ |
| Travis CI  | [![Build Status](https://travis-ci.org/9livesdata/whylog.svg?branch=master)](https://travis-ci.org/9livesdata/whylog)  |
| AppVeyor  | [![AppVeyor build status](https://ci.appveyor.com/api/projects/status/github/9livesdata/whylog?branch=master&svg=true)](https://ci.appveyor.com/project/9livesdata/whylog)  |
| Requirements  | [![Requirements Status](https://requires.io/github/9livesdata/whylog/requirements.svg?branch=master)](https://requires.io/github/9livesdata/whylog/requirements/?branch=master)  |


#### License:
BSD 3-clause

#### Command for installing:
```sh
$ pip install -r requirements.txt
$ python setup.py install
```

#### Command for developing
```sh
$ python setup.py develop
 ```

#### Commands to test
```sh
$ pip install -r requirements-test.txt
$ nosetests
```
