import pygame
import json
import os
import sys
import numpy as np
import threading
import queue
from dotenv import load_dotenv
from engine.grid import GridEngine
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine

load_dotenv()

# ─── CONSTANTS ───
GRID_SIZE = 10
CELL_SIZE = 55
SIDEBAR_WIDTH = 420
GRID_PX = GRID_SIZE * CELL_SIZE
WIDTH = GRID_PX + SIDEBAR_WIDTH + 60
HEIGHT = GRID_PX + 160
FPS = 30

# ─── COLORS ───
BG        = (18, 18, 22)
ROAD      = (30, 30, 35)
BUILDING  = (160, 160, 175)
BLDG_BORDER = (100, 100, 110)
FIRE_CORE = (255, 100, 20)
FIRE_GLOW = (255, 60, 0)
GREEN     = (46, 204, 113)
RED       = (231, 76, 60)
YELLOW    = (241, 196, 15)
BLUE      = (52, 152, 219)
PURPLE    = (155, 89, 182)
WHITE     = (240, 240, 240)
GRAY      = (140, 140, 140)
DARK_GRAY = (80, 80, 80)
SAVED_CLR = (46, 204, 113)


class Visualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SENTINEL 2.0 — Live Disaster Response")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 14)
        self.small_font = pygame.font.SysFont("Consolas", 12)
        self.title_font = pygame.font.SysFont("Consolas", 22, bold=True)
        self.big_font = pygame.font.SysFont("Consolas", 16, bold=True)

        # ─── Engines ───
        self.engine = GridEngine(size=GRID_SIZE)
        self.voter = VotingEngine()

        # ─── Agents ───
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("ERROR: Set GROQ_API_KEY in your .env file.")
            sys.exit(1)
        self.agents = [Casper(api_key), Melchior(api_key), Balthasar(api_key)]

        # ─── Simulation State ───
        self.state = self._build_scenario()
        self.running_sim = False
        self.sim_over = False
        self.sim_over_reason = ""
        self.tick_delay = 1200  # ms between ticks
        self.last_tick_time = 0

        # ─── AI State ───
        self.ai_active = False
        self.is_thinking = False
        self.thinking_agent = ""  # Which agent is currently being queried
        self.decision_queue = queue.Queue()
        self.last_decision = None
        self.decision_log = []  # History of all decisions

    def _build_scenario(self):
        """Create the simple scenario: 1 building in center, fire at [2,5], 3 civilians."""
        size = GRID_SIZE
        grid = [[0]*size for _ in range(size)]
        integrity = [[0.0]*size for _ in range(size)]
        fire_map = [[0.0]*size for _ in range(size)]
        flood_map = [[0.0]*size for _ in range(size)]

        # Building: 3x3 block in center (rows 3-5, cols 3-5)
        for r in range(3, 6):
            for c in range(3, 6):
                grid[r][c] = 1
                integrity[r][c] = 100.0

        # Wire path from fire source to building
        integrity[2][5] = 40.0
        grid[2][5] = 1

        # Starting fire at the wire endpoint
        fire_map[2][5] = 3.0

        # 3 civilians at different distances from the fire
        civilians = [
            {"id": 1, "pos": [3, 4], "health": 100, "status": "stable", "saved": False, "hurt_rate": 0},
            {"id": 2, "pos": [4, 4], "health": 100, "status": "stable", "saved": False, "hurt_rate": 0},
            {"id": 3, "pos": [7, 7], "health": 100, "status": "stable", "saved": False, "hurt_rate": 0},
        ]

        return {
            "name": "simple_crisis",
            "display_name": "Isolated Building Fire",
            "tick": 0,
            "grid": grid,
            "civilians": civilians,
            "resources": {"medical_teams": 3, "supply_caches": 2},
            "fire_map": fire_map,
            "flood_map": flood_map,
            "building_integrity": integrity,
        }

    # ═══════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self._manual_tick()
                    if event.key == pygame.K_a:
                        self.running_sim = not self.running_sim
                    if event.key == pygame.K_v:
                        self.ai_active = not self.ai_active
                        # Auto-start simulation when AI is toggled on
                        if self.ai_active:
                            self.running_sim = True
                    if event.key == pygame.K_r:
                        self.state = self._build_scenario()
                        self.sim_over = False
                        self.sim_over_reason = ""
                        self.last_decision = None
                        self.decision_log = []
                        self.is_thinking = False
                        self.thinking_agent = ""

            # ── Simulation ticks ALWAYS run while active ──
            # This is independent of AI. Fire spreads and health decays
            # even while the agents are deliberating.
            if self.running_sim and not self.sim_over:
                now = pygame.time.get_ticks()
                if now - self.last_tick_time > self.tick_delay:
                    self._manual_tick()
                    self.last_tick_time = now

            # ── AI decision loop (non-blocking) ──
            if self.ai_active and not self.is_thinking and not self.sim_over:
                unsaved = self.engine.get_unsaved_civilians(self.state)
                if len(unsaved) > 0:
                    self.is_thinking = True
                    self.thinking_agent = "Starting..."
                    threading.Thread(
                        target=self._ai_think,
                        args=(self.state.copy(),),
                        daemon=True
                    ).start()

            # ── Process completed AI results ──
            try:
                decision = self.decision_queue.get_nowait()
                self._apply_decision(decision)
                self.is_thinking = False
                self.thinking_agent = ""
            except queue.Empty:
                pass

            # ── Check end condition ──
            over, reason = self.engine.is_simulation_over(self.state)
            if over:
                self.sim_over = True
                self.sim_over_reason = reason

            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _manual_tick(self):
        if not self.sim_over:
            self.state = self.engine.tick(self.state)

    def _ai_think(self, snapshot):
        """Sequential voting with 3s delay between each agent call.
        The main loop keeps ticking the simulation independently."""
        import time
        try:
            votes = []
            agent_names = ["CASPER", "MELCHIOR", "BALTHASAR"]
            for i, agent in enumerate(self.agents):
                self.thinking_agent = f"Asking {agent_names[i]}..."
                vote = agent.vote(snapshot)
                votes.append(vote)
                # 3 second gap between each LLM call (rate limit safety)
                time.sleep(3.0)
            
            result = self.voter.resolve(votes, snapshot)
            self.decision_queue.put(result)
            
            # Cooldown before next decision round
            time.sleep(3.0)
        except Exception as e:
            print(f"AI Error: {e}")
            self.decision_queue.put(None)

    def _apply_decision(self, result):
        if not result:
            return
        self.last_decision = result
        action = result["winning_action"]
        civ_id = result.get("winning_target_civilian_id")
        self.state = self.engine.execute_action(self.state, action, civ_id)
        self.decision_log.append(result)

    # ═══════════════════════════════════════
    # DRAWING
    # ═══════════════════════════════════════
    def _draw(self):
        self.screen.fill(BG)
        ox, oy = 20, 100  # grid offset

        fire = np.array(self.state["fire_map"], dtype=float)
        integrity = np.array(self.state["building_integrity"], dtype=float)

        # ─── GRID ───
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                rect = pygame.Rect(ox + c*CELL_SIZE, oy + r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                integ = integrity[r, c]

                if integ > 0:
                    shade = int(120 + integ * 0.55)
                    pygame.draw.rect(self.screen, (shade, shade, shade+10), rect)
                    pygame.draw.rect(self.screen, BLDG_BORDER, rect, 1)
                else:
                    pygame.draw.rect(self.screen, ROAD, rect)
                    pygame.draw.rect(self.screen, (40, 40, 45), rect, 1)

                # Fire
                f = fire[r, c]
                if f > 0.1:
                    # Outer glow
                    glow_sz = CELL_SIZE + 12
                    glow_surf = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
                    glow_alpha = int(min(120, 30 + f * 18))
                    pygame.draw.rect(glow_surf, (*FIRE_GLOW, glow_alpha), glow_surf.get_rect(), border_radius=6)
                    self.screen.blit(glow_surf, (rect.x - 6, rect.y - 6))
                    # Core
                    core = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    core_alpha = int(min(240, 140 + f * 20))
                    pygame.draw.rect(core, (*FIRE_CORE, core_alpha), core.get_rect())
                    self.screen.blit(core, rect)

        # ─── CIVILIANS ───
        for civ in self.state["civilians"]:
            r, c = civ["pos"]
            cx = ox + c * CELL_SIZE + CELL_SIZE // 2
            cy = oy + r * CELL_SIZE + CELL_SIZE // 2

            if civ.get("saved"):
                pygame.draw.circle(self.screen, SAVED_CLR, (cx, cy), 10)
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 10, 2)
                lbl = self.small_font.render("OK", True, WHITE)
                self.screen.blit(lbl, (cx - 8, cy - 6))
            elif civ["health"] <= 0:
                pygame.draw.circle(self.screen, DARK_GRAY, (cx, cy), 8)
                lbl = self.small_font.render("X", True, RED)
                self.screen.blit(lbl, (cx - 4, cy - 6))
            else:
                color = GREEN if civ["status"] == "stable" else RED
                pygame.draw.circle(self.screen, color, (cx, cy), 10)
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 10, 2)
                # HP label
                hp_lbl = self.small_font.render(f"{int(civ['health'])}", True, WHITE)
                self.screen.blit(hp_lbl, (cx - 8, cy - 6))

        # ─── HEADER ───
        title = self.title_font.render("SENTINEL 2.0", True, WHITE)
        self.screen.blit(title, (20, 15))
        sub = self.font.render(f"Tick: {self.state['tick']}  |  {self.state['display_name']}", True, GRAY)
        self.screen.blit(sub, (20, 45))

        # Status bar
        alive = sum(1 for c in self.state["civilians"] if c["health"] > 0 and not c.get("saved"))
        saved = sum(1 for c in self.state["civilians"] if c.get("saved"))
        dead = sum(1 for c in self.state["civilians"] if c["health"] <= 0)
        status_str = f"In Danger: {alive}  |  Saved: {saved}  |  Dead: {dead}"
        self.screen.blit(self.font.render(status_str, True, YELLOW), (20, 70))

        # ─── SIDEBAR ───
        sx = GRID_PX + 50
        sy = 20

        # Resources
        self.screen.blit(self.big_font.render("RESOURCES", True, WHITE), (sx, sy))
        sy += 25
        res = self.state["resources"]
        self.screen.blit(self.font.render(f"Medical Teams:  {res['medical_teams']}", True, GREEN), (sx, sy)); sy += 18
        self.screen.blit(self.font.render(f"Supply Caches:  {res['supply_caches']}", True, BLUE), (sx, sy)); sy += 25

        # Civilian Details
        pygame.draw.line(self.screen, DARK_GRAY, (sx, sy), (sx + SIDEBAR_WIDTH - 40, sy))
        sy += 8
        self.screen.blit(self.big_font.render("CIVILIAN STATUS", True, WHITE), (sx, sy)); sy += 22

        for civ in self.state["civilians"]:
            if civ.get("saved"):
                color = SAVED_CLR
                txt = f"#{civ['id']} [{civ['pos'][0]},{civ['pos'][1]}]  SAVED"
            elif civ["health"] <= 0:
                color = DARK_GRAY
                txt = f"#{civ['id']} [{civ['pos'][0]},{civ['pos'][1]}]  DEAD"
            else:
                color = GREEN if civ["status"] == "stable" else RED
                txt = f"#{civ['id']} [{civ['pos'][0]},{civ['pos'][1]}]  HP:{int(civ['health'])}  -{civ.get('hurt_rate', 0)}/t"
            self.screen.blit(self.font.render(txt, True, color), (sx, sy))
            sy += 18

        # AI Decision Panel
        sy += 10
        pygame.draw.line(self.screen, DARK_GRAY, (sx, sy), (sx + SIDEBAR_WIDTH - 40, sy))
        sy += 8

        ai_color = GREEN if self.ai_active else RED
        ai_label = "AI: ACTIVE" if self.ai_active else "AI: INACTIVE"
        self.screen.blit(self.big_font.render(ai_label, True, ai_color), (sx, sy)); sy += 22

        if self.is_thinking:
            # Pulsing "thinking" indicator showing which agent is being queried
            pulse = int(abs(pygame.time.get_ticks() % 1000 - 500) / 500.0 * 255)
            self.screen.blit(self.font.render(self.thinking_agent, True, (255, pulse, 0)), (sx, sy))
            sy += 20

        if self.last_decision:
            d = self.last_decision
            self.screen.blit(self.font.render(f"Winner: {d['winner']}", True, PURPLE), (sx, sy)); sy += 18
            self.screen.blit(self.font.render(f"Action: {d['winning_action']}", True, WHITE), (sx, sy)); sy += 18
            cid = d.get("winning_target_civilian_id")
            if cid:
                self.screen.blit(self.font.render(f"Target: Civilian #{cid}", True, YELLOW), (sx, sy)); sy += 18
            self.screen.blit(self.font.render(f"Method: {d['resolution_method']}", True, GRAY), (sx, sy)); sy += 22

            # Show all 3 agent votes
            for v in d.get("votes", []):
                agent_name = v["agent"]
                reason = v["reasoning"]
                if len(reason) > 45:
                    reason = reason[:42] + "..."
                color = PURPLE if agent_name == d["winner"] else GRAY
                self.screen.blit(self.small_font.render(f"[{agent_name}]", True, color), (sx, sy)); sy += 14
                self.screen.blit(self.small_font.render(f"  {v['proposed_action']} -> Civ#{v.get('target_civilian_id', '?')}", True, WHITE), (sx, sy)); sy += 14
                self.screen.blit(self.small_font.render(f"  \"{reason}\"", True, DARK_GRAY), (sx, sy)); sy += 16

        # Decision history
        if self.decision_log:
            sy += 5
            pygame.draw.line(self.screen, DARK_GRAY, (sx, sy), (sx + SIDEBAR_WIDTH - 40, sy))
            sy += 8
            self.screen.blit(self.big_font.render(f"DECISION LOG ({len(self.decision_log)})", True, WHITE), (sx, sy)); sy += 20
            # Show last 4 decisions
            for d in self.decision_log[-4:]:
                txt = f"T{d['tick']}: {d['winner']} -> {d['winning_action']}"
                cid = d.get("winning_target_civilian_id")
                if cid:
                    txt += f" (Civ#{cid})"
                self.screen.blit(self.small_font.render(txt, True, GRAY), (sx, sy)); sy += 15

        # Game Over overlay
        if self.sim_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            msg = self.title_font.render("SIMULATION COMPLETE", True, WHITE)
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))
            
            reason_lbl = self.font.render(self.sim_over_reason, True, YELLOW)
            self.screen.blit(reason_lbl, (WIDTH//2 - reason_lbl.get_width()//2, HEIGHT//2))

            saved = sum(1 for c in self.state["civilians"] if c.get("saved"))
            result = self.font.render(f"Saved: {saved}/3  |  Press [R] to restart", True, GREEN)
            self.screen.blit(result, (WIDTH//2 - result.get_width()//2, HEIGHT//2 + 30))

        # Controls
        controls_y = HEIGHT - 30
        ctrl_str = "[A] Auto-Tick   [V] Toggle AI   [SPACE] Manual Tick   [R] Reset"
        self.screen.blit(self.small_font.render(ctrl_str, True, DARK_GRAY), (20, controls_y))

        pygame.display.flip()


if __name__ == "__main__":
    vis = Visualizer()
    vis.run()
