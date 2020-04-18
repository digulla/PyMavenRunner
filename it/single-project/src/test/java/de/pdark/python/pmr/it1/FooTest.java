package de.pdark.python.pmr.it1;

import static org.junit.Assert.*;

import org.junit.Test;

public class FooTest {
	@Test
	public void testStrip() {
		assertEquals("X", new Foo().bar("X:"));
	}
	@Test
	public void testStripOnce() {
		assertEquals("X:", new Foo().bar("X::"));
	}
	@Test
	public void testNoStrip() {
		assertEquals("X:Y", new Foo().bar("X:Y"));
	}
}