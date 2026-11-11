/* No CDN, framework, telemetry or API calls. Generated data also works over file://. */
"use strict";
(() => {
  const data = window.RESEARCH_GRAPH;
  const $ = id => document.getElementById(id);
  if (!data || data.schemaVersion !== 2) {
    $("empty").hidden = false;
    $("empty").textContent = "图谱数据尚未生成，请先运行 scripts/research_graph.py。";
    return;
  }
  const canvas = $("graph"), ctx = canvas.getContext("2d"), container = $("map");
  const byId = new Map(data.nodes.map(n => [n.id, n]));
  const kindNames = {theme: "主题", object: "调研工作"};
  const reportLabels = {reported: "已有报告", planned: "仅有计划"};
  const reportState = n => n.kind === "object" ? (n.reportIds?.length ? "reported" : "planned") : null;
  const filters = [$("theme-filter"), $("type-filter")];
  const reportButtons = [...document.querySelectorAll(".report-filters button")];
  const reportAccent = getComputedStyle(canvas).getPropertyValue("--report-accent").trim();
  let reportFilter = "all";
  const displayLabel = node => node.displayLabel || node.taskId || node.label;
  const relationNames = {includes: "关联", depends: "依赖"};
  const reportById = new Map(data.reports.map(r => [r.id, r]));
  const neighbors = new Map(data.nodes.map(n => [n.id, new Set()]));
  for (const e of data.edges) {
    if (neighbors.has(e.source) && neighbors.has(e.target)) {
      neighbors.get(e.source).add(e.target);
      neighbors.get(e.target).add(e.source);
    }
  }
  let width = 0, height = 0, dpr = 1, visible = [], visibleEdges = [], selected = null, hovered = null;
  let camera = {x: 0, y: 0, zoom: 1}, drag = null, activePointer = null, frame = null;
  let inViewport = true, lastTime = 0;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let paused = reducedMotion.matches;
  let phase = 0;
  const offsets = new Map();
  const phases = new Map(data.nodes.map(n => [n.id, hash(n.id) * Math.PI * 2]));
  const themeOrder = new Map(data.themeOverview.map((entry, index) => [entry.theme, index]));
  const themeRank = n => themeOrder.get(n.theme) ?? Number.MAX_SAFE_INTEGER;
  const themes = data.nodes.filter(n => n.kind === "theme").sort((a, b) => themeRank(a) - themeRank(b));
  const revisionTime = n => Math.max(Date.parse(n.updatedAt) || 0,
    ...(n.reportIds || []).map(id => Date.parse(reportById.get(id)?.updatedAt) || 0));

  function hash(value) {
    let h = 2166136261;
    for (let i = 0; i < value.length; i++) h = Math.imul(h ^ value.charCodeAt(i), 16777619);
    return (h >>> 0) / 4294967295;
  }
  function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function option(select, value, text) {
    const el = element("option", "", text);
    el.value = value;
    select.append(el);
  }
  function link(text, url, className) {
    const el = element("a", className, text);
    // The builder creates GitHub URLs, but data stays untrusted at the DOM boundary.
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "https:" || parsed.hostname !== "github.com") return element("span", className, text);
      el.href = parsed.href;
    } catch { return element("span", className, text); }
    el.target = "_blank";
    el.rel = "noopener noreferrer";
    return el;
  }
  $("branch").textContent = data.branch;
  $("repository-link").href = `https://github.com/${data.repository}/tree/${encodeURIComponent(data.branch)}`;
  $("guide-link").href = `https://github.com/${data.repository}/blob/${encodeURIComponent(data.branch)}/docs/research-graph-guide.md`;
  for (const [key, label] of [["themes", "调研主题"], ["types", "调研类型"], ["objects", "具体调研工作"]]) {
    const stat = element("div", "stat");
    stat.append(element("strong", "", String(data.stats[key])), element("span", "", label));
    $("stats").append(stat);
  }
  $("provenance").textContent = `最近记录日期 ${data.updatedAt || "未标注"} · 数据 ${data.fingerprint.slice(0, 8)}`;
  for (const n of themes) option($("theme-filter"), n.theme, n.label);
  for (const [type, label] of Object.entries(data.types)) {
    option($("type-filter"), type, label);
    const item = element("span", "", label), dot = element("i");
    dot.style.backgroundColor = data.colors[type];
    item.prepend(dot); $("type-legend").append(item);
  }

  function applyFilters() {
    const query = $("search").value.trim().toLocaleLowerCase();
    const [theme, type] = filters.map(filter => filter.value);
    const candidates = data.nodes.filter(n => {
      if (theme !== "all" && !(n.themes || [n.theme]).includes(theme)) return false;
      if (type !== "all" && n.type !== type) return false;
      return !query || `${displayLabel(n)} ${n.label} ${n.target || ""} ${n.path} ${n.taskId || ""}`.toLocaleLowerCase().includes(query);
    });
    const counts = {all: 0, reported: 0, planned: 0};
    for (const n of candidates) {
      const state = reportState(n);
      if (state) {
        counts[state]++;
        counts.all++;
      }
    }
    for (const button of reportButtons) {
      button.setAttribute("aria-pressed", String(button.value === reportFilter));
      button.querySelector(".report-count").textContent = String(counts[button.value]);
    }
    const matched = reportFilter === "all" ? candidates : candidates.filter(n => reportState(n) === reportFilter);
    const ids = new Set(matched.map(n => n.id));
    // Keep theme centers as context, but do not let contextual nodes mask zero results.
    for (const n of matched) for (const t of n.themes || [n.theme]) if (byId.has("theme:" + t)) ids.add("theme:" + t);
    visible = data.nodes.filter(n => ids.has(n.id));
    visibleEdges = data.edges.filter(e => ids.has(e.source) && ids.has(e.target));
    if (selected && !ids.has(selected)) { selected = null; showDetail(null); }
    if (hovered && !ids.has(hovered)) hovered = null;
    $("tooltip").hidden = true;
    $("empty").hidden = matched.length !== 0;
    $("empty").textContent = data.nodes.length ? "没有匹配的调研工作。试试调整筛选条件。" : "暂无调研工作。新增主题计划或报告并纳入 Git 后，这里会自动更新。";
    $("visible-count").textContent = `${matched.length} 个匹配节点 · ${visibleEdges.length} 条关系`;
    $("result-count").textContent = String(matched.length);
    $("results").replaceChildren();
    if (!matched.length) $("results").append(element("p", "results-empty", "暂无匹配结果"));
    const order = {theme: 0, object: 1};
    for (const n of [...matched].sort((a, b) => themeRank(a) - themeRank(b) || order[a.kind] - order[b.kind] ||
      revisionTime(b) - revisionTime(a) || a.label.localeCompare(b.label, "zh-CN"))) {
      const button = element("button", "result");
      button.dataset.nodeId = n.id;
      button.setAttribute("aria-pressed", String(n.id === selected));
      const state = reportState(n);
      if (state) button.dataset.reportState = state;
      const swatch = element("span", state ? `swatch ${state}-symbol` : "swatch");
      swatch.style.color = n.color;
      button.append(swatch, element("span", "result-label", displayLabel(n)),
        element("span", "result-kind", reportLabels[state] || kindNames[n.kind]));
      button.title = displayLabel(n);
      button.addEventListener("click", () => select(n.id));
      $("results").append(button);
    }
    requestDraw();
  }
  function clearFilters() {
    $("search").value = "";
    for (const filter of filters) filter.value = "all";
    reportFilter = "all";
    applyFilters();
  }
  function select(id) {
    if (id && !visible.some(n => n.id === id)) clearFilters();
    selected = id;
    showDetail(id ? byId.get(id) : null);
    for (const button of $("results").children) if (button.tagName === "BUTTON") button.setAttribute("aria-pressed", String(button.dataset.nodeId === id));
    requestDraw();
  }
  function showDetail(n) {
    const detail = $("detail");
    detail.replaceChildren();
    $("detail-eyebrow").textContent = n ? kindNames[n.kind] + " / DETAIL" : "探索入口";
    if (!n) {
      detail.append(element("h2", "", data.nodes.length ? "探索调研工作" : "暂无调研工作"), element("p", "", data.nodes.length ? "点击节点查看具体调研工作及其主题、类型。也可以从下方列表选择。" : "当前没有纳入总览的调研内容。后续新增正式调研时，这里会自动更新。"));
      const badges = element("div", "detail-badges");
      for (const [key, name] of Object.entries(data.types)) {
        const badge = element("span", "badge", name);
        badge.style.color = data.colors[key];
        badges.append(badge);
      }
      detail.append(badges);
      if (data.warnings.length) detail.append(element("p", "edge-note", `数据提示：${data.warnings.join("；")}`));
      return;
    }
    detail.append(element("h2", "", n.label));
    const badges = element("div", "detail-badges");
    for (const label of [data.types[n.type] || kindNames[n.kind]].filter(Boolean)) badges.append(element("span", "badge", label));
    const state = reportState(n);
    if (state) badges.append(element("span", `badge report-state ${state}`, reportLabels[state]));
    if (n.target) detail.append(element("p", "", n.target));
    const openLabel = n.inferredFromDirectory ? "打开相关资料 ↗" : n.kind === "theme" || n.sourceKind === "plan" ? "打开主题计划 ↗" : "打开调研报告 ↗";
    detail.append(badges, element("div", "path", n.path), link(openLabel, n.url, "open-link"));
    if (n.inferredFromDirectory) detail.append(element("p", "edge-note", "由报告目录归类；尚未发现主题计划。"));
    const connections = data.edges.filter(e => e.source === n.id || e.target === n.id);
    const list = element("ul", "detail-links");
    // Merge parallel theme/report grouping and explicit result links for readability.
    const seen = new Set();
    for (const edge of connections) {
      const target = byId.get(edge.source === n.id ? edge.target : edge.source);
      if (!target || seen.has(target.id)) continue;
      seen.add(target.id);
      const row = element("li");
      let relation = relationNames[edge.relation];
      if (edge.relation === "depends") relation = edge.target === n.id ? "前置调研工作" : "后续调研工作";
      const action = element("button", "text-button", displayLabel(target));
      action.style.marginLeft = "0";
      action.title = edge.evidence;
      action.addEventListener("click", () => select(target.id));
      row.append(element("span", "relation", relation), action);
      list.append(row);
    }
    detail.append(list);
    if (n.kind === "object") for (const id of n.reportIds) {
      const report = reportById.get(id);
      if (report) detail.append(link(reportLinkLabel(report), report.url, "detail-links"));
    }
    if (n.kind === "object" && (n.pendingReportIds || []).length) {
      detail.append(element("p", "edge-note", "同目录补充报告待关联，尚未作为本项工作的交付成果："));
      for (const id of n.pendingReportIds) {
        const report = reportById.get(id);
        if (report) detail.append(link("待关联：" + reportLinkLabel(report), report.url, "detail-links"));
      }
    }
  }

  function reportLinkLabel(report) {
    const status = report.statusLabel ? `（${report.statusLabel}）` : "";
    return `${report.label}${status} ↗`;
  }

  function point(n) {
    const offset = offsets.get(n.id) || {x: 0, y: 0};
    const p = phases.get(n.id);
    const float = n.kind === "theme" || (drag && drag.id === n.id) ? 0 : 2;
    return {x: width / 2 + camera.x + ((n.x - 0.5) * width * .98 + offset.x + Math.cos(phase + p) * float) * camera.zoom,
      y: height / 2 + camera.y + ((n.y - 0.5) * height * .92 + offset.y + Math.sin(phase + p) * float) * camera.zoom};
  }
  function radius(n) {
    const size = n.kind === "theme" ? 11 : reportState(n) === "reported" ? 10 : 5;
    return size * Math.sqrt(camera.zoom);
  }
  function nodeAt(x, y) {
    return [...visible].reverse().find(n => { const p = point(n); return Math.hypot(p.x - x, p.y - y) < Math.max(10, radius(n) + 5); });
  }
  function requestDraw() {
    if (!frame) frame = requestAnimationFrame(draw);
  }
  function draw(time) {
    frame = null;
    if (!paused && !document.hidden && inViewport && lastTime) phase += Math.min(time - lastTime, 60) / 2200;
    lastTime = time;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    // Background specks are decorative, fixed, and are not graph nodes.
    ctx.fillStyle = "#30425c";
    ctx.globalAlpha = .45;
    for (let i = 0; i < (data.nodes.length ? 115 : 0); i++) {
      ctx.beginPath(); ctx.arc(hash("x" + i) * width, hash("y" + i) * height, .65, 0, Math.PI * 2); ctx.fill();
    }
    const focus = hovered || selected;
    const adjacent = focus ? neighbors.get(focus) : null;
    const points = new Map(visible.map(n => [n.id, point(n)]));
    for (const e of visibleEdges) {
      const a = points.get(e.source), b = points.get(e.target);
      const active = focus && (e.source === focus || e.target === focus);
      ctx.globalAlpha = focus ? active ? .8 : .08 : .26;
      ctx.strokeStyle = active ? "#b6d9eb" : byId.get(e.target).color;
      ctx.lineWidth = active ? 1.3 : .8;
      ctx.setLineDash(e.relation === "depends" ? [4, 5] : []);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      ctx.setLineDash([]);
      if (e.relation === "depends" || e.relation === "cites") {
        const angle = Math.atan2(b.y - a.y, b.x - a.x), r = radius(byId.get(e.target)) + 5;
        const x = b.x - Math.cos(angle) * r, y = b.y - Math.sin(angle) * r;
        ctx.beginPath(); ctx.moveTo(x - Math.cos(angle - .55) * 6, y - Math.sin(angle - .55) * 6); ctx.lineTo(x, y); ctx.lineTo(x - Math.cos(angle + .55) * 6, y - Math.sin(angle + .55) * 6); ctx.stroke();
      }
    }
    const labelBoxes = [];
    const labelRank = n => n.kind === "theme" ? 0 : reportState(n) === "reported" ? 1 : 2;
    const sorted = [...visible].sort((a, b) => Number(b.id === focus) - Number(a.id === focus) || labelRank(a) - labelRank(b));
    for (const n of [...sorted].reverse()) {
      const p = points.get(n.id), r = radius(n), active = !focus || n.id === focus || adjacent.has(n.id);
      const state = reportState(n);
      const accent = state === "reported" ? reportAccent : n.color;
      ctx.globalAlpha = active ? 1 : .22;
      if (n.kind === "theme" || n.id === focus || state === "reported") {
        const halo = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r + 22);
        halo.addColorStop(0, accent + "2b"); halo.addColorStop(1, accent + "00");
        ctx.fillStyle = halo;
        ctx.beginPath(); ctx.arc(p.x, p.y, r + 22, 0, Math.PI * 2); ctx.fill();
      }
      if (n.id === focus) {
        ctx.strokeStyle = accent; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(p.x, p.y, r + 7, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.fillStyle = state === "planned" ? "#0d1728" : n.color;
      ctx.beginPath();
      if (state === "reported") {
        ctx.moveTo(p.x, p.y - r);
        ctx.lineTo(p.x + r, p.y);
        ctx.lineTo(p.x, p.y + r);
        ctx.lineTo(p.x - r, p.y);
        ctx.closePath();
      } else {
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      }
      ctx.fill();
      if (state) {
        ctx.strokeStyle = accent;
        ctx.lineWidth = state === "reported" ? 2 : 1.4;
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
    for (const n of sorted) {
      const active = !focus || n.id === focus || adjacent.has(n.id);
      const state = reportState(n);
      if (!active || (visible.length > 35 && state === "planned" && n.id !== focus && camera.zoom < 1.7)) continue;
      const p = points.get(n.id), r = radius(n);
      let label = displayLabel(n);
      if (label.length > 26 && n.id !== focus) label = label.slice(0, 25) + "…";
      const font = n.kind === "theme" ? "12px" : state === "reported" ? "600 12px" : "10px";
      ctx.font = `${font} "Segoe UI","Microsoft YaHei","Noto Sans CJK SC",sans-serif`;
      const textWidth = ctx.measureText(label).width;
      let tx = p.x - textWidth / 2, ty = p.y + r + 19;
      tx = Math.max(8, Math.min(width - textWidth - 8, tx));
      const box = {x: tx - 3, y: ty - 12, w: textWidth + 6, h: 17};
      if (n.id !== focus && labelBoxes.some(b => box.x < b.x + b.w && box.x + box.w > b.x && box.y < b.y + b.h && box.y + box.h > b.y)) continue;
      labelBoxes.push(box);
      ctx.lineWidth = 4; ctx.strokeStyle = "#0c1626"; ctx.lineJoin = "round"; ctx.strokeText(label, tx, ty);
      ctx.fillStyle = state === "reported" ? reportAccent : n.kind === "theme" || n.id === focus ? "#e4edf8" : "#a1b3cc";
      ctx.fillText(label, tx, ty);
    }
    if (data.nodes.length && !paused && !document.hidden && inViewport) requestDraw();
  }
  function resize() {
    width = container.clientWidth; height = container.clientHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    requestDraw();
  }
  function location(event) {
    const rect = canvas.getBoundingClientRect();
    return {x: event.clientX - rect.left, y: event.clientY - rect.top};
  }
  canvas.addEventListener("pointerdown", event => {
    if (event.button !== 0 || activePointer !== null) return;
    activePointer = event.pointerId;
    const p = location(event), n = nodeAt(p.x, p.y);
    drag = {id: n ? n.id : null, start: p, previous: p, moved: false};
    canvas.setPointerCapture(event.pointerId);
    $("tooltip").hidden = true;
  });
  canvas.addEventListener("pointermove", event => {
    if (activePointer !== null && event.pointerId !== activePointer) return;
    const p = location(event);
    if (drag) {
      if (Math.hypot(p.x - drag.start.x, p.y - drag.start.y) > 4) drag.moved = true;
      const dx = p.x - drag.previous.x, dy = p.y - drag.previous.y;
      if (drag.id) {
        const offset = offsets.get(drag.id) || {x: 0, y: 0};
        offsets.set(drag.id, {x: offset.x + dx / camera.zoom, y: offset.y + dy / camera.zoom});
      } else { camera.x += dx; camera.y += dy; }
      drag.previous = p;
      requestDraw();
      return;
    }
    const n = nodeAt(p.x, p.y);
    hovered = n ? n.id : null;
    canvas.style.cursor = n ? "pointer" : "grab";
    $("tooltip").hidden = !n;
    if (n) {
      const state = reportState(n);
      $("tooltip").textContent = state ? `${displayLabel(n)}\n${reportLabels[state]}` : displayLabel(n);
      $("tooltip").style.left = `${Math.max(8, Math.min(width - 265, p.x + 14))}px`;
      $("tooltip").style.top = `${Math.max(8, Math.min(height - 85, p.y + 14))}px`;
    }
    requestDraw();
  });
  function endDrag(event) {
    if (!drag || event.pointerId !== activePointer) return;
    if (!drag.moved && event.type === "pointerup") select(drag.id);
    drag = null; activePointer = null;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    requestDraw();
  }
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("pointerleave", () => { hovered = null; $("tooltip").hidden = true; requestDraw(); });
  function zoom(factor, x = width / 2, y = height / 2) {
    const next = Math.min(4, Math.max(.35, camera.zoom * factor)), ratio = next / camera.zoom;
    camera.x = x - width / 2 - (x - width / 2 - camera.x) * ratio;
    camera.y = y - height / 2 - (y - height / 2 - camera.y) * ratio;
    camera.zoom = next; requestDraw();
  }
  canvas.addEventListener("wheel", event => { event.preventDefault(); const p = location(event); zoom(Math.exp(-event.deltaY * .001), p.x, p.y); }, {passive: false});
  $("zoom-in").addEventListener("click", () => zoom(1.25));
  $("zoom-out").addEventListener("click", () => zoom(.8));
  $("reset").addEventListener("click", () => { camera = {x: 0, y: 0, zoom: 1}; offsets.clear(); select(null); });
  function syncMotion() {
    $("motion").setAttribute("aria-pressed", String(paused));
    $("motion").setAttribute("aria-label", paused ? "播放动画" : "暂停动画");
    $("motion").title = paused ? "播放动画" : "暂停动画";
    $("motion").textContent = paused ? "▷" : "Ⅱ";
    lastTime = 0; requestDraw();
  }
  $("motion").addEventListener("click", () => { paused = !paused; syncMotion(); });
  reducedMotion.addEventListener("change", event => { paused = event.matches; syncMotion(); });
  document.addEventListener("visibilitychange", () => { lastTime = 0; requestDraw(); });
  document.addEventListener("keydown", event => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
    if (event.key === "/") { event.preventDefault(); $("search").focus(); }
    if (event.key === "Escape") select(null);
    if (document.activeElement === canvas) {
      if (["+", "="].includes(event.key)) zoom(1.25);
      if (event.key === "-") zoom(.8);
      const pan = {ArrowLeft: [30, 0], ArrowRight: [-30, 0], ArrowUp: [0, 30], ArrowDown: [0, -30]}[event.key];
      if (pan) { event.preventDefault(); camera.x += pan[0]; camera.y += pan[1]; requestDraw(); }
    }
  });
  $("search").addEventListener("input", applyFilters);
  for (const filter of filters) filter.addEventListener("change", applyFilters);
  for (const button of reportButtons) button.addEventListener("click", () => {
    reportFilter = button.value;
    applyFilters();
  });
  $("clear-filters").addEventListener("click", clearFilters);
  new ResizeObserver(resize).observe(container);
  new IntersectionObserver(entries => { inViewport = entries[0].isIntersecting; lastTime = 0; if (inViewport) requestDraw(); }).observe(container);
  showDetail(null); applyFilters(); resize(); syncMotion();
})();
