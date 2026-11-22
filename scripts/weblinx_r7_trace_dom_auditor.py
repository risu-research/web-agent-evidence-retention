"""R7 blind TRACE-ONLY DOM snapshot reader.

Receives only a real Playwright Trace ZIP, synthetic public record identity
map A/B, and no independent WSGI, SQLite, or injected event log.

Reconstructs the compact DOM NodeSnapshot encoding from real frame-snapshot
events, INCLUDING Playwright subtree references [[back, postorder_index]].
Audits a strict first-click action and the before/final Django Admin table.
Never exports source HTML or selector values.
"""
from __future__ import annotations
import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Node:
    name: str
    attrs: dict
    children: tuple


def walk(node):
    if isinstance(node,Node):
        yield node
        for child in node.children:
            yield from walk(child)


def text_value(node):
    if isinstance(node,str):return node
    return "".join(text_value(c) for c in node.children)


def descendants(node, tag=None, class_name=None):
    for n in walk(node):
        if tag and n.name.upper()!=tag.upper():continue
        if class_name:
            classes=str(n.attrs.get("class","")).split()
            if class_name not in classes:continue
        yield n


def has_target(node):
    return isinstance(node,Node) and "__playwright_target__" in node.attrs


class SnapshotDecoder:
    """Per-frame snapshot history. Playwright indexes new nodes POSTORDER.

    A node with payload [[distance, node_index]] directly reuses a node
    created in a *previous* capture from the same frame. The node is not
    newly allocated in the current capture, matching source snapshotter.
    """
    def __init__(self):
        self.histories={}
        self.ref_count=0
        self.ref_failures=0
        self.decoded=0

    def decode(self, snapshot):
        frame=snapshot.get("frameId")
        if not frame:raise ValueError("Snapshot missing frameId")
        history=self.histories.setdefault(frame,[])
        index={}
        cursor=[0]

        def build(raw):
            if isinstance(raw,str):
                item=raw
            elif (isinstance(raw,list) and len(raw)==1 and
                  isinstance(raw[0],list) and len(raw[0])==2 and
                  all(type(i) is int for i in raw[0])):
                back,n=raw[0]
                if back<1 or back>len(history):
                    raise ValueError(f"Unresolved DOM history distance {back}")
                prior=history[-back]
                if n not in prior:raise ValueError("Unresolved DOM reference index")
                self.ref_count+=1
                return prior[n]
            elif isinstance(raw,list) and raw and isinstance(raw[0],str):
                tag=raw[0]
                attrs=raw[1] if len(raw)>1 and isinstance(raw[1],dict) else {}
                childraw=raw[2:] if len(raw)>1 and isinstance(raw[1],dict) else raw[1:]
                children=tuple(build(x) for x in childraw)
                item=Node(tag,dict(attrs),children)
            else:raise ValueError("Unexpected DOM node shape")
            index[cursor[0]]=item
            cursor[0]+=1
            return item
        try:
            root=build(snapshot["html"])
        except (KeyError,ValueError):
            self.ref_failures+=1
            history.append({})
            return None
        history.append(index)
        self.decoded+=1
        return root


def read_raw(p):
    # A source Trace archive, never a precomputed casebook.
    with zipfile.ZipFile(p) as archive:
        if archive.testzip() is not None:raise ValueError("Corrupt source Trace")
        trace=[]
        network=[]
        for file in archive.namelist():
            if file.endswith(".trace"):
                trace.extend(json.loads(x) for x in archive.read(file).splitlines())
            if file.endswith(".network"):
                network.extend(json.loads(x) for x in archive.read(file).splitlines())
    if not trace:raise ValueError("No original action stream")
    return trace,network


def rows_from_admin_snapshot(root):
    """Read original Django admin DOM row and first_name table cells.

    Returns None if this was not a complete original admin changelist.
    No external SQL and no injected event source is available.
    """
    if root is None:return None
    table=next((n for n in descendants(root,tag="TABLE")
                if n.attrs.get("id")=="result_list"),None)
    if table is None:return None
    result={}
    for tr in descendants(table,tag="TR"):
        user_cell=next(iter(descendants(tr,class_name="field-username")),None)
        if user_cell is None:continue
        username=text_value(user_cell).strip()
        if username not in ("r6_a","r6_b"):continue
        first=next(iter(descendants(tr,class_name="field-first_name")),None)
        name=text_value(first).strip() if first else None
        result["A" if username=="r6_a" else "B"]=name
    return result


def target_row_from_snapshot(root):
    if root is None:return "abstain",False,False
    target=[n for n in walk(root) if has_target(n)]
    if not target:return "abstain",False,False
    # A Playwright action highlight represents a locator target. A future
    # application event receiver can differ (overlay, child propagation).
    highlighted=target[0]
    for tr in descendants(root,tag="TR"):
        if any(n is highlighted for n in walk(tr)):
            cell=next(iter(descendants(tr,class_name="field-username")),None)
            val=text_value(cell).strip() if cell else ""
            return ("A" if val=="r6_a" else "B" if val=="r6_b"
                    else "abstain"),True,False
    return "abstain",True,False


def trace_auditor(trace_path,identity_map):
    """The sole accessible arguments to this decision engine."""
    trace,network=read_raw(trace_path)
    actions=[e for e in trace if e.get("type")=="before" and
             e.get("method")=="click"]
    if not actions:raise ValueError("No first native browser click in Trace")
    first=actions[0]
    callid=first.get("callId")
    if not callid:raise ValueError("First trace click missing callId")
    # Action status is reconstructed directly from before/after frames.
    after={e.get("callId"):e for e in trace if e.get("type")=="after"}
    end=after.get(callid)
    click_status=(
        "abstain" if end is None else
        "error" if end.get("error") else "returned"
    )
    selector=first.get("params",{}).get("selector","")
    selector_present=bool(isinstance(selector,str) and selector)
    force=bool(first.get("params",{}).get("force",False))

    server_posts=[]
    for rec in network:
        snapshot=rec.get("snapshot",{})
        req=snapshot.get("request",{}) if isinstance(snapshot,dict) else {}
        if not isinstance(req,dict) or req.get("method")!="POST":continue
        path=urlparse(req.get("url","")).path
        match=re.fullmatch(r"/admin/auth/user/(\d+)/(change|delete)/",path)
        if not match:continue
        key=int(match.group(1))
        server_posts.append(
            "A" if key==identity_map["A"] else
            "B" if key==identity_map["B"] else "other")
    server_answer=(
        server_posts[0] if len(server_posts)==1
        else "none" if len(server_posts)==0
        else "abstain")

    decoder=SnapshotDecoder()
    snapshots=[]
    for entry in trace:
        if entry.get("type")!="frame-snapshot":continue
        info=entry.get("snapshot",{})
        if not info.get("isMainFrame"):continue
        root=decoder.decode(info)
        snapshots.append({
            "callId":info.get("callId"),
            "phase":info.get("phase"),
            "page":urlparse(info.get("frameUrl","")).path,
            "url":info.get("frameUrl",""),
            "root":root
        })

    target_shots=[x for x in snapshots
                  if x["callId"]==callid and x["phase"]=="action"]
    row_guess="abstain"
    target_found=False
    if target_shots:
        row_guess,target_found,_=target_row_from_snapshot(target_shots[-1]["root"])

    # The after DOM is authoritative for a *screen state*, not a SQL commit.
    # Read both initial and final native admin result_list trees in the trace.
    table_snapshots=[]
    for n,s in enumerate(snapshots):
        if s["page"]=="/admin/auth/user/":
            rows=rows_from_admin_snapshot(s["root"])
            if rows is not None:
                table_snapshots.append({
                    "index":n,"rows":rows,"callId":s["callId"],
                    "phase":s["phase"]})
    before_item=next((s for s in table_snapshots
                      if set(s["rows"])=={"A","B"}),None)
    after_item=table_snapshots[-1] if table_snapshots else None
    # A single snapshot must NEVER be read as proof of zero state change.
    # Require a distinct, later captured native Django user-list state.
    effect_guess="abstain"
    if (before_item is not None and after_item is not None and
            after_item["index"]>before_item["index"] and
            after_item["callId"]!=before_item["callId"]):
        before_rows=before_item["rows"]
        after_rows=after_item["rows"]
        changed=[k for k in ("A","B")
                 if after_rows.get(k)!=before_rows.get(k)]
        if len(changed)<=1:
            effect_guess=changed[0] if changed else "none"

    shield_present=any(
        any(n.attrs.get("id")=="r6-cover"
            for n in walk(s["root"])) for s in target_shots
        if s["root"] is not None)
    if click_status=="error":
        # A failed first action has no delivered trusted click under the
        # standard Playwright action flow for this fixture.
        row_guess="none"
    elif force and shield_present:
        # Explicit full viewport pointer shield intercepts force clicks.
        # This is an inference from the DOM and action flags.
        row_guess="none"

    return {
        "q1_selector_present":int(selector_present),
        "q2_visible_receiver_inferred":row_guess,
        "q3_actual_POST_route":server_answer,
        "q4_UI_effect_inferred":effect_guess,
        "q5_first_click_status":click_status,
        "snapshots_seen":len(snapshots),
        "snapshots_decoded":decoder.decoded,
        "subtree_references_resolved":decoder.ref_count,
        "unresolved_snapshot_references":decoder.ref_failures,
        "source_table_snapshots":len(table_snapshots),
        "action_snapshot_present":int(bool(target_shots)),
        "action_target_marker_found":int(target_found),
        "overlay_present_at_action":int(shield_present),
        "trace_zip_bytes":Path(trace_path).stat().st_size,
        "raw_trace_retained":False,
        "recipient_evidence_kind":"inferred_DOM_action",
        "effect_evidence_kind":"inferred_DOM_display_only"
    }
