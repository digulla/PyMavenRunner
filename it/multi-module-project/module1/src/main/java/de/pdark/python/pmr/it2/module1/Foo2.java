package de.pdark.python.pmr.it2.module1;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Foo2 {
	private static final Logger log = LoggerFactory.getLogger(Foo2.class);

	public String bar(String input) {
		log.debug("bar({})", input);
		return StringUtils.removeEnd(input, ":");
	}

	public void logException() {
		log.error("Just a test", new IllegalArgumentException("Catch me if you can"));
	}

	public void logWarning() {
		log.warn("Please don't call me");
	}
}