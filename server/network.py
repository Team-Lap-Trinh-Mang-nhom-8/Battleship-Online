import json
import socket
import string
import random
import os
from threading import Lock, Thread

from server.utils import layout_ships

lock = Lock()


class Room:
    def __init__(self):
        self.players = []
        self.sent_board = False
        self.rematch_votes = set()
        self.game_over = False
        self._id = ""

    def send_board(self):
        self.players[0].turn = random.choice((True, False))
        self.players[1].turn = not self.players[0].turn
        self.players[0].layout, self.players[1].layout = layout_ships(), layout_ships()
        self.players[0].opponent, self.players[1].opponent = (
            self.players[1],
            self.players[0],
        )
        for player in self.players:
            opponent_name = player.opponent.name
            opponent_avatar = player.opponent.avatar
            player.conn.send(
                {
                    "category": "BOARD",
                    "payload": [
                        player.turn,
                        player.layout,
                        [
                            (xi, yi, square["ship"])
                            for xi, x in enumerate(player.opponent.layout)
                            for yi, square in enumerate(x)
                            if square["ship"]
                        ],
                        opponent_name,
                        opponent_avatar,
                    ],
                }
            )
        # Reset game_over/rematch state when starting a new board
        self.game_over = False
        self.rematch_votes.clear()


class ServerPlayer:
    def __init__(self, conn, room=None):
        self.conn = conn
        self.room = room
        self.name = ""
        self.avatar = 0


class Network:
    # Allow overriding host/port via environment variables for easier testing and
    # running on LAN. Defaults remain localhost:1234 for backward compatibility.
    server_addr = os.getenv("SERVER_HOST", "localhost")
    port = int(os.getenv("SERVER_PORT", "1234"))
    address = (server_addr, port)

    def __init__(
        self, sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM), is_server=True
    ):
        self.server = sock
        if is_server:
            self.game_list = {}
            self.server.bind(self.address)
            self.wait_for_connection()

    def wait_for_connection(self):
        self.server.listen()
        while True:
            conn, address = self.server.accept()
            print("Connected to: ", address)

            conn = Network(sock=conn, is_server=False)
            lock.acquire()
            Thread(
                target=self.proceed_with_connection,
                args=(ServerPlayer(conn),),
            ).start()
            lock.release()
            print(self.game_list)
    def proceed_with_connection(self, player):
        while True:
            try:
                data = player.conn.receive()
                if not data:
                    break
                if data["category"] == "OVER":
                    # Mark room as game over and broadcast to both players.
                    if player.room:
                        player.room.game_over = True
                        # Broadcast GAME_OVER with player who sent the message as "by"
                        for p in list(player.room.players):
                            try:
                                p.conn.send({"category": "GAME_OVER", "payload": {"by": player.name}})
                            except Exception:
                                pass
                    # Do not delete the room immediately; allow rematch flow.
                    player.room = player.room
                elif data["category"] == "CREATE":
                    player.name = data.get("name", "")
                    player.avatar = data.get("avatar", 0)
                    i = self.generate_id()
                    self.game_list[i] = Room()
                    self.game_list[i]._id = i
                    self.game_list[i].players.append(player)
                    player.room = self.game_list[i]
                    player.conn.send({"category": "ID", "payload": i})
                elif data["category"] == "JOIN":
                    player.name = data.get("name", "")
                    player.avatar = data.get("avatar", 0)
                    try:
                        if len(self.game_list[data["payload"]].players) == 2:
                            player.conn.send("TAKEN")
                        else:
                            player.room = self.game_list[data["payload"]]
                            self.game_list[data["payload"]].players.append(player)
                            self.game_list[data["payload"]].send_board()
                    except KeyError:
                        player.conn.send("INVALID")
                elif data["category"] == "POSITION":
                    player.opponent.conn.send(data)
                elif data["category"] == "REMATCH_OFFER":
                    # Add player's vote and start a new board when both agree
                    if player.room:
                        with lock:
                            player.room.rematch_votes.add(player)
                            # Notify both players about current rematch status
                            try:
                                offered_names = [p.name for p in player.room.rematch_votes]
                                for p in list(player.room.players):
                                    try:
                                        p.conn.send({"category": "REMATCH_STATUS", "payload": {"offers": offered_names}})
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            # Only start rematch when both players present and both voted
                            if len(player.room.players) == 2 and len(player.room.rematch_votes) == 2:
                                try:
                                    # Inform clients rematch is starting
                                    for p in list(player.room.players):
                                        try:
                                            p.conn.send({"category": "REMATCH_START", "payload": {}})
                                        except Exception:
                                            pass
                                    player.room.rematch_votes.clear()
                                    player.room.send_board()
                                except Exception:
                                    pass
                elif data["category"] == "SURRENDER" or data["category"] == "FORFEIT":
                    # Player concedes — declare opponent as winner
                    if player.room:
                        player.room.game_over = True
                        winner_name = None
                        try:
                            winner = player.opponent
                            winner_name = winner.name if winner else None
                        except Exception:
                            winner_name = None
                        for p in list(player.room.players):
                            try:
                                p.conn.send({"category": "GAME_OVER", "payload": {"by": winner_name, "reason": "surrender"}})
                            except Exception:
                                pass
                elif data["category"] == "CHAT":
                    player.opponent.conn.send(data)
            except:
                break
        try:
            player.opponent.conn.send("END")
        except AttributeError:
            print("Closed Without Pair")
        if player.room and player.room._id in self.game_list:
            del self.game_list[player.room._id]
        player.conn.close()
        return

    def receive(self):
        buff = b""
        n = int.from_bytes(self.server.recv(4)[:4], "big")
        while n > 0:
            b = self.server.recv(n)
            buff += b
            n -= len(b)
        return json.loads(buff.decode())

    def send(self, *data):
        if len(data) == 1:
            data = data[0]
        final_data = b""
        data = json.dumps(data)
        final_data += len(data).to_bytes(4, "big")
        final_data += data.encode()
        try:
            self.server.send(final_data)
        except:
            pass

    def close(self):
        self.server.close()

    def generate_id(self):
        _id = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
        while _id in self.game_list.keys():
            _id = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
        return _id
