/**
 * Automaton algorithms: simulation, subset construction, minimization,
 * property analysis and trivial conversions.
 *
 * Faithful JavaScript port of the algorithms/ package of the desktop app.
 * Every function here is pure: it takes an Automaton and returns a result
 * object that also carries the intermediate steps, so the UI can show the
 * process and not only the outcome.
 */

/* ------------------------------------------------------------------ */
/* Simulation (algorithms/simulation.py)                               */
/* ------------------------------------------------------------------ */

function epsilonClosure(automaton, states) {
  const closure = new Set(states);
  const stack = Array.from(states);
  while (stack.length) {
    const state = stack.pop();
    for (const target of automaton.targets(state, EPSILON)) {
      if (!closure.has(target)) {
        closure.add(target);
        stack.push(target);
      }
    }
  }
  return closure;
}

/**
 * Simulate any automaton (DFA or NFA) by tracking a set of active states.
 * Returns { inputString, accepted, steps, finalStates, error }.
 */
function simulate(automaton, inputString) {
  if (automaton.startState === null) {
    return {
      inputString: inputString,
      accepted: false,
      steps: [],
      finalStates: new Set(),
      error: "The automaton has no start state.",
    };
  }

  const steps = [];
  let current = epsilonClosure(automaton, new Set([automaton.startState]));
  steps.push({
    index: 0,
    symbol: null,
    fromStates: new Set(),
    toStates: new Set(current),
    description: "Start state (ε-closure): {" + sortedArray(current).join(", ") + "}",
  });

  const symbols = Array.from(inputString);
  for (let i = 0; i < symbols.length; i++) {
    const symbol = symbols[i];
    if (automaton.alphabet.indexOf(symbol) === -1) {
      return {
        inputString: inputString,
        accepted: false,
        steps: steps,
        finalStates: new Set(),
        error: 'Symbol "' + symbol + '" is not in the alphabet.',
      };
    }
    let nextStates = new Set();
    for (const state of current) {
      nextStates = setUnion(nextStates, automaton.targets(state, symbol));
    }
    nextStates = epsilonClosure(automaton, nextStates);
    const fromLabel = sortedArray(current).join(", ") || "∅";
    const toLabel = sortedArray(nextStates).join(", ") || "∅";
    steps.push({
      index: i + 1,
      symbol: symbol,
      fromStates: new Set(current),
      toStates: new Set(nextStates),
      description: "On '" + symbol + "': {" + fromLabel + "} → {" + toLabel + "}",
    });
    current = nextStates;
    if (!current.size) break;
  }

  const accepted = setIntersection(current, automaton.acceptStates).size > 0;
  return {
    inputString: inputString,
    accepted: accepted,
    steps: steps,
    finalStates: current,
    error: null,
  };
}

/* ------------------------------------------------------------------ */
/* NFA -> DFA, subset construction (algorithms/subset_construction.py)  */
/* ------------------------------------------------------------------ */

function subsetLabel(states) {
  if (!states.size) return "∅";
  return "{" + sortedArray(states).join(",") + "}";
}

/**
 * Convert an NFA into an equivalent DFA by subset construction.
 * Returns { dfa, steps, table }, where each step records the DFA state
 * being expanded, the NFA states it stands for, and its transitions.
 */
function nfaToDfa(nfa) {
  if (nfa.startState === null) {
    throw new Error("The NFA has no start state defined.");
  }

  const alphabet = nfa.alphabet.filter((s) => s !== EPSILON);
  const dfa = new Automaton({ name: nfa.name + " (DFA)", alphabet: alphabet.slice() });

  const startClosure = epsilonClosure(nfa, new Set([nfa.startState]));
  const startKey = setKey(startClosure);

  /** key -> { states: Set, name: string } */
  const known = {};
  known[startKey] = { states: startClosure, name: subsetLabel(startClosure) };

  const queue = [startKey];
  const steps = [];

  dfa.addState(known[startKey].name);
  dfa.setStartState(known[startKey].name);
  if (setIntersection(startClosure, nfa.acceptStates).size) {
    dfa.acceptStates.add(known[startKey].name);
  }

  const processed = new Set();
  let stepIndex = 0;

  while (queue.length) {
    const currentKey = queue.shift();
    if (processed.has(currentKey)) continue;
    processed.add(currentKey);

    const currentStates = known[currentKey].states;
    const currentName = known[currentKey].name;
    const step = {
      index: stepIndex,
      dfaState: currentName,
      sourceNfaStates: currentStates,
      transitions: {},
    };
    stepIndex += 1;

    for (const symbol of alphabet) {
      let move = new Set();
      for (const state of currentStates) {
        move = setUnion(move, nfa.targets(state, symbol));
      }
      const targetClosure = move.size ? epsilonClosure(nfa, move) : new Set();

      if (!targetClosure.size) {
        step.transitions[symbol] = "∅";
        continue;
      }

      const targetKey = setKey(targetClosure);
      if (!(targetKey in known)) {
        const newName = subsetLabel(targetClosure);
        known[targetKey] = { states: targetClosure, name: newName };
        dfa.addState(newName);
        if (setIntersection(targetClosure, nfa.acceptStates).size) {
          dfa.acceptStates.add(newName);
        }
        queue.push(targetKey);
      }

      const targetName = known[targetKey].name;
      dfa.addTransition(currentName, symbol, targetName);
      step.transitions[symbol] = targetName;
    }

    steps.push(step);
  }

  const table = steps.map((s) => [s.dfaState, s.sourceNfaStates, s.transitions]);
  return { dfa: dfa, steps: steps, table: table };
}

/* ------------------------------------------------------------------ */
/* DFA minimization, partition refinement (algorithms/minimization.py)  */
/* ------------------------------------------------------------------ */

/**
 * Minimize a DFA with Moore partition refinement.
 * Returns { dfa, steps, removedUnreachable, groupOfState }, where steps
 * holds the partition after every refinement round.
 */
function minimizeDfa(dfa) {
  if (!dfa.isDeterministic()) {
    throw new Error("Only deterministic automata (DFA) can be minimized.");
  }
  if (dfa.startState === null) {
    throw new Error("The DFA has no start state defined.");
  }

  const reachable = dfa.getReachableStates();
  const unreachable = setDifference(new Set(dfa.states), reachable);
  const working = dfa.clone();
  for (const s of unreachable) working.removeState(s);

  const alphabet = working.alphabet.slice();
  const steps = [];

  const accepting = working.states.filter((s) => working.acceptStates.has(s));
  const nonAccepting = working.states.filter((s) => !working.acceptStates.has(s));
  let partition = [accepting, nonAccepting]
    .filter((g) => g.length)
    .map((g) => new Set(g));

  steps.push({
    index: 0,
    groups: partition.map((g) => new Set(g)),
    description: "Initial partition: accepting vs. non-accepting states.",
  });

  function groupIndex(state, part) {
    for (let i = 0; i < part.length; i++) {
      if (part[i].has(state)) return i;
    }
    return -1;
  }

  let changed = true;
  let iteration = 1;
  while (changed) {
    changed = false;
    const newPartition = [];
    for (const group of partition) {
      /** signature -> Set of states sharing it */
      const subgroups = new Map();
      for (const state of sortedArray(group)) {
        const signature = alphabet
          .map((sym) => {
            const targets = working.targets(state, sym);
            if (!targets.size) return -1;
            return groupIndex(Array.from(targets)[0], partition);
          })
          .join(",");
        if (!subgroups.has(signature)) subgroups.set(signature, new Set());
        subgroups.get(signature).add(state);
      }
      if (subgroups.size > 1) changed = true;
      for (const sub of subgroups.values()) newPartition.push(sub);
    }
    if (changed) {
      partition = newPartition;
      steps.push({
        index: iteration,
        groups: partition.map((g) => new Set(g)),
        description: "Refinement #" + iteration + ": " + partition.length + " groups distinguished.",
      });
      iteration += 1;
    }
  }

  const groupNames = partition.map((g) => "{" + sortedArray(g).join(",") + "}");

  const minDfa = new Automaton({ name: dfa.name + " (minimal)", alphabet: alphabet.slice() });
  for (const name of groupNames) minDfa.addState(name);

  for (let i = 0; i < partition.length; i++) {
    const group = partition[i];
    const representative = sortedArray(group)[0];
    const name = groupNames[i];
    if (working.acceptStates.has(representative)) minDfa.acceptStates.add(name);
    if (group.has(working.startState)) minDfa.startState = name;
    for (const sym of alphabet) {
      const targets = working.targets(representative, sym);
      if (targets.size) {
        const targetState = Array.from(targets)[0];
        const targetGroup = groupIndex(targetState, partition);
        minDfa.addTransition(name, sym, groupNames[targetGroup]);
      }
    }
  }

  const groupOfState = {};
  for (let i = 0; i < partition.length; i++) {
    for (const state of partition[i]) groupOfState[state] = i;
  }

  return {
    dfa: minDfa,
    steps: steps,
    removedUnreachable: unreachable,
    groupOfState: groupOfState,
  };
}

/* ------------------------------------------------------------------ */
/* Property analysis (algorithms/properties.py)                        */
/* ------------------------------------------------------------------ */

function analyzeProperties(automaton) {
  const unreachable = automaton.getUnreachableStates();
  const dead = automaton.getDeadStates();
  const missing = [];
  if (automaton.alphabet.length) {
    for (const state of automaton.states) {
      for (const symbol of automaton.alphabet) {
        if (!automaton.targets(state, symbol).size) {
          missing.push(state + " --" + symbol + "--> (undefined)");
        }
      }
    }
  }
  return {
    isDeterministic: automaton.isDeterministic(),
    isComplete: automaton.isComplete(),
    isConnected: unreachable.size === 0,
    hasEpsilonTransitions: automaton.hasEpsilonTransitions(),
    unreachableStates: unreachable,
    deadStates: dead,
    missingTransitions: missing,
    validationErrors: automaton.validate(),
  };
}

/* ------------------------------------------------------------------ */
/* Trivial conversions (algorithms/conversions.py)                     */
/* ------------------------------------------------------------------ */

/** Every DFA is already a valid NFA; return an equivalent copy. */
function dfaToNfa(dfa) {
  const nfa = dfa.clone();
  nfa.name = dfa.name + " (equivalent NFA)";
  return nfa;
}

function removeUnreachableStates(automaton) {
  const result = automaton.clone();
  for (const state of result.getUnreachableStates()) {
    result.removeState(state);
  }
  return result;
}

/* ------------------------------------------------------------------ */
/* Regex to NFA (Thompson's Construction)                             */
/* ------------------------------------------------------------------ */

class RegexParser {
  static expandShorthands(regex) {
    let s = String(regex || "").replace(/\\\./g, ".");
    s = s.replace(/\[([^\]]+)\]/g, (_, content) => {
      const chars = [];
      let i = 0;
      while (i < content.length) {
        if (i + 2 < content.length && content[i + 1] === "-") {
          const startCode = content.charCodeAt(i);
          const endCode = content.charCodeAt(i + 2);
          for (let code = startCode; code <= endCode; code++) {
            chars.push(String.fromCharCode(code));
          }
          i += 3;
        } else {
          chars.push(content[i]);
          i += 1;
        }
      }
      return chars.length ? "(" + chars.join("|") + ")" : "";
    });

    const expandRepeat = (expr) => {
      const m = expr.match(/\{(\d+)\}/);
      if (!m) return expr;
      const count = parseInt(m[1], 10);
      const startIdx = m.index;
      const endIdx = startIdx + m[0].length;
      if (startIdx === 0) return expr;
      if (expr[startIdx - 1] === ")") {
        let depth = 1;
        let p = startIdx - 2;
        while (p >= 0 && depth > 0) {
          if (expr[p] === ")") depth += 1;
          else if (expr[p] === "(") depth -= 1;
          p -= 1;
        }
        const token = expr.slice(p + 1, startIdx);
        let expanded = "";
        for (let k = 0; k < count; k++) expanded += token;
        return expandRepeat(expr.slice(0, p + 1) + expanded + expr.slice(endIdx));
      } else {
        const token = expr[startIdx - 1];
        let expanded = "";
        for (let k = 0; k < count; k++) expanded += token;
        return expandRepeat(expr.slice(0, startIdx - 1) + expanded + expr.slice(endIdx));
      }
    };

    return expandRepeat(s);
  }

  static insertConcat(regex) {
    const cleaned = [];
    for (const ch of regex) {
      if (!/\s/.test(ch)) cleaned.push(ch);
    }
    if (!cleaned.length) return "";

    const output = [];
    const postfixOps = new Set(["*", "+", "?"]);
    const ops = new Set(["|", "·", "*", "+", "?", "(", ")"]);

    for (let i = 0; i < cleaned.length; i++) {
      const c1 = cleaned[i];
      output.push(c1);

      if (i + 1 < cleaned.length) {
        const c2 = cleaned[i + 1];
        const isC1Source = (!ops.has(c1) && c1 !== "(" && c1 !== "|") || postfixOps.has(c1) || c1 === ")";
        const isC2Dest = (!ops.has(c2) && c2 !== ")" && !postfixOps.has(c2) && c2 !== "|") || c2 === "(";

        if (isC1Source && isC2Dest) {
          output.push("·");
        }
      }
    }
    return output.join("");
  }

  static toPostfix(regex) {
    const withConcat = this.insertConcat(this.expandShorthands(regex));
    const prec = { "|": 1, "·": 2, "*": 3, "+": 3, "?": 3 };
    const output = [];
    const stack = [];
    const postfixUnary = new Set(["*", "+", "?"]);

    for (let i = 0; i < withConcat.length; i++) {
      const c = withConcat[i];
      if (postfixUnary.has(c)) {
        output.push(c);
      } else if (c === "|") {
        while (stack.length && stack[stack.length - 1] !== "(" && (prec[stack[stack.length - 1]] || 0) >= prec["|"]) {
          output.push(stack.pop());
        }
        stack.push(c);
      } else if (c === "·") {
        while (stack.length && stack[stack.length - 1] !== "(" && (prec[stack[stack.length - 1]] || 0) >= prec["·"]) {
          output.push(stack.pop());
        }
        stack.push(c);
      } else if (c === "(") {
        stack.push(c);
      } else if (c === ")") {
        while (stack.length && stack[stack.length - 1] !== "(") {
          output.push(stack.pop());
        }
        if (stack.length && stack[stack.length - 1] === "(") {
          stack.pop();
        }
      } else {
        output.push(c);
      }
    }

    while (stack.length) {
      output.push(stack.pop());
    }
    return output.join("");
  }
}

function computeLayeredPositions(automaton) {
  if (!automaton.states.length || automaton.startState === null) return;

  const layers = {};
  const stateLayer = {};
  stateLayer[automaton.startState] = 0;
  const queue = [automaton.startState];

  while (queue.length) {
    const curr = queue.shift();
    const currLayer = stateLayer[curr];
    if (!layers[currLayer]) layers[currLayer] = [];
    layers[currLayer].push(curr);

    const trans = automaton.transitions[curr] || {};
    for (const sym of Object.keys(trans)) {
      for (const d of trans[sym]) {
        if (stateLayer[d] === undefined) {
          stateLayer[d] = currLayer + 1;
          queue.push(d);
        }
      }
    }
  }

  const existingLayers = Object.keys(layers).map(Number);
  let maxLayer = existingLayers.length ? Math.max.apply(null, existingLayers) : 0;
  for (const s of automaton.states) {
    if (stateLayer[s] === undefined) {
      maxLayer += 1;
      stateLayer[s] = maxLayer;
      if (!layers[maxLayer]) layers[maxLayer] = [];
      layers[maxLayer].push(s);
    }
  }

  const xStart = 80;
  const xGap = 130;
  const yCenter = 220;
  const yGap = 100;

  for (const layerStr of Object.keys(layers)) {
    const layerIdx = Number(layerStr);
    const stList = layers[layerIdx];
    const count = stList.length;
    const yOffset = yCenter - (count - 1) * (yGap / 2);
    for (let i = 0; i < stList.length; i++) {
      const st = stList[i];
      const x = xStart + layerIdx * xGap;
      const y = yOffset + i * yGap;
      automaton.positions[st] = [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
    }
  }
}

function regexToNfa(regexStr, automatonName) {
  const regexClean = String(regexStr || "").trim();
  if (!regexClean) {
    const nfa = new Automaton({ name: automatonName || "NFA from regex (empty)" });
    nfa.addState("q0", [150, 150]);
    nfa.setStartState("q0");
    nfa.acceptStates.add("q0");
    return nfa;
  }

  const postfix = RegexParser.toPostfix(regexClean);
  let stateCounter = 0;
  const newState = () => {
    const s = "q" + stateCounter;
    stateCounter += 1;
    return s;
  };

  const transitions = {};
  const states = [];
  const alphabetSet = new Set();

  const addSt = (st) => {
    if (states.indexOf(st) === -1) {
      states.push(st);
      transitions[st] = {};
    }
  };

  const addTr = (src, sym, dst) => {
    addSt(src);
    addSt(dst);
    if (!transitions[src][sym]) transitions[src][sym] = new Set();
    transitions[src][sym].add(dst);
    if (sym !== EPSILON) alphabetSet.add(sym);
  };

  const stack = [];

  for (let i = 0; i < postfix.length; i++) {
    const token = postfix[i];
    if (token === "*") {
      if (!stack.length) continue;
      const frag = stack.pop();
      const s = newState();
      const e = newState();
      addTr(s, EPSILON, frag.start);
      addTr(s, EPSILON, e);
      addTr(frag.accept, EPSILON, frag.start);
      addTr(frag.accept, EPSILON, e);
      stack.push({ start: s, accept: e });
    } else if (token === "+") {
      if (!stack.length) continue;
      const frag = stack.pop();
      const s = newState();
      const e = newState();
      addTr(s, EPSILON, frag.start);
      addTr(frag.accept, EPSILON, frag.start);
      addTr(frag.accept, EPSILON, e);
      stack.push({ start: s, accept: e });
    } else if (token === "?") {
      if (!stack.length) continue;
      const frag = stack.pop();
      const s = newState();
      const e = newState();
      addTr(s, EPSILON, frag.start);
      addTr(s, EPSILON, e);
      addTr(frag.accept, EPSILON, e);
      stack.push({ start: s, accept: e });
    } else if (token === "|") {
      if (stack.length < 2) continue;
      const f2 = stack.pop();
      const f1 = stack.pop();
      const s = newState();
      const e = newState();
      addTr(s, EPSILON, f1.start);
      addTr(s, EPSILON, f2.start);
      addTr(f1.accept, EPSILON, e);
      addTr(f2.accept, EPSILON, e);
      stack.push({ start: s, accept: e });
    } else if (token === "·") {
      if (stack.length < 2) continue;
      const f2 = stack.pop();
      const f1 = stack.pop();
      addTr(f1.accept, EPSILON, f2.start);
      stack.push({ start: f1.start, accept: f2.accept });
    } else {
      const sym = (token === "ε" || token === "e" || token === "E") ? EPSILON : token;
      const s = newState();
      const e = newState();
      addTr(s, sym, e);
      stack.push({ start: s, accept: e });
    }
  }

  if (!stack.length) {
    const nfa = new Automaton({ name: automatonName || "NFA: " + regexClean });
    nfa.addState("q0", [150, 150]);
    nfa.setStartState("q0");
    return nfa;
  }

  const finalFrag = stack[0];
  const alphabet = sortedArray(alphabetSet);
  const nfa = new Automaton({
    name: automatonName || "NFA: " + regexClean,
    alphabet: alphabet,
    states: states.slice(),
    startState: finalFrag.start,
    acceptStates: [finalFrag.accept],
    transitions: transitions,
  });

  computeLayeredPositions(nfa);
  return nfa;
}

function regexToCleanDfa(regexStr, automatonName) {
  const nfa = regexToNfa(regexStr, automatonName);
  const dfa = nfaToDfa(nfa).dfa;
  const minDfa = minimizeDfa(dfa).dfa;

  const layers = {};
  const stateLayer = {};
  if (minDfa.startState) {
    stateLayer[minDfa.startState] = 0;
    const queue = [minDfa.startState];
    while (queue.length) {
      const curr = queue.shift();
      const currL = stateLayer[curr];
      if (!layers[currL]) layers[currL] = [];
      layers[currL].push(curr);
      const trans = minDfa.transitions[curr] || {};
      for (const targets of Object.values(trans)) {
        for (const d of targets) {
          if (stateLayer[d] === undefined) {
            stateLayer[d] = currL + 1;
            queue.push(d);
          }
        }
      }
    }
  }

  const orderedStates = [];
  const layerKeys = Object.keys(layers).map(Number).sort((a, b) => a - b);
  for (const l of layerKeys) {
    for (const s of layers[l]) {
      if (orderedStates.indexOf(s) === -1) orderedStates.push(s);
    }
  }
  for (const s of minDfa.states) {
    if (orderedStates.indexOf(s) === -1) orderedStates.push(s);
  }

  const stateMap = {};
  for (let i = 0; i < orderedStates.length; i++) {
    stateMap[orderedStates[i]] = "q" + i;
  }

  const cleanDfa = new Automaton({
    name: automatonName || ("DFA: " + regexStr),
    alphabet: [...minDfa.alphabet],
  });

  for (const s of orderedStates) cleanDfa.addState(stateMap[s]);
  if (minDfa.startState) cleanDfa.setStartState(stateMap[minDfa.startState]);
  for (const s of minDfa.acceptStates) cleanDfa.acceptStates.add(stateMap[s]);

  for (const src of orderedStates) {
    const trans = minDfa.transitions[src] || {};
    for (const [sym, targets] of Object.entries(trans)) {
      for (const dst of targets) {
        cleanDfa.addTransition(stateMap[src], sym, stateMap[dst]);
      }
    }
  }

  computeLayeredPositions(cleanDfa);
  return cleanDfa;
}

/* ------------------------------------------------------------------ */
/* Automaton to Regular Expression (State Elimination GNFA)           */
/* ------------------------------------------------------------------ */

function unionRegex(r1, r2) {
  if (!r1) return r2;
  if (!r2) return r1;
  if (r1 === r2) return r1;
  const parts1 = (!r1.startsWith("(") || !r1.endsWith(")")) ? r1.split("|") : [r1];
  const parts2 = (!r2.startsWith("(") || !r2.endsWith(")")) ? r2.split("|") : [r2];
  const combined = sortedArray(new Set(parts1.concat(parts2)));
  return combined.length > 1 ? combined.join("|") : combined[0];
}

function concatRegex(r1, r2) {
  if (r1 === null || r2 === null) return null;
  if (r1 === EPSILON) return r2;
  if (r2 === EPSILON) return r1;

  const p1 = (r1.indexOf("|") !== -1 && !(r1.startsWith("(") && r1.endsWith(")"))) ? "(" + r1 + ")" : r1;
  const p2 = (r2.indexOf("|") !== -1 && !(r2.startsWith("(") && r2.endsWith(")"))) ? "(" + r2 + ")" : r2;
  return p1 + p2;
}

function starRegex(r) {
  if (!r || r === EPSILON) return EPSILON;
  if (r.endsWith("*")) return r;
  if (r.length === 1) return r + "*";
  if (r.startsWith("(") && r.endsWith(")") && (r.match(/\(/g) || []).length === 1) {
    return r + "*";
  }
  return "(" + r + ")*";
}

function automatonToRegex(automaton) {
  if (automaton.startState === null || !automaton.acceptStates.size) {
    return { regex: "∅", steps: [] };
  }

  const states = automaton.states.slice();
  let qInit = "__init__";
  let qFinal = "__final__";
  while (states.indexOf(qInit) !== -1) qInit = "_" + qInit;
  while (states.indexOf(qFinal) !== -1) qFinal = "_" + qFinal;

  const allGnfaStates = [qInit].concat(states).concat([qFinal]);
  const R = {};
  for (const u of allGnfaStates) {
    R[u] = {};
    for (const v of allGnfaStates) R[u][v] = null;
  }

  R[qInit][automaton.startState] = EPSILON;
  for (const acc of automaton.acceptStates) {
    if (states.indexOf(acc) !== -1) {
      R[acc][qFinal] = EPSILON;
    }
  }

  for (const src of states) {
    const row = automaton.transitions[src] || {};
    for (const sym of Object.keys(row)) {
      const symLabel = sym === EPSILON ? EPSILON : sym;
      for (const dst of row[sym]) {
        if (states.indexOf(dst) !== -1) {
          R[src][dst] = unionRegex(R[src][dst], symLabel);
        }
      }
    }
  }

  const steps = [];
  let remaining = states.slice();
  let stepIdx = 1;

  for (const qRip of states) {
    remaining = remaining.filter((s) => s !== qRip);
    const rLoop = R[qRip][qRip];
    const rLoopStar = starRegex(rLoop);

    const active = [qInit].concat(remaining).concat([qFinal]);

    for (const p of active) {
      if (p === qFinal) continue;
      const rPRip = R[p][qRip];
      if (rPRip === null) continue;

      for (const s of active) {
        if (s === qInit) continue;
        const rRipS = R[qRip][s];
        if (rRipS === null) continue;

        const bypass = concatRegex(concatRegex(rPRip, rLoopStar), rRipS);
        R[p][s] = unionRegex(R[p][s], bypass);
      }
    }

    steps.push({
      index: stepIdx,
      eliminatedState: qRip,
      remainingStates: remaining.slice(),
      description: "Eliminated state '" + qRip + "'. " + remaining.length + " intermediate states remaining.",
    });
    stepIdx += 1;
  }

  const finalRegex = R[qInit][qFinal] || "∅";
  return { regex: finalRegex, steps: steps };
}

/* ------------------------------------------------------------------ */
/* Operations: Complete, Complement, Intersection, Union, Equiv       */
/* ------------------------------------------------------------------ */

function completeDfa(automaton) {
  if (!automaton.isDeterministic()) {
    throw new Error("Only deterministic automata (DFA) can be completed.");
  }
  if (automaton.isComplete()) {
    return automaton.clone();
  }

  const comp = automaton.clone();
  comp.name = automaton.name + " (completed)";
  const alphabet = comp.alphabet.slice();

  let trapState = "trap";
  let counter = 1;
  while (comp.states.indexOf(trapState) !== -1) {
    trapState = "trap_" + counter;
    counter += 1;
  }

  let trapNeeded = false;
  for (const s of comp.states) {
    for (const sym of alphabet) {
      if (!comp.targets(s, sym).size) {
        trapNeeded = true;
        break;
      }
    }
    if (trapNeeded) break;
  }

  if (!trapNeeded) return comp;

  comp.addState(trapState, [300, 350]);
  for (const sym of alphabet) {
    comp.addTransition(trapState, sym, trapState);
  }

  for (const s of comp.states) {
    for (const sym of alphabet) {
      if (!comp.targets(s, sym).size) {
        comp.addTransition(s, sym, trapState);
      }
    }
  }

  return comp;
}

function complementDfa(automaton) {
  if (!automaton.isDeterministic()) {
    throw new Error("Only deterministic automata (DFA) can be complemented.");
  }
  if (automaton.startState === null) {
    throw new Error("The automaton has no start state.");
  }

  const comp = completeDfa(automaton);
  comp.name = automaton.name + " (complement)";
  const allStates = new Set(comp.states);
  const oldAccept = comp.acceptStates;
  comp.acceptStates = setDifference(allStates, oldAccept);
  return comp;
}

function productConstruction(dfa1, dfa2, mode) {
  if (!dfa1.isDeterministic() || !dfa2.isDeterministic()) {
    throw new Error("Both automata must be deterministic (DFA) for product construction.");
  }
  if (dfa1.startState === null || dfa2.startState === null) {
    throw new Error("Both automata must have a defined start state.");
  }

  const commonAlphabet = sortedArray(new Set(dfa1.alphabet.concat(dfa2.alphabet)));
  let c1 = completeDfa(dfa1);
  let c2 = completeDfa(dfa2);

  for (const sym of commonAlphabet) {
    if (c1.alphabet.indexOf(sym) === -1) {
      c1.addSymbol(sym);
      c1 = completeDfa(c1);
    }
    if (c2.alphabet.indexOf(sym) === -1) {
      c2.addSymbol(sym);
      c2 = completeDfa(c2);
    }
  }

  const startPair = c1.startState + KEY_SEP + c2.startState;
  const startName = "(" + c1.startState + "," + c2.startState + ")";

  const prodName = mode === "intersection"
    ? dfa1.name + " ∩ " + dfa2.name
    : dfa1.name + " ∪ " + dfa2.name;

  const product = new Automaton({ name: prodName, alphabet: commonAlphabet.slice() });
  product.addState(startName);
  product.setStartState(startName);

  const pairToName = {};
  pairToName[startPair] = startName;
  const queue = [[c1.startState, c2.startState]];
  const visited = new Set([startPair]);

  while (queue.length) {
    const pair = queue.shift();
    const p1 = pair[0];
    const p2 = pair[1];
    const currKey = p1 + KEY_SEP + p2;
    const currName = pairToName[currKey];

    const isAcc1 = c1.acceptStates.has(p1);
    const isAcc2 = c2.acceptStates.has(p2);
    if (mode === "intersection" && (isAcc1 && isAcc2)) {
      product.acceptStates.add(currName);
    } else if (mode === "union" && (isAcc1 || isAcc2)) {
      product.acceptStates.add(currName);
    } else if (mode === "diff1" && (isAcc1 && !isAcc2)) {
      product.acceptStates.add(currName);
    }

    for (const sym of commonAlphabet) {
      const t1Set = c1.targets(p1, sym);
      const t2Set = c2.targets(p2, sym);
      if (!t1Set.size || !t2Set.size) continue;
      const t1 = Array.from(t1Set)[0];
      const t2 = Array.from(t2Set)[0];
      const targetKey = t1 + KEY_SEP + t2;

      if (!pairToName[targetKey]) {
        const tName = "(" + t1 + "," + t2 + ")";
        pairToName[targetKey] = tName;
        product.addState(tName);
      }

      if (!visited.has(targetKey)) {
        visited.add(targetKey);
        queue.push([t1, t2]);
      }

      product.addTransition(currName, sym, pairToName[targetKey]);
    }
  }

  // Circular layout
  const n = product.states.length;
  const cx = 260;
  const cy = 220;
  const r = Math.max(120, n * 24);
  for (let i = 0; i < product.states.length; i++) {
    const s = product.states[i];
    const angle = (2 * Math.PI * i) / Math.max(1, n) - (Math.PI / 2);
    product.positions[s] = [
      Math.round((cx + r * Math.cos(angle)) * 10) / 10,
      Math.round((cy + r * Math.sin(angle)) * 10) / 10,
    ];
  }

  return product;
}

function intersectDfas(dfa1, dfa2) {
  return productConstruction(dfa1, dfa2, "intersection");
}

function unionDfas(dfa1, dfa2) {
  return productConstruction(dfa1, dfa2, "union");
}

function findShortestAcceptedString(automaton) {
  if (automaton.startState === null) return null;
  if (automaton.acceptStates.has(automaton.startState)) return "";

  const queue = [[automaton.startState, ""]];
  const visited = new Set([automaton.startState]);

  while (queue.length) {
    const item = queue.shift();
    const curr = item[0];
    const word = item[1];
    for (const sym of sortedArray(automaton.alphabet)) {
      for (const dest of automaton.targets(curr, sym)) {
        if (automaton.acceptStates.has(dest)) {
          return word + sym;
        }
        if (!visited.has(dest)) {
          visited.add(dest);
          queue.push([dest, word + sym]);
        }
      }
    }
  }

  return null;
}

function checkEquivalence(dfa1, dfa2) {
  if (!dfa1.isDeterministic() || !dfa2.isDeterministic()) {
    throw new Error("Both automata must be deterministic (DFA) to test equivalence.");
  }

  const diff1 = productConstruction(dfa1, dfa2, "diff1");
  const ce1Not2 = findShortestAcceptedString(diff1);

  const diff2 = productConstruction(dfa2, dfa1, "diff1");
  const ce2Not1 = findShortestAcceptedString(diff2);

  const subset1In2 = ce1Not2 === null;
  const subset2In1 = ce2Not1 === null;
  const equivalent = subset1In2 && subset2In1;

  let message = "";
  if (equivalent) {
    message = "The two automata are equivalent! They accept the exact same language.";
  } else if (subset1In2) {
    message = "L(M1) ⊂ L(M2). M2 accepts additional string '" + ce2Not1 + "'.";
  } else if (subset2In1) {
    message = "L(M2) ⊂ L(M1). M1 accepts additional string '" + ce1Not2 + "'.";
  } else {
    message = "The automata are not equivalent. E.g. '" + ce1Not2 + "' ∈ L1\\L2, '" + ce2Not1 + "' ∈ L2\\L1.";
  }

  return {
    equivalent: equivalent,
    subset1In2: subset1In2,
    subset2In1: subset2In1,
    counterexample1Not2: ce1Not2,
    counterexample2Not1: ce2Not1,
    message: message,
  };
}

/* ------------------------------------------------------------------ */
/* Batch Simulation & Accepted String Generator                       */
/* ------------------------------------------------------------------ */

function isLanguageEmpty(automaton) {
  if (automaton.startState === null) return true;
  const reachable = automaton.getReachableStates();
  return setIntersection(reachable, automaton.acceptStates).size === 0;
}

function isLanguageInfinite(automaton) {
  if (automaton.startState === null || isLanguageEmpty(automaton)) return false;

  const alive = setDifference(new Set(automaton.states), automaton.getDeadStates());
  const reachable = automaton.getReachableStates();
  const useful = setIntersection(reachable, alive);

  const visited = new Set();
  const recStack = new Set();

  function hasCycle(u) {
    visited.add(u);
    recStack.add(u);
    const trans = automaton.transitions[u] || {};
    for (const sym of Object.keys(trans)) {
      for (const v of trans[sym]) {
        if (useful.has(v)) {
          if (!visited.has(v)) {
            if (hasCycle(v)) return true;
          } else if (recStack.has(v)) {
            return true;
          }
        }
      }
    }
    recStack.delete(u);
    return false;
  }

  for (const st of useful) {
    if (!visited.has(st)) {
      if (hasCycle(st)) return true;
    }
  }
  return false;
}

function generateAcceptedStrings(automaton, limit, maxLength) {
  const lim = limit || 15;
  const maxLen = maxLength || 12;

  if (automaton.startState === null || isLanguageEmpty(automaton)) return [];

  const alphabet = sortedArray(automaton.alphabet.filter((s) => s !== EPSILON));
  if (!alphabet.length) {
    const startClosure = epsilonClosure(automaton, new Set([automaton.startState]));
    return setIntersection(startClosure, automaton.acceptStates).size ? [""] : [];
  }

  const results = [];
  const startSet = epsilonClosure(automaton, new Set([automaton.startState]));
  if (setIntersection(startSet, automaton.acceptStates).size) {
    results.push("");
    if (results.length >= lim) return results;
  }

  const queue = [[startSet, ""]];

  while (queue.length && results.length < lim) {
    const item = queue.shift();
    const currStates = item[0];
    const word = item[1];
    if (word.length >= maxLen) continue;

    for (const sym of alphabet) {
      let nextStates = new Set();
      for (const s of currStates) {
        nextStates = setUnion(nextStates, automaton.targets(s, sym));
      }
      nextStates = epsilonClosure(automaton, nextStates);
      if (!nextStates.size) continue;

      const newWord = word + sym;
      if (setIntersection(nextStates, automaton.acceptStates).size) {
        results.push(newWord);
        if (results.length >= lim) break;
      }

      queue.push([nextStates, newWord]);
    }
  }

  return results;
}

function batchSimulate(automaton, strings) {
  const results = [];
  for (const s of strings) {
    const res = simulate(automaton, s);
    results.push({
      string: s,
      accepted: res.accepted,
      stepsCount: res.steps.length,
      finalStates: sortedArray(res.finalStates),
      error: res.error,
    });
  }
  return results;
}

/* ------------------------------------------------------------------ */
/* Random automaton generator                                          */
/* ------------------------------------------------------------------ */

/**
 * mulberry32 — a tiny deterministic PRNG. Passing a seed reproduces the
 * exact same automaton, which is handy for classroom demos and tests.
 * Without a seed we fall back to Math.random for fresh results.
 */
function makeRandom(seed) {
  if (seed === null || seed === undefined) return Math.random;
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function randomCircularPositions(n) {
  const positions = {};
  const cx = 400;
  const cy = 250;
  const radius = 180;
  for (let i = 0; i < n; i++) {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    positions["q" + i] = [
      Math.round((cx + radius * Math.cos(angle)) * 10) / 10,
      Math.round((cy + radius * Math.sin(angle)) * 10) / 10,
    ];
  }
  return positions;
}

/** Pick k distinct items at random (order not guaranteed to be sorted). */
function randomPick(rng, items, k) {
  const pool = items.slice();
  const picked = [];
  const count = Math.min(k, pool.length);
  for (let i = 0; i < count; i++) {
    const idx = Math.floor(rng() * pool.length);
    picked.push(pool[idx]);
    pool.splice(idx, 1);
  }
  return picked;
}

function randomAlphabetItems(alphabet) {
  return alphabet && alphabet.length ? alphabet.slice() : ["a", "b"];
}

/**
 * Generate a random *complete* DFA.
 *
 * density in (0, 1]: probability that a (state, symbol) transition points
 * to a *different* state than the current one. density=1 randomises every
 * transition; a lower density biases toward self-loops (sparser automaton).
 */
function generateRandomDfa(opts) {
  const o = opts || {};
  const numStates = o.numStates === undefined ? 5 : o.numStates;
  const alphabet = randomAlphabetItems(o.alphabet);
  const density = o.density === undefined ? 1.0 : o.density;
  const acceptRatio = o.acceptRatio === undefined ? 0.4 : o.acceptRatio;
  const rng = makeRandom(o.seed);

  if (numStates < 1) throw new Error("Number of states must be >= 1.");
  if (!(density > 0 && density <= 1)) throw new Error("Density must be in (0, 1].");
  if (!(acceptRatio >= 0 && acceptRatio <= 1)) throw new Error("Accept ratio must be in [0, 1].");

  const states = [];
  for (let i = 0; i < numStates; i++) states.push("q" + i);

  const transitions = {};
  for (const src of states) {
    transitions[src] = {};
    for (const sym of alphabet) {
      let target = src;
      if (numStates > 1 && rng() < density) {
        const others = states.filter((s) => s !== src);
        target = others[Math.floor(rng() * others.length)];
      }
      transitions[src][sym] = new Set([target]);
    }
  }

  const numAccept = Math.max(1, Math.round(numStates * acceptRatio));
  return new Automaton({
    name: "Random DFA (" + numStates + " states)",
    states: states,
    alphabet: alphabet.slice(),
    startState: states[0],
    acceptStates: randomPick(rng, states, numAccept),
    transitions: transitions,
    positions: randomCircularPositions(numStates),
  });
}

/**
 * Generate a random NFA, optionally with epsilon transitions.
 *
 * density:        probability a (state, symbol) pair has any transition.
 * nondeterminism: probability a transition fans out to a further target.
 * epsilonProb:    probability per state of having an epsilon transition.
 */
function generateRandomNfa(opts) {
  const o = opts || {};
  const numStates = o.numStates === undefined ? 5 : o.numStates;
  const alphabet = randomAlphabetItems(o.alphabet);
  const density = o.density === undefined ? 0.6 : o.density;
  const epsilonProb = o.epsilonProb === undefined ? 0.15 : o.epsilonProb;
  const acceptRatio = o.acceptRatio === undefined ? 0.4 : o.acceptRatio;
  const nondeterminism = o.nondeterminism === undefined ? 0.3 : o.nondeterminism;
  const rng = makeRandom(o.seed);

  if (numStates < 1) throw new Error("Number of states must be >= 1.");
  if (!(density > 0 && density <= 1)) throw new Error("Density must be in (0, 1].");
  if (!(epsilonProb >= 0 && epsilonProb <= 1)) throw new Error("Epsilon probability must be in [0, 1].");
  if (!(nondeterminism >= 0 && nondeterminism <= 1)) throw new Error("Non-determinism must be in [0, 1].");

  const states = [];
  for (let i = 0; i < numStates; i++) states.push("q" + i);

  const pickState = () => states[Math.floor(rng() * states.length)];
  const transitions = {};
  for (const src of states) transitions[src] = {};

  let usesEpsilon = false;
  for (const src of states) {
    for (const sym of alphabet) {
      if (rng() < density) {
        const targets = new Set([pickState()]);
        while (rng() < nondeterminism && targets.size < numStates) targets.add(pickState());
        transitions[src][sym] = targets;
      }
    }
    if (rng() < epsilonProb) {
      const targets = new Set([pickState()]);
      while (rng() < nondeterminism / 2 && targets.size < numStates) targets.add(pickState());
      transitions[src][EPSILON] = targets;
      usesEpsilon = true;
    }
  }

  const fullAlphabet = alphabet.slice();
  if (usesEpsilon) fullAlphabet.push(EPSILON);

  const numAccept = Math.max(1, Math.round(numStates * acceptRatio));
  return new Automaton({
    name: "Random NFA (" + numStates + " states)",
    states: states,
    alphabet: fullAlphabet,
    startState: states[0],
    acceptStates: randomPick(rng, states, numAccept),
    transitions: transitions,
    positions: randomCircularPositions(numStates),
  });
}

/* ------------------------------------------------------------------ */
/* Word-length distribution                                            */
/* ------------------------------------------------------------------ */

/**
 * For each length 0..maxLength report whether the language contains at
 * least one string of that length (1) or not (0). Uses dynamic programming
 * over the set of active states, so it works for DFAs and NFAs alike
 * (including epsilon transitions) and never enumerates the strings.
 */
function wordLengthDistribution(automaton, maxLength) {
  const maxLen = maxLength === undefined ? 10 : maxLength;
  const result = {};

  if (automaton.startState === null) {
    for (let n = 0; n <= maxLen; n++) result[n] = 0;
    return result;
  }

  const alphabet = automaton.alphabet.filter((s) => s !== EPSILON);
  if (!alphabet.length) {
    const closure = epsilonClosure(automaton, new Set([automaton.startState]));
    result[0] = setIntersection(closure, automaton.acceptStates).size ? 1 : 0;
    for (let n = 1; n <= maxLen; n++) result[n] = 0;
    return result;
  }

  let active = epsilonClosure(automaton, new Set([automaton.startState]));
  result[0] = setIntersection(active, automaton.acceptStates).size ? 1 : 0;

  for (let len = 1; len <= maxLen; len++) {
    const next = new Set();
    for (const state of active) {
      for (const sym of alphabet) {
        for (const dest of automaton.targets(state, sym)) next.add(dest);
      }
    }
    active = epsilonClosure(automaton, next);
    result[len] = setIntersection(active, automaton.acceptStates).size ? 1 : 0;
  }

  return result;
}

/* ------------------------------------------------------------------ */
/* Exporters: Graphviz DOT, LaTeX TikZ, JFLAP XML                     */
/* ------------------------------------------------------------------ */

function toDot(automaton) {
  const lines = [
    "digraph finite_state_machine {",
    '  rankdir=LR;',
    '  size="8,5";',
    '  node [fontname="Helvetica,Arial,sans-serif"];',
    '  edge [fontname="Helvetica,Arial,sans-serif"];',
  ];

  const accepting = sortedArray(automaton.acceptStates);
  if (accepting.length) {
    const names = accepting.map((s) => '"' + s + '"').join(" ");
    lines.push("  node [shape = doublecircle]; " + names + ";");
  }

  lines.push("  node [shape = circle];");

  if (automaton.startState !== null) {
    lines.push('  __start [shape = none, label = "", width = 0, height = 0];');
    lines.push('  __start -> "' + automaton.startState + '";');
  }

  const edges = {};
  for (const src of automaton.states) {
    const row = automaton.transitions[src] || {};
    for (const sym of Object.keys(row)) {
      const symLabel = sym === EPSILON ? "ε" : sym;
      for (const dst of row[sym]) {
        const key = src + KEY_SEP + dst;
        if (!edges[key]) edges[key] = [];
        edges[key].push(symLabel);
      }
    }
  }

  for (const key of Object.keys(edges).sort()) {
    const parts = key.split(KEY_SEP);
    const src = parts[0];
    const dst = parts[1];
    const label = sortedArray(edges[key]).join(", ");
    lines.push('  "' + src + '" -> "' + dst + '" [label = "' + label + '"];');
  }

  lines.push("}");
  return lines.join("\n");
}

function toMermaid(automaton) {
  const lines = ["stateDiagram-v2"];
  if (automaton.startState !== null) {
    lines.push("    [*] --> " + automaton.startState);
  }
  const edges = {};
  for (const src of automaton.states) {
    const row = automaton.transitions[src] || {};
    for (const sym of Object.keys(row)) {
      const symLabel = sym === EPSILON ? "ε" : sym;
      for (const dst of row[sym]) {
        const key = src + KEY_SEP + dst;
        if (!edges[key]) edges[key] = [];
        edges[key].push(symLabel);
      }
    }
  }
  for (const key of Object.keys(edges).sort()) {
    const parts = key.split(KEY_SEP);
    const src = parts[0];
    const dst = parts[1];
    const label = sortedArray(edges[key]).join(", ");
    lines.push("    " + src + " --> " + dst + " : " + label);
  }
  for (const st of sortedArray(automaton.acceptStates)) {
    lines.push("    " + st + " --> [*]");
  }
  return lines.join("\n");
}

function toTikz(automaton) {
  const lines = [
    "% Requires: \\usepackage{tikz}",
    "% \\usetikzlibrary{automata, positioning, arrows}",
    "\\begin{tikzpicture}[shorten >=1pt, node distance=2.8cm, on grid, auto, >=stealth]",
  ];

  const scale = 0.025;
  for (const s of automaton.states) {
    const options = ["state"];
    if (s === automaton.startState) options.push("initial");
    if (automaton.acceptStates.has(s)) options.push("accepting");

    const optStr = options.join(", ");
    if (automaton.positions[s]) {
      const pos = automaton.positions[s];
      const x = Math.round(pos[0] * scale * 100) / 100;
      const y = Math.round(-pos[1] * scale * 100) / 100;
      lines.push("  \\node[" + optStr + "] (" + s + ") at (" + x + "," + y + ") {" + s + "};");
    } else {
      lines.push("  \\node[" + optStr + "] (" + s + ") {" + s + "};");
    }
  }

  lines.push("  \\path[->]");
  for (const src of automaton.states) {
    const row = automaton.transitions[src] || {};
    for (const sym of Object.keys(row)) {
      const symTex = sym === EPSILON ? "$\\varepsilon$" : sym;
      for (const dst of row[sym]) {
        if (src === dst) {
          lines.push("    (" + src + ") edge [loop above] node {" + symTex + "} (" + dst + ")");
        } else {
          lines.push("    (" + src + ") edge node {" + symTex + "} (" + dst + ")");
        }
      }
    }
  }

  lines.push("  ;");
  lines.push("\\end{tikzpicture}");
  return lines.join("\n");
}

function toJflapXml(automaton) {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<structure>\n  <type>fa</type>\n  <automaton>\n';
  const stateToId = {};
  for (let i = 0; i < automaton.states.length; i++) {
    const s = automaton.states[i];
    stateToId[s] = i;
    const pos = automaton.positions[s] || [100 + i * 80, 150];
    xml += '    <state id="' + i + '" name="' + s + '">\n';
    xml += '      <x>' + Math.round(pos[0]) + '</x>\n';
    xml += '      <y>' + Math.round(pos[1]) + '</y>\n';
    if (s === automaton.startState) xml += "      <initial/>\n";
    if (automaton.acceptStates.has(s)) xml += "      <final/>\n";
    xml += "    </state>\n";
  }

  for (const src of automaton.states) {
    const srcId = stateToId[src];
    const row = automaton.transitions[src] || {};
    for (const sym of Object.keys(row)) {
      const symRead = sym === EPSILON ? "" : sym;
      for (const dst of row[sym]) {
        const dstId = stateToId[dst];
        xml += "    <transition>\n";
        xml += "      <from>" + srcId + "</from>\n";
        xml += "      <to>" + dstId + "</to>\n";
        xml += "      <read>" + symRead + "</read>\n";
        xml += "    </transition>\n";
      }
    }
  }

  xml += "  </automaton>\n</structure>";
  return xml;
}

function fromJflapXml(xmlContent) {
  const stateRegex = /<state\s+id="([^"]+)"\s+name="([^"]+)"[\s\S]*?<\/state>/g;
  const transRegex = /<transition>[\s\S]*?<from>([^<]+)<\/from>[\s\S]*?<to>([^<]+)<\/to>(?:[\s\S]*?<read>([^<]*)<\/read>)?[\s\S]*?<\/transition>/g;

  const idToName = {};
  const states = [];
  const positions = {};
  const acceptStates = [];
  let startState = null;

  let match;
  while ((match = stateRegex.exec(xmlContent)) !== null) {
    const sId = match[1];
    const sName = match[2];
    idToName[sId] = sName;
    states.push(sName);

    const fullTag = match[0];
    const xMatch = /<x>([^<]+)<\/x>/.exec(fullTag);
    const yMatch = /<y>([^<]+)<\/y>/.exec(fullTag);
    if (xMatch && yMatch) {
      positions[sName] = [parseFloat(xMatch[1]), parseFloat(yMatch[1])];
    }
    if (/<initial\s*\/?>/.test(fullTag)) startState = sName;
    if (/<final\s*\/?>/.test(fullTag)) acceptStates.push(sName);
  }

  const transitions = {};
  for (const s of states) transitions[s] = {};
  const alphabetSet = new Set();

  while ((match = transRegex.exec(xmlContent)) !== null) {
    const fromId = match[1].trim();
    const toId = match[2].trim();
    const readSym = match[3] ? match[3].trim() : "";

    const src = idToName[fromId];
    const dst = idToName[toId];
    if (!src || !dst) continue;

    const sym = (!readSym || readSym === "ε" || readSym === "\\e") ? EPSILON : readSym;
    if (!transitions[src][sym]) transitions[src][sym] = new Set();
    transitions[src][sym].add(dst);
    if (sym !== EPSILON) alphabetSet.add(sym);
  }

  return new Automaton({
    name: "Imported JFLAP Automaton",
    states: states,
    alphabet: sortedArray(alphabetSet),
    startState: startState || (states.length ? states[0] : null),
    acceptStates: acceptStates,
    transitions: transitions,
    positions: positions,
  });
}
