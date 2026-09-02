import pygame
import math
import random
import sys

# ============================================================
# VOYAGER'S VIEW — CINEMATIC SOLAR SYSTEM EXPLORER
# Keeps the original theme, but adds atmospheric motion,
# richer lighting, orbit trails, particles, and a polished HUD.
# ============================================================

pygame.init()

WIDTH, HEIGHT = 1600, 800
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE
)
pygame.display.set_caption("Voyager's View - Solar System Journey")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 230, 150)
ORANGE = (255, 180, 80)
RED = (220, 80, 50)
BLUE = (80, 150, 255)
DARK_BLUE = (40, 80, 180)
PURPLE = (180, 100, 255)
GREEN = (100, 200, 100)
BROWN = (180, 120, 80)
GRAY = (180, 180, 180)
LIGHT_BLUE = (150, 200, 255)
GOLD = (255, 200, 50)

CENTER = (WIDTH // 2, HEIGHT // 2)


def clamp(value, low, high):
    return max(low, min(high, value))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def world_to_screen(x, y, view_x, view_y, scale):
    sx = CENTER[0] + (x - CENTER[0] - view_x) * scale
    sy = CENTER[1] + (y - CENTER[1] - view_y) * scale
    return sx, sy


def make_glow(radius, color, alpha=255):
    radius = max(2, int(radius))
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = radius

    # Layered falloff gives a soft photographic glow without a harsh edge.
    for i in range(radius, 0, -max(1, radius // 24)):
        t = i / radius
        a = int(alpha * (1.0 - t) ** 2.4 * 0.16)
        if a:
            pygame.draw.circle(surf, (*color, a), (cx, cy), i)

    return surf


class StarField:
    """Layered deep-space star field with colored stars, twinkling and shooting stars."""

    def __init__(self, count=900):
        self.layers = []

        # Distant stars are smaller and move less; nearby stars have stronger parallax.
        for depth, amount in [(1, count // 2), (2, count // 3), (4, count // 6)]:
            stars = []
            for _ in range(amount):
                temperature = random.random()
                if temperature < 0.10:
                    color = (150, 190, 255)       # blue-white
                elif temperature < 0.22:
                    color = (255, 220, 175)       # warm
                else:
                    color = (225, 232, 255)       # white

                stars.append({
                    "x": random.uniform(-WIDTH, WIDTH * 2),
                    "y": random.uniform(-HEIGHT, HEIGHT * 2),
                    "size": random.uniform(0.45, 2.0) / (depth ** 0.10),
                    "brightness": random.randint(75, 235),
                    "speed": random.uniform(0.25, 1.8),
                    "phase": random.uniform(0, math.tau),
                    "depth": depth,
                    "color": color,
                })
            self.layers.append(stars)

        self.shooters = []
        self.timer = 0.0

    def update(self, dt, time):
        self.timer += dt

        # Occasional cinematic shooting star.
        if len(self.shooters) < 2 and random.random() < dt * 0.08:
            self.shooters.append({
                "x": random.uniform(-100, WIDTH * 0.8),
                "y": random.uniform(0, HEIGHT * 0.35),
                "vx": random.uniform(500, 900),
                "vy": random.uniform(160, 360),
                "life": 0.0,
                "maxlife": random.uniform(0.65, 1.1),
            })

        for s in self.shooters[:]:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["life"] += dt
            if s["life"] > s["maxlife"]:
                self.shooters.remove(s)

    def draw(self, surface, time, view_x, view_y):
        for layer in self.layers:
            for star in layer:
                parallax = 0.06 + 0.075 * star["depth"]
                x = (star["x"] - view_x * parallax) % (WIDTH + 120) - 60
                y = (star["y"] - view_y * parallax) % (HEIGHT + 120) - 60

                twinkle = 0.72 + 0.28 * math.sin(
                    time * star["speed"] + star["phase"]
                )
                b = int(clamp(star["brightness"] * twinkle, 18, 255))
                size = max(1, int(star["size"] * (0.75 + twinkle * 0.9)))

                base = star["color"]
                color = (
                    int(base[0] * b / 255),
                    int(base[1] * b / 255),
                    int(base[2] * b / 255),
                )

                pygame.draw.circle(surface, color, (int(x), int(y)), size)

                # Only the brighter foreground stars get a tiny diffraction sparkle.
                if star["depth"] == 4 and b > 205 and size >= 2:
                    sparkle = max(2, size * 2)
                    pygame.draw.line(
                        surface, (*color, 80) if len(color) == 3 else color,
                        (int(x - sparkle), int(y)),
                        (int(x + sparkle), int(y)), 1
                    )
                    pygame.draw.line(
                        surface, color,
                        (int(x), int(y - sparkle)),
                        (int(x), int(y + sparkle)), 1
                    )

        for s in self.shooters:
            fade = 1.0 - s["life"] / s["maxlife"]
            length = 120 * fade
            speed = max(1, math.hypot(s["vx"], s["vy"]))
            dx = s["vx"] / speed * length
            dy = s["vy"] / speed * length
            pygame.draw.line(
                surface, (175, 215, 255),
                (int(s["x"] - dx), int(s["y"] - dy)),
                (int(s["x"]), int(s["y"])),
                max(1, int(2.5 * fade)),
            )


class Nebula:
    """Soft, slowly breathing nebula clouds for depth behind the star field."""

    def __init__(self):
        self.clouds = []
        for _ in range(20):
            self.clouds.append({
                "x": random.randint(-350, WIDTH + 350),
                "y": random.randint(-200, HEIGHT + 200),
                "r": random.randint(120, 330),
                "color": random.choice([
                    (28, 48, 125), (52, 25, 115), (18, 72, 115),
                    (75, 28, 105), (22, 62, 100), (45, 55, 120),
                ]),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(0.025, 0.09),
            })

    def draw(self, surface, time):
        neb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        for cloud in self.clouds:
            pulse = 0.90 + 0.10 * math.sin(
                time * cloud["speed"] + cloud["phase"]
            )
            r = int(cloud["r"] * pulse)

            # More layers, lower alpha = smoother atmospheric depth.
            for rr in range(r, max(12, r // 7), -max(3, r // 20)):
                t = rr / r
                alpha = int(6.5 * (1.0 - t) ** 2)
                if alpha:
                    pygame.draw.circle(
                        neb, (*cloud["color"], alpha),
                        (int(cloud["x"]), int(cloud["y"])), rr
                    )

        surface.blit(neb, (0, 0))


class Sun:
    """Layered cinematic Sun with corona, granulation, sunspots and lens flare."""

    def __init__(self):
        self.x, self.y = CENTER
        self.radius = 58
        self.rotation = 0.0
        self.particles = []
        self.sunspots = []
        self.glow = make_glow(260, (255, 150, 45), 255)

        for _ in range(260):
            a = random.uniform(0, math.tau)
            d = random.uniform(self.radius * 0.95, self.radius * 2.9)
            self.particles.append({
                "a": a,
                "d": d,
                "base": d,
                "size": random.uniform(0.6, 2.8),
                "speed": random.uniform(0.04, 0.30),
                "phase": random.uniform(0, math.tau),
            })

        for _ in range(16):
            self.sunspots.append({
                "a": random.uniform(0, math.tau),
                "d": random.uniform(0, self.radius * 0.65),
                "size": random.uniform(2, 6),
                "phase": random.uniform(0, math.tau),
            })

    def update(self, dt, time):
        self.rotation += dt * 0.24

        for p in self.particles:
            p["a"] += p["speed"] * dt
            p["d"] = p["base"] + math.sin(
                time * p["speed"] + p["phase"]
            ) * 8

    def draw(self, surface, time, scale=1.0):
        x, y = self.x, self.y

        glow = pygame.transform.smoothscale(
            self.glow, (int(520 * scale), int(520 * scale))
        )
        surface.blit(
            glow,
            (int(x - glow.get_width() / 2), int(y - glow.get_height() / 2))
        )

        # Animated corona particles.
        for p in self.particles:
            px = x + math.cos(p["a"]) * p["d"] * scale
            py = y + math.sin(p["a"]) * p["d"] * scale * 0.72
            fade = clamp(
                1.0 - (p["d"] - self.radius) / (self.radius * 2.1),
                0, 1
            )
            if fade <= 0:
                continue

            c = (
                255,
                int(135 + 105 * fade),
                int(50 + 115 * fade),
            )
            pygame.draw.circle(
                surface, c,
                (int(px), int(py)),
                max(1, int(p["size"] * scale))
            )

        r = max(4, int(self.radius * scale))

        # Outer corona rings.
        for n in range(5, 0, -1):
            rr = r + n * max(2, int(4 * scale))
            alpha = 8 + (5 - n) * 4
            ring = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(
                ring, (255, 180, 70, alpha),
                (rr + 2, rr + 2), rr
            )
            surface.blit(ring, (int(x - rr - 2), int(y - rr - 2)))

        # Solar disk.
        pygame.draw.circle(surface, (255, 165, 55), (int(x), int(y)), r)
        pygame.draw.circle(surface, (255, 205, 95), (int(x), int(y)), int(r * 0.93))
        pygame.draw.circle(surface, (255, 232, 155), (int(x), int(y)), int(r * 0.78))

        # Deterministic animated granulation.
        rng = random.Random(9000)
        for _ in range(max(25, int(75 * scale))):
            a = rng.random() * math.tau + self.rotation
            d = rng.random() * r * 0.72
            px = x + math.cos(a) * d
            py = y + math.sin(a) * d
            rr = rng.randint(1, max(1, int(3 * scale)))
            col = rng.choice([
                (255, 180, 65), (255, 210, 105), (255, 238, 160),
                (255, 196, 80)
            ])
            pygame.draw.circle(surface, col, (int(px), int(py)), rr)

        # Sunspots add visible surface structure.
        for spot in self.sunspots:
            a = spot["a"] + self.rotation * 0.45
            d = spot["d"] * scale
            px = x + math.cos(a) * d
            py = y + math.sin(a) * d * 0.85
            rr = max(1, int(spot["size"] * scale))
            pygame.draw.circle(surface, (190, 105, 40), (int(px), int(py)), rr)
            pygame.draw.circle(
                surface, (225, 145, 50),
                (int(px - rr * 0.25), int(py - rr * 0.20)),
                max(1, rr // 2)
            )

        # Bright central highlight.
        pygame.draw.circle(
            surface, (255, 248, 205),
            (int(x - r * 0.22), int(y - r * 0.24)),
            max(1, int(r * 0.12))
        )

        # Cinematic lens flare.
        flare = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for length, alpha, width in [(240, 10, 3), (150, 16, 2), (90, 25, 1)]:
            pygame.draw.line(
                flare, (255, 225, 165, alpha),
                (x - length, y), (x + length, y), width
            )
            pygame.draw.line(
                flare, (255, 225, 165, alpha),
                (x, y - length * 0.55),
                (x, y + length * 0.55), width
            )
        surface.blit(flare, (0, 0))


class Planet:
    """Planet with orbital movement, atmospheric glow, rings and moons."""

    def __init__(self, name, distance, size, color, orbit_speed,
                 tilt=0, rings=False, moons=0, has_atmosphere=False):
        self.name = name
        self.distance = distance
        self.size = size
        self.color = color
        self.orbit_speed = orbit_speed
        self.tilt = tilt
        self.rings = rings
        self.has_atmosphere = has_atmosphere
        self.angle = random.uniform(0, math.tau)
        self.rotation = random.uniform(0, math.tau)
        self.moons = []

        for i in range(moons):
            self.moons.append({
                "angle": random.uniform(0, math.tau),
                "speed": random.uniform(0.02, 0.06),
                "distance": self.size + 12 + i * 11,
                "size": random.uniform(1.5, 3.5),
                "color": random.choice([GRAY, WHITE, (200, 200, 180)])
            })

        self.trail = []
        self.max_trail = 120

    def update(self, dt):
        self.angle += self.orbit_speed * dt * 7
        self.rotation += dt * 0.35
        for moon in self.moons:
            moon["angle"] += moon["speed"] * dt * 7

        x, y = self.get_position()
        if not self.trail or math.hypot(x - self.trail[-1][0], y - self.trail[-1][1]) > 3:
            self.trail.append((x, y))
            if len(self.trail) > self.max_trail:
                self.trail.pop(0)

    def get_position(self):
        return (
            CENTER[0] + math.cos(self.angle) * self.distance,
            CENTER[1] + math.sin(self.angle) * self.distance * 0.60
        )

    def draw_orbit(self, surface, scale):
        points = []
        for i in range(120):
            a = i * math.tau / 120
            x = CENTER[0] + math.cos(a) * self.distance * scale
            y = CENTER[1] + math.sin(a) * self.distance * 0.60 * scale
            points.append((int(x), int(y)))
        if len(points) > 1:
            pygame.draw.lines(surface, (38, 45, 78), False, points, 1)

    def draw_trail(self, surface, scale):
        if len(self.trail) < 2:
            return
        pts = []
        for x, y in self.trail:
            sx = CENTER[0] + (x - CENTER[0]) * scale
            sy = CENTER[1] + (y - CENTER[1]) * scale
            pts.append((int(sx), int(sy)))
        pygame.draw.lines(surface, (55, 80, 130), False, pts, 1)

    def draw(self, surface, scale=1.0, time=0.0, selected=False):
        x, y = self.get_position()
        x = CENTER[0] + (x - CENTER[0]) * scale
        y = CENTER[1] + (y - CENTER[1]) * scale
        r = max(1, int(self.size * scale * (1.0 + 0.035 * math.sin(time * 0.8 + self.distance))))

        if r < 1:
            return

        # Selected target halo
        if selected:
            pulse = 1.0 + 0.10 * math.sin(time * 3)
            halo_r = int(r * 2.2 * pulse)
            halo = pygame.Surface((halo_r * 2 + 4, halo_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(halo, (100, 190, 255, 28),
                               (halo_r + 2, halo_r + 2), halo_r)
            pygame.draw.circle(halo, (120, 210, 255, 130),
                               (halo_r + 2, halo_r + 2), max(2, halo_r - 2), 1)
            surface.blit(halo, (int(x - halo_r - 2), int(y - halo_r - 2)))

        # Atmospheric rim
        if self.has_atmosphere and r >= 2:
            for n in range(3, 0, -1):
                rr = r + n * 3
                alpha = 14 * (4 - n)
                atmo = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(atmo, (80, 170, 255, alpha),
                                   (rr + 2, rr + 2), rr)
                surface.blit(atmo, (int(x - rr - 2), int(y - rr - 2)))

        # Rings behind the planet
        if self.rings and r >= 3:
            ring = pygame.Surface((r * 7 + 10, r * 4 + 10), pygame.SRCALPHA)
            cx, cy = ring.get_width() // 2, ring.get_height() // 2
            for i in range(8):
                rr = r + 8 + i * max(1, r // 5)
                pygame.draw.ellipse(
                    ring, (175, 175, 190, 35 + i * 4),
                    (cx - rr, cy - rr * 0.24, rr * 2, rr * 0.48), 1
                )
            surface.blit(ring, (int(x - ring.get_width() / 2),
                                int(y - ring.get_height() / 2)))

        pygame.draw.circle(surface, self.color, (int(x), int(y)), r)

        # Deterministic surface details
        if r >= 5:
            rng = random.Random(self.name)
            for _ in range(max(3, int(r * 0.65))):
                a = rng.random() * math.tau + self.rotation
                d = rng.random() * r * 0.70
                px = x + math.cos(a) * d
                py = y + math.sin(a) * d
                shade = rng.randint(20, 65)
                col = (
                    max(0, self.color[0] - shade),
                    max(0, self.color[1] - shade),
                    max(0, self.color[2] - shade)
                )
                pygame.draw.circle(surface, col, (int(px), int(py)),
                                   max(1, int(r * rng.uniform(0.08, 0.18))))

        # Thin illuminated atmospheric rim.
        if self.has_atmosphere and r >= 4:
            rim = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(
                rim, (100, 190, 255, 90),
                (r + 5 - int(r * 0.12), r + 5 - int(r * 0.10)),
                r + 2, max(1, int(r * 0.10))
            )
            surface.blit(rim, (int(x - r - 5), int(y - r - 5)))

        # Soft shadow
        if r >= 3:
            shadow = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(shadow, (0, 0, 0, 80),
                               (r + 2, r + 2), r)
            shadow_offset = int(r * 0.28)
            surface.blit(shadow, (int(x - r - 2 + shadow_offset),
                                  int(y - r - 2)))

        # Highlight
        if r >= 4:
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(x - r * 0.30), int(y - r * 0.30)),
                               max(1, int(r * 0.13)))

        # Moons
        for moon in self.moons:
            mx = x + math.cos(moon["angle"]) * moon["distance"] * scale
            my = y + math.sin(moon["angle"]) * moon["distance"] * 0.5 * scale
            mr = max(1, int(moon["size"] * scale))
            if -10 < mx < WIDTH + 10 and -10 < my < HEIGHT + 10:
                pygame.draw.circle(surface, moon["color"], (int(mx), int(my)), mr)


class AsteroidBelt:
    def __init__(self):
        self.asteroids = []
        for _ in range(450):
            self.asteroids.append({
                "angle": random.uniform(0, math.tau),
                "dist": random.uniform(180, 240),
                "size": random.uniform(0.7, 3.0),
                "speed": random.uniform(0.02, 0.05),
                "phase": random.uniform(0, math.tau)
            })

    def update(self, dt):
        for a in self.asteroids:
            a["angle"] += a["speed"] * dt * 5

    def draw(self, surface, scale, time):
        for a in self.asteroids:
            x = CENTER[0] + math.cos(a["angle"]) * a["dist"] * scale
            y = CENTER[1] + math.sin(a["angle"]) * a["dist"] * 0.60 * scale
            r = max(1, int(a["size"] * scale))
            if -5 < x < WIDTH + 5 and -5 < y < HEIGHT + 5:
                brightness = int(100 + 70 * (
                    0.5 + 0.5 * math.sin(time * 0.7 + a["phase"])
                ))
                pygame.draw.circle(surface, (brightness, brightness, brightness),
                                   (int(x), int(y)), r)


class KuiperBelt:
    """The Kuiper Belt - a vast ring of icy bodies beyond Neptune.
    
    Unlike the asteroid belt, the Kuiper Belt is:
    - Much wider (spanning ~30-50 AU in our scaled model)
    - More vertically dispersed (has thickness)
    - Contains mostly icy/blue-white objects
    - Has a more elliptical distribution with some clustering
    """
    
    def __init__(self):
        self.objects = []
        
        # The Kuiper Belt spans from about 550 to 750 in our scaled system
        # (Neptune is at 500, so this places it appropriately beyond)
        for _ in range(800):
            # Objects can be on slightly inclined orbits
            incline_factor = random.uniform(-0.3, 0.3)
            
            # More elliptical distribution - some objects cluster in certain regions
            # This mimics the actual non-uniform distribution of the Kuiper Belt
            if random.random() < 0.3:
                # Some objects in the "classical" Kuiper Belt region
                dist = random.uniform(560, 620)
            elif random.random() < 0.5:
                # Scattered disk objects
                dist = random.uniform(620, 720)
            else:
                # Outer edge and general population
                dist = random.uniform(530, 750)
            
            # Objects can have varying eccentricities
            eccentricity = random.uniform(0.0, 0.15)
            
            # Determine object color - mostly icy blues, whites, and pale grays
            color_choice = random.random()
            if color_choice < 0.4:
                color = (180, 200, 230)  # icy blue
            elif color_choice < 0.65:
                color = (200, 210, 220)  # pale gray-blue
            elif color_choice < 0.85:
                color = (160, 180, 210)  # darker icy blue
            else:
                color = (220, 215, 200)  # warm icy (slightly reddish)
            
            self.objects.append({
                "angle": random.uniform(0, math.tau),
                "dist": dist,
                "eccentricity": eccentricity,
                "inclination": incline_factor,
                "size": random.uniform(0.5, 2.5),
                "speed": random.uniform(0.008, 0.025),  # Slower than inner planets
                "phase": random.uniform(0, math.tau),
                "color": color,
                "brightness": random.randint(100, 200),
                # Some objects have a slight "wobble" for visual interest
                "wobble_speed": random.uniform(0.1, 0.5),
                "wobble_phase": random.uniform(0, math.tau),
                "wobble_amplitude": random.uniform(0.5, 3.0),
            })
        
        # Add some larger "dwarf planet" candidates (like Pluto, Eris, etc.)
        self.dwarf_candidates = []
        for _ in range(15):
            dist = random.uniform(540, 720)
            self.dwarf_candidates.append({
                "angle": random.uniform(0, math.tau),
                "dist": dist,
                "size": random.uniform(4, 8),
                "speed": random.uniform(0.008, 0.018),
                "color": random.choice([
                    (190, 180, 170), (210, 200, 190), (180, 195, 210),
                    (170, 160, 150), (200, 190, 180)
                ]),
                "phase": random.uniform(0, math.tau),
            })
    
    def update(self, dt):
        for obj in self.objects:
            obj["angle"] += obj["speed"] * dt * 5
            # Some objects have slight orbital wobble
            obj["dist"] += math.sin(obj["wobble_speed"] * dt + obj["wobble_phase"]) * obj["wobble_amplitude"] * dt * 0.1
        
        for obj in self.dwarf_candidates:
            obj["angle"] += obj["speed"] * dt * 5
    
    def draw(self, surface, scale, time):
        # Draw the main Kuiper Belt population
        for obj in self.objects:
            # Apply eccentricity to the orbit
            angle_offset = obj["eccentricity"] * math.sin(obj["angle"] * 2)
            
            x = CENTER[0] + math.cos(obj["angle"] + angle_offset) * obj["dist"] * scale
            y = CENTER[1] + math.sin(obj["angle"] + angle_offset) * obj["dist"] * 0.60 * scale
            
            # Add vertical displacement for the belt's thickness
            y += obj["inclination"] * obj["dist"] * 0.1 * scale
            
            r = max(1, int(obj["size"] * scale))
            
            if -10 < x < WIDTH + 10 and -10 < y < HEIGHT + 10:
                # Some objects twinkle like stars
                twinkle = 0.85 + 0.15 * math.sin(time * 0.5 + obj["phase"])
                brightness = int(obj["brightness"] * twinkle)
                
                color = (
                    min(255, int(obj["color"][0] * brightness / 200)),
                    min(255, int(obj["color"][1] * brightness / 200)),
                    min(255, int(obj["color"][2] * brightness / 200))
                )
                
                pygame.draw.circle(surface, color, (int(x), int(y)), r)
                
                # Small glow for larger objects
                if r >= 2:
                    glow_alpha = 10 + r * 2
                    glow = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
                    pygame.draw.circle(
                        glow, (*color, min(40, glow_alpha)),
                        (r * 3, r * 3), r * 2
                    )
                    surface.blit(glow, (int(x - r * 3), int(y - r * 3)))
        
        # Draw dwarf planet candidates
        for obj in self.dwarf_candidates:
            x = CENTER[0] + math.cos(obj["angle"]) * obj["dist"] * scale
            y = CENTER[1] + math.sin(obj["angle"]) * obj["dist"] * 0.60 * scale
            
            r = max(2, int(obj["size"] * scale))
            
            if -10 < x < WIDTH + 10 and -10 < y < HEIGHT + 10:
                # Larger, brighter objects
                glow_r = r * 3
                glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow, (*obj["color"], 30),
                    (glow_r, glow_r), glow_r
                )
                surface.blit(glow, (int(x - glow_r), int(y - glow_r)))
                
                pygame.draw.circle(surface, obj["color"], (int(x), int(y)), r)
                
                # Tiny highlight
                if r >= 3:
                    pygame.draw.circle(
                        surface, (255, 255, 255, 80),
                        (int(x - r * 0.3), int(y - r * 0.3)),
                        max(1, r // 3)
                    )
    
    def draw_outer_ring(self, surface, scale, time):
        """Draw a faint, almost invisible ring to show the extent of the belt."""
        # Inner edge
        pts_inner = []
        # Outer edge
        pts_outer = []
        
        for i in range(60):
            a = i * math.tau / 60
            # Inner edge of the belt (approximate)
            x1 = CENTER[0] + math.cos(a) * 530 * scale
            y1 = CENTER[1] + math.sin(a) * 530 * 0.60 * scale
            pts_inner.append((int(x1), int(y1)))
            
            # Outer edge
            x2 = CENTER[0] + math.cos(a) * 750 * scale
            y2 = CENTER[1] + math.sin(a) * 750 * 0.60 * scale
            pts_outer.append((int(x2), int(y2)))
        
        if len(pts_inner) > 1:
            # Draw as a very faint ring
            for i in range(len(pts_inner)):
                pygame.draw.line(
                    surface, (40, 60, 90, 20),
                    pts_inner[i], pts_outer[i], 1
                )
            
            pygame.draw.lines(surface, (40, 60, 90, 30), False, pts_inner, 1)
            pygame.draw.lines(surface, (40, 60, 90, 30), False, pts_outer, 1)


class Voyager:
    """Voyager spacecraft that smoothly follows the selected planet.

    The trail is intentionally temporary: old points fade away instead of
    remaining on screen permanently.
    """

    def __init__(self):
        self.x, self.y = CENTER
        self.angle = 0.0
        self.speed = 0.5
        self.trail = []
        self.max_trail = 45
        self.golden_record = True

    def update(self, target_x, target_y, dt):
        # Same smooth "move toward target" behavior as the original version.
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist > 10:
            self.x += dx * 0.02 * dt * 60
            self.y += dy * 0.02 * dt * 60
            self.angle = math.atan2(dy, dx)

            # Short-lived motion trail.
            if not self.trail or math.hypot(
                self.x - self.trail[-1][0],
                self.y - self.trail[-1][1]
            ) > 3:
                self.trail.append((self.x, self.y))

        # Keep only a short history so the trail disappears behind Voyager.
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    def draw(self, surface, time, scale=1.0):
        # Draw the temporary trail using ONE surface per frame.
        # The old version created a full 1600x800 alpha surface for every
        # trail segment, which caused severe stuttering.
        if len(self.trail) > 1:
            trail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

            for i in range(len(self.trail) - 1):
                x1, y1 = self.trail[i]
                x2, y2 = self.trail[i + 1]

                sx1 = CENTER[0] + (x1 - CENTER[0]) * scale
                sy1 = CENTER[1] + (y1 - CENTER[1]) * scale
                sx2 = CENTER[0] + (x2 - CENTER[0]) * scale
                sy2 = CENTER[1] + (y2 - CENTER[1]) * scale

                fade = (i + 1) / len(self.trail)
                alpha = int(65 * fade)

                if alpha > 0:
                    pygame.draw.line(
                        trail_surf,
                        (65, 145, 220, alpha),
                        (int(sx1), int(sy1)),
                        (int(sx2), int(sy2)),
                        max(1, int(scale))
                    )

            surface.blit(trail_surf, (0, 0))

        x = CENTER[0] + (self.x - CENTER[0]) * scale
        y = CENTER[1] + (self.y - CENTER[1]) * scale

        pulse = 1 + 0.2 * math.sin(time * 5)
        glow_r = max(4, int(15 * scale * pulse))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (80, 190, 255, 55),
                           (glow_r, glow_r), glow_r)
        surface.blit(glow, (int(x - glow_r), int(y - glow_r)))

        points = []
        for off in (0, 120, 240):
            a = self.angle + math.radians(off)
            points.append((
                int(x + math.cos(a) * 8 * scale),
                int(y + math.sin(a) * 8 * scale)
            ))
        if len(points) >= 3:
            pygame.draw.polygon(surface, (200, 220, 255), points)

        pygame.draw.circle(
            surface, GOLD, (int(x), int(y)), max(1, int(3 * scale))
        )

        end_x = x + math.cos(self.angle - math.pi / 2) * 15 * scale
        end_y = y + math.sin(self.angle - math.pi / 2) * 15 * scale
        pygame.draw.line(
            surface, (170, 170, 180),
            (int(x), int(y)), (int(end_x), int(end_y)),
            max(1, int(scale))
        )


class CosmicScale:
    def __init__(self):
        self.scale = 1.0
        self.target_scale = 1.0
        self.min_scale = 0.12  # Allow zooming out further to see the Kuiper Belt
        self.max_scale = 2.8

    def update(self, dt):
        self.scale += (self.target_scale - self.scale) * min(1, dt * 5)

    def zoom_in(self):
        self.target_scale = min(self.max_scale, self.target_scale * 1.28)

    def zoom_out(self):
        self.target_scale = max(self.min_scale, self.target_scale / 1.28)

    def reset(self):
        self.target_scale = 1.0


class Dashboard:
    def __init__(self):
        self.font_small = pygame.font.Font(None, 19)
        self.font_medium = pygame.font.Font(None, 27)
        self.font_big = pygame.font.Font(None, 34)
        self.visible = True

    def draw(self, surface, time, planet_name, distance, speed, scale):
        panel = pygame.Surface((310, 218), pygame.SRCALPHA)
        panel.fill((4, 8, 28, 195))
        pygame.draw.rect(panel, (55, 90, 145, 150),
                         (0, 0, 309, 217), 1)
        surface.blit(panel, (14, 14))

        title = self.font_medium.render("VOYAGER TELECOM", True, (110, 205, 255))
        surface.blit(title, (28, 27))

        pygame.draw.line(surface, (45, 80, 125),
                         (28, 58), (302, 58), 1)

        signal = int(70 + 30 * math.sin(time * 0.8))
        data = [
            ("TARGET", planet_name),
            ("DISTANCE", f"{distance:.2f} AU"),
            ("VELOCITY", f"{speed:.1f} km/s"),
            ("MISSION", f"{int(time / 3.0):06d} DAYS"),
            ("SIGNAL", f"{signal}%"),
            ("ZOOM", f"{scale:.2f}x"),
        ]

        y = 73
        for label, value in data:
            a = self.font_small.render(f"{label:<9}", True, (105, 135, 175))
            b = self.font_small.render(value, True, (165, 215, 255))
            surface.blit(a, (28, y))
            surface.blit(b, (125, y))
            y += 22

        # Status light
        pulse = 100 + int(70 * (0.5 + 0.5 * math.sin(time * 3)))
        pygame.draw.circle(surface, (40, pulse, 110), (283, 36), 4)

        status = self.font_small.render("STATUS: NOMINAL", True, (100, 220, 145))
        surface.blit(status, (170, 185))


def draw_scanlines(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(overlay, (10, 20, 40, 10),
                         (0, y), (WIDTH, y))
    surface.blit(overlay, (0, 0))


def draw_vignette(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # Border darkening, kept subtle so the scene remains visible.
    for i in range(14):
        alpha = int(2 + i * 1.5)
        pygame.draw.rect(
            overlay, (0, 0, 8, alpha),
            (i * 4, i * 4, WIDTH - i * 8, HEIGHT - i * 8), 4
        )
    surface.blit(overlay, (0, 0))


def draw_title(surface, font, current_planet, time):
    title = font.render("VOYAGER'S VIEW", True, (110, 190, 255))
    surface.blit(title, (WIDTH - title.get_width() - 25, 22))

    sub = pygame.font.Font(None, 18).render(
        f"DEEP SPACE OBSERVATION  //  TARGET: {current_planet.upper()}",
        True, (85, 110, 150)
    )
    surface.blit(sub, (WIDTH - sub.get_width() - 25, 47))


def main():
    running = True
    time = 0.0

    star_field = StarField(700)
    nebula = Nebula()
    sun = Sun()

    planets = [
        Planet("Mercury", 70, 8, (180, 180, 180), 0.04, 0.1, False, 0, False),
        Planet("Venus", 110, 12, (220, 200, 170), 0.03, 177, False, 0, True),
        Planet("Earth", 155, 13, (70, 150, 220), 0.025, 23, False, 1, True),
        Planet("Mars", 200, 10, (200, 100, 70), 0.02, 25, False, 2, True),
        Planet("Jupiter", 280, 30, (200, 170, 130), 0.015, 3, True, 4, True),
        Planet("Saturn", 360, 25, (210, 190, 170), 0.01, 27, True, 5, True),
        Planet("Uranus", 430, 18, (150, 210, 230), 0.008, 98, True, 3, True),
        Planet("Neptune", 500, 17, (70, 70, 200), 0.006, 28, True, 2, True),
    ]

    asteroid_belt = AsteroidBelt()
    kuiper_belt = KuiperBelt()  # Add the Kuiper Belt
    voyager = Voyager()
    current_target = 2  # Start at Earth — feels more like Voyager's departure point.
    dashboard = Dashboard()
    cosmic_scale = CosmicScale()

    font_label = pygame.font.Font(None, 18)
    font_title = pygame.font.Font(None, 30)
    tutorial_font = pygame.font.Font(None, 22)
    tutorial_title = pygame.font.Font(None, 34)

    tutorial_time = 0.0
    show_tutorial = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    current_target = (current_target + 1) % len(planets)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    cosmic_scale.zoom_in()
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    cosmic_scale.zoom_out()
                elif event.key == pygame.K_r:
                    cosmic_scale.reset()
                elif event.key == pygame.K_d:
                    dashboard.visible = not dashboard.visible
                elif event.key == pygame.K_h:
                    show_tutorial = not show_tutorial

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    cosmic_scale.zoom_in()
                elif event.button == 5:
                    cosmic_scale.zoom_out()

        if show_tutorial:
            tutorial_time += dt
            if tutorial_time > 9:
                show_tutorial = False

        cosmic_scale.update(dt)
        scale = cosmic_scale.scale

        star_field.update(dt, time)
        sun.update(dt, time)

        for planet in planets:
            planet.update(dt)

        asteroid_belt.update(dt)
        kuiper_belt.update(dt)  # Update the Kuiper Belt

        target = planets[current_target]
        target_x, target_y = target.get_position()
        voyager.update(target_x, target_y, dt)

        # ------------------- RENDER -------------------
        screen.fill((1, 2, 10))

        nebula.draw(screen, time)
        star_field.draw(screen, time, 0, 0)

        # Extremely subtle blue space haze keeps the background from looking flat.
        haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(4):
            margin = i * 35
            pygame.draw.rect(
                haze, (20, 45, 95, 3),
                (margin, margin, WIDTH - margin * 2, HEIGHT - margin * 2), 28
            )
        screen.blit(haze, (0, 0))

        # Orbits become clearer as you zoom out.
        for planet in planets:
            if scale < 1.15:
                planet.draw_orbit(screen, scale)
            planet.draw_trail(screen, scale)

        asteroid_belt.draw(screen, scale, time)
        
        # Draw the Kuiper Belt - only visible when zoomed out enough
        if scale < 0.9:
            kuiper_belt.draw_outer_ring(screen, scale, time)
        kuiper_belt.draw(screen, scale, time)
        
        sun.draw(screen, time, scale)

        for i, planet in enumerate(planets):
            planet.draw(
                screen, scale, time,
                selected=(i == current_target)
            )

        voyager.draw(screen, time, scale)

        # Planet labels become useful without cluttering the normal view.
        if scale > 1.25:
            for planet in planets:
                x, y = planet.get_position()
                x = CENTER[0] + (x - CENTER[0]) * scale
                y = CENTER[1] + (y - CENTER[1]) * scale
                if -100 < x < WIDTH + 100 and -100 < y < HEIGHT + 100:
                    label = font_label.render(
                        planet.name.upper(), True,
                        (120, 145, 190) if planet != target else (150, 220, 255)
                    )
                    screen.blit(label, (int(x - label.get_width() / 2),
                                        int(y + planet.size * scale + 8)))
        
        # Label for Kuiper Belt when zoomed out
        if scale < 0.8:
            kb_label = font_label.render("KUIPER BELT", True, (80, 120, 180))
            kb_x = CENTER[0] + 640 * scale
            kb_y = CENTER[1] + 0 * scale
            screen.blit(kb_label, (int(kb_x - kb_label.get_width() / 2), 
                                   int(kb_y + 30)))

        if dashboard.visible:
            dist_au = target.distance / 150
            speed = 15 + 2.5 * math.sin(time * 0.08)
            dashboard.draw(screen, time, target.name, dist_au, speed, scale)

        draw_title(screen, font_title, target.name, time)

        # Minimal bottom control bar
        control = "SPACE  TARGET     W/UP  ZOOM IN     S/DOWN  ZOOM OUT     R  RESET     D  TELEMETRY     H  HELP"
        control_text = font_label.render(control, True, (75, 95, 130))
        screen.blit(
            control_text,
            (WIDTH // 2 - control_text.get_width() // 2, HEIGHT - 25)
        )

        # Intro overlay: fades away rather than abruptly disappearing.
        if show_tutorial:
            fade = 1.0
            if tutorial_time > 5:
                fade = 1.0 - smoothstep((tutorial_time - 5) / 4)

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 10, int(105 * fade)))

            box_w, box_h = 570, 210
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box.fill((3, 8, 25, int(215 * fade)))
            pygame.draw.rect(
                box, (70, 125, 190, int(150 * fade)),
                (0, 0, box_w - 1, box_h - 1), 1
            )
            overlay.blit(box, (WIDTH // 2 - box_w // 2,
                               HEIGHT // 2 - box_h // 2))

            title = tutorial_title.render(
                "VOYAGER'S VIEW", True, (125, 205, 255)
            )
            title.set_alpha(int(255 * fade))
            overlay.blit(title, (
                WIDTH // 2 - title.get_width() // 2,
                HEIGHT // 2 - 82
            ))

            instructions = [
                "A CINEMATIC JOURNEY THROUGH THE SOLAR SYSTEM",
                "",
                "SPACE  —  Cycle target planets",
                "W / UP / SCROLL  —  Zoom in",
                "S / DOWN / SCROLL  —  Zoom out",
                "D  —  Telemetry     H  —  Toggle help"
            ]

            for i, text in enumerate(instructions):
                rendered = tutorial_font.render(
                    text, True,
                    (145, 165, 195) if i else (90, 125, 165)
                )
                rendered.set_alpha(int(255 * fade))
                overlay.blit(rendered, (
                    WIDTH // 2 - rendered.get_width() // 2,
                    HEIGHT // 2 - 35 + i * 27
                ))

            screen.blit(overlay, (0, 0))

        draw_scanlines(screen)
        draw_vignette(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()