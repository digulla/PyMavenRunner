PyMavenRunner
=============

This a Qt-based UI for running Maven. It can parse the Maven output and display it.

Features
========

- You can start it
- It can parse some important parts of the Maven output, namely the reactor build order and summary

TODO
====

- Support to add projects
- Remember Maven history per project
- Detect test cases
- Detect Java exceptions in the output
- Detect error and warning log output
- Detect arbitrary custom patterns
- Dump log file to disk
- Load only the necessary parts of the log file
- Keep N old log files
- Combobox to select common Maven options
- Checkbox to build without running the tests
- Build a chain of projects
- Resume a failed build
- Detect the first changed module and start build from there
