import asyncio
import random
from collections import Counter

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import F
from django.utils import timezone

from accounts.avatars import get_emoji
from .models import (
    Answer, Game, PERSIAN_LETTERS, Player, Round,
)


class GameConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        room = await self._get_room()
        if room is None:
            await self.close()
            return

        self.room_id = str(room.id)
        self.group = f"game_{self.room_id}"

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        await self._add_player()
        await self._broadcast_state()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content):
        action = content.get("action")
        if action == "ready":
            await self._set_ready(True)
            await self._broadcast_state()
        elif action == "unready":
            await self._set_ready(False)
            await self._broadcast_state()
        elif action == "start":
            await self._start_round()
        elif action == "submit":
            await self._handle_submit(content.get("answers", {}))

    # ---- DB helpers ----

    @database_sync_to_async
    def _get_room(self):
        return Game.objects.filter(code=self.room_code).first()

    @database_sync_to_async
    def _add_player(self):
        room = Game.objects.get(id=self.room_id)
        Player.objects.get_or_create(game=room, user=self.user)

    @database_sync_to_async
    def _set_ready(self, value):
        Player.objects.filter(game_id=self.room_id, user=self.user).update(is_ready=value)

    @database_sync_to_async
    def _state_payload(self):
        room = Game.objects.get(id=self.room_id)
        players = []
        for p in room.players.select_related("user"):
            players.append({
                "user_id": p.user.id,
                "user__alias": p.user.alias,
                "avatar": get_emoji(p.user.avatar_id),
                "score": p.score,
                "is_ready": p.is_ready,
            })
        last_round = room.rounds.order_by("-number").first()
        return {
            "room_id": self.room_id,
            "code": room.code,
            "status": room.status,
            "host_id": room.host_id,
            "categories": room.categories,
            "players": players,
            "letter": last_round.letter if last_round else None,
            "round_number": last_round.number if last_round else 0,
            "duration": last_round.duration if last_round else 60,
            "stopped": bool(last_round and last_round.stopped_at),
        }

    async def _broadcast_state(self):
        state = await self._state_payload()
        await self.channel_layer.group_send(self.group, {
            "type": "ev.state", "state": state,
        })

    async def ev_state(self, event):
        await self.send_json({"type": "state", "state": event["state"]})

    # ---- Round flow ----

    @database_sync_to_async
    def _create_round(self):
        room = Game.objects.get(id=self.room_id)
        number = room.rounds.count() + 1
        letter = random.choice(PERSIAN_LETTERS)
        r = Round.objects.create(game=room, number=number, letter=letter, duration=60)
        room.status = "in_round"
        room.save(update_fields=["status"])
        return {
            "letter": letter,
            "number": number,
            "duration": 60,
            "categories": room.categories,
        }

    async def _start_round(self):
        info = await self._create_round()
        await self.channel_layer.group_send(self.group, {
            "type": "ev.round_start", "info": info,
        })

    async def ev_round_start(self, event):
        await self.send_json({"type": "round_start", **event["info"]})

    @database_sync_to_async
    def _save_answers_and_maybe_stop(self, answers):
        room = Game.objects.get(id=self.room_id)
        rnd = room.rounds.order_by("-number").first()
        if rnd is None:
            return None

        Answer.objects.filter(round=rnd, user=self.user).delete()
        for cat in room.categories:
            raw = (answers.get(cat) or "")[:64]
            norm = self._normalize(raw)
            score = 10 if (norm and norm[0] == rnd.letter) else 0
            Answer.objects.create(
                round=rnd, user=self.user, category=cat,
                value=raw, normalized=norm, score=score,
            )

        first_stop = False
        if rnd.stopped_at is None:
            rnd.stopped_at = timezone.now()
            rnd.stopper = self.user
            rnd.save(update_fields=["stopped_at", "stopper"])
            first_stop = True

        return first_stop

    @database_sync_to_async
    def _evaluate_round(self):
        room = Game.objects.get(id=self.room_id)
        rnd = room.rounds.order_by("-number").first()
        if rnd is None:
            return None

        answers = list(rnd.answers.select_related("user"))
        by_cat = {}
        for a in answers:
            by_cat.setdefault(a.category, []).append(a)

        per_user_total = {}
        for cat, items in by_cat.items():
            counts = Counter(a.normalized for a in items if a.normalized)
            for a in items:
                score = 0
                if a.normalized and a.normalized[0] == rnd.letter:
                    if counts[a.normalized] == 1:
                        score = 20
                    else:
                        score = 5
                a.score = score
                a.save(update_fields=["score"])
                per_user_total[a.user_id] = per_user_total.get(a.user_id, 0) + score

        for uid, add in per_user_total.items():
            Player.objects.filter(game=room, user_id=uid).update(score=F("score") + add)

        room.status = "round_result"
        room.save(update_fields=["status"])

        players = list(room.players.select_related("user").values(
            "user_id", "user__alias", "score",
        ))
        return {"players": players, "letter": rnd.letter, "number": rnd.number}

    async def _handle_submit(self, answers):
        first_stop = await self._save_answers_and_maybe_stop(answers)
        if first_stop is None:
            return

        if first_stop:
            await self.channel_layer.group_send(self.group, {
                "type": "ev.stopping",
                "stopper": self.user.alias,
                "seconds": 10,
            })
            await asyncio.sleep(10)
            results = await self._evaluate_round()
            await self.channel_layer.group_send(self.group, {
                "type": "ev.round_result", "results": results,
            })
            await self._broadcast_state()

    async def ev_stopping(self, event):
        await self.send_json({"type": "stopping", **event})

    async def ev_round_result(self, event):
        await self.send_json({"type": "round_result", "results": event["results"]})

    @staticmethod
    def _normalize(text):
        if not text:
            return ""
        t = text.strip().replace("\u200c", "").replace(" ", "")
        return t.replace("ي", "ی").replace("ك", "ک")