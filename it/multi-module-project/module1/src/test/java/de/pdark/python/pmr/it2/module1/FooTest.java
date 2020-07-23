package de.pdark.python.pmr.it2.module1;

import static org.junit.Assert.*;

import org.junit.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FooTest {
	private static final Logger log = LoggerFactory.getLogger(Foo2.class);

	@Test
	public void test1() {
		for(int i=0; i<10; i++) {
			log.info("test1 Round {}", i);
		}
	}
	@Test
	public void test2() {
		for(int i=0; i<20; i++) {
			log.info("test2 Round {}", i);
		}
	}
}