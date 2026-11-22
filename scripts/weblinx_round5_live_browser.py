"""R5A: instrumented real Chromium clicks, separately observing intention,
trusted browser event, application handler and application state effect.

Two synthetic first-party fixtures; not an external WebLINX replay. The
source and fixed 72-case matrix were frozen before running the experiment.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import sys
import zlib
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError

OUT=Path("out_round5a")
APPS=("list","table")
SCENARIOS=(
    "baseline","nested_icon","reorder","reuse_id","rerender_same_id",
    "overlay_standard","overlay_force","disabled","handler_no_effect",
    "stop_bubble","target_removed","duplicate_accessible_name",
)
LOCATORS=("positional","native_id","accessible_role")
INTENDED="A"
TIMEOUT_MS=650

OBSERVE_SCRIPT=r"""(() => {
  window.__independentObserver={events:[]};
  document.addEventListener("click", e => {
    if (!e.isTrusted) return;
    const path=e.composedPath();
    let pathItem=null;
    for(const item of path) {
      if(item && typeof item.getAttribute==="function") {
        const value=item.getAttribute("data-entity");
        if(value !== null) {pathItem=value;break;}
      }
    }
    window.__independentObserver.events.push({
      rawTargetTag:String(e.target.tagName||""),
      pathItem:pathItem,
      pathHasButton:path.some(x=>x && x.tagName==="BUTTON"),
      isTrusted:e.isTrusted
    });
  },true);
})();"""


def episodes():
    return [(app,scenario,locator)
            for app in APPS
            for scenario in SCENARIOS
            for locator in LOCATORS]


def source_html(app,scenario):
    if app not in APPS or scenario not in SCENARIOS:
        raise AssertionError("Unexpected frozen fixture")
    def button(key):
        aria='aria-label="Apply A"' if scenario=="duplicate_accessible_name" else ""
        inner=(
          '<span class="inside" data-child="1">Apply '+key+'</span>'
          if scenario in ("nested_icon","stop_bubble") and key=="A"
          else "Apply "+key
        )
        return (f'<button type="button" id="target-{key}" '
                f'data-action="apply" data-entity="{key}" {aria}>'
                f'{inner}</button>')
    if app=="list":
        rows="".join(
            f'<div class="item" id="row-{k}" data-entity="{k}">'
            f'<span class="name">Record {k}</span>{button(k)}</div>'
            for k in ("A","B")
        )
        root=f'<section id="records">{rows}</section>'
    else:
        rows="".join(
            f'<tr id="row-{k}" data-entity="{k}">'
            f'<td>Permission {k}</td><td>{button(k)}</td></tr>'
            for k in ("A","B")
        )
        root=f'<table><tbody id="records">{rows}</tbody></table>'

    app_js=r"""
      window.__applicationState={A:0,B:0};
      window.__applicationHandlers=[];
      document.addEventListener("click",e=>{
        const button=e.target && e.target.closest && e.target.closest('button[data-action="apply"]');
        if(!button) return;
        const item=button.getAttribute("data-entity");
        if(item!=="A" && item!=="B") throw Error("Fixture state key");
        window.__applicationHandlers.push({item});
        if(window.__frozenScenario==="handler_no_effect") return;
        window.__applicationState[item]+=1;
        document.getElementById("count-"+item).textContent=String(
          window.__applicationState[item]);
      },false);
    """
    css="""
      body {font:16px system-ui,sans-serif;margin:30px;}
      #records {max-width:720px;}
      .item, td {padding:12px;min-height:70px;}
      button[data-action] {position:relative;display:inline-block;
        width:180px;height:52px;cursor:pointer;}
      .inside {position:absolute;inset:0;display:flex;align-items:center;
        justify-content:center;background:#eee;}
      .item button {margin-left:25px;}
      table,td {border:1px solid #999;border-collapse:collapse;}
    """
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<style>{css}</style></head><body><h1>{app} fixture</h1>'
            f'<aside>Changed A <output id="count-A">0</output>. '
            f'Changed B <output id="count-B">0</output>.</aside>'
            f'{root}<script>window.__frozenScenario={json.dumps(scenario)};'
            f'{app_js}</script></body></html>')


def mutate(page,scenario):
    script=r"""name => {
      const target=document.querySelector('button[data-entity="A"]');
      const distractor=document.querySelector('button[data-entity="B"]');
      if(name==="reorder") {
        const container=document.querySelector("#records");
        container.insertBefore(document.querySelector("#row-B"),document.querySelector("#row-A"));
      }
      if(name==="reuse_id") {
        target.id="target-A-old";
        distractor.id="target-A";
      }
      if(name==="rerender_same_id") {
        const replacement=target.cloneNode(true);
        target.replaceWith(replacement);
      }
      if(name==="overlay_standard" || name==="overlay_force") {
        const box=target.getBoundingClientRect();
        const overlay=document.createElement("div");
        overlay.setAttribute("data-entity","OVERLAY");
        overlay.id="overlaid";
        Object.assign(overlay.style,{
          position:"fixed",left:box.left+"px",top:box.top+"px",
          width:box.width+"px",height:box.height+"px",
          zIndex:"999999",pointerEvents:"auto",background:"rgba(0,0,0,0.14)"
        });
        document.body.appendChild(overlay);
      }
      if(name==="disabled") target.disabled=true;
      if(name==="stop_bubble") {
        const child=target.querySelector(".inside");
        if(!child)throw Error("No nested target for stop_bubble");
        child.addEventListener("click",e=>e.stopPropagation(),false);
      }
      if(name==="target_removed")document.getElementById("row-A").remove();
    }"""
    page.evaluate(script,scenario)


def locator_for(page,kind):
    if kind=="positional":
        return page.locator('xpath=(//button[@data-action="apply"])[1]')
    if kind=="native_id":
        return page.locator('xpath=id("target-A")')
    if kind=="accessible_role":
        return page.get_by_role("button",name="Apply A",exact=True)
    raise AssertionError("Unknown locator")


def readback(page):
    return page.evaluate("""() => ({
      state:{A:window.__applicationState.A,B:window.__applicationState.B},
      rendered:{
        A:Number(document.getElementById("count-A").textContent),
        B:Number(document.getElementById("count-B").textContent)
      },
      handlerEvents:window.__applicationHandlers.map(v=>v.item),
      captureExists:!!window.__independentObserver,
      trustedEvents:(window.__independentObserver?.events||[]).map(e=>({...e}))
    })""")


def encoded_bytes(obj):
    raw=json.dumps(obj,ensure_ascii=False,sort_keys=True,
                   separators=(",",":")).encode("utf-8")
    return len(raw),len(zlib.compress(raw,9))


def one_episode(browser,app,scenario,method):
    context=browser.new_context(viewport={"width":1280,"height":800})
    context.add_init_script(script=OBSERVE_SCRIPT)
    page=context.new_page()
    try:
        content=source_html(app,scenario)
        import base64
        uri="data:text/html;base64,"+base64.b64encode(content.encode("utf-8")).decode("ascii")
        page.goto(uri,wait_until="load")
        if not page.evaluate("!!window.__independentObserver"):
            raise AssertionError("Independent capture listener unavailable")
        chosen=locator_for(page,method)
        pre=readback(page)
        assert pre["state"]==pre["rendered"]=={"A":0,"B":0}
        assert not pre["trustedEvents"] and not pre["handlerEvents"]
        mutate(page,scenario)
        after_mutation=readback(page)
        assert after_mutation["state"]==after_mutation["rendered"]=={"A":0,"B":0}
        assert not after_mutation["trustedEvents"] and not after_mutation["handlerEvents"]
        force=scenario=="overlay_force"
        status="returned"
        try:
            chosen.click(force=force,timeout=TIMEOUT_MS)
        except PlaywrightTimeoutError:
            status="timeout"
        except Exception as exc:
            # The raw error can contain selectors and browser internals.
            status="playwright_error_"+type(exc).__name__
        after=readback(page)
        if not after["captureExists"]:
            raise AssertionError("Observer vanished from live page")
        if after["state"]!=after["rendered"]:
            raise AssertionError("Independent UI render and app state diverged")
        events=after["trustedEvents"]
        if any(not e["isTrusted"] for e in events):
            raise AssertionError("Browser event was not trusted")
        handler=after["handlerEvents"]
        delta={k:after["state"][k]-pre["state"][k] for k in ("A","B")}
        if any(v not in (0,1) for v in delta.values()):
            raise AssertionError("Unexpected number of state effects")
        if sum(delta.values())>1:
            raise AssertionError("Fixture performed multiple effects")
        effect_item=next((k for k,v in delta.items() if v==1),"none")
        event_item=events[0]["pathItem"] if events else "none"
        event_target=events[0]["rawTargetTag"] if events else "none"
        event_has_button=int(bool(events and events[0]["pathHasButton"]))
        handler_item=handler[0] if handler else "none"
        record={
          "app":app,"condition":scenario,"locator":method,
          "intended_item":INTENDED,
          "click_status":status,
          "trusted_event_count":len(events),
          "event_path_item":event_item,
          "event_raw_target_tag":event_target,
          "event_path_contains_button":event_has_button,
          "handler_invocation_count":len(handler),
          "handler_item":handler_item,
          "effect_item":effect_item,
          "state_delta_A":delta["A"],"state_delta_B":delta["B"],
          "state_render_verified":1,
          "event_matches_intent":int(event_item=="A"),
          "handler_matches_intent":int(handler_item=="A"),
          "effect_matches_intent":int(effect_item=="A"),
          "wrong_item_effect":int(effect_item=="B"),
          "handler_without_effect":int(bool(handler) and effect_item=="none"),
          "event_without_handler":int(bool(events) and not handler),
          "successful_tool_call_without_effect":int(status=="returned" and effect_item=="none"),
          "force_used":int(force)
        }
        # Real bytes of independently reconstructable log packets.
        req={"app":app,"condition":scenario,"locator":method,"intended":"A"}
        event_packet={**req,"click_status":status,"trusted_events":events}
        handler_packet={**event_packet,"handler_items":handler}
        effect_packet={**handler_packet,"initial_state":pre["state"],
                       "final_state":after["state"],
                       "final_rendered":after["rendered"]}
        for prefix,packet in [
            ("request",req),("event",event_packet),
            ("handler",handler_packet),("effect",effect_packet)
        ]:
            n,c=encoded_bytes(packet)
            record[f"{prefix}_bytes"]=n
            record[f"{prefix}_zlib_bytes"]=c
        return record
    finally:
        context.close()


def aggregate(rows,version):
    assert len(rows)==72 and len({(r["app"],r["condition"],r["locator"])
                                  for r in rows})==72
    def groups(rows,field):
        return dict(sorted(Counter(r[field] for r in rows).items()))
    def describe(arr):
        return {
            "episodes":len(arr),
            "status_counts":groups(arr,"click_status"),
            "event_path_counts":groups(arr,"event_path_item"),
            "handler_item_counts":groups(arr,"handler_item"),
            "effect_counts":groups(arr,"effect_item"),
            "correct_effects":sum(r["effect_matches_intent"] for r in arr),
            "wrong_effects":sum(r["wrong_item_effect"] for r in arr),
            "no_effects":sum(r["effect_item"]=="none" for r in arr),
            "trusted_events_observed":sum(r["trusted_event_count"]>0 for r in arr),
            "event_without_handler":sum(r["event_without_handler"] for r in arr),
            "handler_without_effect":sum(r["handler_without_effect"] for r in arr),
            "tool_returned_but_no_effect":sum(
                r["successful_tool_call_without_effect"] for r in arr)
        }
    comparisons={}
    for app in APPS:
        comparisons[app]=describe([r for r in rows if r["app"]==app])
    by_scenario={s:describe([r for r in rows if r["condition"]==s])
                 for s in SCENARIOS}
    by_locator={l:describe([r for r in rows if r["locator"]==l])
                for l in LOCATORS}
    total=describe(rows)
    total["bytes_by_retention_tier"]={
        tier:{
            "sum_utf8":sum(r[f"{tier}_bytes"] for r in rows),
            "sum_zlib_per_episode":sum(r[f"{tier}_zlib_bytes"] for r in rows)
        }
        for tier in ("request","event","handler","effect")
    }
    return {
        "protocol":"Round 5A controlled trusted Chromium event, handler and effect audit",
        "environment":{
            "python":sys.version.split()[0],
            "playwright_version":"1.65.2",
            "browser":"Chromium",
            "browser_version":version,
            "fixture_layouts":list(APPS),
        },
        "frozen_case_spec":{
            "apps":list(APPS),"scenarios":list(SCENARIOS),
            "locators":list(LOCATORS),
            "intended_record":"A","timeout_ms":TIMEOUT_MS,
            "cases":len(rows),
        },
        "total":total,"per_app":comparisons,"per_scenario":by_scenario,
        "per_locator":by_locator,
        "real_trusted_browser_clicks":True,
        "original_weblinx_replay_reexecuted":False,
        "external_live_websites":False,
        "external_agent_trajectories":False,
        "independent_browser_capture":True,
        "application_effect_checked_against_rendered_counters":True,
        "posthoc_case_selection":False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=episodes()
    assert len(cases)==72
    results=[]
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(headless=True)
        try:
            version=browser.version
            for i,(app,scenario,locator) in enumerate(cases,1):
                result=one_episode(browser,app,scenario,locator)
                results.append(result)
                if i%12==0:
                    print("ROUND5A_EPISODES",i,"/",len(cases),flush=True)
        finally:
            browser.close()
    report=aggregate(results,version)
    out_file=OUT/"round5a_actions_72.csv"
    with out_file.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    (OUT/"round5a_summary.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R5A_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
