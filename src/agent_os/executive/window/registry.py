from __future__ import annotations

from typing import Any, Callable

from .. import window_queue

TABS = ("work", "personal")


class Registry:
    """Providers (outstanding items) and actions (item options and model tools)."""

    def __init__(self) -> None:
        self._providers: dict[str, Callable[[], list[dict[str, Any]]]] = {}
        self._actions: dict[str, dict[str, Any]] = {}
        self.event_bus: Any = None

    def register_provider(self, name: str, fn: Callable[[], list[dict[str, Any]]]) -> None:
        self._providers[name] = fn

    def register_action(
        self,
        id: str,
        label: str,
        applies_to: list[str] | str,
        handler: Callable[..., dict[str, Any]],
        consequential: bool,
        description: str = "",
        params_schema: dict[str, Any] | None = None,
    ) -> None:
        kinds = "*" if applies_to == "*" else list(applies_to)
        self._actions[id] = {
            "id": id,
            "label": label,
            "applies_to": kinds,
            "handler": handler,
            "consequential": bool(consequential),
            "description": description,
            "params_schema": params_schema,
        }

    def attach_event_bus(self, bus: Any) -> None:
        self.event_bus = bus

    def queue(self, tab: str | None = None, state: Any = None) -> dict[str, Any]:
        queue_items: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for name, fn in list(self._providers.items()):
            try:
                produced = list(fn() or [])
            except Exception as exc:
                errors.append({"provider": name, "error": f"{type(exc).__name__}: {exc}"})
                continue
            for raw in produced:
                if not isinstance(raw, dict):
                    continue
                if self.event_bus is not None:
                    try:
                        window_queue.publish_window_item(self.event_bus, raw, name)
                    except Exception:
                        pass
                if tab is not None and raw.get("tab") != tab:
                    continue
                if state is not None and state.is_hidden(str(raw.get("id"))):
                    continue
                queue_item = window_queue.queue_item_from_window_item(raw, name)
                queue_items.append(queue_item)
        return {"queue_items": queue_items, "errors": errors}

    def actions(self) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in action.items() if k != "handler"}
            for action in self._actions.values()
        ]

    @staticmethod
    def _applies(action: dict[str, Any], kind: Any) -> bool:
        applies = action["applies_to"]
        return applies == "*" or "*" in applies or kind in applies

    def outstanding(self, tab: str | None = None, state: Any = None) -> dict[str, Any]:
        result = self.queue(tab, state)
        items: list[dict[str, Any]] = []
        for qi in result["queue_items"]:
            item = window_queue.window_item_from_queue_item(qi)
            item["options"] = [
                {"action_id": a["id"], "label": a["label"], "consequential": a["consequential"]}
                for a in self._actions.values()
                if self._applies(a, item.get("kind"))
            ]
            items.append(item)
        return {"items": items, "errors": result["errors"]}

    def _get(self, action_id: str) -> dict[str, Any]:
        try:
            return self._actions[action_id]
        except KeyError:
            raise KeyError(f"unknown action: {action_id}") from None

    def invoke(self, action_id: str, item: dict[str, Any], params: dict[str, Any] | None, pending: Any) -> dict[str, Any]:
        action = self._get(action_id)
        params = params or {}
        result = action["handler"](item, params, confirm=False)
        if not action["consequential"]:
            return {"status": "done", "result": result}
        token = pending.create(action_id, item, params, result)
        return {"status": "needs_confirmation", "confirm_token": token, "preview": result}

    def confirm(self, token: str, pending: Any) -> dict[str, Any]:
        record = pending.take(token)
        action_id = record["action_id"]
        item = record.get("item") or {}
        params = record.get("params") or {}
        action = self._get(action_id)
        event = {"action_id": action_id, "item_id": item.get("id"), "params": params}
        try:
            result = action["handler"](item, params, confirm=True)
        except Exception as exc:
            pending.audit({**event, "error": f"{type(exc).__name__}: {exc}"})
            raise
        pending.audit({**event, "result": result})
        return result


REGISTRY = Registry()


def register_provider(name: str, fn: Callable[[], list[dict[str, Any]]]) -> None:
    REGISTRY.register_provider(name, fn)


def register_action(*args: Any, **kwargs: Any) -> None:
    REGISTRY.register_action(*args, **kwargs)
