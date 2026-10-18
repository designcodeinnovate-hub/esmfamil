import asyncio
import random
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from .models import Game, Player, Round, Answer
from accounts.avatars import get_emoji

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        room = await self._get_room()
        if not room:
            await self.close()
            return

        self.room_id = str(room.id)
        self.group_name = f"game_{self.room_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._add_player()
        await self._broadcast_state()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        action = content.get("action")
        if action == "ready":
            await self._set_ready(True)
            await self._broadcast_state()
        elif action == "unready":
            await self._set_ready(False)
            await self._broadcast_state()
        elif action == "start":
            await self._start_game()
        elif action == "submit":
            await self._handle_submit(content.get("answers", {}))

    @database_sync_to_async
    def _get_room(self):
        return Game.objects.filter(code=self.room_code).first()

    @database_sync_to_async
    def _add_player(self):
        room = Game.objects.get(id=self.room_id)
        Player.objects.get_or_create(game=room, user=self.user)

    @database_sync_to_async
    def _set_ready(self, status):
        Player.objects.filter(game_id=self.room_id, user=self.user).update(is_ready=status)

    @database_sync_to_async
    def _state_payload(self):
        room = Game.objects.get(id=self.room_id)
        players = []
        for p in room.players.select_related("user"):
            players.append({
                "user_id": p.user.id,
                "alias": p.user.alias,
                "avatar": get_emoji(p.user.avatar_id),
                "is_ready": p.is_ready,
                "score": p.score,
            })
        rnd = room.rounds.order_by("-number").first()
        return {
            "status": room.status,
            "host_id": room.host_id,
            "players": players,
            "round_number": rnd.number if rnd else 0,
            "letter": rnd.letter if rnd else "",
            "categories": room.categories,
        }

    async def _broadcast_state(self):
        state = await self._state_payload()
        await self.channel_layer.group_send(
            self.group_name, {"type": "ev.state", "state": state}
        )

    async def ev_state(self, event):
        await self.send_json({"type": "state", "state": event["state"]})

    @database_sync_to_async
    def _create_round(self):
        room = Game.objects.get(id=self.room_id)
        if room.host != self.user:
            return None
        
        if not all(p.is_ready for p in room.players.all()) or room.players.count() < 2:
            return None

        letter = random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))
        rnd = Round.objects.create(game=room, number=room.rounds.count() + 1, letter=letter, duration=60)
        room.status = "in_round"
        room.save()
        return rnd

    async def _start_game(self):
        rnd = await self._create_round()
        if rnd:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "ev.round_start", "letter": rnd.letter, "duration": rnd.duration},
            )
            await self._broadcast_state()

    async def ev_round_start(self, event):
        await self.send_json({"type": "round_start", "letter": event["letter"], "duration": event["duration"]})

    @database_sync_to_async
    def _handle_submit_db(self, answers):
        room = Game.objects.get(id=self.room_id)
        rnd = room.rounds.order_by("-number").last()
        if not rnd or rnd.stopped_at:
            return None

        for cat, val in answers.items():
            norm = val.strip()
            score = 10 if norm.startswith(rnd.letter) else 0
            Answer.objects.update_or_create(
                round=rnd, user=self.user, category=cat,
                defaults={"value": val, "normalized": norm, "score": score}
            )

        first_stop = False
        if not rnd.stopped_at:
            rnd.stopped_at = timezone.now()
            rnd.stopper = self.user
            rnd.save()
            first_stop = True

        return first_stop

    async def _handle_submit(self, answers):
        first_stop = await self._handle_submit_db(answers)
        if first_stop:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "ev.stopping", "stopper": self.user.alias},
            )
            await asyncio.sleep(10)
            results = await self._evaluate_round()
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "ev.round_result", "results": results},
            )
            await self._broadcast_state()

    async def ev_stopping(self, event):
        await self.send_json({"type": "stopping", "stopper": event["stopper"]})

    @database_sync_to_async
    def _evaluate_round(self):
        room = Game.objects.get(id=self.room_id)
        rnd = room.rounds.order_by("-number").last()
        answers = list(rnd.answers.select_related("user"))

        cat_counts = {}
        for a in answers:
            if a.normalized.startswith(rnd.letter):
                cat_counts[a.normalized] = cat_counts.get(a.normalized, 0) + 1

        player_totals = {}
        for a in answers:
            score = 0
            if a.normalized.startswith(rnd.letter):
                if cat_counts.get(a.normalized, 0) == 1:
                    score = 20
                else:
                    score = 5
            a.score = score
            a.save()
            player_totals[a.user_id] = player_totals.get(a.user_id, 0) + score

        for p in room.players.all():
            p.score += player_totals.get(p.user_id, 0)
            p.save()

        room.status = "round_result"
        room.save()

        return [{"alias": p.user.alias, "score": p.score} for p in room.players.select_related("user")]
