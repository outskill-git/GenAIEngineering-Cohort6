"""Build the Lumio Solar field-service knowledge base used by the multimodal RAG notebook.

Deterministic: same seed, same corpus. Produces
    corpus/images/*.png      manual pages, charts, labels, equipment photos
    corpus/docs/*.md         the text-only knowledge base (the RAG baseline)
    corpus/video/*.mp4       a short training video, plus its transcript
    corpus/manifest.json     what each asset is (ground truth, for evaluation)

Some facts live ONLY in an image or ONLY in the video. That is the point of the session.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).parent / "corpus"
IMG, DOC, VID = OUT / "images", OUT / "docs", OUT / "video"
for d in (IMG, DOC, VID):
    d.mkdir(parents=True, exist_ok=True)

NAVY, INK, ACC = "#1a2332", "#2d3748", "#2b6cb0"
manifest = []


def save(fig, name, kind, caption_truth, holds_fact=None):
    fig.savefig(IMG / name, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    manifest.append({"asset": f"images/{name}", "modality": "image", "kind": kind,
                     "ground_truth": caption_truth, "unique_fact": holds_fact})


# ---------------------------------------------------------------- 1. performance charts
def chart_normal():
    fig, ax = plt.subplots(figsize=(6, 3.4))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ax.bar(days, [21.4, 20.8, 21.9, 20.1, 21.2, 19.8, 20.6], color=ACC)
    ax.set_title("Site PUN-114 — daily yield, week of 3 Aug 2026", fontsize=11)
    ax.set_ylabel("kWh"); ax.set_ylim(0, 26); ax.grid(axis="y", alpha=.25)
    save(fig, "chart_yield_normal.png", "performance chart",
         "Bar chart of daily solar yield for site PUN-114, all days around 20-22 kWh, no fault.")


def chart_fault():
    fig, ax = plt.subplots(figsize=(6, 3.4))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    vals = [21.1, 20.4, 4.2, 5.1, 20.8, 21.3, 20.9]
    bars = ax.bar(days, vals, color=[ACC if v > 10 else "#c53030" for v in vals])
    ax.set_title("Site PUN-114 — daily yield, week of 10 Aug 2026", fontsize=11)
    ax.set_ylabel("kWh"); ax.set_ylim(0, 26); ax.grid(axis="y", alpha=.25)
    ax.annotate("string 2 offline", xy=(2.5, 5), xytext=(3.4, 14), fontsize=10, color="#c53030",
                arrowprops=dict(arrowstyle="->", color="#c53030"))
    save(fig, "chart_yield_fault.png", "performance chart",
         "Bar chart of daily yield for site PUN-114 week of 10 Aug 2026 showing a sharp drop to "
         "4.2 kWh on Wednesday and 5.1 kWh on Thursday, annotated 'string 2 offline'.",
         "Yield collapsed to 4.2 kWh on Wednesday 12 Aug 2026 because string 2 went offline.")


def chart_shading():
    fig, ax = plt.subplots(figsize=(6, 3.4))
    h = np.arange(6, 19)
    clear = np.clip(-0.09 * (h - 12.5) ** 2 + 4.2, 0, None)
    shaded = clear.copy(); shaded[9:12] *= 0.35
    ax.plot(h, clear, label="expected", color=ACC, lw=2)
    ax.plot(h, shaded, label="measured", color="#c53030", lw=2, ls="--")
    ax.fill_between(h[9:12], shaded[9:12], clear[9:12], color="#c53030", alpha=.2)
    ax.set_title("Site BLR-207 — power curve, 14 Aug 2026", fontsize=11)
    ax.set_xlabel("hour of day"); ax.set_ylabel("kW"); ax.legend(fontsize=9); ax.grid(alpha=.25)
    save(fig, "chart_shading_signature.png", "performance chart",
         "Line chart comparing expected and measured power across the day for site BLR-207; the "
         "measured curve dips sharply between 15:00 and 17:00, the signature of afternoon shading.",
         "Afternoon shading at BLR-207 appears as a dip between 15:00 and 17:00, not a whole-day loss.")


# ---------------------------------------------------------------- 2. error-code label
def error_label():
    fig, ax = plt.subplots(figsize=(5.2, 3.6)); ax.axis("off")
    fig.patch.set_facecolor("#f7f5ef")
    ax.add_patch(mpatches.FancyBboxPatch((0.04, 0.05), 0.92, 0.9, boxstyle="round,pad=0.02",
                                         fc="white", ec=INK, lw=2))
    ax.text(0.5, 0.88, "LUMIO INVERTER — FAULT CODES", ha="center", fontsize=11, weight="bold", color=INK)
    rows = [("E-12", "Grid voltage out of range"), ("E-19", "Isolation resistance low"),
            ("E-27", "String 2 input current zero"), ("E-33", "Over-temperature, derating"),
            ("E-41", "Fan failure")]
    for i, (code, meaning) in enumerate(rows):
        y = 0.72 - i * 0.125
        ax.text(0.10, y, code, fontsize=11, weight="bold", family="monospace",
                color="#c53030" if code == "E-27" else INK)
        ax.text(0.30, y, meaning, fontsize=10, color=INK)
    ax.text(0.5, 0.10, "Part no. LMO-INV-5K  ·  sticker inside the front cover", ha="center",
            fontsize=8, color="#718096")
    save(fig, "label_fault_codes.png", "equipment label",
         "Photograph of the fault-code sticker inside a Lumio inverter cover, listing E-12 grid "
         "voltage out of range, E-19 isolation resistance low, E-27 string 2 input current zero, "
         "E-33 over-temperature derating, E-41 fan failure.",
         "Error code E-27 means string 2 input current is zero.")


# ---------------------------------------------------------------- 3. wiring diagram
def wiring():
    fig, ax = plt.subplots(figsize=(6.2, 3.8)); ax.axis("off")
    fig.patch.set_facecolor("white")
    for i in range(3):
        x = 0.06 + i * 0.13
        ax.add_patch(mpatches.Rectangle((x, 0.62), 0.11, 0.22, fc="#1a2332", ec=INK))
        ax.text(x + 0.055, 0.73, f"PV{i+1}", color="white", ha="center", va="center", fontsize=8)
        ax.plot([x + 0.11, 0.52], [0.73, 0.52], color=INK, lw=1.2)
    ax.add_patch(mpatches.Rectangle((0.52, 0.38), 0.18, 0.28, fc="#e2e8f0", ec=INK, lw=1.5))
    ax.text(0.61, 0.52, "String\ncombiner", ha="center", va="center", fontsize=9)
    ax.plot([0.70, 0.80], [0.52, 0.52], color=INK, lw=1.5)
    ax.add_patch(mpatches.Rectangle((0.80, 0.34), 0.15, 0.36, fc="#bee3f8", ec=INK, lw=1.5))
    ax.text(0.875, 0.52, "Inverter\nLMO-5K", ha="center", va="center", fontsize=9)
    ax.annotate("DC terminals:\ntorque to 4.5 Nm", xy=(0.80, 0.44), xytext=(0.47, 0.14),
                fontsize=9, color="#c53030",
                arrowprops=dict(arrowstyle="->", color="#c53030"))
    ax.text(0.5, 0.95, "Figure 4.2 — DC side wiring, 3-string residential", ha="center",
            fontsize=10, weight="bold", color=INK)
    save(fig, "diagram_dc_wiring.png", "wiring diagram",
         "Wiring diagram figure 4.2 showing three PV strings into a string combiner and then the "
         "Lumio LMO-5K inverter, with a callout that the DC terminals must be torqued to 4.5 Nm.",
         "The inverter DC terminals must be torqued to 4.5 Nm.")


# ---------------------------------------------------------------- 4. spec sheet page
def spec_page():
    fig, ax = plt.subplots(figsize=(5.0, 6.2)); ax.axis("off")
    fig.patch.set_facecolor("#fdfdfd")
    ax.text(0.5, 0.96, "LUMIO LMO-INV-5K", ha="center", fontsize=13, weight="bold", color=INK)
    ax.text(0.5, 0.925, "Technical specification — sheet 1 of 2", ha="center", fontsize=9, color="#718096")
    specs = [("Rated AC output", "5.0 kW"), ("Max DC input voltage", "600 V"),
             ("MPPT range", "120 – 500 V"), ("Max input current per string", "13 A"),
             ("Number of MPP trackers", "2"), ("Efficiency (Euro)", "97.2 %"),
             ("Protection rating", "IP65"), ("Operating temperature", "-25 °C to +60 °C"),
             ("Warranty", "7 years standard, extendable to 12")]
    for i, (k, v) in enumerate(specs):
        y = 0.85 - i * 0.07
        ax.text(0.08, y, k, fontsize=9.5, color=INK)
        ax.text(0.92, y, v, fontsize=9.5, color=INK, ha="right", weight="bold")
        ax.plot([0.08, 0.92], [y - 0.022, y - 0.022], color="#e2e8f0", lw=0.8)
    ax.text(0.5, 0.12, "Max DC input voltage must never be exceeded, including at\n"
                       "cold-morning open-circuit voltage.", ha="center", fontsize=8.5, color="#c53030")
    save(fig, "page_spec_inverter.png", "spec sheet page",
         "Scanned specification sheet for the Lumio LMO-INV-5K inverter: 5.0 kW rated AC output, "
         "600 V maximum DC input, MPPT range 120-500 V, 13 A per string, IP65, 7 year warranty.",
         "The LMO-INV-5K maximum DC input voltage is 600 V and warranty is 7 years.")


# ---------------------------------------------------------------- 5. equipment 'photos'
def equipment(name, kind, truth, draw):
    fig, ax = plt.subplots(figsize=(4.6, 3.4)); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    draw(ax)
    save(fig, name, kind, truth)


def draw_array(ax):
    ax.add_patch(mpatches.Rectangle((0, 0), 1, 0.42, fc="#8fae6b"))
    ax.add_patch(mpatches.Rectangle((0, 0.42), 1, 0.58, fc="#9fc5e8"))
    for r in range(2):
        for c in range(4):
            ax.add_patch(mpatches.Rectangle((0.06 + c * 0.22, 0.30 + r * 0.17), 0.19, 0.14,
                                            fc="#1a2744", ec="#cbd5e0", lw=1.2))
    ax.text(0.5, 0.06, "rooftop array, 8 panels", ha="center", fontsize=8, color="#2d3748")


def draw_connector_ok(ax):
    ax.add_patch(mpatches.Rectangle((0, 0), 1, 1, fc="#edf2f7"))
    ax.add_patch(mpatches.FancyBboxPatch((0.18, 0.42), 0.3, 0.16, boxstyle="round,pad=0.01",
                                         fc="#1a2332", ec="#000"))
    ax.add_patch(mpatches.FancyBboxPatch((0.52, 0.42), 0.3, 0.16, boxstyle="round,pad=0.01",
                                         fc="#1a2332", ec="#000"))
    ax.plot([0.48, 0.52], [0.5, 0.5], color="#000", lw=3)
    ax.text(0.5, 0.26, "MC4 connector pair, mated", ha="center", fontsize=9, color="#2d3748")


def draw_connector_burnt(ax):
    ax.add_patch(mpatches.Rectangle((0, 0), 1, 1, fc="#edf2f7"))
    ax.add_patch(mpatches.FancyBboxPatch((0.18, 0.42), 0.3, 0.16, boxstyle="round,pad=0.01",
                                         fc="#1a2332", ec="#000"))
    ax.add_patch(mpatches.FancyBboxPatch((0.52, 0.42), 0.3, 0.16, boxstyle="round,pad=0.01",
                                         fc="#3b2412", ec="#000"))
    ax.add_patch(mpatches.Circle((0.52, 0.5), 0.07, fc="#7b341e"))
    ax.add_patch(mpatches.Circle((0.52, 0.5), 0.04, fc="#1a202c"))
    ax.text(0.5, 0.26, "MC4 connector, burnt contact", ha="center", fontsize=9, color="#7b341e")


def draw_inverter(ax):
    ax.add_patch(mpatches.Rectangle((0, 0), 1, 1, fc="#e2e8f0"))
    ax.add_patch(mpatches.FancyBboxPatch((0.28, 0.18), 0.44, 0.64, boxstyle="round,pad=0.02",
                                         fc="#f7fafc", ec="#4a5568", lw=2))
    ax.add_patch(mpatches.Rectangle((0.36, 0.6), 0.28, 0.12, fc="#1a2332"))
    ax.text(0.5, 0.66, "LUMIO", color="#63b3ed", ha="center", va="center", fontsize=8)
    for i in range(3):
        ax.add_patch(mpatches.Circle((0.4 + i * 0.1, 0.45), 0.025, fc="#48bb78" if i == 0 else "#cbd5e0"))
    ax.text(0.5, 0.1, "wall-mounted string inverter", ha="center", fontsize=8.5, color="#2d3748")


# ---------------------------------------------------------------- 6. text docs
DOCS = {
"install_overview.md": """# Lumio residential installation — overview

A standard residential installation is a rooftop array, a string combiner, a wall-mounted
string inverter and an AC isolator into the consumer unit. A two-person crew completes a
typical 5 kW system in a day.

Sequence: survey, mounting rails, panels, DC wiring, inverter mount, AC connection,
commissioning, customer handover. Commissioning writes the site id (for example PUN-114)
into the monitoring portal; from that point the site reports daily yield.

Do not energise the DC side before the inverter is mounted and earthed.
""",
"maintenance_schedule.md": """# Preventive maintenance schedule

| Interval | Task |
|---|---|
| Monthly (remote) | review the yield chart in the portal for unexplained drops |
| Six-monthly | visual inspection of array, mounts and cable runs |
| Annually | thermal scan of DC connectors, inverter fan clean, torque check on DC terminals |

A sustained drop in daily yield against the previous week is the single most useful remote
signal. Compare the same site week on week before dispatching a technician; weather explains
most differences, and a partial drop usually points at one string rather than the inverter.
""",
"safety_rules.md": """# DC safety rules

The DC side remains live whenever the array is illuminated. Switching off the AC isolator does
not make the array safe.

Before opening any enclosure: isolate AC, then isolate DC at the combiner, then confirm zero
voltage with a meter rated for the task. Use insulated tools. Never work on the roof alone.

Burnt or discoloured connectors must be replaced, never re-mated. A connector that has arced
once will arc again.
""",
"warranty_and_support.md": """# Warranty and support

Warranty claims require the site id, the inverter serial number, the fault code shown on the
display, and a photograph of the fault-code sticker inside the front cover.

Support tiers: remote triage within 4 working hours, on-site attendance within 2 working days
for a total outage, 5 working days for a partial loss of output.

Claims are refused where the installation does not follow the published wiring figures, where
torque specifications were not met, or where a connector shows evidence of re-mating after
arcing.
""",
}


# ---------------------------------------------------------------- 7. training video
def build_video():
    """Render a short training video frame by frame, with a timestamped transcript."""
    import shutil
    import subprocess
    import tempfile
    scenes = [
        (0,  "Replacing a Lumio string inverter", "Training module 7"),
        (6,  "Step 1 — isolate the AC supply", "Switch off and lock the AC isolator"),
        (14, "Step 2 — isolate the DC supply", "Open the string combiner isolator"),
        (22, "Step 3 — wait five minutes", "Capacitors inside the inverter stay charged"),
        (32, "Step 4 — confirm zero volts", "Meter across the DC terminals before opening"),
        (42, "Step 5 — release the DC connectors", "Use the MC4 release tool, never pliers"),
        (52, "Step 6 — unmount and replace", "Two M8 bolts hold the bracket"),
        (62, "Step 7 — torque the DC terminals", "4.5 Nm, checked with a torque driver"),
        (72, "Step 8 — re-energise in reverse order", "DC first, then AC, then check the portal"),
    ]
    transcript = [
        (0,  "Welcome to training module seven, replacing a Lumio string inverter."),
        (6,  "Step one. Switch off the AC isolator and lock it off before you touch anything."),
        (14, "Step two. Open the DC isolator at the string combiner."),
        (22, "Step three, and this is the one people skip. Wait five minutes after isolating "
             "before you open the inverter lid. The capacitors inside stay charged."),
        (32, "Step four. Confirm zero volts across the DC terminals with a meter rated for the job."),
        (42, "Step five. Release the MC4 connectors with the proper release tool. Never use pliers."),
        (52, "Step six. Two M8 bolts hold the bracket. Support the unit as you remove the second one."),
        (62, "Step seven. Torque the DC terminals to four point five newton metres with a torque driver."),
        (72, "Step eight. Re-energise in reverse order: DC first, then AC, then confirm the site "
             "is reporting in the portal."),
    ]
    dur = 82
    keyframes = VID / "keyframes"
    keyframes.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp())

    def render(t, path):
        scene = [sc for sc in scenes if sc[0] <= t][-1]
        fig, ax = plt.subplots(figsize=(6.4, 3.6)); ax.axis("off")
        fig.patch.set_facecolor("#0f1626")
        ax.add_patch(mpatches.Rectangle((0.04, 0.2), 0.92, 0.62, fc="#1a2332", ec="#2d4263"))
        ax.text(0.5, 0.66, scene[1], color="#e2e8f0", ha="center", fontsize=14, weight="bold")
        ax.text(0.5, 0.49, scene[2], color="#90cdf4", ha="center", fontsize=10)
        ax.text(0.06, 0.1, f"{t//60:02d}:{t%60:02d}", color="#718096", fontsize=9, family="monospace")
        ax.text(0.94, 0.1, "LUMIO TRAINING", color="#4a5568", fontsize=8, ha="right")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
        plt.close(fig)

    for i, t in enumerate(range(dur)):
        render(t, tmp / f"f{i:04d}.png")
    # one keyframe per scene, so the notebook works even without ffmpeg installed
    for t, _, _ in scenes:
        render(t, keyframes / f"t{t:03d}.png")

    mp4 = VID / "inverter_replacement.mp4"
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1",
                        "-i", str(tmp / "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-vf", "scale=640:-2", str(mp4)], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    json.dump([{"start_s": t, "text": txt} for t, txt in transcript],
              open(VID / "inverter_replacement_transcript.json", "w"), indent=2)
    manifest.append({"asset": "video/inverter_replacement.mp4", "modality": "video",
                     "kind": "training video", "duration_s": dur,
                     "ground_truth": "An eight-step training video on replacing a Lumio string inverter.",
                     "unique_fact": "You must wait five minutes after isolating before opening the "
                                    "inverter lid, because the capacitors stay charged."})


def main():
    chart_normal(); chart_fault(); chart_shading()
    error_label(); wiring(); spec_page()
    equipment("photo_rooftop_array.png", "equipment photo",
              "Photograph of a rooftop solar array of eight dark panels on a blue-sky day.", draw_array)
    equipment("photo_mc4_connector_ok.png", "equipment photo",
              "Close-up photograph of a healthy mated pair of black MC4 DC connectors.", draw_connector_ok)
    equipment("photo_mc4_connector_burnt.png", "equipment photo",
              "Close-up photograph of an MC4 connector with a burnt, blackened contact and scorching.",
              draw_connector_burnt)
    equipment("photo_inverter_unit.png", "equipment photo",
              "Photograph of a wall-mounted white Lumio string inverter with a green status light.",
              draw_inverter)
    for name, text in DOCS.items():
        (DOC / name).write_text(text)
        manifest.append({"asset": f"docs/{name}", "modality": "text", "kind": "manual page",
                         "ground_truth": text.splitlines()[0].lstrip("# "), "unique_fact": None})
    build_video()
    json.dump(manifest, open(OUT / "manifest.json", "w"), indent=2)
    print(f"images : {len(list(IMG.glob('*.png')))}")
    print(f"docs   : {len(list(DOC.glob('*.md')))}")
    print(f"video  : {len(list(VID.glob('*')))} files")
    print(f"facts that exist ONLY in an image or the video: "
          f"{sum(1 for m in manifest if m.get('unique_fact'))}")


if __name__ == "__main__":
    main()
