#!/usr/bin/env python3
"""Rank Skyrim Mod Factory implementation patterns from typed feature intent.

This is a conservative router, not an LLM replacement. It auto-selects only when
the pattern is explicitly chosen or when layer/text evidence produces a clear
margin. Ambiguous results become research/prototype work, not user tool-choice.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

STOP={
    "a","an","and","or","the","to","of","for","in","on","with","without","by",
    "is","are","be","this","that","it","should","must","can","new","mod","mods",
    "player","players","game","skyrim"
}

ALIASES={
    "npc":{"actor","actors","npc","npcs"},
    "actor":{"actor","actors","npc","npcs"},
    "animation":{"animation","animations","animate","motion","idle","idles"},
    "dialogue":{"dialogue","dialog","conversation","voice","voiced"},
    "quest":{"quest","quests","stage","stages","objective","objectives"},
    "weather":{"weather","climate","rain","snow","fog"},
    "lighting":{"lighting","light","lights","imagespace"},
    "armor":{"armor","armour","outfit","clothing"},
    "weapon":{"weapon","weapons","sword","axe","bow","staff"},
    "spell":{"spell","spells","magic","magicka"},
    "perk":{"perk","perks","skill","skills","progression"},
    "world":{"world","worldspace","cell","cells","location","interior","exterior"},
    "navmesh":{"navmesh","pathing","navigation"},
    "runtime":{"runtime","dynamic","distribute","distribution","inject","patch"},
    "ui":{"ui","menu","menus","hud","interface","mcm"},
    "mesh":{"mesh","nif","model","geometry"},
    "texture":{"texture","textures","dds","material","materials","pbr","parallax"},
    "audio":{"audio","sound","music","voice"},
    "vr":{"vr","higgs","planck","vrik"},
}

def words(value: str) -> set[str]:
    raw={x for x in re.findall(r"[a-z0-9]+",value.lower()) if len(x)>1 and x not in STOP}
    expanded=set(raw)
    for key,vals in ALIASES.items():
        if raw & vals:
            expanded.add(key)
            expanded |= vals
    return expanded

def feature_text(feature: dict[str,Any]) -> str:
    bits=[feature.get("summary","")]
    bits.extend(feature.get("player_observable_behavior") or [])
    bits.extend(feature.get("triggers") or [])
    bits.extend(feature.get("must_not_happen") or [])
    bits.extend(feature.get("constraints") or [])
    bits.extend(feature.get("compatibility_expectations") or [])
    return " ".join(str(x) for x in bits if x)

def rank(feature: dict[str,Any], pack: dict[str,Any], limit: int=8) -> dict[str,Any]:
    fid=feature.get("feature_id") or "feature"
    impl=feature.get("implementation") or {}
    explicit=impl.get("selected_pattern")
    patterns=pack.get("patterns") or []
    by_id={p.get("pattern_id"):p for p in patterns if p.get("pattern_id")}

    if explicit:
        p=by_id.get(explicit)
        if p:
            return {
              "schema_version":"skyrim-pattern-selection-v1",
              "feature_id":fid,
              "status":"selected",
              "selected_pattern":explicit,
              "confidence":"high",
              "candidates":[{
                "pattern_id":explicit,
                "score":100.0,
                "reasons":["Feature intent explicitly selected this pattern."],
                "preferred_layers":p.get("preferred_layers",[]),
                "preferred_providers":(p.get("selection") or {}).get("preferred",[]),
                "conditions":(p.get("selection") or {}).get("conditions",[]),
                "avoid_by_default":(p.get("selection") or {}).get("avoid_by_default",[])
              }],
              "next_action":"Validate the explicit pattern's conditions and providers before implementation.",
              "evidence":["implementation.selected_pattern"]
            }
        return {
          "schema_version":"skyrim-pattern-selection-v1",
          "feature_id":fid,
          "status":"research-required",
          "selected_pattern":None,
          "confidence":"low",
          "candidates":[],
          "next_action":f"Selected pattern '{explicit}' is not in the current pattern registry; research/register it or correct the feature intent.",
          "evidence":["implementation.selected_pattern references an unknown pattern"]
        }

    text=feature_text(feature)
    ftokens=words(text)
    selected_layers=set(impl.get("selected_layers") or [])
    selected_frameworks=set(impl.get("selected_frameworks") or [])
    ranked=[]

    for p in patterns:
        reasons=[]
        score=0.0
        intents=p.get("intent") or []
        intent_text=" ".join(intents)
        ptokens=words(intent_text)
        overlap=ftokens & ptokens
        if overlap:
            # Bounded token evidence; avoids giant descriptions dominating.
            token_score=min(10.0,2.0*len(overlap))
            score+=token_score
            reasons.append("Intent token overlap: "+", ".join(sorted(overlap)[:12]))

        for phrase in intents:
            ps=" ".join(words(phrase))
            if phrase.lower() in text.lower() and len(phrase)>=8:
                score+=6.0
                reasons.append(f"Intent phrase match: {phrase}")

        layers=set(p.get("preferred_layers") or [])
        if selected_layers:
            common=selected_layers & layers
            if common:
                score+=4.0*len(common)
                reasons.append("Selected-layer match: "+", ".join(sorted(common)))
            missing=selected_layers-layers
            # Do not punish patterns for being one component of a multi-layer feature too strongly.
            score-=0.75*len(missing)

        selection=p.get("selection") or {}
        providers=set(selection.get("preferred") or [])|set(selection.get("alternatives") or [])
        fwmatch=selected_frameworks & providers
        if fwmatch:
            score+=5.0*len(fwmatch)
            reasons.append("Selected-framework match: "+", ".join(sorted(fwmatch)))

        if score>0:
            ranked.append({
              "pattern_id":p["pattern_id"],
              "score":round(score,2),
              "reasons":reasons,
              "preferred_layers":p.get("preferred_layers",[]),
              "preferred_providers":selection.get("preferred",[]),
              "conditions":selection.get("conditions",[]),
              "avoid_by_default":selection.get("avoid_by_default",[])
            })

    ranked.sort(key=lambda x:(-x["score"],x["pattern_id"]))
    ranked=ranked[:limit]

    if not ranked:
        return {
          "schema_version":"skyrim-pattern-selection-v1",
          "feature_id":fid,
          "status":"no-match",
          "selected_pattern":None,
          "confidence":"unknown",
          "candidates":[],
          "next_action":"Decompose the requested behavior into engine layers, search current frameworks and analogous vanilla behavior, then prototype/register a new pattern.",
          "evidence":["No current pattern received positive deterministic evidence."]
        }

    top=ranked[0]["score"]
    second=ranked[1]["score"] if len(ranked)>1 else 0.0
    margin=top-second
    if top>=12.0 and margin>=4.0:
        status="selected"; confidence="high"; selected=ranked[0]["pattern_id"]
        action="Validate the selected pattern conditions/provider availability, then derive quality/test plans."
    elif top>=8.0 and margin>=2.0:
        status="selected"; confidence="medium"; selected=ranked[0]["pattern_id"]
        action="Run a minimal feasibility/schema probe for the leading pattern before committing architecture."
    else:
        status="research-required"; confidence="low" if top<8 else "medium"; selected=None
        action="Research/prototype the leading candidates and select by invasiveness, compatibility surface, testability, and current provider support; do not ask the user to choose tools."

    return {
      "schema_version":"skyrim-pattern-selection-v1",
      "feature_id":fid,
      "status":status,
      "selected_pattern":selected,
      "confidence":confidence,
      "candidates":ranked,
      "next_action":action,
      "evidence":[f"top_score={top}",f"runner_up={second}",f"margin={margin}",f"selected_layers={sorted(selected_layers)}"]
    }

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("feature_intent",type=Path)
    ap.add_argument("--patterns",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=rank(
      json.loads(args.feature_intent.read_text(encoding="utf-8")),
      json.loads(args.patterns.read_text(encoding="utf-8"))
    )
    rendered=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")

if __name__=="__main__":
    main()
