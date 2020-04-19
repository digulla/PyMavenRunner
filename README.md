PyMavenRunner
=============

This a Qt-based UI for running Maven. It can parse the Maven output and display it.

Features
========

- You can start it
- It can parse some important parts of the Maven output, namely the reactor build order and summary

TODO
====

- Hide successful test output
- Mark the message line of a Java stack trace as an error
- Remember Maven history per project
- Detect arbitrary custom patterns
- Dump log file to disk
- Load only the necessary parts of the log file
- Keep N old log files
- Build a chain of projects
- Detect the first changed module and start build from there

Dev Setup
=========

Run the script `prepare_tests.sh`. It will:

- Check that all necessary tools (`pyenv`, `pipenv`, `java`) are available.
- Install all necessary dependencies
- Run Maven to create some test examples

Change Log
==========

v0.2
----

- Detect test cases
- Detect Java exceptions in the output
- Checkbox to build without running the tests
- Resume a failed build

v0.1
----

- Support to add projects
- Detect Maven plugins in output
- Detect error and warning log output
- Log important events in a tree widget. Jump to the location in the log output by clicking on the tree nodes.
- Combobox to select common Maven options
