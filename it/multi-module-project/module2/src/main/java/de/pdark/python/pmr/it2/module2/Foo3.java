package de.pdark.python.pmr.it2.module2;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Foo3 {
	private static final Logger log = LoggerFactory.getLogger(Foo3.class);

	public String bar(String input) {
		log.trace("bar({})", input);
		log.debug("bar({})", input);
		log.info("bar() was called");
		return StringUtils.removeEnd(input, ":");
	}
}