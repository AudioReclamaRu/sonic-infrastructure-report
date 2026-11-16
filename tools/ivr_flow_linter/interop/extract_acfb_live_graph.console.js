/*
 * Read-only browser-console helper for the upstream Asterisk Call Flow Builder.
 *
 * Run only on the locally self-hosted upstream app in its own browser tab.
 * It reads the App component's React state and reproduces normalizeGraph().
 * It does not mutate React state, the canvas, local storage, or repository files.
 */
(() => {
  const fail = (message) => {
    throw new Error("[ACFB graph capture] " + message);
  };

  const seed = document.querySelector("h1") || document.querySelector(".react-flow");
  if (!seed) fail("App root not found. Confirm the Asterisk Call Flow Builder page is loaded.");

  const fiberKey = Object.keys(seed).find((key) => key.startsWith("__reactFiber$"));
  if (!fiberKey) {
    fail("React Fiber marker not found on the page. Use the dev build and inspect the rendered app.");
  }

  let fiber = seed[fiberKey];
  let appFiber = null;

  while (fiber) {
    const component = fiber.elementType || fiber.type;
    const name = component && (component.displayName || component.name);
    if (name === "App") {
      appFiber = fiber;
      break;
    }
    fiber = fiber.return;
  }

  if (!appFiber) fail("Could not locate the App function component in the React Fiber ancestry.");

  const isNodeArray = (value) =>
    Array.isArray(value) &&
    value.length > 0 &&
    value.every((item) =>
      item &&
      typeof item.id === "string" &&
      item.data &&
      typeof item.data.kind === "string" &&
      item.position &&
      typeof item.position.x === "number" &&
      typeof item.position.y === "number"
    );

  const isEdgeArray = (value) =>
    Array.isArray(value) &&
    value.length > 0 &&
    value.every((item) =>
      item &&
      typeof item.id === "string" &&
      typeof item.source === "string" &&
      typeof item.target === "string"
    );

  let hook = appFiber.memoizedState;
  let nodes = null;
  let edges = null;
  let hookIndex = 0;
  const matches = [];

  while (hook) {
    const value = hook.memoizedState;
    if (isNodeArray(value)) {
      nodes = value;
      matches.push({ hookIndex, state: "nodes", count: value.length });
    } else if (isEdgeArray(value)) {
      edges = value;
      matches.push({ hookIndex, state: "edges", count: value.length });
    }
    hook = hook.next;
    hookIndex += 1;
  }

  if (!nodes) fail("No React state array matching ACFB nodes (id/data.kind/position) was found.");
  if (!edges) fail("No React state array matching ACFB edges (id/source/target) was found.");

  const normalized = {
    version: 1,
    asterisk: {
      context: "from-internal",
      trunk: "main",
    },
    nodes,
    edges: edges.map(({ id, source, sourceHandle, target }) => ({
      id,
      source,
      sourceHandle: sourceHandle || null,
      target,
    })),
  };

  const json = JSON.stringify(normalized, null, 2);
  const copied = typeof copy === "function";

  console.info("[ACFB graph capture] Captured the live App state.", {
    appTitle: document.title,
    nodes: nodes.length,
    edges: edges.length,
    hookMatches: matches,
    copiedToClipboard: copied,
  });

  if (copied) {
    copy(json);
    console.info("[ACFB graph capture] Normalized JSON copied to clipboard.");
  } else {
    console.info("[ACFB graph capture] Clipboard helper unavailable; copy the JSON returned below.");
  }

  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    hookMatches: matches,
    normalizedGraph: json,
  };
})();
