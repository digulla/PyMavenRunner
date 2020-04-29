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
- Save memory. Either dump successful tests to disk and load them on demand or just keep pointers in the log file and render the section on demand
- Mark the message line of a Java stack trace as an error
- Remember Maven history per project
- Keep N old log files; delete old ones automatically
- Build a chain of projects
- Detect the first changed module and start build from there
- Only change preferences file on disk if the preferences changed
- Context menu in log view to add the selected text to the test input for custom patterns
- Replace tab character in custom patterns with something the user can see. Either `\t` or a Unicode [tab] symbol. Add a context menu to insert this character.

Dev Setup
=========

Run the script `prepare_tests.sh`. It will:

- Check that all necessary tools (`pyenv`, `pipenv`, `java`) are available.
- Install all necessary dependencies
- Run Maven to create some test examples

Change Log
==========

v0.3
----

- Per-project config file
- Detect arbitrary custom patterns
- Debugger for custom patterns
- Editor to edit arbitrary patterns

v0.2
----

- Dump log file to disk
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
