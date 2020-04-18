package de.pdark.python.pmr.it1;

import org.apache.commons.lang3.StringUtils;

public class Foo {
	public String bar(String input) {
		return StringUtils.removeEnd(input, ":");
	}
}