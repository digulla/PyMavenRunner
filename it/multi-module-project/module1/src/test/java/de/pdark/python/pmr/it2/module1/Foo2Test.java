package de.pdark.python.pmr.it2.module1;

import static org.junit.Assert.*;

import org.junit.Test;

public class Foo2Test {
	@Test
	public void testStrip() {
		assertEquals("X", new Foo2().bar("X:"));
	}
	@Test
	public void testStripOnce() {
		assertEquals("X:", new Foo2().bar("X::"));
	}
	@Test
	public void testNoStrip() {
		assertEquals("X:Y", new Foo2().bar("X:Y"));
	}
	@Test
	public void testLogWarning() {
		new Foo2()
			.logWarning();
	}
	@Test
	public void testLogException() {
		new Foo2()
			.logException();
	}
}