"""M5 - AI Assistant.

Explains the current alarm and recommends safe operator actions. It reads the
latest tags, the active alarm code and recent history, then returns:
    recommendation_text, diagnosis_label, confidence_level

Two engines are supported:
* Claude (Anthropic API) - used when the ANTHROPIC_API_KEY environment variable
  is set. The prompt constrains the model to operator-facing advice only.
* Rule-based fallback - deterministic advice keyed on the alarm code. Used when
  no API key is configured, so the dashboard always shows a recommendation even
  offline.

Safety rule (from the README): the assistant recommends operator actions but
never directly controls actuators.
"""

from __future__ import annotations

import os
from typing import Dict, List

import config


SYSTEM_PROMPT = (
    "You are an operator-support assistant for a beverage pasteurization and "
    "bottling line. You receive live process tags, an alarm code and recent "
    "history. Diagnose the most likely cause and recommend concrete, safe "
    "operator actions. You must NOT command equipment directly - only advise the "
    "human operator. Keep the answer under 120 words, plain language, and end "
    "with a one-line 'Diagnosis:' label."
)

CONSULT_SYSTEM_PROMPT = (
    "You are an expert operator-support assistant for a beverage pasteurization "
    "and bottling line digital twin. The line has 5 stages: S1 Raw Tank (level "
    "control), S2 Pasteurizer (72°C target, 68-78°C safe band), S3 Cooler "
    "(20°C target), S4 Inline Filler (4-nozzle monoblock, 500mL bottles), S5 "
    "Capper/Conveyor (accumulation buffer, P-controlled speed). "
    "You receive live sensor tags and recent history. Answer the operator's "
    "question concisely (under 150 words). Be specific about values and actions. "
    "Never command actuators directly — only advise the human operator."
)

# Deterministic fallback advice keyed on alarm code.
_RULE_ADVICE: Dict[int, Dict[str, str]] = {
    config.ALARM_NONE: {
        "label": "Normal operation",
        "text": "All readings are within range. No action required. Continue "
                "monitoring tank level and pasteurization temperature.",
    },
    config.ALARM_SENSOR_TEMP_STUCK: {
        "label": "Temperature sensor fault",
        "text": "The pasteurization temperature reading is frozen while the "
                "heater command is changing. Treat the reading as unreliable. "
                "Do NOT trust the temperature interlock: stop the line, switch "
                "to the backup temperature sensor or a manual probe, and replace "
                "the faulty sensor before restarting.",
    },
    config.ALARM_PUMP_NO_FLOW: {
        "label": "Feed pump failure",
        "text": "The feed pump is ON but there is no flow or feedback. Stop the "
                "line to avoid dry-running the pasteurizer. Check the pump motor "
                "breaker, the pump coupling and the inlet for blockage, then "
                "restart and confirm flow returns.",
    },
    config.ALARM_TEMP_OUT_OF_RANGE: {
        "label": "Pasteurization temperature excursion",
        "text": "Pasteurization temperature is outside the safe band. Product "
                "safety is at risk: divert or quarantine product processed during "
                "the excursion, reduce or cut heater power, and inspect the "
                "heating element/steam valve before resuming production.",
    },
    config.ALARM_DATA_STALE: {
        "label": "Data link stale",
        "text": "Live data has stopped updating. Operate with caution and do not "
                "rely on on-screen values. Check the MQTT broker, the network "
                "link and the publisher process, then confirm tags resume "
                "updating before trusting the dashboard.",
    },
    config.ALARM_TANK_OVERFLOW: {
        "label": "Raw tank overflow risk",
        "text": f"Tank level has exceeded {config.TANK_CRITICAL_HIGH:.0f}%. "
                "Immediate action: stop the feed pump, fully close the inlet "
                "valve, and check the level sensor. If level continues to rise, "
                "activate the emergency overflow diversion.",
    },
    config.ALARM_TANK_EMPTY: {
        "label": "Raw tank empty",
        "text": f"Tank level has dropped below {config.TANK_CRITICAL_LOW:.0f}%. "
                "The feed pump is at risk of dry-running. Stop the pump "
                "immediately, open the inlet valve fully, and verify raw "
                "beverage supply availability before restarting.",
    },
    config.ALARM_BUFFER_HIGH: {
        "label": "Conveyor buffer critically high",
        "text": f"Conveyor buffer is at {config.CONVEYOR_MAX_BOTTLES * 0.9:.0f}+ bottles "
                "(near capacity). The filler is back-pressuring. Increase "
                "conveyor speed to clear the buffer. If the belt is already at "
                "max, reduce feed pump speed to slow fill rate. Check the "
                "capper for jams.",
    },
    config.ALARM_COOLER_HIGH: {
        "label": "Cooler outlet temperature high",
        "text": f"Cooler outlet temperature has exceeded {config.COOLER_ALARM_HIGH:.0f}°C. "
                "Product is too hot for safe bottling. Increase cooling valve "
                "opening to at least 20-30%. If the valve is already high, "
                "reduce feed pump speed to lower the thermal load. Check glycol "
                "supply temperature and heat exchanger for fouling or blockage.",
    },
}


class AIAssistant:
    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self._client = None
        if self.api_key:
            self._init_client(self.api_key)

    def _init_client(self, key: str) -> None:
        try:
            import anthropic  # noqa: WPS433
            self._client = anthropic.Anthropic(api_key=key)
        except Exception as exc:  # noqa: BLE001
            print(f"[AIAssistant] Anthropic client unavailable ({exc}); using rule-based fallback.")
            self._client = None

    def update_api_key(self, key: str) -> None:
        """Hot-swap the API key from the dashboard UI. Re-initializes the client."""
        key = key.strip()
        if key == self.api_key:
            return
        self.api_key = key
        if key:
            self._init_client(key)
        else:
            self._client = None

    @property
    def using_claude(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------
    def consult(self, question: str, latest_tags: Dict,
                recent_history: List[Dict]) -> str:
        """Free-form operator question. Returns plain-text answer string."""
        if self._client is not None:
            try:
                return self._consult_with_claude(question, latest_tags, recent_history)
            except Exception as exc:  # noqa: BLE001
                print(f"[AIAssistant] Claude consult failed ({exc}); falling back.")
        return self._consult_with_rules(question, latest_tags)

    def _consult_with_rules(self, question: str, latest_tags: Dict) -> str:
        alarm_code = int(latest_tags.get("alarm_code", 0))
        advice = _RULE_ADVICE.get(alarm_code, _RULE_ADVICE[config.ALARM_NONE])
        return (
            f"[Rule-based fallback — no API key configured]\n\n"
            f"Current alarm: {config.ALARM_LABELS.get(alarm_code, 'None')}\n"
            f"{advice['text']}\n\n"
            f"For Claude-powered answers, enter your Anthropic API key in the sidebar."
        )

    def _consult_with_claude(self, question: str, latest_tags: Dict,
                              recent_history: List[Dict]) -> str:
        alarm_code = int(latest_tags.get("alarm_code", 0))
        alarm_label = config.ALARM_LABELS.get(alarm_code, "None")
        trend = _summarize_history(recent_history)
        user_msg = (
            f"Operator question: {question}\n\n"
            f"Active alarm: {alarm_label} (code {alarm_code})\n"
            f"Latest tags:\n{_format_tags(latest_tags)}\n\n"
            f"Recent trend:\n{trend}"
        )
        response = self._client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.ANTHROPIC_MAX_TOKENS,
            system=CONSULT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(block.text for block in response.content
                       if getattr(block, "type", "") == "text").strip()

    # ------------------------------------------------------------------
    def diagnose(self, latest_tags: Dict, alarm_code: int,
                 recent_history: List[Dict]) -> Dict:
        """Return a recommendation dict for the dashboard (M4)."""
        if self._client is not None:
            try:
                return self._diagnose_with_claude(latest_tags, alarm_code,
                                                  recent_history)
            except Exception as exc:  # noqa: BLE001 - never break the dashboard
                print(f"[AIAssistant] Claude call failed ({exc}); falling back.")
        return self._diagnose_with_rules(alarm_code)

    # ------------------------------------------------------------------
    def _diagnose_with_rules(self, alarm_code: int) -> Dict:
        advice = _RULE_ADVICE.get(alarm_code, _RULE_ADVICE[config.ALARM_NONE])
        confidence = "high" if alarm_code in _RULE_ADVICE else "medium"
        return {
            "recommendation_text": advice["text"],
            "diagnosis_label": advice["label"],
            "confidence_level": confidence,
            "engine": "rule-based",
        }

    def _diagnose_with_claude(self, latest_tags: Dict, alarm_code: int,
                              recent_history: List[Dict]) -> Dict:
        alarm_label = config.ALARM_LABELS.get(alarm_code, str(alarm_code))
        alarm_desc = config.ALARM_DESCRIPTIONS.get(alarm_code, "")

        # Compact the history to keep the prompt small.
        trend = _summarize_history(recent_history)
        user_msg = (
            f"Active alarm: {alarm_label} (code {alarm_code}).\n"
            f"Alarm meaning: {alarm_desc}\n\n"
            f"Latest tags:\n{_format_tags(latest_tags)}\n\n"
            f"Recent trend (last samples):\n{trend}\n\n"
            "Give the operator a short diagnosis and the safe actions to take."
        )

        response = self._client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.ANTHROPIC_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = "".join(block.text for block in response.content
                       if getattr(block, "type", "") == "text").strip()

        label = config.ALARM_LABELS.get(alarm_code, "Diagnosis")
        if "Diagnosis:" in text:
            label = text.split("Diagnosis:")[-1].strip()[:60]
        return {
            "recommendation_text": text,
            "diagnosis_label": label,
            "confidence_level": "model",
            "engine": f"claude ({config.ANTHROPIC_MODEL})",
        }


def _format_tags(tags: Dict) -> str:
    keys = ["plc_state", "stage_state", "tank_level", "pasteur_temp",
            "cooler_temp", "flow_rate", "pump_feedback", "bottle_count",
            "heater_power_cmd"]
    return "\n".join(f"  {k} = {tags.get(k)}" for k in keys if k in tags)


def _summarize_history(history: List[Dict], n: int = 8) -> str:
    if not history:
        return "  (no history yet)"
    tail = history[-n:]
    lines = []
    for row in tail:
        lines.append(
            f"  t={row.get('tick', '?')} temp={row.get('pasteur_temp')} "
            f"flow={row.get('flow_rate')} level={row.get('tank_level')}"
        )
    return "\n".join(lines)
