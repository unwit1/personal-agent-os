import ast, json, os, re, sys, pathlib, subprocess
root = pathlib.Path("src/agent_os/orchestrator")
mods = sorted(p for p in root.rglob("*.py"))
name = lambda p: ".".join(p.relative_to("src").with_suffix("").parts).replace(".__init__","")
names = {name(p): p for p in mods}
def resolve(cur, node):
    if isinstance(node, ast.ImportFrom):
        if node.level:
            base = cur.split(".")
            # for packages (__init__), level 1 = itself
            pk = base[:-1] if not str(names.get(cur,'')).endswith("__init__.py") else base
            pk = pk[:len(pk)-(node.level-1)] if node.level>1 else pk
            mod = ".".join(pk + ([node.module] if node.module else []))
        else: mod = node.module or ""
        out = [mod] + [mod + "." + a.name for a in node.names]
        return out
    return [a.name for a in node.names]
imports = {}
for n, p in names.items():
    t = ast.parse(p.read_text())
    deps = set()
    for node in ast.walk(t):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for m in resolve(n, node):
                if m in names: deps.add(m)
                elif m.startswith("agent_os.") and not m.startswith("agent_os.orchestrator"): deps.add(m.split(".")[0]+"."+m.split(".")[1])
    imports[n] = sorted(deps - {n})
dependents = {n: [] for n in names}
for n, ds in imports.items():
    for d in ds:
        if d in dependents: dependents[d].append(n)
# tests referencing
tests = {}
for tp in pathlib.Path("tests").glob("test_*.py"):
    txt = tp.read_text(errors="ignore")
    for n in names:
        short = n.split(".")[-1]
        if re.search(rf"orchestrator(\.|\s+import\s+.*\b){re.escape(short)}\b|orchestrator\.{re.escape(short)}\b|from agent_os\.orchestrator import [^\n]*\b{re.escape(short)}\b", txt):
            tests.setdefault(n, []).append(tp.name)
# reachability from production entrypoints (cli.py, service.py, server.py) + external importers
entry = ["agent_os.orchestrator.cli","agent_os.orchestrator.service","agent_os.orchestrator.server","agent_os.orchestrator.simple","agent_os.orchestrator.evidence"]
seen=set(); stack=list(entry)
while stack:
    m=stack.pop()
    if m in seen or m not in names: continue
    seen.add(m); stack += imports.get(m,[])
inv=[]
for n,p in names.items():
    src=p.read_text()
    inv.append(dict(module=n, path=str(p), lines=src.count("\n"), imports_internal=[d for d in imports[n] if d in names], imports_agent_os=[d for d in imports[n] if d not in names], dependents=sorted(dependents[n]), tests=sorted(tests.get(n,[])), reachable_from_entrypoints=n in seen,
      writes_files=bool(re.search(r"write_text|write_json|open\([^)]*['\"][wa]", src)), subprocess=("subprocess" in src), network=bool(re.search(r"urllib|http\.client|requests|socket", src))))
json.dump(inv, open(sys.argv[1],"w"), indent=1)
print(len(inv), "modules;", sum(i["lines"] for i in inv), "lines;", sum(not i["reachable_from_entrypoints"] for i in inv), "unreachable")
for i in sorted(inv, key=lambda i:-i["lines"]):
    print(f'{i["lines"]:5} {i["module"].replace("agent_os.orchestrator.",""):26} deps_in={len(i["dependents"]):2} tests={len(i["tests"]):2} reach={int(i["reachable_from_entrypoints"])}')
