package de.pdark.python.pmr.it2.module2;

import static org.junit.Assert.*;

import org.junit.Test;

public class Foo3Test {
	@Test
	public void testStrip() {
		// Failing test
		assertEquals("XYZ", new Foo3().bar("X:"));
	}
}