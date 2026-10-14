"""Plot admitted finite counts and work; no experiment or inferred missing values."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator


def main():
    base = Path(__file__).resolve().parent
    admission = json.loads((base / "proof/admission.json").read_text())
    arms = admission["arms"]
    colors = {"shooting": "#326784", "forward": "#ad603b"}
    labels = {"shooting": "Centered shooting", "forward": "Forward proposals"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axs = plt.subplots(2, 2, figsize=(12, 7.5))
    fig.patch.set_facecolor("#fafaf7")
    for ax in axs.flat:
        ax.set_facecolor("#fafaf7")
        ax.spines[["top", "right"]].set_visible(False)
    for index, arm in enumerate(["shooting", "forward"]):
        offset = (-.18 if index == 0 else .18)
        vals = [arms[arm]["admissible_requests"], arms[arm]["improved_requests"]]
        bars = axs[0, 0].bar([offset, 1+offset], vals, .34, color=colors[arm], label=labels[arm])
        axs[0, 0].bar_label(bars, padding=3)
        bars = axs[0, 1].bar(index, arms[arm]["constructive_complete"], .6, color=colors[arm])
        axs[0, 1].bar_label(bars, padding=3)
        request_rows = [r for r in admission["records"] if r["population"] == "request" and r["arm"] == arm]
        counts = [sum(r["metrics"]["cost_curve"][j]["improved"] for r in request_rows) for j in range(4)]
        axs[1, 0].plot([128, 256, 512, 1024], counts, "o-", color=colors[arm], label=labels[arm])
        work = [sum(r["attempts"] for r in admission["records"]
                    if r["arm"] == arm and r["population"] == pop)
                for pop in ["request", "constructive"]]
        bars = axs[1, 1].bar([offset, 1+offset], work, .34, color=colors[arm])
        axs[1, 1].bar_label(bars, labels=[f"{value:,}" for value in work], padding=3)
    axs[0, 0].set(xticks=[0, 1], xticklabels=["Admissible return", "Target distance improves"],
                  ylim=(0, 90), ylabel="Requests out of 80", title="Returned motion under matched per-request caps")
    axs[0, 0].legend(frameon=False, fontsize=9, loc="upper left")
    axs[0, 1].axhline(14, linestyle="--", color="#667078", linewidth=1)
    axs[0, 1].set(xticks=[0, 1], xticklabels=list(labels.values()), ylim=(0, 16),
                  ylabel="Completed tasks out of 14", title="Full stop, wait, turn and detour controls")
    axs[1, 0].set(xscale="log", xticks=[128, 256, 512, 1024],
                  xticklabels=["128", "256", "512", "1,024"], ylim=(0, 85),
                  xlabel="Available transitions, clipped to each request's original cap",
                  ylabel="Requests with improved target distance", title="Only complete evaluations within each budget count")
    axs[1, 0].xaxis.set_minor_locator(NullLocator())
    axs[1, 1].set(xticks=[0, 1], xticklabels=["Retained requests", "Constructed tasks"],
                  ylabel="Attempted transitions", title="Actual work differs between populations")
    axs[1, 1].set_ylim(0, max(a["attempts"] for a in arms.values())*1.2)
    axs[1, 1].ticklabel_format(axis="y", style="plain")
    fig.suptitle("Shooting versus bounded forward-control proposals", fontsize=18, y=.98)
    fig.text(.06, .025, "Iter173 · Exposed requests and constructed tasks. Equal caps are not equal wall time. "
             "No integrated or source recovery claim.", fontsize=10, color="#465057")
    fig.subplots_adjust(left=.08, right=.97, top=.89, bottom=.14, hspace=.48, wspace=.27)
    fig.savefig(base / "proof/comparison.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
