/**
 * Smoke tests for the ported algorithms.
 *
 * This mirrors tests/test_algorithms.py case for case: the same automata,
 * the same strings, the same expected answers. If both suites pass, the
 * JavaScript port and the Python original agree.
 *
 * Run with:  node web/tests/run-tests.js
 *
 * The file is executed inside a context where automaton.js, algorithms.js
 * and examples.js have already been evaluated, so their globals are here.
 */

let failures = 0;
let checks = 0;

function assert(condition, message) {
  checks += 1;
  if (!condition) {
    failures += 1;
    console.error("  FAIL: " + message);
  }
}

function assertEqual(actual, expected, message) {
  assert(
    actual === expected,
    message + " (expected " + JSON.stringify(expected) + ", got " + JSON.stringify(actual) + ")"
  );
}

/* ------------------------------------------------------------------ */

function buildNfaEndsWithAb() {
  // NFA over {a,b} accepting strings that end with "ab".
  const nfa = new Automaton({ name: "Ends with ab" });
  for (const s of ["q0", "q1", "q2"]) nfa.addState(s);
  nfa.alphabet = ["a", "b"];
  nfa.setStartState("q0");
  nfa.acceptStates = new Set(["q2"]);
  nfa.addTransition("q0", "a", "q0");
  nfa.addTransition("q0", "b", "q0");
  nfa.addTransition("q0", "a", "q1");
  nfa.addTransition("q1", "b", "q2");
  return nfa;
}

function testSimulation() {
  const nfa = buildNfaEndsWithAb();
  assert(simulate(nfa, "ab").accepted, 'simulate "ab" should be accepted');
  assert(simulate(nfa, "aab").accepted, 'simulate "aab" should be accepted');
  assertEqual(simulate(nfa, "aba").accepted, false, 'simulate "aba"');
  assertEqual(simulate(nfa, "").accepted, false, "simulate empty string");
  console.log("OK simulate NFA");
}

function testSubsetConstruction() {
  const nfa = buildNfaEndsWithAb();
  const result = nfaToDfa(nfa);
  const dfa = result.dfa;
  assert(dfa.isDeterministic(), "subset construction must yield a DFA");

  const strings = ["ab", "aab", "bbab", "aababab", "", "a", "ba", "aba", "bb"];
  for (const s of strings) {
    const nfaResult = simulate(nfa, s).accepted;
    const dfaResult = simulate(dfa, s).accepted;
    assertEqual(dfaResult, nfaResult, 'NFA and DFA disagree on "' + s + '"');
  }
  console.log("OK subset construction, steps: " + result.steps.length);
}

function testEpsilonNfa() {
  const nfa = new Automaton({ name: "epsilon test" });
  for (const s of ["q0", "q1", "q2"]) nfa.addState(s);
  nfa.alphabet = ["a"];
  nfa.setStartState("q0");
  nfa.acceptStates = new Set(["q2"]);
  nfa.addTransition("q0", EPSILON, "q1");
  nfa.addTransition("q1", "a", "q2");

  assert(simulate(nfa, "a").accepted, 'epsilon-NFA should accept "a"');
  assertEqual(simulate(nfa, "").accepted, false, "epsilon-NFA on empty string");

  const dfa = nfaToDfa(nfa).dfa;
  assert(dfa.isDeterministic(), "converted epsilon-NFA must be a DFA");
  assert(simulate(dfa, "a").accepted, 'converted DFA should accept "a"');
  console.log("OK epsilon-NFA handling");
}

function testMinimization() {
  // Classic textbook example: DFA over {0,1} with equivalent states to merge.
  const dfa = new Automaton({ name: "min test" });
  for (const s of ["A", "B", "C", "D", "E", "F"]) dfa.addState(s);
  dfa.alphabet = ["0", "1"];
  dfa.setStartState("A");
  dfa.acceptStates = new Set(["C", "D", "E"]);
  const trans = [
    ["A", "0", "B"], ["A", "1", "C"],
    ["B", "0", "A"], ["B", "1", "D"],
    ["C", "0", "E"], ["C", "1", "F"],
    ["D", "0", "E"], ["D", "1", "F"],
    ["E", "0", "E"], ["E", "1", "F"],
    ["F", "0", "F"], ["F", "1", "F"],
  ];
  for (const t of trans) dfa.addTransition(t[0], t[1], t[2]);

  const result = minimizeDfa(dfa);
  const minDfa = result.dfa;
  assertEqual(minDfa.states.length, 3, "minimal DFA state count");

  for (const s of ["", "0", "1", "01", "10", "0011", "111", "000"]) {
    const original = simulate(dfa, s).accepted;
    const minimal = simulate(minDfa, s).accepted;
    assertEqual(minimal, original, 'original and minimal DFA disagree on "' + s + '"');
  }
  console.log("OK minimization, groups: " + minDfa.states.length);
}

function testProperties() {
  const dfa = new Automaton({ name: "props test" });
  dfa.addState("q0");
  dfa.addState("q1");
  dfa.addState("unreachable");
  dfa.alphabet = ["a"];
  dfa.setStartState("q0");
  dfa.acceptStates = new Set(["q1"]);
  dfa.addTransition("q0", "a", "q1");
  dfa.addTransition("q1", "a", "q1");

  const report = analyzeProperties(dfa);
  assert(report.isDeterministic, "should be deterministic");
  assert(!report.isConnected, "should not be connected");
  assert(report.unreachableStates.has("unreachable"), "unreachable state must be detected");
  console.log("OK properties analysis");
}

function testSerializationRoundTrip() {
  // The .afjson format is shared with the desktop app, so it must survive
  // a full save/load cycle unchanged.
  const original = buildNfaEndsWithAb();
  const restored = Automaton.fromJSON(JSON.parse(JSON.stringify(original.toJSON())));
  assertEqual(
    JSON.stringify(restored.toJSON()),
    JSON.stringify(original.toJSON()),
    "round-trip through .afjson must be lossless"
  );
  for (const s of ["ab", "ba", "aab", ""]) {
    assertEqual(
      simulate(restored, s).accepted,
      simulate(original, s).accepted,
      'round-tripped automaton disagrees on "' + s + '"'
    );
  }
  console.log("OK .afjson round-trip");
}

function testBundledExamples() {
  // Every bundled example must load and analyse without throwing.
  const names = Object.keys(EXAMPLES);
  assert(names.length >= 5, "expected at least 5 bundled examples, got " + names.length);
  for (const name of names) {
    const automaton = Automaton.fromJSON(EXAMPLES[name]);
    assertEqual(automaton.validate().length, 0, 'example "' + name + '" should be valid');
    analyzeProperties(automaton);
  }

  // Spot-check the semantics of two of them.
  const endsIn1 = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  assert(simulate(endsIn1, "1011").accepted, '"1011" ends in 1');
  assertEqual(simulate(endsIn1, "1010").accepted, false, '"1010" does not end in 1');

  const divBy3 = Automaton.fromJSON(EXAMPLES["DFA: divisible by 3"]);
  // 110 binary = 6, divisible by 3; 111 = 7, not divisible.
  assert(simulate(divBy3, "110").accepted, "110 (=6) is divisible by 3");
  assertEqual(simulate(divBy3, "111").accepted, false, "111 (=7) is not divisible by 3");
  console.log("OK bundled examples");
}

function testRegexToNfa() {
  const nfa = regexToNfa("(a|b)*abb");
  assert(nfa.states.length > 0, "regexToNfa should generate states");
  assert(simulate(nfa, "abb").accepted, "should accept 'abb'");
  assert(simulate(nfa, "aabb").accepted, "should accept 'aabb'");
  assert(simulate(nfa, "babb").accepted, "should accept 'babb'");
  assertEqual(simulate(nfa, "abba").accepted, false, "should reject 'abba'");
  assertEqual(simulate(nfa, "ab").accepted, false, "should reject 'ab'");
  console.log("OK regex to NFA");
}

function testAutomatonToRegex() {
  const endsIn1 = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  const res = automatonToRegex(endsIn1);
  assert(typeof res.regex === "string" && res.regex.length > 0, "regex should be non-empty");
  assert(res.steps.length === endsIn1.states.length, "all states should be eliminated step-by-step");
  console.log("OK automaton to regex (GNFA)");
}

function testOperations() {
  const dfa1 = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  const comp = complementDfa(dfa1);
  assert(comp.isDeterministic(), "complement must be deterministic");
  assertEqual(simulate(comp, "101").accepted, false, "complement rejects 101");
  assertEqual(simulate(comp, "100").accepted, true, "complement accepts 100");

  const selfEquiv = checkEquivalence(dfa1, dfa1);
  assert(selfEquiv.equivalent, "DFA must be equivalent to itself");

  const compEquiv = checkEquivalence(dfa1, comp);
  assertEqual(compEquiv.equivalent, false, "DFA and complement cannot be equivalent");
  assert(compEquiv.counterexample1Not2 !== null, "counterexample must be found");

  const intersection = intersectDfas(dfa1, comp);
  assertEqual(isLanguageEmpty(intersection), true, "DFA ∩ complement must be empty");

  const union = unionDfas(dfa1, comp);
  assert(simulate(union, "0").accepted && simulate(union, "1").accepted, "DFA ∪ complement accepts all");
  console.log("OK automata operations (complement, intersection, union, equivalence)");
}

function testWordGeneratorAndBatch() {
  const dfa = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  const words = generateAcceptedStrings(dfa, 5);
  assertEqual(words.length, 5, "should generate 5 accepted strings");
  assert(words.indexOf("1") !== -1 && words.indexOf("01") !== -1, "words should end in 1");
  assert(isLanguageInfinite(dfa), "DFA language should be infinite");

  const batch = batchSimulate(dfa, ["0", "1", "00", "01"]);
  assertEqual(batch.length, 4, "batch length");
  assertEqual(batch[0].accepted, false, "0 not accepted");
  assertEqual(batch[1].accepted, true, "1 accepted");
  assertEqual(batch[2].accepted, false, "00 not accepted");
  assertEqual(batch[3].accepted, true, "01 accepted");
  console.log("OK string generation and batch testing");
}

function testExporters() {
  const dfa = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  const dot = toDot(dfa);
  assert(dot.includes("digraph") && dot.includes("doublecircle"), "DOT format check");

  const tikz = toTikz(dfa);
  assert(tikz.includes("tikzpicture") && tikz.includes("\\node"), "TikZ format check");

  const xml = toJflapXml(dfa);
  assert(xml.includes("<structure>") && xml.includes("<automaton>"), "JFLAP XML check");

  const imported = fromJflapXml(xml);
  assertEqual(imported.states.length, dfa.states.length, "JFLAP round-trip state count");
  assert(simulate(imported, "101").accepted, "JFLAP imported sim 101");
  assertEqual(simulate(imported, "100").accepted, false, "JFLAP imported sim 100");
  console.log("OK exporters (DOT, TikZ, JFLAP)");
}

function testAtmPinVerification() {
  const nfa = regexToNfa("[0-9]{4}", "ATM PIN Verification");
  assertEqual(simulate(nfa, "1234").accepted, true, "1234 accepted");
  assertEqual(simulate(nfa, "0000").accepted, true, "0000 accepted");
  assertEqual(simulate(nfa, "9876").accepted, true, "9876 accepted");
  assertEqual(simulate(nfa, "123").accepted, false, "123 rejected");
  assertEqual(simulate(nfa, "12345").accepted, false, "12345 rejected");
  assertEqual(simulate(nfa, "").accepted, false, "empty string rejected");
  console.log("OK ATM PIN verification (regex [0-9]{4} -> NFA)");
}

function testEmailValidation() {
  const nfa = regexToNfa("[a-c]+@[a-c]+\\.[a-c]+", "Email Validation");
  assertEqual(simulate(nfa, "a@b.c").accepted, true, "a@b.c accepted");
  assertEqual(simulate(nfa, "ab@ba.cb").accepted, true, "ab@ba.cb accepted");
  assertEqual(simulate(nfa, "c@a.b").accepted, true, "c@a.b accepted");
  assertEqual(simulate(nfa, "@b.c").accepted, false, "@b.c rejected");
  assertEqual(simulate(nfa, "a@.c").accepted, false, "a@.c rejected");
  assertEqual(simulate(nfa, "a@b.").accepted, false, "a@b. rejected");
  assertEqual(simulate(nfa, "a@b").accepted, false, "a@b rejected");
  assertEqual(simulate(nfa, "").accepted, false, "empty string rejected");
  console.log("OK Email validation (regex [a-c]+@[a-c]+\\.[a-c]+ -> NFA)");
}

function testPasswordVerification() {
  const pwdRegex = "(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*";
  const nfa = regexToNfa(pwdRegex, "Password Verification");
  assertEqual(simulate(nfa, "a1").accepted, true, "a1 accepted");
  assertEqual(simulate(nfa, "1a").accepted, true, "1a accepted");
  assertEqual(simulate(nfa, "aaa1").accepted, true, "aaa1 accepted");
  assertEqual(simulate(nfa, "111a11").accepted, true, "111a11 accepted");
  assertEqual(simulate(nfa, "aaaa").accepted, false, "aaaa rejected (no digit)");
  assertEqual(simulate(nfa, "1111").accepted, false, "1111 rejected (no letter)");
  assertEqual(simulate(nfa, "").accepted, false, "empty string rejected");
  console.log("OK Password verification (regex (a|1)*(a(a|1)*1|1(a|1)*a)(a|1)* -> NFA)");
}

function testCleanDfaGeneration() {
  const pin = regexToCleanDfa("[0-9]{4}", "ATM PIN (Clean)");
  assertEqual(pin.states.length, 5, "ATM PIN clean DFA must have exactly 5 states");
  assertEqual(simulate(pin, "1234").accepted, true, "1234 accepted");
  assertEqual(simulate(pin, "123").accepted, false, "123 rejected");

  const email = regexToCleanDfa("[a-c]+@[a-c]+\\.[a-c]+", "Email (Clean)");
  assertEqual(email.states.length, 6, "Email clean DFA must have exactly 6 states");
  assertEqual(simulate(email, "a@b.c").accepted, true, "a@b.c accepted");
  assertEqual(simulate(email, "a@b").accepted, false, "a@b rejected");

  const pwd = regexToCleanDfa("(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*", "Password (Clean)");
  assertEqual(pwd.states.length, 4, "Password clean DFA must have exactly 4 states");
  assertEqual(simulate(pwd, "a1").accepted, true, "a1 accepted");
  assertEqual(simulate(pwd, "aaaa").accepted, false, "aaaa rejected");

  const abb = regexToCleanDfa("(a|b)*abb", "abb (Clean)");
  assertEqual(abb.states.length, 4, "(a|b)*abb clean DFA must have exactly 4 states");
  assertEqual(simulate(abb, "abb").accepted, true, "abb accepted");
  assertEqual(simulate(abb, "ab").accepted, false, "ab rejected");
  console.log("OK clean minimal DFA generation (no state explosion)");
}

function testRandomGenerator() {
  const dfa = generateRandomDfa({ numStates: 6, alphabet: ["a", "b"], seed: 42 });
  assertEqual(dfa.states.length, 6, "random DFA state count");
  assert(dfa.isDeterministic(), "random DFA must be deterministic");
  assert(dfa.isComplete(), "random DFA must be complete");
  assertEqual(dfa.validate().length, 0, "random DFA must be valid");

  const dfaAgain = generateRandomDfa({ numStates: 6, alphabet: ["a", "b"], seed: 42 });
  assertEqual(
    JSON.stringify(dfa.toJSON()),
    JSON.stringify(dfaAgain.toJSON()),
    "the same seed must reproduce the same random DFA"
  );

  const nfa = generateRandomNfa({ numStates: 6, alphabet: ["a", "b"], seed: 7 });
  assertEqual(nfa.states.length, 6, "random NFA state count");
  assertEqual(nfa.validate().length, 0, "random NFA must be valid");

  let threw = false;
  try {
    generateRandomDfa({ numStates: 0 });
  } catch (e) {
    threw = true;
  }
  assert(threw, "numStates < 1 must throw");
  console.log("OK random automaton generator");
}

function testWordLengthDistribution() {
  const dfa = Automaton.fromJSON(EXAMPLES["DFA: ends with 1"]);
  const dist = wordLengthDistribution(dfa, 6);
  assertEqual(dist[0], 0, "empty string is not accepted");
  for (let n = 1; n <= 6; n++) {
    assertEqual(dist[n], 1, "a word of length " + n + " should be accepted");
  }

  const onlyA = new Automaton({ name: "only a" });
  onlyA.addState("s0");
  onlyA.addState("s1");
  onlyA.alphabet = ["a", "b"];
  onlyA.setStartState("s0");
  onlyA.acceptStates = new Set(["s1"]);
  onlyA.addTransition("s0", "a", "s1");
  const d2 = wordLengthDistribution(onlyA, 3);
  assertEqual(d2[1], 1, "length 1 accepted");
  assertEqual(d2[2], 0, "length 2 not accepted");
  assertEqual(d2[3], 0, "length 3 not accepted");

  const eps = new Automaton({ name: "eps" });
  for (const s of ["q0", "q1", "q2"]) eps.addState(s);
  eps.alphabet = ["a"];
  eps.setStartState("q0");
  eps.acceptStates = new Set(["q2"]);
  eps.addTransition("q0", EPSILON, "q1");
  eps.addTransition("q1", "a", "q2");
  const d3 = wordLengthDistribution(eps, 2);
  assertEqual(d3[0], 0, "epsilon-NFA: empty string not accepted");
  assertEqual(d3[1], 1, 'epsilon-NFA: "a" accepted');
  assertEqual(d3[2], 0, "epsilon-NFA: no length-2 word");

  const empty = new Automaton({ name: "empty" });
  const d4 = wordLengthDistribution(empty, 3);
  assertEqual(d4[0], 0, "no start state: length 0");
  assertEqual(d4[3], 0, "no start state: length 3");
  console.log("OK word-length distribution");
}

/* ------------------------------------------------------------------ */

console.log("Running AutomataForge algorithm tests (JavaScript port)\n");
testSimulation();
testSubsetConstruction();
testEpsilonNfa();
testMinimization();
testProperties();
testSerializationRoundTrip();
testBundledExamples();
testRegexToNfa();
testAutomatonToRegex();
testOperations();
testWordGeneratorAndBatch();
testExporters();
testAtmPinVerification();
testEmailValidation();
testPasswordVerification();
testCleanDfaGeneration();
testRandomGenerator();
testWordLengthDistribution();

console.log("\n" + checks + " checks, " + failures + " failures.");
if (failures === 0) console.log("All algorithm smoke tests passed.");

// Picked up by the runner to set the process exit code.
globalThis.__TEST_FAILURES__ = failures;
